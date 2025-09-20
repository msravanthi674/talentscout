# backend/utils.py
import re
import json

# Map common shorthand/mistypes to normalized display names
COMMON_NORMALIZATIONS = {
    "pytho": "Python",
    "py": "Python",
    "python3": "Python",
    "postgres": "PostgreSQL",
    "psql": "PostgreSQL",
    "pg": "PostgreSQL",
    "dja": "Django",
    "dj": "Django",
    "js": "JavaScript",
    "ts": "TypeScript",
    "sql": "SQL",
    "c#": "C#",
    "c++": "C++",
    "go": "Go",
}

def split_tech_stack(text: str):
    """
    Split freeform tech stack text into a normalized, deduped list of tech names.
    """
    if not text:
        return []
    parts = re.split(r"[,\n;/|]+", text)
    cleaned = []
    seen = set()
    for p in parts:
        t = p.strip()
        if not t:
            continue
        # remove stray punctuation except +, #, . (for c++, c#)
        t = re.sub(r"[^\w\+\#\.\- ]+", "", t)
        key = t.lower()
        normalized = COMMON_NORMALIZATIONS.get(key)
        if not normalized:
            if key in {"sql"}:
                normalized = "SQL"
            elif key in {"go"}:
                normalized = "Go"
            else:
                normalized = t.title()
        if normalized not in seen:
            cleaned.append(normalized)
            seen.add(normalized)
    return cleaned

def extract_json_blob(text: str):
    """
    Extract the first JSON object from a text blob.
    Raises ValueError if no JSON object found.
    """
    if not text or "{" not in text:
        raise ValueError("No JSON found in text")
    # naive but works for typical LLM outputs: find first '{' and matching '}' by scanning.
    start = text.find("{")
    # Find matching closing brace by counting braces
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                return text[start:end+1]
    raise ValueError("Unbalanced JSON braces in text")

def format_questions_as_text(payload: dict):
    lines = []
    c = payload.get("candidate", {})
    lines.append(f"Candidate: {c.get('full_name','')}")
    lines.append(f"Position: {c.get('desired_position','')}")
    lines.append(f"Years exp: {c.get('years_experience','')}")
    lines.append("")
    for block in payload.get("questions", []):
        lines.append(f"=== {block.get('technology','Unknown')} (difficulty: {block.get('difficulty','medium')}) ===")
        for i, q in enumerate(block.get("questions", []), 1):
            lines.append(f"{i}. {q}")
        lines.append("")
    return "\n".join(lines)

def fallback_generate_questions(techs, difficulty="medium"):
    """
    Templated fallback generator - returns 3-5 questions per tech.
    Difficulty can be 'easy', 'medium', 'hard' and slightly affects phrasing.
    """
    easy_templates = [
        "What is {t} commonly used for?",
        "Name one advantage of using {t}.",
        "Describe a simple example or code snippet using {t}.",
    ]
    medium_templates = [
        "Explain the main use-cases of {t}.",
        "Describe a common pitfall when working with {t} and how to avoid it.",
        "Write a short code snippet or algorithm demonstrating a typical {t} task.",
        "How would you debug a performance issue related to {t}?",
    ]
    hard_templates = [
        "Explain a complex performance/pitfall scenario in {t} and how you'd mitigate it.",
        "Design an algorithm/architecture decision involving {t} for scalability.",
        "Discuss trade-offs between {t} and an alternative technology in large systems.",
    ]
    out = []
    for t in techs:
        if difficulty == "easy":
            templates = easy_templates
        elif difficulty == "hard":
            templates = hard_templates + medium_templates[:1]
        else:
            templates = medium_templates
        qs = [tpl.format(t=t) for tpl in templates][:5]
        out.append({"technology": t, "difficulty": difficulty, "questions": qs})
    return out
