# app/streamlit_app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st # type: ignore
import json
import time
from backend.generator import generate_questions_for_techs
from backend.storage import save_candidate_with_questions, load_recent_with_questions
from backend.utils import split_tech_stack, format_questions_as_text

# Basic CSS for nicer cards / layout
CARD_CSS = """
<style>
.card {
  background-color: rgba(255,255,255,0.02);
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.header {
  display:flex;
  align-items:center;
  gap:12px;
}
.title {
  font-size:28px;
  font-weight:700;
  margin:0;
}
.subtitle {
  color:#9aa0a6;
  margin:0;
}
.copy-btn {
  background-color: transparent;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 6px 10px;
  border-radius: 6px;
}
</style>
"""

st.set_page_config(page_title="TalentScout — Hiring Assistant", page_icon="🤖", layout="wide")
st.markdown(CARD_CSS, unsafe_allow_html=True)

# Header
colL, colR = st.columns([4,1])
with colL:
    st.markdown('<div class="header"><img src="https://img.icons8.com/emoji/48/000000/robot-emoji.png" alt="robot"/><div><p class="title">TalentScout — Hiring Assistant</p><p class="subtitle">Initial technical screening — generate role-specific questions</p></div></div>', unsafe_allow_html=True)
with colR:
    if st.button("Recent"):
        st.write("Showing recent submissions below.")

# Form
with st.form("candidate_form"):
    st.subheader("Candidate Details")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")
    years_exp = st.number_input("Years of Experience", min_value=0, max_value=60, value=1)
    desired_position = st.text_input("Desired Position(s)")
    location = st.text_input("Current Location")
    tech_stack_raw = st.text_area("Tech Stack (comma or newline separated). Example: Python, Django, React, PostgreSQL")
    difficulty = st.selectbox("Question difficulty", options=["easy", "medium", "hard"], index=1)
    submit = st.form_submit_button("Submit & Generate")

# Ensure session keys
if "generated" not in st.session_state:
    st.session_state.generated = None
if "candidate" not in st.session_state:
    st.session_state.candidate = None

if submit:
    techs = split_tech_stack(tech_stack_raw)
    if not techs:
        st.error("Please provide at least one technology.")
    else:
        candidate = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "years_experience": int(years_exp),
            "desired_position": desired_position.strip(),
            "location": location.strip(),
            "tech_stack_raw": tech_stack_raw.strip(),
            "tech_stack": techs,
            "timestamp": int(time.time()),
        }
        with st.spinner("Generating questions..."):
            questions = generate_questions_for_techs(techs, difficulty=difficulty, years_experience=years_exp)
            st.session_state.generated = questions
            st.session_state.candidate = candidate
            # Save to DB
            try:
                db_id = save_candidate_with_questions(candidate, questions)
                st.success(f"Saved submission (id={db_id}).")
            except Exception as e:
                st.warning(f"Could not save to DB: {e}")

# Display generated questions in "cards" with copy-button
if st.session_state.get("generated"):
    st.success("Questions generated:")
    for i, block in enumerate(st.session_state["generated"]):
        tech = block.get("technology", "Unknown")
        diff = block.get("difficulty", "medium")
        qs = block.get("questions", []) or []
        st.markdown(f'<div class="card"><h4 style="margin:0;">{tech} <small style="color:#9aa0a6;">({diff})</small></h4>', unsafe_allow_html=True)
        # Numbered list
        for idx, q in enumerate(qs, 1):
            st.write(f"{idx}. {q}")
        # Copy button (small HTML widget)
        safe_text = "\n".join([f"{idx}. {q}" for idx, q in enumerate(qs, 1)])
        # unique id per block
        uid = f"copy_{i}_{tech}".replace(" ", "_")
        html = f"""
        <div style="margin-top:8px;">
          <button class="copy-btn" onclick="const t=document.getElementById('{uid}'); navigator.clipboard.writeText(t.innerText).then(()=>{{alert('Copied to clipboard')}});">Copy to clipboard</button>
          <pre id="{uid}" style="display:none;">{safe_text}</pre>
        </div>
        """
        st.components.v1.html(html, height=60)
        st.markdown("</div>", unsafe_allow_html=True)

    payload = {"candidate": st.session_state.get("candidate"), "questions": st.session_state.get("generated")}
    st.download_button("Download JSON", data=json.dumps(payload, ensure_ascii=False, indent=2), file_name="screening_result.json", mime="application/json")
    st.download_button("Download TXT", data=format_questions_as_text(payload), file_name="screening_result.txt")

# Show recent submissions from DB
st.markdown("---")
st.subheader("Recent Submissions")
recent = load_recent_with_questions(8)
if recent:
    for item in recent:
        c = item["candidate"]
        st.markdown(f"**{c.get('full_name')}** — {c.get('desired_position','')} • {c.get('created_at')}")
        # show short tech stack
        st.write(c.get("tech_stack_raw"))
        # small collapse for questions
        with st.expander("View generated questions"):
            for block in item["question_blocks"]:
                st.write(f"**{block['technology']}** ({block['difficulty']})")
                for idx, q in enumerate(block["questions"], 1):
                    st.write(f"{idx}. {q}")
else:
    st.info("No submissions yet. Submit a candidate above to create entries.")

st.markdown("---")
st.caption("TalentScout — persisted with SQLite. Keep your DB file secure.")
