import streamlit as st
import json
import random
import os
from utils import save_score, load_leaderboard

# Auto Dark Mode Script
st.markdown("""
    <script>
    const darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (darkMode) {
        document.body.setAttribute('data-theme', 'dark');
    }
    </script>
""", unsafe_allow_html=True)

# Load questions from selected category
def load_questions():
    with open("quizdata.json", "r") as f:
        all_questions = json.load(f)
    selected = st.session_state.get("category", "Funny")
    return [q for q in all_questions if q["category"] == selected]

# Category icon map
category_icon = {
    "Funny": "funny.png",
    "Knowledge": "knowledge.png",
    "Math": "math.png",
    "Science": "science.png",
    "History": "history.png"
}

# Init session state
if "questions" not in st.session_state:
    st.session_state.questions = load_questions()
    random.shuffle(st.session_state.questions)
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.answer_selected = False
    st.session_state.selected_option = None
    st.session_state.show_result = False

questions = st.session_state.questions
current_q = st.session_state.current_q
score = st.session_state.score
cat = st.session_state.get("category", "Funny")
icon_path = f"assets/icon/{category_icon.get(cat)}"

# Show category icon + name
st.image(icon_path, width=60)
st.markdown(f"#### Category: {cat}")

# Progress Bar
progress = int((current_q + 1) / len(questions) * 100)
st.progress(progress, text=f"Question {current_q + 1} of {len(questions)}")

# Result Page
if st.session_state.show_result:
    st.title("Quiz Completed!")
    st.subheader(f"Your Score: {score} / {len(questions)}")

    name = st.text_input("Enter your name to save your score")
    if st.button("Submit Score"):
        if name.strip() != "":
            save_score(name, score, cat)
            st.success("Score submitted successfully!")
            st.experimental_rerun()
        else:
            st.warning("Please enter a name before submitting.")

    st.markdown("### Leaderboard (Top 5)")
    leaderboard = load_leaderboard()
    for entry in leaderboard:
        st.markdown(f"- *{entry['name']}: {entry['score']} in *{entry['category']}")

    if st.button("Play Again"):
        for key in ["quiz_started", "selected_category", "questions", "current_q",
                    "score", "answer_selected", "selected_option", "show_result"]:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("MAIN.py")
    st.stop()

# Show Question
q = questions[current_q]
st.markdown(f"### Q{current_q + 1}: {q['question']}")

# Show Options
for option in q["options"]:
    if st.session_state.answer_selected:
        correct = option == q["answer"]
        selected = option == st.session_state.selected_option
        if correct:
            st.success(f"{option} ✅")
        elif selected:
            st.error(f"{option} ❌")
        else:
            st.button(option, disabled=True)
    else:
        if st.button(option):
            st.session_state.answer_selected = True
            st.session_state.selected_option = option
            if option == q["answer"]:
                st.session_state.score += 1
            st.experimental_rerun()

# Next Button
if st.session_state.answer_selected:
    if st.button("Next"):
        st.session_state.current_q += 1
        st.session_state.answer_selected = False
        st.session_state.selected_option = None
        if st.session_state.current_q >= len(questions):
            st.session_state.show_result = True
        st.experimental_rerun()