from enum import Enum


class TransactionType(Enum):
    SWAP = 0
    FUND = 1
    EARN = 2
    SAVE = 3
    SUBSCRIPTION = 4
    SEND = 5  # Simple ETH/token transfer
    APPROVE = 6  # Token approval
    CONTRACT_CALL = 7  # Generic contract interaction
