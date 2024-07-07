import duckdb
import streamlit as st
from streamlit_option_menu import option_menu
from typing import Optional
import os.path


# Set up the DuckDB database if it doesn't exist. Otherwise just connect
if os.path.isfile('responses.db'):
    conn = duckdb.connect('responses.db')
else:
    conn = duckdb.connect('responses.db')

    # Create sequence for primary keys
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_question START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_response START 1")

    # Create tables for questions and responses
    conn.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_question'),
        question_text TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY DEFAULT NEXTVAL('seq_response'),
        question_id INTEGER,
        student_name TEXT,
        response_text TEXT,
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    """)

# Authentication
TEACHER_USERNAME = st.secrets['LOGIN']
TEACHER_PASSWORD = st.secrets['PASSWORD']


def submit_question(new_question: str) -> None:
    """Submit a new question to the database."""
    conn.execute("INSERT INTO questions (question_text) VALUES (?)", (new_question,))
    st.experimental_rerun()


def submit_response(question_id: int, student_name: str, student_response: str) -> None:
    """Submit or update a student response in the database."""
    existing_response = conn.execute("SELECT id FROM responses WHERE question_id = ? AND student_name = ?",
                                     (question_id, student_name)).fetchone()
    if existing_response:
        conn.execute("UPDATE responses SET response_text = ? WHERE id = ?",
                     (student_response, existing_response[0]))
    else:
        conn.execute("INSERT INTO responses (question_id, student_name, response_text) VALUES (?, ?, ?)",
                     (question_id, student_name, student_response))
    st.experimental_rerun()


def display_teacher_page() -> None:
    """Display the teacher page where the teacher can submit questions and view responses."""
    st.title("Teacher Page")
    new_question = st.text_input("Enter a new question:")
    if st.button("Submit Question"):
        submit_question(new_question)

    # Display current question
    st.header("Current Question")
    current_question = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC LIMIT 1").fetchone()
    if current_question:
        with st.chat_message("user"):
            st.write(current_question[1])

        # Display all responses to the current question
        st.header("All Responses")
        if st.button("Check for Responses"):
            st.experimental_rerun()
        responses = conn.execute("SELECT student_name, response_text FROM responses WHERE question_id = ?",
                                 (current_question[0],)).fetchall()
        for response in responses:
            with st.chat_message(response[0]):
                st.write(f"**{response[0]}**: {response[1]}")
    else:
        st.write("No question available")


def display_student_page() -> None:
    """Display the student page where students can submit and edit their responses."""
    st.title("Student Page")
    current_question = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC LIMIT 1").fetchone()

    if current_question:
        st.header("Current Question")
        
        student_name = st.text_input("Enter your name")
        with st.chat_message("user"):
            st.write(current_question[1])
        
        if student_name:
            # Check if the student has already submitted a response
            existing_response = conn.execute("SELECT response_text FROM responses WHERE question_id = ? AND student_name = ?",
                                             (current_question[0], student_name)).fetchone()
            if existing_response:
                student_response = st.text_area("Your response:", value=existing_response[0])
                if st.button("Edit Response"):
                    submit_response(current_question[0], student_name, student_response)
                    st.success("Response updated!")
            else:
                student_response = st.text_area("Your response:")
                if st.button("Submit Response"):
                    if student_response:
                        submit_response(current_question[0], student_name, student_response)
                        st.success("Response submitted!")
                    else:
                        st.error("Please enter your response")

        if st.button("Check for Next Question"):
            st.experimental_rerun()
    else:
        st.write("No question available")


def display_archive_page() -> None:
    """Display the archive page where the teacher can view old questions and responses."""
    st.title("Archive")
    questions = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC").fetchall()
    for question in questions:
        st.header(f"Question: {question[1]}")
        responses = conn.execute("SELECT student_name, response_text FROM responses WHERE question_id = ?",
                                 (question[0],)).fetchall()
        for response in responses:
            with st.chat_message(response[0]):
                st.write(f"**{response[0]}**: {response[1]}")


def display_login_page() -> None:
    """Display the login page for the teacher."""
    st.title("Teacher Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == TEACHER_USERNAME and password == TEACHER_PASSWORD:
            st.session_state['logged_in'] = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")


# Navigation menu
with st.sidebar:
    if st.session_state.get('logged_in', False):
        selected = option_menu(
            menu_title="Live Questions",
            options=["Teacher", "Archive", "Logout"],
            icons=["person", "archive", "box-arrow-right"],
            menu_icon="cast",
            default_index=0,
        )
    else:
        selected = option_menu(
            menu_title="Live Questions",
            options=["Student", "Teacher"],
            icons=["people", "person"],
            menu_icon="cast",
            default_index=0,
        )

if selected == "Teacher":
    if not st.session_state.get('logged_in', False):
        display_login_page()
    else:
        display_teacher_page()

elif selected == "Student":
    display_student_page()

elif selected == "Archive" and st.session_state.get('logged_in', False):
    display_archive_page()

elif selected == "Logout":
    st.session_state['logged_in'] = False
    st.experimental_rerun()
