from models.schemas import AnswerSubmission, EvaluationResult
from services.quiz_generator import ANSWER_STORE


def evaluate_answers(submission: AnswerSubmission) -> EvaluationResult:
    """
    Evaluate user answers against stored correct answers
    and classify the user's skill level.
    """

    # Validate quiz existence
    answer_key = ANSWER_STORE.get(submission.quiz_id)
    if not answer_key:
        raise ValueError("Invalid quiz_id or quiz expired")

    correct = 0
    total = len(answer_key)

    for q_id, correct_answer in answer_key.items():
        user_answer = submission.answers.get(q_id)

        if user_answer is not None and user_answer == correct_answer:
            correct += 1

    percentage = (correct / total) * 100 if total > 0 else 0

    # Skill classification (logic > AI)
    if percentage < 40:
        level = "Beginner"
    elif percentage < 70:
        level = "Intermediate"
    else:
        level = "Advanced"

    return EvaluationResult(
        score=correct,
        total=total,
        level=level
    )
