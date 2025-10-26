"""Wrapper client for calling Gemini (Generative) API or returning a mock result.

This module uses environment variables to decide whether to call the real API:
- GEMINI_API_KEY : Bearer token / API key to send in Authorization header
- GEMINI_API_URL : Full endpoint URL to POST generation requests to

If those are not set, the client returns a deterministic mock response suitable
for local development.

The expected return value of analyze_resume(...) is a dict with keys:
 - score: int (0-100)
 - skills: list[str]
 - recommendations: list[str]

Note: the exact Gemini HTTP API may differ by product/version. This wrapper
keeps the network code minimal; adapt request/response parsing to the exact
API format your project has access to (Vertex AI GenerativeEndpoints, PaLM,
or Google Cloud's Generative API). No network calls are made at authoring time.
"""
from __future__ import annotations

import os
import json
import logging
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)


def _build_prompt(resume_text: str, target_role: str) -> str:
    # Prompt engineering: ask the model explicitly for JSON output
    prompt = (
        "You are an expert resume reviewer.\n"
        "Given the resume text and the target job role, extract the candidate's"
        " key technical and soft skills as a JSON array, produce a short list of"
        " actionable recommendations to improve the resume for the role, and"
        " provide a relevance score from 0 to 100 (higher is better).\n\n"
        "Respond ONLY with a JSON object with keys: score (integer), skills (array of strings),"
        " recommendations (array of strings). Do not add extra explanation.\n\n"
        "Resume:\n" + resume_text + "\n\n"
        "Target role: " + target_role + "\n"
    )
    return prompt


def analyze_resume(resume_text: str, target_role: str, timeout: int = 20) -> Dict:
    """Analyze resume using Gemini API if configured, otherwise return a mock.

    Args:
        resume_text: Plain text of resume (caller should extract/convert PDF if needed).
        target_role: Target job role string.
        timeout: HTTP request timeout in seconds.

    Returns:
        A dict with keys: score:int, skills:list[str], recommendations:list[str]
    """

    api_key = os.environ.get('GEMINI_API_KEY')
    api_url = os.environ.get('GEMINI_API_URL')

    prompt = _build_prompt(resume_text or '(no text provided)', target_role or '')

    if api_key and api_url:
        # Call the real Gemini endpoint. The exact request body depends on the
        # provider; many generative endpoints accept a `prompt` field or similar.
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'prompt': prompt,
            # Provider-specific tuning parameters
            'max_output_tokens': 1024,
            'temperature': 0.0,
        }

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            text = resp.text.strip()

            # Try to extract JSON object from the model response. Many LLM
            # endpoints return a JSON envelope; adjust parsing as needed.
            try:
                data = resp.json()
                # If the response is an envelope (e.g., {"candidates": [...]})
                # try to find the text inside common keys.
                if isinstance(data, dict):
                    if 'content' in data:
                        body = data['content']
                    elif 'candidates' in data and data['candidates']:
                        body = data['candidates'][0].get('content', '')
                    elif 'output' in data:
                        body = json.dumps(data['output'])
                    else:
                        body = json.dumps(data)
                else:
                    body = json.dumps(data)
            except ValueError:
                # Not JSON: the model responded with a text blob, attempt to parse JSON within
                body = text

            # Attempt to load JSON from the body
            try:
                parsed = json.loads(body)
                # Normalize result
                return {
                    'score': int(parsed.get('score', 0)),
                    'skills': parsed.get('skills', []),
                    'recommendations': parsed.get('recommendations', []),
                }
            except Exception:
                # As a last resort, attempt to find a JSON substring inside the text
                import re

                m = re.search(r'(\{[\s\S]*\})', body)
                if m:
                    try:
                        parsed = json.loads(m.group(1))
                        return {
                            'score': int(parsed.get('score', 0)),
                            'skills': parsed.get('skills', []),
                            'recommendations': parsed.get('recommendations', []),
                        }
                    except Exception:
                        logger.exception('Failed parsing JSON from model body')

            # If parsing failed, log and fallback to mock
            logger.warning('Gemini response could not be parsed as JSON; returning mock result')

        except Exception:
            logger.exception('Error calling Gemini API; falling back to mock result')

    # Mock deterministic fallback for dev / missing credentials
    # Create simple heuristics: score based on presence of keywords
    lower = (resume_text or '').lower()
    score = 40
    skills: List[str] = []
    recommendations: List[str] = []

    if 'python' in lower:
        skills.append('Python')
        score += 15
    if 'django' in lower:
        skills.append('Django')
        score += 10
    if 'sql' in lower or 'postgres' in lower or 'mysql' in lower:
        skills.append('SQL')
        score += 5

    if len(lower.split()) > 250:
        score += 10
    else:
        recommendations.append('Add more detail to experience and projects to increase score')

    if not skills:
        skills = ['Communication', 'Teamwork']
        recommendations.append('Highlight technical tools and keywords relevant to your target role')

    score = max(0, min(100, int(score)))

    return {
        'score': score,
        'skills': skills,
        'recommendations': recommendations,
    }
