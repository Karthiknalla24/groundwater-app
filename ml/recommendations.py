# ml/recommendations.py
import os
import time
import logging
from typing import Dict, Any, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure API key from environment (must be set before running app)
API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    logger.warning(
        "GOOGLE_API_KEY environment variable not set. Gemini recommendations will be disabled."
    )
else:
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        logger.exception("Failed to configure google.generativeai: %s", e)

# Use a reasonably capable, cost-efficient model
DEFAULT_MODEL = "gemini-2.5-flash"

# ------- Prompt builders (keep short, deterministic) -------

def build_drinking_prompt(predicted_class: str, input_data: Dict[str, Any], insights: Dict[str, Any]) -> str:
    return f"""
You are a groundwater quality specialist. Usage: DRINKING WATER.
Predicted class: {predicted_class}

Input readings:
{input_data}

Parameter insights (status & percent):
{insights}

Write 3 short sections (use plain text):
1) Drinking suitability — 2 sentences: overall suitability + 1–2 key parameter issues.
2) Key issues — 2–4 bullet points: "Parameter – issue – likely impact".
3) Safe household actions — 3–5 bullet points (practical, non-technical).

End with exactly one sentence:
"These suggestions are based on model outputs and do not replace certified laboratory testing."

Keep under 220 words. No medical/legal advice or design formulas.
""".strip()


def build_irrigation_prompt(predicted_class: str, input_data: Dict[str, Any], insights: Dict[str, Any]) -> str:
    return f"""
You are an irrigation-water advisor. Usage: IRRIGATION WATER.
Predicted class: {predicted_class}

Input readings:
{input_data}

Parameter insights (status & percent):
{insights}

Write 3 short sections (plain text):
1) Irrigation suitability — 2 sentences summarizing salinity/sodicity risk.
2) Soil & crop concerns — 2–4 bullet points: "Parameter – issue – likely crop/soil impact".
3) Field recommendations — 3–5 bullet points (practical, no dosages).

End with exactly one sentence:
"Consult local agricultural experts and certified lab reports before major decisions."

Keep under 220 words. No engineering formulas.
""".strip()

# ------- Main function called from app.py -------

def get_recommendations(mode: str, predicted_class: str, input_data: Dict[str, Any], insights: Optional[Dict[str, Any]] = None) -> str:
    """
    Returns a short recommendations string (Gemini-powered) or a fallback message.
    """
    # quick fallback when API not configured
    if not API_KEY:
        return "AI recommendations unavailable (server not configured with GOOGLE_API_KEY)."

    # choose prompt
    insights = insights or {}
    if mode == "drinking":
        prompt = build_drinking_prompt(predicted_class, input_data, insights)
    else:
        prompt = build_irrigation_prompt(predicted_class, input_data, insights)

    # try to call Gemini with simple retry logic
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL)
            response = model.generate_content(prompt)
            # Modern SDK returns .text on many builds; otherwise try .content or str()
            text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
            text = text.strip()
            # Simple safety: if empty or too short, fallback
            if not text or len(text) < 10:
                raise ValueError("Empty or too-short response from model")
            return text
        except Exception as e:
            logger.warning("Gemini attempt %s/%s failed: %s", attempt, attempts, e)
            # exponential backoff
            if attempt < attempts:
                time.sleep(1.5 ** attempt)
            else:
                logger.exception("All Gemini attempts failed.")
                break

    # final fallback summary built from model output + insights (deterministic)
    try:
        # build a minimal deterministic fallback using predicted_class and top 2 flagged params
        flagged = [k for k, v in (insights or {}).items() if v.get("status") in ("High", "Low")]
        top_flags = flagged[:2] if flagged else []
        fallback_lines = [
            f"Predicted class: {predicted_class}.",
            "AI recommendations currently unavailable.",
        ]
        if top_flags:
            fallback_lines.append("Top concerns: " + ", ".join(top_flags) + ".")
        fallback_lines.append("Suggested actions: verify with laboratory testing; use appropriate treatment (e.g., RO for high salts); consult local experts.")
        fallback_lines.append("These suggestions are based on model outputs and do not replace certified laboratory testing.")
        return " ".join(fallback_lines)
    except Exception:
        return "AI recommendations unavailable. Please check server logs."
