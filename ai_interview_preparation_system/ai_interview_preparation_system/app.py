import os
import json
import random
import sqlite3
from datetime import datetime

import streamlit as st

# Optional AI integration:
# Set OPENAI_API_KEY in your environment or in Streamlit secrets.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "interview_history.db")

QUESTION_BANK = {
    "Technical": {
        "Python Developer": [
            "What is the difference between a list and a tuple in Python?",
            "What is a dictionary in Python, and when would you use it?",
            "Explain the difference between == and is in Python.",
            "What is exception handling? Explain try and except.",
            "What is the purpose of a function in Python?"
        ],
        "Java Developer": [
            "What is the difference between a class and an object in Java?",
            "What is inheritance, and why is it useful?",
            "What is the difference between an interface and an abstract class?",
            "What is exception handling in Java?",
            "What is the difference between ArrayList and LinkedList?"
        ],
        "Web Developer": [
            "What is the difference between HTML, CSS, and JavaScript?",
            "What is responsive web design?",
            "What is an API?",
            "What is the difference between frontend and backend development?",
            "What is the purpose of a database in a web application?"
        ],
        "General Software Developer": [
            "What is an algorithm?",
            "What is the difference between a stack and a queue?",
            "What is a database, and why do applications use databases?",
            "What is version control, and why is Git useful?",
            "How would you debug a program that gives the wrong output?"
        ],
    },
    "HR": {
        "Python Developer": [
            "Tell me about yourself.",
            "Why do you want to become a Python developer?",
            "What is one skill you are currently improving?",
            "Tell me about a time you solved a difficult problem.",
            "Why should a company select you for this role?"
        ],
        "Java Developer": [
            "Tell me about yourself.",
            "Why are you interested in Java development?",
            "How do you respond to feedback?",
            "Describe a project you worked on and your contribution.",
            "How do you manage deadlines?"
        ],
        "Web Developer": [
            "Tell me about yourself.",
            "Why do you want to work as a web developer?",
            "How do you learn a new technology?",
            "Describe a challenge you faced while building something.",
            "What kind of team environment helps you do your best work?"
        ],
        "General Software Developer": [
            "Tell me about yourself.",
            "What are your strengths?",
            "What is one skill you want to improve?",
            "Describe a time you worked with others to solve a problem.",
            "Why are you interested in this role?"
        ],
    }
}

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                role TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                score INTEGER NOT NULL,
                feedback TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def save_result(name, role, interview_type, question, answer, score, feedback):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO results
            (student_name, role, interview_type, question, answer, score, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, role, interview_type, question, answer, score, feedback,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

def get_history(name):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT role, interview_type, question, score, feedback, created_at
            FROM results WHERE student_name = ? ORDER BY id DESC LIMIT 50""",
            (name,)
        ).fetchall()
    return [dict(row) for row in rows]

def get_api_key():
    # Streamlit secrets are convenient when deployed; environment variables work locally.
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("OPENAI_API_KEY", "")

def ai_text(prompt):
    api_key = get_api_key()
    if not api_key or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        response = client.responses.create(model=model, input=prompt)
        return response.output_text.strip()
    except Exception as exc:
        st.warning(
            "The AI service could not be reached, so the app will use demo feedback for this answer. "
            "Check your API key, model access, and internet connection if you expected AI feedback."
        )
        return None

def generate_question(role, interview_type, difficulty, asked_questions):
    if interview_type == "Both":
        category = st.session_state.get("current_category", "Technical")
    else:
        category = interview_type

    prompt = (
        "You are a supportive interview coach for a college student. "
        f"Create exactly one {difficulty.lower()}-level {category.lower()} interview question "
        f"for a {role}. Do not include the answer. Keep it clear and specific. "
        f"Do not repeat these questions: {asked_questions[-12:]}"
    )
    result = ai_text(prompt)
    if result:
        return result, category

    questions = QUESTION_BANK[category].get(role, QUESTION_BANK[category]["General Software Developer"])
    available = [q for q in questions if q not in asked_questions]
    if not available:
        available = questions[:]
    return random.choice(available), category

def demo_evaluate(question, answer, interview_type):
    """Simple offline demo scoring; this is not a real AI evaluation."""
    words = answer.strip().split()
    length = len(words)
    score = 0
    if length >= 35:
        score += 35
    elif length >= 20:
        score += 28
    elif length >= 8:
        score += 20
    elif length >= 3:
        score += 10

    relevant_terms = set(question.lower().replace("?", "").replace(",", "").split())
    answer_terms = set(answer.lower().replace(".", "").replace(",", "").split())
    overlap = len(relevant_terms & answer_terms)
    score += min(35, overlap * 7)
    if length >= 8 and any(word in answer.lower() for word in ["because", "for example", "such as", "therefore", "first", "also"]):
        score += 15
    if length >= 8:
        score += 15
    score = min(100, score)

    if length < 8:
        feedback = (
            "Your answer is very short. Try explaining the main idea, then add a reason or example. "
            "Demo mode uses simple rules, so this score is only a rough practice indicator."
        )
    else:
        feedback = (
            "You have made a start. Improve your answer by defining the key idea, explaining why it matters, "
            "and adding a clear example. For HR questions, use a real experience and explain what you learned. "
            "Demo mode uses simple rules, so this score is only a rough practice indicator."
        )
    return score, feedback, "Demo mode cannot generate a reliable model answer. Review your class notes and try adding a specific example."

def evaluate_answer(question, answer, interview_type):
    prompt = f"""
You are a fair, encouraging interview coach for a college student.
Evaluate the student's answer to the interview question below.
Do not judge accent, appearance, personality, disability, or protected traits.
For technical questions, focus on correctness, relevance, and explanation.
For HR questions, focus on relevance, clarity, a concrete example, and reflection.
Give constructive feedback. Do not claim that your score is an objective hiring decision.

Interview type: {interview_type}
Question: {question}
Student answer: {answer}

Return ONLY valid JSON with these keys:
"score": an integer from 0 to 100,
"strengths": a short string,
"improvements": a short string,
"model_answer": a concise example answer for learning.
"""
    result = ai_text(prompt)
    if result:
        try:
            # Handle occasional code fences from a model.
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned)
            score = max(0, min(100, int(data.get("score", 0))))
            feedback = (
                f"**What went well:** {data.get('strengths', 'Keep practicing.')}\n\n"
                f"**What to improve:** {data.get('improvements', 'Add more detail and an example.')}"
            )
            model_answer = str(data.get("model_answer", "Try structuring your answer with a clear point and example."))
            return score, feedback, model_answer, True
        except (ValueError, TypeError, json.JSONDecodeError):
            st.warning("The AI response format was unexpected. Showing demo feedback for this answer.")
    score, feedback, model_answer = demo_evaluate(question, answer, interview_type)
    return score, feedback, model_answer, False

# ---------------- UI ----------------
st.set_page_config(page_title="AI Interview Coach", page_icon="🎯", layout="wide")
init_db()

st.title("🎯 AI Interview Preparation System")
st.caption("Practice technical and HR interviews, get feedback, and track your progress.")

with st.sidebar:
    st.header("Your interview")
    student_name = st.text_input("Your name", value=st.session_state.get("student_name", "Student"))
    role = st.selectbox(
        "Target role",
        ["General Software Developer", "Python Developer", "Java Developer", "Web Developer"]
    )
    interview_type = st.selectbox("Interview type", ["Both", "Technical", "HR"])
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    total_questions = st.slider("Questions per session", min_value=3, max_value=10, value=5)
    st.divider()
    if get_api_key() and OpenAI is not None:
        st.success("AI mode is configured")
    else:
        st.info("Demo mode: no API key detected")
        st.caption("Demo mode works offline with sample questions and simple feedback.")

    if st.button("Start new interview", type="primary", use_container_width=True):
        st.session_state.student_name = student_name.strip() or "Student"
        st.session_state.role = role
        st.session_state.interview_type = interview_type
        st.session_state.difficulty = difficulty
        st.session_state.total_questions = total_questions
        st.session_state.asked_questions = []
        st.session_state.answers = []
        st.session_state.current_index = 0
        st.session_state.current_question = None
        st.session_state.current_category = "Technical"
        st.session_state.finished = False
        st.session_state.last_evaluation = None
        st.rerun()

if "student_name" not in st.session_state:
    st.session_state.student_name = student_name.strip() or "Student"
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "finished" not in st.session_state:
    st.session_state.finished = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None
if "current_category" not in st.session_state:
    st.session_state.current_category = "Technical"
if "total_questions" not in st.session_state:
    st.session_state.total_questions = total_questions
if "role" not in st.session_state:
    st.session_state.role = role
if "interview_type" not in st.session_state:
    st.session_state.interview_type = interview_type
if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

tab_interview, tab_dashboard, tab_history = st.tabs(["🗣️ Interview", "📊 Dashboard", "🕘 History"])

with tab_interview:
    if st.session_state.finished:
        st.success("Interview completed! Open the Dashboard tab to review your results.")
        if st.button("Practice another interview"):
            st.session_state.asked_questions = []
            st.session_state.answers = []
            st.session_state.current_index = 0
            st.session_state.current_question = None
            st.session_state.finished = False
            st.session_state.last_evaluation = None
            st.rerun()
    else:
        if st.session_state.current_question is None:
            if st.session_state.interview_type == "Both":
                category = "Technical" if st.session_state.current_index % 2 == 0 else "HR"
            else:
                category = st.session_state.interview_type
            st.session_state.current_category = category
            question, _ = generate_question(
                st.session_state.role,
                category,
                st.session_state.difficulty,
                st.session_state.asked_questions
            )
            st.session_state.current_question = question

        current_num = st.session_state.current_index + 1
        st.progress(min(st.session_state.current_index / max(st.session_state.total_questions, 1), 1.0))
        st.caption(f"Question {current_num} of {st.session_state.total_questions} · {st.session_state.current_category}")
        st.subheader(st.session_state.current_question)
        answer_key = f"answer_{st.session_state.current_index}"
        answer = st.text_area(
            "Type your answer",
            key=answer_key,
            height=180,
            placeholder="Write your answer here. Explain the main idea and include an example if possible."
        )
        if st.button("Evaluate my answer", type="primary", disabled=not answer.strip()):
            with st.spinner("Reviewing your answer..."):
                score, feedback, model_answer, used_ai = evaluate_answer(
                    st.session_state.current_question, answer, st.session_state.current_category
                )
                evaluation = {
                    "question": st.session_state.current_question,
                    "answer": answer.strip(),
                    "category": st.session_state.current_category,
                    "score": score,
                    "feedback": feedback,
                    "model_answer": model_answer,
                    "used_ai": used_ai
                }
                st.session_state.last_evaluation = evaluation
                st.session_state.answers.append(evaluation)
                save_result(
                    st.session_state.student_name,
                    st.session_state.role,
                    st.session_state.current_category,
                    evaluation["question"],
                    evaluation["answer"],
                    score,
                    feedback
                )
        evaluation = st.session_state.last_evaluation
        if evaluation and evaluation["question"] == st.session_state.current_question:
            st.divider()
            st.metric("Practice score", f"{evaluation['score']}/100")
            if evaluation["used_ai"]:
                st.caption("Feedback generated by AI. Use it as practice guidance, not as a hiring decision.")
            else:
                st.caption("Rule-based demo feedback — not a reliable measure of interview ability.")
            st.markdown(evaluation["feedback"])
            with st.expander("Example answer / learning guidance"):
                st.write(evaluation["model_answer"])
            if st.button("Next question", type="primary"):
                st.session_state.asked_questions.append(st.session_state.current_question)
                st.session_state.current_index += 1
                st.session_state.current_question = None
                st.session_state.last_evaluation = None
                if st.session_state.current_index >= st.session_state.total_questions:
                    st.session_state.finished = True
                st.rerun()

with tab_dashboard:
    st.subheader("Your performance dashboard")
    history = get_history(st.session_state.student_name)
    if not history:
        st.info("Complete an interview to see your saved scores here.")
    else:
        scores = [row["score"] for row in history]
        average = sum(scores) / len(scores)
        c1, c2, c3 = st.columns(3)
        c1.metric("Saved answers", len(history))
        c2.metric("Average score", f"{average:.1f}/100")
        c3.metric("Best score", f"{max(scores)}/100")
        st.bar_chart({"Score": scores[:20]})
        st.caption("Scores are practice feedback only. Demo-mode scores are rule-based and should not be treated as accurate evaluations.")
        st.markdown("#### Recent results")
        st.dataframe(
            [{"Date": row["created_at"], "Type": row["interview_type"], "Role": row["role"],
              "Score": row["score"], "Question": row["question"]} for row in history],
            use_container_width=True,
            hide_index=True
        )

with tab_history:
    st.subheader("Previous interview answers")
    history = get_history(st.session_state.student_name)
    if not history:
        st.info("No history saved for this name yet.")
    else:
        for index, row in enumerate(history):
            with st.expander(f"{row['created_at']} · {row['interview_type']} · Score {row['score']}/100"):
                st.markdown(f"**Question:** {row['question']}")
                st.markdown(f"**Feedback:** {row['feedback']}")
                st.caption(f"Role: {row['role']}")
