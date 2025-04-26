import streamlit as st
import google.generativeai as genai
import json

# Configuration
GEMINI_API_KEY = st.secrets.get("gemini_api_key", "YOUR_API_KEY")
TOPICS = ["Python Basics", "Data Structures", "Machine Learning"]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Helpers for Gemini
def call_gemini(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text

# App layout
st.set_page_config(page_title="SkillPath AI MVP")
st.title("SkillPath AI MVP: Screening & Roadmap")

# Topic selection
topic = st.selectbox("Choose a topic to start:", ["-- Select --"] + TOPICS)

if topic != "-- Select --":
    if "questions" not in st.session_state:
        with st.spinner("Generating test..."):
            prompt = f"""
You are an expert quiz generator.
Generate 5 beginner to intermediate level MCQ questions for the topic: {topic}.
Each question should have:
- an 'id' (1-5)
- a 'prompt' (the question)
- 4 answer choices in a list
- 'answer' (the correct one)

Return ONLY a JSON array in this exact format:
[
  {{
    "id": 1,
    "prompt": "What does print() do in Python?",
    "choices": ["It loops", "It prints", "It stores", "It defines"],
    "answer": "It prints"
  }},
  ...
]
"""
            result = call_gemini(prompt)
            try:
                json_start = result.find('[')
                json_end = result.rfind(']') + 1
                json_data = result[json_start:json_end]
                st.session_state.questions = json.loads(json_data)
                st.session_state.answers = []
            except Exception as e:
                st.error(f"Failed to parse generated questions. Error: {e}")

    if "questions" in st.session_state:
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

        if submit:
            correct_count = 0
            feedback = []
            for i, response in enumerate(st.session_state.answers):
                correct = st.session_state.questions[i]['answer']
                is_correct = response['answer'] == correct
                if is_correct:
                    correct_count += 1
                feedback.append({"question": st.session_state.questions[i]['prompt'], "your_answer": response['answer'], "correct_answer": correct, "result": "✅" if is_correct else "❌"})

            st.header("Evaluation Insights")
            st.write(f"You got {correct_count} out of {len(st.session_state.questions)} correct.")
            for item in feedback:
                st.write(f"- {item['result']} **{item['question']}** | Your answer: `{item['your_answer']}` | Correct: `{item['correct_answer']}`")

            # Generate roadmap prompt
            weak_topics = [q['prompt'] for i, q in enumerate(st.session_state.questions) if st.session_state.answers[i]['answer'] != q['answer']]
            roadmap_prompt = f"Generate a step-by-step learning roadmap for someone struggling with the following questions/topics in {topic}: {weak_topics}. Include brief explanations and a useful video/document link for each. Return as markdown list."

            with st.spinner("Generating roadmap..."):
                roadmap = call_gemini(roadmap_prompt)
            st.header("Personalized Roadmap")
            st.markdown(roadmap)
