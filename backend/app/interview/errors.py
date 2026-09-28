"""模拟面试模块错误码与异常。

InterviewError.code 既可以是 InterviewErrorCode（面试业务错误），也可以是
AIErrorCode（上游模型错误，复用 Step 6 的统一错误分类）。
"""
from enum import Enum


class InterviewErrorCode(str, Enum):
    interview_model_not_found = "INTERVIEW_MODEL_NOT_FOUND"
    interview_session_not_found = "INTERVIEW_SESSION_NOT_FOUND"
    interview_session_completed = "INTERVIEW_SESSION_COMPLETED"
    interview_invalid_state = "INTERVIEW_INVALID_STATE"
    interview_invalid_answer = "INTERVIEW_INVALID_ANSWER"
    interview_structured_output_error = "INTERVIEW_STRUCTURED_OUTPUT_ERROR"
    interview_question_bank_error = "INTERVIEW_QUESTION_BANK_ERROR"
    evaluation_not_found = "EVALUATION_NOT_FOUND"
    evaluation_failed = "EVALUATION_FAILED"


class InterviewError(Exception):
    def __init__(self, code, message: str) -> None:
        self.code = code  # InterviewErrorCode 或 AIErrorCode
        self.message = message
        super().__init__(f"[{code.value}] {message}")
