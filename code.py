```python
import streamlit as st
import requests

# Configuration
GEMINI_ENDPOINT = "https://api.gemini.example.com/v1"
GEMINI_API_KEY = st.secrets.get("gemini_api_key", "YOUR_API_KEY")
TOPICS = ["Python Basics", "Data Structures", "Machine Learning"]

# Helpers for Gemini API

def call_gemini(task: str, params: dict) -> dict:
    payload = {"task": task, **params}
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{GEMINI_ENDPOINT}/{task}", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# App layout
st.set_page_config(page_title="SkillPath AI MVP")
st.title("SkillPath AI MVP: Screening & Roadmap")

# Topic selection
topic = st.selectbox("Choose a topic to start:", ["-- Select --"] + TOPICS)

if topic != "-- Select --":
    if "questions" not in st.session_state:
        # Generate MCQ test
        with st.spinner("Generating test..."):
            result = call_gemini("generate_test", {"topic": topic, "num_questions": 5})
            st.session_state.questions = result.get("questions", [])
            st.session_state.answers = []

    # Display test form
    st.header(f"Screening Test: {topic}")
    with st.form(key="test_form"):
        for q in st.session_state.questions:
            st.write(f"**Q{q['id']}:** {q['prompt']}")
            choice = st.radio(
                label=f"Select answer for question {q['id']}",
                options=q.get("choices", []),
                key=f"q_{q['id']}"
            )
            st.session_state.answers.append({"id": q['id'], "answer": choice})
        submit = st.form_submit_button("Submit Test")

    # On submission, evaluate and show roadmap
    if submit:
        with st.spinner("Evaluating answers..."):
            insights = call_gemini("evaluate_test", {"responses": st.session_state.answers})
        st.header("Evaluation Insights")
        st.json(insights)

        with st.spinner("Generating roadmap..."):
            roadmap = call_gemini("generate_roadmap", {"insights": insights})
        st.header("Personalized Roadmap")
        for step in roadmap.get("steps", []):
            st.markdown(f"- **{step['title']}**: {step['description']} ([Link]({step['resource']}))")
```
