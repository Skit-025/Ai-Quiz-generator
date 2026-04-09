import os
import json
import uuid
import requests
import streamlit as st
from models.schemas import QuizRequest, Question


HF_TOKEN = st.secrets["default"]["HF_TOKEN"]
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN environment variable not set")

HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}

# =========================
# In-memory Answer Store
# =========================

ANSWER_STORE: dict[str, dict[int, str]] = {}

# =========================
# LLM Call
# =========================

def call_llm(prompt: str) -> str:
    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON generator. "
                    "You never return markdown, explanations, or extra text. "
                    "You return valid, parsable JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 5500,
    }

    response = requests.post(
        HF_CHAT_URL,
        headers=HEADERS,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"HuggingFace Router error {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected HF response format: {data}")

# =========================
# Quiz Generator
# =========================

def generate_quiz(request: QuizRequest):
    quiz_id = str(uuid.uuid4())

    prompt = f"""
You are an expert-level computer science question generator.

Return ONLY valid JSON.
Do NOT return markdown.
Do NOT return explanations.
Do NOT return comments.
Return STRICTLY parsable JSON.

==============================
MANDATORY ADVANCED REQUIREMENTS
==============================

You are generating ADVANCED-LEVEL multiple-choice questions.

Advanced means:
- Requires deep reasoning about edge cases, internal mechanics, or failure scenarios
- Requires understanding of trade-offs or subtle behavior
- Cannot be solved by memorizing definitions
- Cannot be answered by recalling Big-O alone
- Must challenge experienced developers

==============================
CRITICAL CONTEXT RULE
==============================

If a question references:
- "following code"
- "code snippet"
- "implementation below"
- "given function"
- "the following algorithm"

Then the FULL code snippet MUST be included directly inside the question text.

NEVER reference code without including it.
NEVER say "following snippet" unless you actually include it.
Questions missing required context are INVALID.

If ANY question lacks required context, DISCARD it and regenerate internally before returning.

==============================
QUESTION REQUIREMENTS
==============================

Each question MUST:
- Contain either:
    (A) a full code snippet, OR
    (B) a detailed real-world failure scenario, OR
    (C) a non-obvious systems-level tradeoff
- Have exactly 4 options
- Have exactly ONE correct answer
- Include at least one highly plausible but incorrect distractor
- Require reasoning, not recall

DO NOT GENERATE:
- Simple complexity questions (e.g., "What is the time complexity of binary search?")
- Definition questions
- Textbook-level DS/Algo basics
- Questions solvable without careful thinking

==============================
QUIZ CONFIGURATION
==============================

Domain: {request.domain}
Difficulty: ADVANCED
Number of questions: {request.num_questions}

==============================
ANSWER FORMAT RULE
==============================

- The "answer" value MUST be the FULL option string.
- DO NOT return "A", "B", "C", or "D".
- The answer string must EXACTLY match one of the options.

==============================
OUTPUT FORMAT (STRICT JSON)
==============================

{{
  "questions": [
    {{
      "id": 1,
      "question": "Full question text (including code snippet if referenced)",
      "options": [
        "First option text",
        "Second option text",
        "Third option text",
        "Fourth option text"
      ],
      "answer": "Exact full option string"
    }}
  ]
}}

Return ONLY the JSON object.
"""
    raw_response = call_llm(prompt)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\n{raw_response}")

    if "questions" not in data or not isinstance(data["questions"], list):
        raise ValueError("LLM response missing 'questions' array")

    questions: list[Question] = []
    answer_key: dict[int, str] = {}

    for q in data["questions"]:
        if not all(k in q for k in ("id", "question", "options", "answer")):
            raise ValueError(f"Malformed question object: {q}")

        if not isinstance(q["options"], list) or len(q["options"]) != 4:
            raise ValueError(f"Each question must have exactly 4 options: {q}")

        if q["answer"] not in q["options"]:
            raise ValueError(f"Answer must match one of the options: {q}")

        questions.append(
            Question(
                id=int(q["id"]),
                question=q["question"],
                options=q["options"],
            )
        )

        answer_key[int(q["id"])] = q["answer"]

    if len(questions) != request.num_questions:
        raise ValueError(
            f"Expected {request.num_questions} questions, got {len(questions)}"
        )

    ANSWER_STORE[quiz_id] = answer_key

    return {
        "quiz_id": quiz_id,
        "questions": questions,
    }
