import json
import re
import os
from typing import List, Dict, Any

# Optional heavy/third-party imports
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

from django.conf import settings

# --- Paths for Windows ---
POPPLER_PATH = r"C:\STUDIES\hacktober-25\poppler-25.07.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if PYTESSERACT_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# --- Load SentenceTransformer model ---
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

# --- Helper Functions ---


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pdfplumber or OCR if needed (runs OCR only once)."""
    text_parts = []

    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            print(f"pdfplumber failed: {e}")

    text = "\n".join(text_parts).strip()
    
    if not text and PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE:
        # Only run OCR if no text extracted
            print("⚠️ PDF seems scanned — using OCR once...")
            try:
                images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
                ocr_text = []
                for img in images:
                    page_text = pytesseract.image_to_string(img).strip()
                    if page_text:
                        ocr_text.append(page_text)
                text = "\n".join(ocr_text)
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                text = ""
            

    return text

def extract_text_from_docx(file_path: str) -> str:
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx not installed; cannot extract .docx")
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text(file_path: str) -> str:
    """Unified extraction function for PDF, DOCX, TXT."""
    path = file_path.lower()
    if path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- Analysis Functions ---
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
        kw_percent = 0.0
        if job_keywords:
            present = sum(1 for k in job_keywords if k in resume_text.lower())
            kw_percent = present / len(job_keywords) * 100
        return {"semantic_similarity": float(sim), "keyword_coverage_percent": kw_percent, "job_keyword_count": len(job_keywords)}
    except Exception as e:
        return {"semantic_similarity": -1.0, "keyword_coverage_percent": 0.0, "error": str(e)}

# --- Feedback Functions ---
def generate_feedback_fallback(resume_text: str, analysis: dict, job_text: str = None) -> str:
    suggestions = []
    if analysis.get("action_verbs", 0) < 5 or analysis.get("word_count", 0) < 250:
        suggestions.append("Add measurable achievements for each role (e.g., 'reduced cost by 20%').")
    missing = analysis.get("missing_sections", [])
    if missing:
        suggestions.append(f"Add/label these sections: {', '.join(missing)}.")
    ge = analysis.get("grammar", {})
    if ge.get("errors_count", 0) > 0:
        suggestions.append(f"Fix grammar & typos ({ge.get('errors_count')} found).")
    if job_text and analysis.get("keyword_match", {}):
        km = analysis["keyword_match"]
        if km.get("keyword_coverage_percent", 0) < 50:
            suggestions.append("Improve keyword alignment with the job description.")
        else:
            suggestions.append("Good keyword coverage.")
    bullets = len(re.findall(r'^\s*[-•\*]\s+', resume_text, flags=re.MULTILINE))
    if bullets < 5:
        suggestions.append("Use concise bullet points (3–6 per role).")
    suggestions.append("Start with a short professional summary highlighting role, experience, and top skills.")
    return "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))

def generate_feedback_genai(resume_text: str, analysis: dict, genai_api_key: str, job_text: str = None):
    prompt_sections = [
        "You are a professional resume reviewer. Provide 4-6 actionable, concise suggestions.",
        "Focus on structure, clarity, achievements, keywords, formatting."
    ]
    if job_text:
        prompt_sections.append("Also comment briefly on job match.")

    prompt = "\n".join(prompt_sections) + "\n\nRESUME:\n" + resume_text[:3000] + "\n\nANALYSIS:\n" + str(analysis)
    if job_text:
        prompt += "\n\nJOB DESCRIPTION:\n" + job_text[:2000]

    if not GENAI_AVAILABLE:
        return "Gemini library not installed. Fallback:\n\n" + generate_feedback_fallback(resume_text, analysis, job_text)
    try:
        client = genai.Client(api_key=genai_api_key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
        return resp.text.strip()
    except Exception as e:
        return f"Gemini request failed: {e}\n\nFallback:\n" + generate_feedback_fallback(resume_text, analysis, job_text)

# --- Main Function ---
def analyze_resume(resume_file_path: str, job_description: str) -> str:
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        api_key ="AIzaSyBXiMXfVhCpltP1_sGRZDDodoh_HjkwQr8"

    try:
        # ✅ Extract text once
        resume_text = clean_text(extract_text(resume_file_path))
        if not resume_text:
            return "Error: No text extracted from resume."
    except Exception as e:
        return f"Text extraction error: {e}"

    # ✅ Perform analysis
    analysis = {
        "word_count": len(resume_text.split()),
        "action_verbs": count_action_verbs(resume_text),
        "missing_sections": detect_missing_sections(resume_text),
        "grammar": grammar_check(resume_text),
        "keyword_match": compute_keyword_match(resume_text, job_description, EMBED_MODEL)
    }

    # ✅ Generate feedback
    feedback = generate_feedback_genai(resume_text, analysis, api_key, job_description)
    return feedback
