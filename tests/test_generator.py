# tests/test_generator.py
import json
import pytest # type: ignore

from backend.utils import split_tech_stack, extract_json_blob, fallback_generate_questions
from backend.generator import generate_questions_for_techs

def test_split_tech_stack_basic():
    text = "Python, Django, React\nPostgreSQL"
    result = split_tech_stack(text)
    assert "Python" in result
    assert "Django" in result
    assert "React" in result
    assert "PostgreSQL" in result

def test_extract_json_blob_valid():
    raw = "some text {\"hello\": \"world\"} more"
    blob = extract_json_blob(raw)
    parsed = json.loads(blob)
    assert parsed["hello"] == "world"

def test_extract_json_blob_invalid():
    with pytest.raises(ValueError):
        extract_json_blob("no json here")

def test_fallback_generate_questions():
    techs = ["Python"]
    questions = fallback_generate_questions(techs)
    assert len(questions) == 1
    assert questions[0]["technology"] == "Python"
    assert len(questions[0]["questions"]) >= 3

def test_generate_questions_for_techs_with_fallback(monkeypatch):
    # Monkeypatch call_mistral to raise an error → forces fallback
    from backend import generator

    def fake_call_mistral(prompt, model=None, temperature=0.2, timeout=30):
        raise RuntimeError("API not available")

    monkeypatch.setattr(generator, "call_mistral", fake_call_mistral)

    techs = ["Python", "Django"]
    result = generate_questions_for_techs(techs)
    assert isinstance(result, list)
    assert all("technology" in item for item in result)
    assert all("questions" in item for item in result)
