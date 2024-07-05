import duckdb
import streamlit as st
from streamlit_option_menu import option_menu

# Set up the DuckDB database
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
TEACHER_USERNAME = "teacher"
TEACHER_PASSWORD = "password"  # Ideally, use environment variables or a secure method to store passwords

# Function to submit a new question
def submit_question(new_question):
    conn.execute("INSERT INTO questions (question_text) VALUES (?)", (new_question,))

# Function to submit a student response
def submit_response(question_id, student_name, student_response):
    conn.execute("INSERT INTO responses (question_id, student_name, response_text) VALUES (?, ?, ?)",
                 (question_id, student_name, student_response))

# Navigation menu
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Teacher", "Student", "Archive"],
        icons=["person", "people", "archive"],
        menu_icon="cast",
        default_index=0,
    )

if selected == "Teacher":
    # Teacher authentication
    st.title("Teacher Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == TEACHER_USERNAME and password == TEACHER_PASSWORD:
            st.session_state['logged_in'] = True
        else:
            st.error("Invalid username or password")

    if st.session_state.get('logged_in', False):
        st.title("Teacher Page")
        new_question = st.text_input("Enter a new question:")
        if st.button("Submit Question"):
            submit_question(new_question)
            st.success("Question submitted!")

        # Display current question
        st.header("Current Question")
        current_question = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC LIMIT 1").fetchone()
        if current_question:
            st.write(current_question[1])

            # Display all responses to the current question
            st.header("All Responses")
            responses = conn.execute("SELECT student_name, response_text FROM responses WHERE question_id = ?",
                                     (current_question[0],)).fetchall()
            for response in responses:
                st.write(f"{response[0]}: {response[1]}")
        else:
            st.write("No question available")

elif selected == "Student":
    # Student section
    st.title("Student Page")
    student_name = st.text_input("Enter your name")
    st.header("Current Question")
    current_question = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC LIMIT 1").fetchone()
    if current_question:
        st.write(current_question[1])

        # Student response input
        student_response = st.text_input("Your response:")
        if st.button("Submit Response"):
            if student_name and student_response:
                submit_response(current_question[0], student_name, student_response)
                st.success("Response submitted!")
            else:
                st.error("Please enter your name and response")
    else:
        st.write("No question available")

elif selected == "Archive":
    # Archive section for teacher to view old questions and responses
    st.title("Archive")
    questions = conn.execute("SELECT id, question_text FROM questions ORDER BY id DESC").fetchall()
    for question in questions:
        st.header(f"Question: {question[1]}")
        responses = conn.execute("SELECT student_name, response_text FROM responses WHERE question_id = ?",
                                 (question[0],)).fetchall()
        for response in responses:
            st.write(f"{response[0]}: {response[1]}")