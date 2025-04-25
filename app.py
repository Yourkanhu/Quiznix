import streamlit as st
import os
import json
import random
import time
from pathlib import Path
from utils import send_otp, verify_entered_otp

# -------------------- SETUP --------------------
st.set_page_config(
    page_title="Quiznix",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------- PERSISTENT LOGIN SETUP --------------------
USER_DATA_FILE = "user_session.json"

def save_user_session(email, name):
    """Save user session data to local file"""
    session_data = {"email": email, "name": name, "timestamp": time.time()}
    Path(USER_DATA_FILE).write_text(json.dumps(session_data))

def load_user_session():
    """Load user session data from local file"""
    try:
        if os.path.exists(USER_DATA_FILE):
            data = json.loads(Path(USER_DATA_FILE).read_text())
            # Check if session is older than 30 days
            if time.time() - data.get("timestamp", 0) < 30 * 24 * 60 * 60:
                return data
            else:
                os.remove(USER_DATA_FILE)
    except:
        pass
    return None

def clear_user_session():
    """Clear user session data"""
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)

# -------------------- THEME & STYLES --------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        .main {
            background: linear-gradient(135deg, #0B2E33 0%, #1c1c2d 100%);
            color: white;
        }
        
        .stButton>button {
            background: linear-gradient(90deg, #4F7C82 0%, #93B1B5 100%);
            color: black;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px #B8E3E9;
        }
        
        .stRadio>div {
            background: #1c1c2d;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #4F7C82;
        }
        
        .stTextInput>div>div>input {
            background: #1c1c2d !important;
            color: white !important;
            border: 1px solid #4F7C82 !important;
        }
        
        h1, h2, h3 {
            color: #B8E3E9 !important;
            text-align: center;
        }
        
        .quiz-card {
            background: #1c1c2d;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #4F7C82;
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
            background: linear-gradient(90deg, #4F7C82 0%, #93B1B5 100%);
            border-radius: 10px;
            transition: width 0.5s;
        }
        
        .home-button {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 1000;
        }
        
        .home-button button {
            background: #0B2E33 !important;
            color: #B8E3E9 !important;
            border: 1px solid #B8E3E9 !important;
            border-radius: 5px;
            padding: 5px 10px;
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

# Check for existing session on app start
if not st.session_state.get("verified"):
    existing_session = load_user_session()
    if existing_session:
        st.session_state.update({
            "email": existing_session["email"],
            "name": existing_session["name"],
            "verified": True,
            "stage": "category"
        })

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

# -------------------- APP SCREENS --------------------
st.markdown("<h1 style='text-align:center;'>Welcome to Quiznix</h1>", unsafe_allow_html=True)

# Add logout button if logged in
if st.session_state.get("verified"):
    if st.sidebar.button("🚪 Logout"):
        clear_user_session()
        st.session_state.clear()
        st.session_state.update(defaults)
        st.rerun()

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
            save_user_session(st.session_state.email, name)  # Save session
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
            st.session_state.score = 0
            st.session_state.stage = "quiz"
            st.rerun()
        else:
            st.error("No questions available. Try another category.")

# 6. QUIZ SCREEN
elif st.session_state.stage == "quiz":
    q_index = st.session_state.q_index
    questions = st.session_state.questions
    
    # Home button
    st.markdown("""
        <div class="home-button">
            <button onclick="window.streamlitScriptHostCommunication.comm.sendMessage({type: 'SET_QUERY_PARAMS', queryParams: {'home': 'true'}});" 
                style="background: #0B2E33; color: #B8E3E9; border: 1px solid #B8E3E9; border-radius: 5px; padding: 5px 10px; cursor: pointer;">
                🏠 Home
            </button>
        </div>
    """, unsafe_allow_html=True)
    
    if st.query_params.get("home") == "true":
        st.session_state.show_confirm_home = True
    
    if q_index < st.session_state.num_questions:
        q = questions[q_index]
        st.markdown(f"""
            <div class="quiz-card">
                <h3>Q{q_index+1}. {q['question']}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Modified radio button with index=None to prevent auto-selection
        selected = st.radio(
            "Choose an option:", 
            q["shuffled_options"], 
            key=f"q_{q_index}",
            index=None  # No option selected by default
        )
        
        # Home Button Confirmation
        if st.session_state.show_confirm_home:
            st.warning("Are you sure you want to quit the quiz?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Quit"):
                    st.session_state.stage = "category"
                    st.session_state.show_confirm_home = False
                    st.query_params.clear()
                    st.rerun()
            with col2:
                if st.button("No, Continue"):
                    st.session_state.show_confirm_home = False
                    st.query_params.clear()
                    st.rerun()
        
        if st.button("Submit Answer", key=f"submit_{q_index}"):
            if selected is None:
                st.warning("Please select an answer before submitting!")
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
                st.session_state.answer_shown = False
                st.rerun()
    
    # QUIZ COMPLETED
    else:
        st.balloons()  # Confetti animation
        st.markdown(f"""
            <div style="text-align:center;">
                <h2>🎉 Quiz Completed!</h2>
                <h3>Your Score: {min(st.session_state.score, st.session_state.num_questions)}/{st.session_state.num_questions}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{int((min(st.session_state.score, st.session_state.num_questions)/st.session_state.num_questions)*100)}%"></div>
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