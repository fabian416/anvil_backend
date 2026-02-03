from enum import Enum


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VERTEX = "vertex"
    BEDROCK = "bedrock"
    DEEPINFRA = "deepinfra"
    OTHER = "other"
