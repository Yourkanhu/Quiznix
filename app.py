import streamlit as st
import os
import json
import random
import time
from pathlib import Path
from utils import send_otp, verify_entered_otp

# -------------------- SOUND SYSTEM SETUP (STREAMLIT CLOUD COMPATIBLE) --------------------
def play_sound(sound_type):
    """HTML5 audio implementation for Streamlit Cloud"""
    sound_files = {
        'click': "assets/sound/click.mp3",
        'correct': "assets/sound/correct.mp3",
        'wrong': "assets/sound/wrong.mp3"
    }
    
    file_path = sound_files.get(sound_type)
    if not file_path or not os.path.exists(file_path):
        st.error(f"Sound file not found: {file_path}")
        return False
        
    audio_html = f"""
        <audio autoplay>
            <source src="{file_path}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# -------------------- APP SETUP --------------------
st.set_page_config(
    page_title="Quiznix",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------- PERSISTENT LOGIN SETUP --------------------
USER_DATA_FILE = "user_session.json"

def save_user_session(email, name):
    session_data = {"email": email, "name": name, "timestamp": time.time()}
    Path(USER_DATA_FILE).write_text(json.dumps(session_data))

def load_user_session():
    try:
        if os.path.exists(USER_DATA_FILE):
            data = json.loads(Path(USER_DATA_FILE).read_text())
            if time.time() - data.get("timestamp", 0) < 30 * 24 * 60 * 60:
                return data
            else:
                os.remove(USER_DATA_FILE)
    except:
        pass
    return None

def clear_user_session():
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)

# -------------------- ROYAL GREEN THEME --------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        .main {
            background: linear-gradient(135deg, #013a30 0%, #025f4c 100%);
            color: white;
        }
        
        .stButton>button {
            background: linear-gradient(90deg, #025f4c 0%, #02a676 100%);
            color: white;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px #02a676;
        }
        
        .stRadio>div {
            background: #013a30;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #02a676;
        }
        
        .stTextInput>div>div>input {
            background: #013a30 !important;
            color: white !important;
            border: 1px solid #02a676 !important;
        }
        
        h1, h2, h3 {
            color: #b8e3d5 !important;
            text-align: center;
        }
        
        .quiz-card {
            background: #013a30;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #02a676;
            margin-bottom: 20px;
        }
        
        .progress-bar {
            height: 20px;
            background: #013a30;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #025f4c 0%, #02a676 100%);
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
    "show_confirm_home": False,
    "language": "english"
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Check for existing session
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
    try:
        with open(f"quizdata/{category}.json", "r") as f:
            data = json.load(f)
            questions = data.get("questions", [])
            
            lang = st.session_state.language
            processed_questions = []
            
            for q in questions:
                if "english" in q and "hinglish" in q:
                    processed_q = {
                        "question": q[lang]["question"],
                        "options": q[lang]["options"],
                        "answer": q[lang]["answer"],
                        "original_data": q
                    }
                else:
                    processed_q = {
                        "question": q["question"],
                        "options": q["options"],
                        "answer": q["answer"],
                        "original_data": q
                    }
                
                processed_questions.append(processed_q)
            
            return processed_questions
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return []

def save_to_leaderboard():
    entry = {
        "name": st.session_state.name,
        "score": min(st.session_state.score, st.session_state.num_questions),
        "category": st.session_state.category,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "language": st.session_state.language
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

# -------------------- LANGUAGE SWITCHER --------------------
def language_switcher():
    st.markdown(f"""
        <div style="position: fixed; top: 10px; right: 10px; z-index: 1000;">
            <button onclick="window.streamlitScriptHostCommunication.comm.sendMessage({{type: 'SET_QUERY_PARAMS', queryParams: {{'toggle_lang': 'true'}}}});" 
                style="background: #013a30 !important; color: #b8e3d5 !important; border: 1px solid #02a676 !important; border-radius: 5px; padding: 5px 10px; cursor: pointer;">
                {'हिंदी' if st.session_state.language == 'english' else 'English'}
            </button>
        </div>
    """, unsafe_allow_html=True)

# -------------------- APP SCREENS --------------------
st.markdown("<h1 style='text-align:center;'>Welcome to Quiznix</h1>", unsafe_allow_html=True)

# Language toggle handler
if st.query_params.get("toggle_lang") == "true":
    st.session_state.language = "hinglish" if st.session_state.language == "english" else "english"
    st.query_params.clear()
    st.rerun()

# Show language switcher after email verification
if st.session_state.stage not in ["email", "otp"]:
    language_switcher()

# Logout button
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
        play_sound('click')
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
        play_sound('click')
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
    name = st.text_input("Name", placeholder="John Doe" if st.session_state.language == "english" else "Your Name")
    if st.button("Continue" if st.session_state.language == "english" else "Continue"):
        play_sound('click')
        if name.strip():
            st.session_state.name = name
            save_user_session(st.session_state.email, name)
            st.session_state.stage = "category"
            st.rerun()
        else:
            st.warning("Name cannot be empty." if st.session_state.language == "english" else "Name cannot be empty.")

# 4. CATEGORY SELECTION
elif st.session_state.stage == "category":
    title = "Choose a Quiz Category" if st.session_state.language == "english" else "Choose a Quiz Category"
    st.subheader(title)
    
    categories = [f.split(".")[0] for f in os.listdir("quizdata") if f.endswith(".json")]
    cols = st.columns(4)
    for i, cat in enumerate(categories):
        with cols[i % 4]:
            icon_path = f"assets/icons/{cat}.png"
            if os.path.exists(icon_path):
                st.image(icon_path, width=80)
            if st.button(cat.capitalize(), key=f"cat_{i}"):
                play_sound('click')
                st.session_state.category = cat
                st.session_state.stage = "choose_num"
                st.rerun()

# 5. NUMBER OF QUESTIONS
elif st.session_state.stage == "choose_num":
    if 'language_confirmed' not in st.session_state:
        st.subheader("Choose Question Language / Questions Bhasha Choose Karein")
        lang = st.radio("", ["English", "Hinglish (English+Hindi)"])
        if st.button("Confirm / Confirm karein"):
            play_sound('click')
            st.session_state.language = 'english' if lang == "English" else 'hinglish'
            st.session_state.language_confirmed = True
            st.rerun()
    else:
        title = f"Select Questions for {st.session_state.category.capitalize()}" 
        if st.session_state.language == 'hinglish':
            title = f"{st.session_state.category.capitalize()} Select Questions for"
        
        st.subheader(title)
        
        num = st.slider(
            "Number of Questions" if st.session_state.language == 'english' else "Number of Questions",
            5, 20, 10, step=5
        )
        
        btn_text = "Start Quiz" if st.session_state.language == 'english' else "Start Quiz"
        if st.button(btn_text):
            play_sound('click')
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
                error_msg = "No questions available" if st.session_state.language == 'english' else "No questions available"
                st.error(error_msg)

# 6. QUIZ SCREEN
elif st.session_state.stage == "quiz":
    q_index = st.session_state.q_index
    questions = st.session_state.questions
    
    # Home button
    home_text = "🏠 Home" if st.session_state.language == "english" else "🏠 Home"
    st.markdown(f"""
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1000;">
            <button onclick="window.streamlitScriptHostCommunication.comm.sendMessage({{type: 'SET_QUERY_PARAMS', queryParams: {{'home': 'true'}}}});" 
                style="background: #013a30; color: #b8e3d5; border: 1px solid #02a676; border-radius: 5px; padding: 5px 10px; cursor: pointer;">
                {home_text}
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
        
        radio_label = "Choose an option:" if st.session_state.language == "english" else "Choose an option::"
        
        selected = st.radio(
            radio_label, 
            q["shuffled_options"], 
            key=f"q_{q_index}",
            index=None
        )
        
        # Home Button Confirmation
        if st.session_state.show_confirm_home:
            confirm_text = "Are you sure you want to quit the quiz?" if st.session_state.language == "english" else "Are you sure you want to quit the quiz?"
            yes_text = "Yes, Quit" if st.session_state.language == "english" else "Yes, Quit"
            no_text = "No, Continue" if st.session_state.language == "english" else "Yes, Quit"
            
            st.warning(confirm_text)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(yes_text):
                    play_sound('click')
                    st.session_state.stage = "category"
                    st.session_state.show_confirm_home = False
                    st.query_params.clear()
                    st.rerun()
            with col2:
                if st.button(no_text):
                    play_sound('click')
                    st.session_state.show_confirm_home = False
                    st.query_params.clear()
                    st.rerun()
        
        submit_text = "Submit Answer" if st.session_state.language == "english" else "Submit Answer"
        
        if st.button(submit_text, key=f"submit_{q_index}"):
            play_sound('click')
            if selected is None:
                warning_text = "Please select an answer before submitting!" if st.session_state.language == "english" else "Please select an answer before submitting!"
                st.warning(warning_text)
            else:
                st.session_state.selected_option = selected
                st.session_state.answer_shown = True
                if selected == q["answer"]:
                    play_sound('correct')
                    st.success("✅ Correct!" if st.session_state.language == "english" else "✅ Correct!")
                    st.session_state.score += 1
                else:
                    play_sound('wrong')
                    st.error("❌ Incorrect!" if st.session_state.language == "english" else "❌ Incorrect!")
                    answer_text = "Correct Answer:" if st.session_state.language == "english" else "Correct Answer:"
                    st.info(f"{answer_text} *{q['answer']}*")
                time.sleep(1.5)
                st.session_state.q_index += 1
                st.session_state.answer_shown = False
                st.rerun()
    
    # QUIZ COMPLETED
    else:
        play_sound('correct')
        st.balloons()
        
        completed_text = "Quiz Completed!" if st.session_state.language == "english" else "Quiz Completed!"
        score_text = "Your Score:" if st.session_state.language == "english" else "Your Score:"
        
        st.markdown(f"""
            <div style="text-align:center;">
                <h2>🎉 {completed_text}</h2>
                <h3>{score_text} {min(st.session_state.score, st.session_state.num_questions)}/{st.session_state.num_questions}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{int(min(st.session_state.score, st.session_state.num_questions)/st.session_state.num_questions)*100}%"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        save_to_leaderboard()
        
        home_text = "🏠 Home" if st.session_state.language == "english" else "🏠 Home"
        suggest_text = "📝 Suggest a Question" if st.session_state.language == "english" else "📝 Suggest a Question"
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(home_text):
                play_sound('click')
                st.session_state.stage = "category"
                st.rerun()
        with col2:
            if st.button(suggest_text):
                play_sound('click')
                st.session_state.stage = "suggest"
                st.rerun()

# 7. SUGGESTION SCREEN
elif st.session_state.stage == "suggest":
    title = "Suggest a New Question" if st.session_state.language == "english" else "Suggest a New Question"
    st.subheader(title)
    
    with st.form("suggestion_form"):
        q_label = "Question" if st.session_state.language == "english" else "Question"
        q_placeholder = "Enter your question here..." if st.session_state.language == "english" else "Enter your question here..."
        new_q = st.text_area(q_label, placeholder=q_placeholder)
        
        opts_label = "Options (comma-separated)" if st.session_state.language == "english" else "Options (comma-separated)"
        opts_placeholder = "Option1, Option2, Option3" if st.session_state.language == "english" else "Option1, Option2, Option3, option4"
        new_opts = st.text_input(opts_label, placeholder=opts_placeholder)
        
        ans_label = "Correct Answer" if st.session_state.language == "english" else "Correct Answer"
        ans_placeholder = "Must match one of the options" if st.session_state.language == "english" else "Must match one of the options"
        new_ans = st.text_input(ans_label, placeholder=ans_placeholder)
        
        submit_text = "Submit" if st.session_state.language == "english" else "Submit"
        submitted = st.form_submit_button(submit_text)
        
        if submitted:
            play_sound('click')
            if new_q and new_opts and new_ans:
                suggestion = {
                    "question": new_q,
                    "options": [opt.strip() for opt in new_opts.split(",")],
                    "answer": new_ans.strip(),
                    "language": st.session_state.language
                }
                try:
                    with open("suggestions.json", "a") as f:
                        f.write(json.dumps(suggestion) + "\n")
                    success_text = "Thank you! Your suggestion has been recorded." if st.session_state.language == "english" else "Thank you! Your suggestion has been recorded."
                    st.success(success_text)
                    time.sleep(1)
                    st.session_state.stage = "category"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving suggestion: {e}")
            else:
                warning_text = "Please fill all fields." if st.session_state.language == "english" else "Please fill all fields."
                st.warning(warning_text)

    back_text = "← Back to Home" if st.session_state.language == "english" else "← Back to Home"
    if st.button(back_text):
        play_sound('click')
        st.session_state.stage = "category"
        st.rerun()