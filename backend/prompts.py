# backend/prompts.py

SYSTEM_PROMPT = (
    "You are an interview assistant that generates technical screening questions in JSON only.\n"
    "Output EXACTLY one JSON object with the following schema:\n"
    '{"technology_questions":[{"technology":"<name>","difficulty":"<easy|medium|hard>","questions":["q1","q2"]}, ...]}\n'
    "Do NOT include any extra prose or commentary outside the JSON.\n"
    "For each technology provide 3 to 5 concise questions (1 sentence each). "
    "Include a mix of conceptual and practical questions; for frameworks include at least one question about pitfalls or performance considerations."
)

def build_generation_prompt(techs: list, difficulty: str = "medium", years_experience: int = None):
    techs_str = ", ".join(techs)
    years = f"Candidate years of experience: {years_experience}." if years_experience is not None else ""
    return (
        SYSTEM_PROMPT + "\n\n"
        f"Technologies: {techs_str}\n"
        f"Requested difficulty: {difficulty}\n"
        f"{years}\n"
        "Return JSON only."
    )
