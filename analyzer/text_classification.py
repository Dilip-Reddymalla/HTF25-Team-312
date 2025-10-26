import json
import re
import io
import os
from typing import List, Dict, Any

# Optional heavy/third-party imports guarded so Django can start even if
# some developer dependencies are missing in the environment. Missing
# packages will be detected at runtime and fallbacks/errors will be used.
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except Exception:
    docx = None
    DOCX_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception:
    np = None
    NUMPY_AVAILABLE = False

try:
    import language_tool_python
    LANG_TOOL_AVAILABLE = True
except Exception:
    language_tool_python = None
    LANG_TOOL_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    util = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except Exception:
    convert_from_path = None
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    Image = None
    PIL_AVAILABLE = False

try:
    from google import genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

from django.conf import settings # Import Django settings

# --- Model Loading (Global) ---
# Load the model once when the app starts, not on every request
try:
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    else:
        EMBED_MODEL = None
    print("Embedding model loaded successfully.")
except Exception as e:
    print(f"Error loading embedding model: {e}")
    EMBED_MODEL = None

# --- Constants ---
ACTION_VERBS = {
    "achieved","improved","managed","led","created","designed","implemented","reduced","increased",
    "developed","engineered","launched","optimized","automated","orchestrated","resolved","boosted",
    "coordinated","spearheaded","delivered","built","founded","mentored","trained","negotiated"
}
REQUIRED_SECTIONS = ["+91","summary", "skills", "experience", "Projects", "education", "LinkedIn"]

# --- Helper Functions (Keep all your extract_... functions as they are) ---

def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []
    # Use POPPLER_PATH from Django settings
    poppler_path = getattr(settings, 'POPPLER_PATH', None)
    # Try pdfplumber first if available
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            print(f"pdfplumber failed: {e}")
    else:
        print("pdfplumber not available; skipping direct PDF text extraction")

    text = "\n".join(text_parts)

    if not text.strip():
        print("⚠️ PDF seems to be scanned or image-based — using OCR...")
        # Fall back to OCR if pdf2image and pytesseract are available
        if PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE:
            try:
                # Set Tesseract command from settings
                tesseract_cmd = getattr(settings, 'TESSERACT_PATH', 'tesseract')
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

                images = convert_from_path(file_path, dpi=300, poppler_path=poppler_path)
                ocr_text = []
                for i, img in enumerate(images):
                    extracted = pytesseract.image_to_string(img)
                    if extracted.strip():
                        ocr_text.append(extracted)
                text = "\n".join(ocr_text)
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                text = ""
        else:
            print("pdf2image/pytesseract not available; cannot perform OCR on PDF")
            text = ""
    return text

def extract_text_from_docx(file_path: str) -> str:
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx is not installed; unable to extract .docx files")
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text(file_path: str) -> str:
    path = file_path.lower()
    if path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type for {file_path}")

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- Analysis Functions (Keep as they are) ---

def count_action_verbs(text: str) -> int:
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    return sum(1 for w in words if w in ACTION_VERBS)

def detect_missing_sections(text: str):
    found = []
    for sec in REQUIRED_SECTIONS:
        if sec.lower() in text.lower():
            found.append(sec)
    missing = [s for s in REQUIRED_SECTIONS if s not in found]
    return missing

def grammar_check(text: str) -> Dict[str, Any]:
    if not LANG_TOOL_AVAILABLE:
        return {"errors_count": -1, "error": "language_tool_python not installed", "sample_errors": []}
    try:
        # NOTE: This still requires the LanguageTool server to be running!
        tool = language_tool_python.LanguageTool('en-US', remote_server_addr='http://localhost:8081')
        matches = tool.check(text)
        tool.close()
        return {
            "errors_count": len(matches),
            "sample_errors": [m.ruleId + " | " + (m.message[:200]) for m in matches[:10]]
        }
    except Exception as e:
        return {"errors_count": -1, "error": str(e), "sample_errors": []}

def compute_keyword_match(resume_text: str, job_text: str, embed_model):
    if embed_model is None:
        return {"semantic_similarity": -1.0, "keyword_coverage_percent": 0.0, "error": "Embedding model not loaded."}
    
    try:
        emb_resume = embed_model.encode(resume_text, convert_to_tensor=True)
        emb_job = embed_model.encode(job_text, convert_to_tensor=True)
        sim = util.cos_sim(emb_resume, emb_job).item()
        job_keywords = list({w.lower() for w in re.findall(r'\b[A-Za-z0-9\+\#\-\_]+\b', job_text) if len(w) > 2})
        
        if len(job_keywords) > 0:
            present = sum(1 for k in job_keywords if k in resume_text.lower())
            kw_percent = float(present) / len(job_keywords) * 100
        else:
            kw_percent = 0.0
            job_keywords = []
        
        return {"semantic_similarity": float(sim), "keyword_coverage_percent": kw_percent, "job_keyword_count": len(job_keywords)}
    except Exception as e:
        return {"semantic_similarity": -1.0, "keyword_coverage_percent": 0.0, "error": str(e)}

