from enum import Enum

class FeedbackType(Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    OFFENSIVE = "offensive"
    OTHER = "other"
