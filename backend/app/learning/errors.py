"""学习计划模块错误码与异常。"""
from enum import Enum


class LearningErrorCode(str, Enum):
    # 目标 / 输入校验
    learning_invalid_target_type = "LEARNING_INVALID_TARGET_TYPE"
    learning_invalid_level = "LEARNING_INVALID_LEVEL"
    learning_invalid_minutes = "LEARNING_INVALID_MINUTES"
    learning_invalid_intensity = "LEARNING_INVALID_INTENSITY"
    learning_invalid_days = "LEARNING_INVALID_DAYS"
    learning_invalid_direction = "LEARNING_INVALID_DIRECTION"
    # 目标 / 资源
    learning_target_not_found = "LEARNING_TARGET_NOT_FOUND"
    learning_target_empty = "LEARNING_TARGET_EMPTY"
    learning_knowledge_not_found = "LEARNING_KNOWLEDGE_NOT_FOUND"
    learning_dependency_cycle = "LEARNING_DEPENDENCY_CYCLE"
    # 计划 / 任务状态
    learning_plan_not_found = "LEARNING_PLAN_NOT_FOUND"
    learning_plan_state = "LEARNING_PLAN_STATE"
    learning_task_not_found = "LEARNING_TASK_NOT_FOUND"
    learning_task_state = "LEARNING_TASK_STATE"


class LearningError(Exception):
    def __init__(self, code, message: str) -> None:
        self.code = code  # LearningErrorCode
        self.message = message
        super().__init__(f"[{code.value}] {message}")
