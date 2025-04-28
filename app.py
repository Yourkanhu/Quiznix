import streamlit as st
import os
import json
import random
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
from utils import send_otp, verify_entered_otp

# -------------------- SETUP --------------------
st.set_page_config(
    page_title="Quiznix",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------- CONSTANTS --------------------
PRIMARY_COLOR = "#2e8b57"
SECONDARY_COLOR = "#3cb371"
ACCENT_COLOR = "#90ee90"
DARK_COLOR = "#1a1a1a"
LIGHT_COLOR = "#f8f9fa"
USER_DATA_FILE = "user_session.json"
USER_STATS_FILE = "user_stats.json"
ACHIEVEMENTS = {
    "first_quiz": {"name": "First Quiz", "icon": "🥇", "desc": "Completed your first quiz"},
    "high_score": {"name": "High Scorer", "icon": "🏆", "desc": "Scored 90% or above in any quiz"},
    "category_master": {"name": "Category Master", "icon": "🎯", "desc": "Completed all quizzes in a category"},
    "streak_3": {"name": "3-Day Streak", "icon": "🔥", "desc": "Played quizzes for 3 consecutive days"},
    "streak_7": {"name": "7-Day Streak", "icon": "🚀", "desc": "Played quizzes for 7 consecutive days"},
    "suggestor": {"name": "Contributor", "icon": "💡", "desc": "Suggested a question that was approved"}
}

# -------------------- LANGUAGE CONTENT --------------------
CONTENT = {
    "english": {
        "welcome": "Welcome to Quiznix",
        "logout": "Logout",
        "dashboard": "Dashboard",
        "play_quiz": "Play Quiz",
        "choose_category": "Choose a Quiz Category",
        "questions": "Questions",
        "time_spent": "Time Spent",
        "total_points": "Total Points",
        "category_performance": "Category Performance",
        "achievements": "Your Achievements",
        "no_achievements": "No achievements yet. Keep playing!",
        "start_quiz": "Start Quiz",
        "submit": "Submit",
        "correct": "✅ Correct!",
        "incorrect": "❌ Incorrect!",
        "quiz_completed": "Quiz Completed!",
        "your_score": "Your Score",
        "suggest_question": "Suggest a Question"
    },
    "hinglish": {
        "welcome": "Quiznix mein aapka swagat hai",
        "logout": "Logout karein",
        "dashboard": "Dashboard",
        "play_quiz": "Quiz khelein",
        "choose_category": "Quiz category chuniye",
        "questions": "Sawaal",
        "time_spent": "Kitna time diya",
        "total_points": "Total points",
        "category_performance": "Category performance",
        "achievements": "Aapke achievements",
        "no_achievements": "Abhi koi achievements nahi. Khelte raho!",
        "start_quiz": "Quiz shuru karein",
        "submit": "Submit karein",
        "correct": "✅ Sahi jawab!",
        "incorrect": "❌ Galat jawab!",
        "quiz_completed": "Quiz poora hua!",
        "your_score": "Aapka score",
        "suggest_question": "Question suggest karein"
    }
}

def get_text(key):
    """Get text in current language"""
    return CONTENT[st.session_state.language][key]

# -------------------- UTILITY FUNCTIONS --------------------
def load_user_stats(email):
    """Load user statistics from JSON file"""
    try:
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r") as f:
                all_stats = json.load(f)
                return all_stats.get(email, {
                    "quizzes_played": 0,
                    "total_score": 0,
                    "categories": {},
                    "achievements": [],
                    "time_spent": 0,
                    "last_played": None,
                    "streak": 0
                })
    except:
        pass
    return {
        "quizzes_played": 0,
        "total_score": 0,
        "categories": {},
        "achievements": [],
        "time_spent": 0,
        "last_played": None,
        "streak": 0
    }

def save_user_stats(email, stats):
    """Save user statistics to JSON file"""
    try:
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, "r") as f:
                all_stats = json.load(f)
        else:
            all_stats = {}
        
        all_stats[email] = stats
        
        with open(USER_STATS_FILE, "w") as f:
            json.dump(all_stats, f, indent=2)
    except Exception as e:
        st.error(f"Error saving user stats: {e}")

