from enum import Enum

class CostAlertType(Enum):
    DAILY_THRESHOLD = "daily_threshold"
    WEEKLY_THRESHOLD = "weekly_threshold"
    MONTHLY_THRESHOLD = "monthly_threshold"
    USER_SPIKE = "user_spike"
