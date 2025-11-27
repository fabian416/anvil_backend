from enum import Enum

class LLMProvider(Enum):
    VERTEX = "vertex"
    BEDROCK = "bedrock"
    OPENAI = "openai" # Added for flexibility given previous codebase refs