def update_user_stats(email, category, score, num_questions, time_taken):
    """Update user statistics after quiz completion"""
    stats = load_user_stats(email)
    
    # Basic stats
    stats["quizzes_played"] += 1
    stats["total_score"] += score
    stats["time_spent"] += time_taken
    
    # Category stats
    if category not in stats["categories"]:
        stats["categories"][category] = {
            "attempts": 0,
            "total_score": 0,
            "highest_score": 0
        }
    
    stats["categories"][category]["attempts"] += 1
    stats["categories"][category]["total_score"] += score
    if score > stats["categories"][category]["highest_score"]:
        stats["categories"][category]["highest_score"] = score
    
    # Streak calculation
    today = datetime.now().date()
    last_played = datetime.strptime(stats["last_played"], "%Y-%m-%d").date() if stats["last_played"] else None
    
    if last_played:
        delta = (today - last_played).days
        if delta == 1:  # Consecutive day
            stats["streak"] += 1
        elif delta > 1:  # Broken streak
            stats["streak"] = 1
    else:
        stats["streak"] = 1
    
    stats["last_played"] = today.strftime("%Y-%m-%d")
    
    # Check for achievements
    achievements = check_achievements(stats)
    for achievement in achievements:
        if achievement not in stats["achievements"]:
            stats["achievements"].append(achievement)
    
    save_user_stats(email, stats)
    return stats

def check_achievements(stats):
    """Check which achievements user has earned"""
    earned = []
    
    if stats["quizzes_played"] == 1:
        earned.append("first_quiz")
    
    for cat, data in stats["categories"].items():
        if data["highest_score"] >= 0.9 * data["attempts"] * 10:  # Assuming 10 questions per quiz
            earned.append("high_score")
    
    if len(stats["categories"]) >= 5:  # Assuming 5 categories exist
        earned.append("category_master")
    
    if stats["streak"] >= 3:
        earned.append("streak_3")
    if stats["streak"] >= 7:
        earned.append("streak_7")
    
    return earned

# -------------------- PERSISTENT LOGIN SETUP --------------------
def save_user_session(email, name):
    """Save user session data to local file"""
    session_data = {"email": email, "name": name, "timestamp": time.time()}
    Path(USER_DATA_FILE).write_text(json.dumps(session_data))

def load_user_session():
    """Load user session data from local file"""
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
    """Clear user session data"""
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)

# -------------------- UI COMPONENTS --------------------
def top_navigation():
    """Create horizontal navigation bar with icon-based language selector"""
    if st.session_state.get("verified") and st.session_state.stage == "category":
        col1, col2, col3 = st.columns([6, 1, 1])
        with col2:
            # Icon-based language toggle with tooltip
            if st.button("🌐", 
                        key="lang_switch",
                        help="Switch to Hinglish" if st.session_state.language == "english" else "Switch to English"):
                st.session_state.language = "hinglish" if st.session_state.language == "english" else "english"
                st.rerun()
        with col3:
            # Logout button remains same
            if st.button("🚪", key="logout_btn", help=get_text("logout")):
                clear_user_session()
                st.session_state.clear()
                st.rerun()

