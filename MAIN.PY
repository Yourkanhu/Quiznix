import streamlit as st
import json
import os

st.set_page_config(page_title="Quiznix", page_icon=":game_die:", layout="wide")

# Load custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

categories = {
    "Funny": "funny.png",
    "Knowledge": "knowledge.png",
    "Math": "math.png",
    "Science": "science.png",
    "History": "history.png"
}

# Store selected category
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

st.title("Welcome to Quiznix!")
st.markdown("#### Choose your quiz category")

# Show categories in columns
cols = st.columns(len(categories))

for idx, (cat, icon) in enumerate(categories.items()):
    with cols[idx]:
        btn = st.button("", key=cat)
        if btn:
            st.session_state.selected_category = cat
        # Highlight selected card
        selected = st.session_state.selected_category == cat
        bg_color = "#d0ebff" if selected else "white"
        st.markdown(f"""
        <div class="category-card" style="background-color:{bg_color};">
            <img class="category-img" src="assets/icon/{icon}" />
            <h5>{cat}</h5>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

if st.session_state.selected_category:
    if st.button("Start Quiz", use_container_width=True):
        st.session_state.quiz_started = True
        st.session_state.category = st.session_state.selected_category
        st.experimental_rerun()