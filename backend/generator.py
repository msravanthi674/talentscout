# backend/generator.py
import json
import logging
from backend.api_client import call_mistral
from backend.prompts import build_generation_prompt
from backend.utils import extract_json_blob, fallback_generate_questions

logger = logging.getLogger(__name__)

def _extract_text_from_mistral_response(resp):
    """
    Attempts to extract a text/yielded string from a Mistral response object.
    Adapt as per the actual response structure you see in your Mistral account.
    """
    if resp is None:
        return None
    # If resp is dict and contains 'output' or 'generations' or 'result' or 'text'
    if isinstance(resp, dict):
        # common keys to inspect
        for k in ("output", "result", "text", "generations", "choices"):
            if k in resp:
                val = resp[k]
                if isinstance(val, str):
                    return val
                if isinstance(val, list) and val:
                    first = val[0]
                    # various shapes
                    if isinstance(first, str):
                        return first
                    if isinstance(first, dict):
                        for tkey in ("text", "content", "output"):
                            if tkey in first:
                                return first[tkey]
                        # some APIs embed nested list
                        if "generation" in first and isinstance(first["generation"], str):
                            return first["generation"]
    # If it's a plain string
    if isinstance(resp, str):
        return resp
    try:
        return json.dumps(resp)
    except Exception:
        return None

def generate_questions_for_techs(techs, difficulty="medium", model=None, years_experience=None):
    """
    High-level function: returns list of {technology, difficulty, questions: [...]}
    """
    if not techs:
        return []

    prompt = build_generation_prompt(techs, difficulty=difficulty, years_experience=years_experience)

    try:
        resp = call_mistral(prompt, model=model)
        text = _extract_text_from_mistral_response(resp)
        if not text:
            raise ValueError("No text extracted from Mistral response")

        # Extract JSON blob from text and parse
        json_blob = extract_json_blob(text)
        parsed = json.loads(json_blob)
        tech_questions = parsed.get("technology_questions") or parsed.get("technology_questions".lower())
        if not isinstance(tech_questions, list):
            raise ValueError("Parsed JSON missing 'technology_questions' list")

        # Validate items and ensure fields present
        out = []
        for item in tech_questions:
            tech = item.get("technology")
            qs = item.get("questions") or []
            diff = item.get("difficulty") or difficulty
            if not tech or not isinstance(qs, list):
                continue
            out.append({"technology": tech, "difficulty": diff, "questions": qs})
        if out:
            return out
        raise ValueError("No valid items parsed from LLM output")

    except Exception as e:
        logger.warning("LLM generation failed or produced unexpected output (%s). Using fallback. Error: %s", type(e).__name__, e)
        return fallback_generate_questions(techs, difficulty=difficulty)