def render_user_dashboard():
    """Render the user statistics dashboard with new layout"""
    if not st.session_state.get("stats"):
        return
    
    stats = st.session_state.stats
    
    # Header with welcome message
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:24px;">
            <h2>📊 {get_text('dashboard')}</h2>
            <p style="font-size:18px;">{get_text('welcome')}, <strong>{st.session_state.name}</strong>!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Main stats cards in 3 columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="stats-card" style="text-align:center;">
                <div style="font-size:24px;">🎯</div>
                <h3>{stats['quizzes_played']}</h3>
                <p>{get_text('questions')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="stats-card" style="text-align:center;">
                <div style="font-size:24px;">📝</div>
                <h3>{stats['total_score']}</h3>
                <p>{get_text('total_points')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="stats-card" style="text-align:center;">
                <div style="font-size:24px;">⏱️</div>
                <h3>{stats['time_spent']//60}m</h3>
                <p>{get_text('time_spent')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Category performance
    st.subheader(get_text("category_performance"))
    if stats["categories"]:
        categories = list(stats["categories"].keys())
        avg_scores = [
            stats["categories"][cat]["total_score"] / stats["categories"][cat]["attempts"] 
            for cat in categories
        ]
        
        fig = px.bar(
            x=categories,
            y=avg_scores,
            labels={"x": "Category", "y": "Average Score"},
            color=avg_scores,
            color_continuous_scale=[PRIMARY_COLOR, ACCENT_COLOR]
        )
        fig.update_layout(
            plot_bgcolor=DARK_COLOR,
            paper_bgcolor=DARK_COLOR,
            font_color=LIGHT_COLOR
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(get_text("no_achievements"))
    
    # Achievements
    st.subheader(get_text("achievements"))
    if stats["achievements"]:
        for ach_id in stats["achievements"]:
            ach = ACHIEVEMENTS[ach_id]
            st.markdown(f"""
                <div class="achievement-card animate-in">
                    <div class="achievement-icon">{ach['icon']}</div>
                    <div>
                        <h4>{ach['name']}</h4>
                        <p>{ach['desc']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info(get_text("no_achievements"))

# -------------------- THEME & STYLES --------------------
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        * {{
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s ease;
        }}
        
        .main {{
            background-color: {DARK_COLOR};
            color: {LIGHT_COLOR};
        }}
        
        .stButton>button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            padding: 12px 28px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stButton>button:hover {{
            background-color: {SECONDARY_COLOR};
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .stRadio>div {{
            background: rgba(46, 139, 87, 0.1);
            border-radius: 12px;
            padding: 16px;
            border: 2px solid {PRIMARY_COLOR};
        }}
        
        .stTextInput>div>div>input {{
            background: rgba(46, 139, 87, 0.1) !important;
            color: {LIGHT_COLOR} !important;
            border: 2px solid {PRIMARY_COLOR} !important;
            border-radius: 8px !important;
        }}
        
        h1, h2, h3 {{
            color: {ACCENT_COLOR} !important;
            text-align: center;
            font-weight: 700 !important;
        }}
        
        .quiz-card {{
            background: rgba(46, 139, 87, 0.15);
            padding: 24px;
            border-radius: 16px;
            border-left: 6px solid {PRIMARY_COLOR};
            margin-bottom: 24px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .progress-bar {{
            height: 24px;
            background: rgba(46, 139, 87, 0.1);
            border-radius: 12px;
            margin: 16px 0;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {PRIMARY_COLOR}, {SECONDARY_COLOR});
            border-radius: 12px;
            transition: width 0.8s cubic-bezier(0.65, 0, 0.35, 1);
        }}
        
        .stats-card {{
            background: rgba(46, 139, 87, 0.15);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid {PRIMARY_COLOR};
        }}
        
        .achievement-card {{
            background: rgba(144, 238, 144, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .achievement-icon {{
            font-size: 24px;
            flex-shrink: 0;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .animate-in {{
            animation: fadeIn 0.5s ease-out forwards;
        }}
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
    "language": "english",
    "quiz_start_time": None,
    "stats": None
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
            "stage": "category",
            "stats": load_user_stats(existing_session["email"])
        })

# -------------------- HELPER FUNCTIONS --------------------
def load_questions(category):
    """Load questions from JSON file with bilingual support"""
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
    """Save user score to leaderboard.json"""
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

# -------------------- APP SCREENS --------------------
top_navigation()  # This will only show on dashboard now

st.markdown(f"<h1 style='text-align:center;'>{get_text('welcome')}</h1>", unsafe_allow_html=True)

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
    if st.button(get_text("submit")):
        if name.strip():
            st.session_state.name = name
            save_user_session(st.session_state.email, name)
            st.session_state.stats = load_user_stats(st.session_state.email)
            st.session_state.stage = "category"
            st.rerun()
        else:
            st.warning("Name cannot be empty.")

# 4. CATEGORY SELECTION
elif st.session_state.stage == "category":
    # Dashboard tab
    tab1, tab2 = st.tabs([f"📊 {get_text('dashboard')}", f"🎯 {get_text('play_quiz')}"])
    
    with tab1:
        render_user_dashboard()
    
    with tab2:
        st.subheader(get_text("choose_category"))
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
    st.subheader(f"{get_text('choose_category')}: {st.session_state.category.capitalize()}")
    
    num = st.slider(get_text("questions"), 5, 20, 10, step=5)
    
    if st.button(get_text("start_quiz")):
        questions = load_questions(st.session_state.category)
        if questions:
            selected_qs = random.sample(questions, min(num, len(questions)))
            for q in selected_qs:
                q["shuffled_options"] = random.sample(q["options"], len(q["options"]))
            st.session_state.questions = selected_qs
            st.session_state.num_questions = num
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.quiz_start_time = time.time()
            st.session_state.stage = "quiz"
            st.rerun()
        else:
            st.error("No questions available")

# 6. QUIZ SCREEN
elif st.session_state.stage == "quiz":
    q_index = st.session_state.q_index
    questions = st.session_state.questions
    
    # Home button
    st.markdown(f"""
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1000;">
            <button onclick="window.streamlitScriptHostCommunication.comm.sendMessage({{'type': 'SET_QUERY_PARAMS', 'queryParams': {{'home': 'true'}}}});" 
                style="background: {DARK_COLOR}; color: {ACCENT_COLOR}; border: 1px solid {ACCENT_COLOR}; border-radius: 5px; padding: 5px 10px; cursor: pointer;">
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
        
        selected = st.radio(f"{get_text('questions')} {q_index+1}/{st.session_state.num_questions}", 
                          q["shuffled_options"], key=f"q_{q_index}", index=None)
        
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
        
        if st.button(get_text("submit"), key=f"submit_{q_index}"):
            if selected is None:
                st.warning("Please select an answer before submitting!")
            else:
                st.session_state.selected_option = selected
                st.session_state.answer_shown = True
                if selected == q["answer"]:
                    st.success(get_text("correct"))
                    st.session_state.score += 1
                else:
                    st.error(get_text("incorrect"))
                    st.info(f"Correct Answer: **{q['answer']}**")
                time.sleep(1.5)
                st.session_state.q_index += 1
                st.session_state.answer_shown = False
                st.rerun()
    
    # QUIZ COMPLETED
    else:
        st.balloons()
        time_taken = int(time.time() - st.session_state.quiz_start_time)
        update_user_stats(
            st.session_state.email,
            st.session_state.category,
            st.session_state.score,
            st.session_state.num_questions,
            time_taken
        )
        
        st.markdown(f"""
            <div style="text-align:center;">
                <h2>🎉 {get_text('quiz_completed')}</h2>
                <h3>{get_text('your_score')}: {min(st.session_state.score, st.session_state.num_questions)}/{st.session_state.num_questions}</h3>
                <p>Time taken: {time_taken//60}m {time_taken%60}s</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{int(min(st.session_state.score, st.session_state.num_questions)/st.session_state.num_questions)*100}%"></div>
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
            if st.button(f"📝 {get_text('suggest_question')}"):
                st.session_state.stage = "suggest"
                st.rerun()

# 7. SUGGESTION SCREEN
elif st.session_state.stage == "suggest":
    st.subheader(f"📝 {get_text('suggest_question')}")
    
    with st.form("suggestion_form"):
        new_q = st.text_area(get_text('questions'), placeholder="Enter your question here...")
        new_opts = st.text_input("Options (comma-separated)", placeholder="Option1, Option2, Option3")
        new_ans = st.text_input("Correct Answer", placeholder="Must match one of the options")
        
        submitted = st.form_submit_button(get_text("submit"))
        
        if submitted:
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