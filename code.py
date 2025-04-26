import streamlit as st
import google.generativeai as genai

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
            prompt = f"Generate 5 multiple-choice beginner to intermediate level questions with 4 options and correct answer indicated on the topic: {topic}. Return as a JSON list with 'id', 'prompt', 'choices', and 'answer'."
            result = call_gemini(prompt)
            try:
                st.session_state.questions = eval(result)  # NOTE: Use safer parsing in production
                st.session_state.answers = []
            except:
                st.error("Failed to parse generated questions.")

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
