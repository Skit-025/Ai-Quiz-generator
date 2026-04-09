import streamlit as st
from models.schemas import QuizRequest, AnswerSubmission
from services.quiz_generator import generate_quiz
from services.evaluator import evaluate_answers

st.set_page_config(page_title="AI Quiz Generator", page_icon="📝", layout="centered")

st.title("📝 AI Quiz Generator")
st.write("Generate advanced domain-specific quizzes powered by AI.")

# Initialize session state for quiz and UI flow
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "is_submitted" not in st.session_state:
    st.session_state.is_submitted = False
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

# Sidebar for generating the quiz
with st.sidebar:
    st.header("Quiz Settings")
    domain = st.text_input("Domain (e.g., Python Basics, React, AWS)", "Python Basics")
    difficulty = st.selectbox("Difficulty", ["beginner", "intermediate", "advanced"], index=2)
    num_questions = st.slider("Number of Questions", min_value=1, max_value=20, value=5)
    
    generate_btn = st.button("Generate Quiz", type="primary", use_container_width=True)

if generate_btn:
    if not domain.strip():
        st.sidebar.error("Please enter a domain.")
    else:
        with st.spinner("Generating your quiz, please wait..."):
            try:
                request = QuizRequest(domain=domain, difficulty=difficulty, num_questions=num_questions)
                st.session_state.quiz_data = generate_quiz(request)
                st.session_state.is_submitted = False
                st.session_state.evaluation = None
            except Exception as e:
                st.sidebar.error(f"Error generating quiz: {e}")

# Main window for displaying the quiz
if st.session_state.quiz_data:
    quiz_data = st.session_state.quiz_data
    quiz_id = quiz_data["quiz_id"]
    questions = quiz_data["questions"]

    st.subheader(f"Quiz on {domain}")
    
    with st.form("quiz_form"):
        user_answers = {}
        for q in questions:
            st.markdown(f"**Q{q.id}. {q.question}**")
            # We add an empty string as a default option if we want to force them to pick,
            # but Streamlit radio requires an index. We'll just provide the options directly.
            selected = st.radio(
                "Select your answer",
                options=q.options,
                key=f"q_{q.id}",
                index=None  # No default selection in newer Streamlit versions
            )
            user_answers[q.id] = selected
            st.write("---")
            
        submit_btn = st.form_submit_button("Submit Answers")
        
        if submit_btn:
            # Check if all questions are answered
            if None in user_answers.values():
                st.error("Please answer all questions before submitting.")
            else:
                st.session_state.is_submitted = True
                
                # Evaluate
                try:
                    submission = AnswerSubmission(quiz_id=quiz_id, answers=user_answers)
                    st.session_state.evaluation = evaluate_answers(submission)
                except Exception as e:
                    st.error(f"Error evaluating answers: {e}")

# Display results
if st.session_state.is_submitted and st.session_state.evaluation:
    eval_res = st.session_state.evaluation
    st.success("Quiz Submitted Successfully!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{eval_res.score} / {eval_res.total}")
    
    percentage = (eval_res.score / eval_res.total) * 100 if eval_res.total > 0 else 0
    col2.metric("Percentage", f"{percentage:.1f}%")
    
    col3.metric("Skill Level", eval_res.level)
    
    if percentage >= 70:
        st.balloons()
