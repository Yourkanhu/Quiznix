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

# -------------------- ORANGE-BLACK NEON THEME & STYLES --------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        .main {
            background: #0a0a0a;
            color: #ffffff;
        }
        
        .stButton>button {
            background: linear-gradient(90deg, #ff7b00 0%, #ff5500 100%);
            color: #000000;
            font-weight: bold;
            border: none;
            border-radius: 12px;
            padding: 12px 28px;
            transition: all 0.3s;
            box-shadow: 0 0 15px rgba(255, 123, 0, 0.5);
            border: 1px solid #ff7b00;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 25px rgba(255, 123, 0, 0.8);
        }
        
        .stRadio>div {
            background: rgba(40, 40, 40, 0.8);
            border-radius: 12px;
            padding: 18px;
            border: 2px solid #ff7b00;
            box-shadow: 0 0 10px rgba(255, 123, 0, 0.3);
        }
        
        /* Prevent auto-selection of first option */
        .stRadio>div>div:first-child {
            display: none !important;
        }
        
        .stTextInput>div>div>input {
            background: rgba(40, 40, 40, 0.8) !important;
            color: white !important;
            border: 2px solid #ff7b00 !important;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 0 10px rgba(255, 123, 0, 0.2);
            transition: all 0.3s;
        }
        
        /* 3D box effect and animation for input fields */
        .stTextInput>div>div>input:focus {
            box-shadow: 0 0 20px rgba(255, 123, 0, 0.5);
            transform: translateY(-2px);
            border: 2px solid #ffaa00 !important;
        }
        
        /* Hover effect for input fields */
        .stTextInput>div>div>input:hover {
            box-shadow: 0 0 15px rgba(255, 123, 0, 0.4);
        }
        
        h1, h2, h3 {
            color: #ff7b00 !important;
            text-align: center;
            text-shadow: 0 0 10px rgba(255, 123, 0, 0.5);
        }
        
        .quiz-card {
            background: rgba(40, 40, 40, 0.8);
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #ff7b00;
            margin-bottom: 25px;
            box-shadow: 0 0 20px rgba(255, 123, 0, 0.3);
        }
        
        .progress-bar {
            height: 20px;
            background: rgba(40, 40, 40, 0.8);
            border-radius: 10px;
            margin: 15px 0;
            box-shadow: 0 0 10px rgba(255, 123, 0, 0.2);
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff7b00 0%, #ff5500 100%);
            border-radius: 10px;
            transition: width 0.5s;
            box-shadow: 0 0 10px rgba(255, 123, 0, 0.5);
        }
        
        /* Home button positioning */
        .home-btn {
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 100;
        }
        
        /* Timer styling */
        .timer-container {
            position: fixed;
            top: 15px;
            left: 15px;
            z-index: 100;
            background: rgba(40, 40, 40, 0.9);
            padding: 8px 15px;
            border-radius: 20px;
            border: 2px solid #ff7b00;
            box-shadow: 0 0 10px rgba(255, 123, 0, 0.3);
        }
        
        .timer {
            color: #ff7b00;
            font-weight: bold;
            font-size: 1.1rem;
            text-shadow: 0 0 5px rgba(255, 123, 0, 0.5);
        }
        
        .timer-warning {
            color: #ff0000;
            animation: pulse 0.5s infinite alternate;
        }
        
        @keyframes pulse {
            from { opacity: 1; }
            to { opacity: 0.7; }
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
    "show_confirm_home": False,
    "start_time": None,
    "question_start_time": None,
    "time_left": 30  # 30 seconds per question
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
            questions = data.get("questions", [])
            return questions
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return []

def save_to_leaderboard():
    """Save user score to leaderboard.json."""
    entry = {
        "name": st.session_state.name,
        "score": min(st.session_state.score, st.session_state.num_questions),
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

def update_timer():
    """Update the timer and handle timeouts."""
    if st.session_state.stage == "quiz" and st.session_state.question_start_time:
        elapsed = time.time() - st.session_state.question_start_time
        st.session_state.time_left = max(0, 30 - int(elapsed))
        
        if st.session_state.time_left <= 0:
            st.session_state.selected_option = None
            st.session_state.answer_shown = True
            st.error("⏰ Time's up! Moving to next question.")
            time.sleep(1.5)
            st.session_state.q_index += 1
            if st.session_state.q_index < st.session_state.num_questions:
                st.session_state.question_start_time = time.time()
                st.session_state.time_left = 30
            st.session_state.answer_shown = False
            st.rerun()

# -------------------- APP SCREENS --------------------
st.markdown("<h1 style='text-align:center;'>Welcome to Quiznix</h1>", unsafe_allow_html=True)

# Global home button (only for quiz screens)
if st.session_state.stage in ["quiz", "suggest"]:
    st.markdown("""
        <div class="home-btn">
            <button onclick="window.streamlitScriptHost.requestRerun({'stage': 'confirm_home'})" style="
                background: linear-gradient(90deg, #ff3d00 0%, #ff1a00 100%);
                color: white;
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                font-size: 20px;
                cursor: pointer;
                box-shadow: 0 0 15px rgba(255, 61, 0, 0.7);
                transition: all 0.3s;
            " onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 0 20px rgba(255, 61, 0, 0.9)'" 
            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 0 15px rgba(255, 61, 0, 0.7)'">🏠</button>
        </div>
    """, unsafe_allow_html=True)

# Timer display (only for quiz screen)
if st.session_state.stage == "quiz":
    update_timer()
    timer_class = "timer-warning" if st.session_state.time_left <= 10 else "timer"
    st.markdown(f"""
        <div class="timer-container">
            <span class="{timer_class}">⏱️ {st.session_state.time_left}s</span>
        </div>
    """, unsafe_allow_html=True)

# 1. EMAIL SCREEN
if st.session_state.stage == "email":
    st.subheader("Enter Your Email")
    email = st.text_input("Email", placeholder="example@email.com", key="email_input")
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
    entered_otp = st.text_input("Enter 4-digit OTP", max_chars=4, key="otp_input")
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
    name = st.text_input("Name", placeholder="John Doe", key="name_input")
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
            if st.button(cat.capitalize(), key=f"cat_{i}"):
                st.session_state.category = cat
                st.session_state.stage = "choose_num"
                st.rerun()

# 5. NUMBER OF QUESTIONS
elif st.session_state.stage == "choose_num":
    st.subheader(f"Select Questions for {st.session_state.category.capitalize()}")
    available_questions = len(load_questions(st.session_state.category))
    max_questions = min(20, available_questions)
    
    num = st.slider(
        "Number of Questions",
        min_value=5,
        max_value=max_questions,
        value=min(10, max_questions),
        step=5,
        help=f"Total available: {available_questions} questions"
    )
    
    if st.button("Start Quiz"):
        questions = load_questions(st.session_state.category)
        if questions:
            selected_qs = random.sample(questions, min(num, len(questions)))
            for q in selected_qs:
                q["shuffled_options"] = random.sample(q["options"], len(q["options"]))
            
            st.session_state.questions = selected_qs
            st.session_state.num_questions = len(selected_qs)
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.session_state.question_start_time = time.time()
            st.session_state.time_left = 30
            st.session_state.stage = "quiz"
            st.rerun()
        else:
            st.error("No questions available. Try another category.")

# 6. QUIZ SCREEN
elif st.session_state.stage == "quiz":
    # Handle home confirmation
    if st.session_state.get("stage") == "confirm_home":
        st.session_state.show_confirm_home = True
        st.session_state.stage = "quiz"
    
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
    
    # Quiz container
    with st.container():
        q_index = st.session_state.q_index
        questions = st.session_state.questions
        
        if q_index < st.session_state.num_questions:
            q = questions[q_index]
            st.markdown(f"""
                <div class="quiz-card">
                    <h3>Q{q_index+1}. {q['question']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            selected = st.radio(
                "Choose an option:", 
                q["shuffled_options"], 
                key=f"q_{q_index}",
                index=None  # No default selection
            )
            
            if st.button("Submit Answer", key=f"submit_{q_index}"):
                if selected is None:
                    st.warning("Please select an option!")
                else:
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
                    if st.session_state.q_index < st.session_state.num_questions:
                        st.session_state.question_start_time = time.time()
                        st.session_state.time_left = 30
                    st.session_state.answer_shown = False
                    st.rerun()
        
        # QUIZ COMPLETED
        else:
            st.balloons()
            correct_answers = min(st.session_state.score, st.session_state.num_questions)
            st.markdown(f"""
                <div style="text-align:center;">
                    <h2>🎉 Quiz Completed!</h2>
                    <h3>Your Score: {correct_answers}/{st.session_state.num_questions}</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:{int((correct_answers/st.session_state.num_questions)*100)}%"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            save_to_leaderboard()
            
            if st.button("📝 Suggest a Question", key="suggest_btn"):
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