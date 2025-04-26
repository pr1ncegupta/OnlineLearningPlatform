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
st.set_page_config(page_title="SkillPath AI MVP", layout="centered", initial_sidebar_state="auto")
st.markdown("""
    <style>
    .stApp {
        background-color: #f9f9f9;
        color: #000000;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
    }
    .stSelectbox>div>div {
        background-color: #ffffff;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 SkillPath AI: Personalized Learning Roadmaps")
st.subheader("Start with a quick screening test and get a roadmap tailored for you!")

# Topic selection
selected_topic = st.selectbox("Choose a topic:", ["-- Select --"] + TOPICS)

if selected_topic != "-- Select --":
    if "active_topic" not in st.session_state or st.session_state.active_topic != selected_topic:
        st.session_state.active_topic = selected_topic
        st.session_state.questions = []
        st.session_state.answers = {}
        with st.spinner("Generating test..."):
            prompt = f"""
You are an expert quiz generator.
Generate 5 beginner to intermediate level MCQ questions for the topic: {selected_topic}.
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
            except Exception as e:
                st.error(f"Failed to parse generated questions. Error: {e}")

    if st.session_state.questions:
        st.header(f"📋 Screening Test: {selected_topic}")
        with st.form(key="test_form"):
            for q in st.session_state.questions:
                st.write(f"**Q{q['id']}:** {q['prompt']}")
                st.session_state.answers[q['id']] = st.radio(
                    label="",
                    options=q.get("choices", []),
                    key=f"q_{q['id']}"
                )
            submitted = st.form_submit_button("✅ Submit Test")

        if submitted:
            correct_count = 0
            feedback = []
            for q in st.session_state.questions:
                qid = q['id']
                user_answer = st.session_state.answers.get(qid, "")
                correct_answer = q['answer']
                is_correct = (user_answer == correct_answer)
                if is_correct:
                    correct_count += 1
                feedback.append({
                    "question": q['prompt'],
                    "your_answer": user_answer,
                    "correct_answer": correct_answer,
                    "result": "✅" if is_correct else "❌"
                })

            st.success(f"You got {correct_count} out of {len(st.session_state.questions)} correct.")
            st.header("🔍 Evaluation Insights")
            for item in feedback:
                st.markdown(f"- {item['result']} **{item['question']}**  \
                            Your answer: `{item['your_answer']}` | Correct: `{item['correct_answer']}`")

            # Generate roadmap
            weak_topics = [item['question'] for item in feedback if item['result'] == "❌"]
            if weak_topics:
                roadmap_prompt = f"Generate a step-by-step learning roadmap for someone struggling with the following questions/topics in {selected_topic}: {weak_topics}. Include brief explanations and a useful video/document link for each. Return as markdown list."
                with st.spinner("Creating your personalized roadmap..."):
                    roadmap = call_gemini(roadmap_prompt)
                st.header("🗺️ Your Learning Roadmap")
                st.markdown(roadmap)
            else:
                st.info("You did great! No roadmap needed.")

    st.markdown("---")
    st.button("🔁 Choose Another Topic", on_click=lambda: st.session_state.pop("active_topic", None))
