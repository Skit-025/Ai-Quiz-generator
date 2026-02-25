from fastapi import FastAPI
from models.schemas import QuizRequest, AnswerSubmission
from services.quiz_generator import generate_quiz
from services.evaluator import evaluate_answers

app = FastAPI(
    title="Quiz AI Backend",
    description="API for generating quizzes and evaluating answers",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/generate-quiz")
def create_quiz(request: QuizRequest):
    """
    Generate a quiz based on domain, difficulty, and number of questions.
    """
    return generate_quiz(request)

@app.post("/submit-answers")
def submit_answers(submission: AnswerSubmission):
    """
    Evaluate submitted answers and classify user level.
    """
    return evaluate_answers(submission)
