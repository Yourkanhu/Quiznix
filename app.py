import streamlit as st
import os
import json
import random
import time
from utils import send_otp, verify_entered_otp

# -------------------- SETUP --------------------
st.set_page_config(
    page_title="Quiznix",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------- THEME & STYLES --------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        .main {
            background: linear-gradient(135deg, #0f0f1a 0%, #1c1c2d 100%);
            color: white;
        }
        
        .stButton>button {
            background: linear-gradient(90deg, #00ffe1 0%, #00b3ff 100%);
            color: black;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px #00ffe1;
        }
        
        .stRadio>div {
            background: #1c1c2d;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #00ffe1;
        }
        
        .stTextInput>div>div>input {
            background: #1c1c2d !important;
            color: white !important;
            border: 1px solid #00ffe1 !important;
        }
        
        h1, h2, h3 {
            color: #00ffe1 !important;
            text-align: center;
        }
        
        .quiz-card {
            background: #1c1c2d;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #00ffe1;
            margin-bottom: 20px;
        }
        
        .progress-bar {
            height: 20px;
            background: #1c1c2d;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ffe1 0%, #00b3ff 100%);
            border-radius: 10px;
            transition: width 0.5s;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE DEFAULTS --------------------
defaults = {
    "stage": "email",
    "email": "",
    "otp": "",
    "name": "",
    "verified": False,
    "category": "",
    "questions": [],
    "score": 0,
    "q_index": 0,
    "num_questions": 10,
    "answer_shown": False,
    "selected_option": None,
    "show_confirm_home": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- HELPER FUNCTIONS --------------------
def load_questions(category):
    """Load questions from JSON file for a category."""
    try:
        with open(f"quizdata/{category}.json", "r") as f:
            data = json.load(f)
            return data.get("questions", [])
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return []

def save_to_leaderboard():
    """Save user score to leaderboard.json."""
    entry = {
        "name": st.session_state.name,
        "score": st.session_state.score,
        "category": st.session_state.category,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        if os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(entry)
        with open("leaderboard.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving leaderboard: {e}")

# -------------------- APP SCREENS --------------------
st.markdown("<h1 style='text-align:center;'>Welcome to Quiznix</h1>", unsafe_allow_html=True)

# 1. EMAIL SCREEN
if st.session_state.stage == "email":
    st.subheader("Enter Your Email")
    email = st.text_input("Email", placeholder="example@email.com")
    if st.button("Send OTP"):
        if "@" in email and "." in email:
            otp = str(random.randint(1000, 9999))
            st.session_state.otp = otp
            st.session_state.email = email
            if send_otp(email, otp):
                st.success("OTP sent successfully!")
                st.session_state.stage = "otp"
                st.rerun()
            else:
                st.error("Failed to send OTP. Try again.")
        else:
            st.warning("Please enter a valid email.")

# 2. OTP SCREEN
elif st.session_state.stage == "otp":
    st.subheader("Verify OTP")
    entered_otp = st.text_input("Enter 4-digit OTP", max_chars=4)
    if st.button("Verify"):
        if verify_entered_otp(entered_otp, st.session_state.otp):
            st.success("OTP Verified! ✅")
            time.sleep(1)
            st.session_state.verified = True
            st.session_state.stage = "name"
            st.rerun()
        else:
            st.error("Incorrect OTP. Try again.")

# 3. NAME SCREEN
elif st.session_state.stage == "name":
    st.subheader("Enter Your Name")
    name = st.text_input("Name", placeholder="John Doe")
    if st.button("Continue"):
        if name.strip():
            st.session_state.name = name
            st.session_state.stage = "category"
            st.rerun()
        else:
            st.warning("Name cannot be empty.")

# 4. CATEGORY SELECTION
elif st.session_state.stage == "category":
    st.subheader("Choose a Quiz Category")
    categories = [f.split(".")[0] for f in os.listdir("quizdata") if f.endswith(".json")]
    cols = st.columns(4)
    for i, cat in enumerate(categories):
        with cols[i % 4]:
            icon_path = f"assets/icons/{cat}.png"
            if os.path.exists(icon_path):
                st.image(icon_path, width=80)
            if st.button(cat.capitalize(), key=f"cat_{i}"):
                st.session_state.category = cat
                st.session_state.stage = "choose_num"
                st.rerun()

# 5. NUMBER OF QUESTIONS
elif st.session_state.stage == "choose_num":
    st.subheader(f"Select Questions for {st.session_state.category.capitalize()}")
    num = st.slider("Number of Questions", 5, 20, 10, step=5)
    if st.button("Start Quiz"):
        questions = load_questions(st.session_state.category)
        if questions:
            selected_qs = random.sample(questions, min(num, len(questions)))
            for q in selected_qs:
                q["shuffled_options"] = random.sample(q["options"], len(q["options"]))
            st.session_state.questions = selected_qs
            st.session_state.num_questions = num
            st.session_state.q_index = 0
            st.session_state.stage = "quiz"
            st.rerun()
        else:
            st.error("No questions available. Try another category.")

# 6. QUIZ SCREEN
elif st.session_state.stage == "quiz":
    q_index = st.session_state.q_index
    questions = st.session_state.questions
    
    if q_index < st.session_state.num_questions:
        q = questions[q_index]
        st.markdown(f"""
            <div class="quiz-card">
                <h3>Q{q_index+1}. {q['question']}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        selected = st.radio("Choose an option:", q["shuffled_options"], key=f"q_{q_index}")
        
        # Home Button with Confirmation
        if st.session_state.show_confirm_home:
            st.warning("Are you sure you want to quit the quiz?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Quit"):
                    st.session_state.stage = "category"
                    st.session_state.show_confirm_home = False
                    st.rerun()
            with col2:
                if st.button("No, Continue"):
                    st.session_state.show_confirm_home = False
                    st.rerun()
        else:
            st.button("🏠 Home", on_click=lambda: st.session_state.update({"show_confirm_home": True}))
        
        if st.button("Submit Answer", key=f"submit_{q_index}"):
            st.session_state.selected_option = selected
            st.session_state.answer_shown = True
            if selected == q["answer"]:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error("❌ Incorrect!")
                st.info(f"Correct Answer: **{q['answer']}**")
            time.sleep(1.5)
            st.session_state.q_index += 1
            st.session_state.answer_shown = False
            st.rerun()
    
    # QUIZ COMPLETED
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align:center;">
                <h2>🎉 Quiz Completed!</h2>
                <h3>Your Score: {st.session_state.score}/{st.session_state.num_questions}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{int((st.session_state.score/st.session_state.num_questions)*100)}%"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        save_to_leaderboard()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Home"):
                st.session_state.stage = "category"
                st.rerun()
        with col2:
            if st.button("📝 Suggest a Question"):
                st.session_state.stage = "suggest"
                st.rerun()

# 7. SUGGESTION SCREEN
elif st.session_state.stage == "suggest":
    st.subheader("Suggest a New Question")
    with st.form("suggestion_form"):
        new_q = st.text_area("Question", placeholder="Enter your question here...")
        new_opts = st.text_input("Options (comma-separated)", placeholder="Option1, Option2, Option3")
        new_ans = st.text_input("Correct Answer", placeholder="Must match one of the options")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if new_q and new_opts and new_ans:
                suggestion = {
                    "question": new_q,
                    "options": [opt.strip() for opt in new_opts.split(",")],
                    "answer": new_ans.strip()
                }
                try:
                    with open("suggestions.json", "a") as f:
                        f.write(json.dumps(suggestion) + "\n")
                    st.success("Thank you! Your suggestion has been recorded.")
                    time.sleep(1)
                    st.session_state.stage = "category"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving suggestion: {e}")
            else:
                st.warning("Please fill all fields.")

    if st.button("← Back to Home"):
        st.session_state.stage = "category"
        st.rerun()