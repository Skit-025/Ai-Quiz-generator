from pydantic import BaseModel, Field
from typing import List, Dict


class QuizRequest(BaseModel):
    domain: str = Field(..., examples="Python Basics"or"java"or"Physics")
    difficulty: str = Field(..., example="beginner")
    num_questions: int = Field(..., ge=1, le=100, example=10)


class Question(BaseModel):
    id: int
    question: str
    options: List[str]


class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[Question]


class AnswerSubmission(BaseModel):
    quiz_id: str
    answers: Dict[int, str]


class EvaluationResult(BaseModel):
    score: int
    total: int
    level: str