# --- Feedback Functions (Keep as they are) ---

def generate_feedback_genai(resume_text: str, analysis: dict, genai_api_key: str, job_text: str = None):
    # ... (keep your existing function)
    prompt_sections = [
        "You are a professional resume reviewer. Provide 4-6 actionable, concise suggestions (numbered).",
        "Focus on structure, clarity, achievements (quantifiable results), keywords, and formatting.",
        "Be polite and constructive. Keep each suggestion to one short paragraph."
    ]
    if job_text:
        prompt_sections.append("Also include one short comment on how well this resume matches the provided job description.")

    prompt = "\n".join(prompt_sections) + "\n\n"
    prompt += "RESUME START\n" + resume_text[:3000] + "\nRESUME END\n\n"
    prompt += "ANALYSIS:\n" + str(analysis) + "\n\n"
    if job_text:
        prompt += "JOB DESCRIPTION:\n" + job_text[:2000] + "\n\n"

    if not GENAI_AVAILABLE:
        return "Gemini client library not installed; using fallback suggestions:\n\n" + generate_feedback_fallback(resume_text, analysis, job_text)

    try:
        client = genai.Client(api_key=genai_api_key)
        resp = client.models.generate_content(
            model="gemini-1.5-flash", # Using a common model
            contents=[prompt]
        )
        out = resp.text.strip()
        return out
    except Exception as e:
        return f"Gemini request failed: {e}\n\nFallback suggestions:\n" + generate_feedback_fallback(resume_text, analysis, job_text)


def generate_feedback_fallback(resume_text: str, analysis: dict, job_text: str = None) -> str:
    # ... (keep your existing function)
    suggestions = []
    if analysis.get("action_verbs", 0) < 5 or analysis.get("word_count", 0) < 250:
        suggestions.append("Add measurable achievements: for each role, include 1–2 quantifiable outcomes (e.g., 'reduced cost by 20%').")
    missing = analysis.get("missing_sections", [])
    if missing:
        suggestions.append(f"Add or clearly label these sections: {', '.join(missing)}. Recruiters look for Skills and Experience upfront.")
    ge = analysis.get("grammar", {})
    if ge.get("errors_count", 0) > 0:
        suggestions.append(f"Fix grammar & typos ({ge.get('errors_count')} issues found). Use consistent tense and bullet punctuation.")
    if job_text and analysis.get("keyword_match", {}):
        km = analysis["keyword_match"]
        if km.get("keyword_coverage_percent", 0) < 50:
            suggestions.append("Improve keyword alignment with the job description: include important technologies and terms used in the JD.")
        else:
            suggestions.append("Good job on keyword coverage vs the job description — ensure those keywords appear in context (achievements, not just skills list).")
    bullets = len(re.findall(r'^\s*[-•\*]\s+', resume_text, flags=re.MULTILINE))
    if bullets < 5:
        suggestions.append("Use concise bullet points for responsibilities and achievements (3–6 bullets per role).")
    suggestions.append("Start with a short (2-3 sentences) professional summary that highlights your role, experience, and top skills.")
    return "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))


# --- MAIN CALLABLE FUNCTION ---

def analyze_resume(resume_file_path: str, job_description: str) -> str:
    """
    Main function to be called from Django.
    Takes a file path and job description, returns analysis feedback.
    """
    
    # 1. Get API Key from settings
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        return "Error: GEMINI_API_KEY not configured in Django settings."

    # 2. Extract resume text
    try:
        resume_text = clean_text(extract_text(resume_file_path))
        if not resume_text:
            return "Error: Could not extract any text from the resume."
    except Exception as e:
        return f"Error during text extraction: {e}"

    # 3. Run analysis
    analysis = {
        "word_count": len(resume_text.split()),
        "action_verbs": count_action_verbs(resume_text),
        "missing_sections": detect_missing_sections(resume_text),
        "grammar": grammar_check(resume_text),
        "keyword_match": compute_keyword_match(resume_text, job_description, EMBED_MODEL)
    }

    # 4. Generate Gemini feedback
    feedback = generate_feedback_genai(resume_text, analysis, api_key, job_description)
    
    return feedback