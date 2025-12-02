"""Intent classification service."""
import re
from typing import Tuple

from app.domain.value_objects.distillation import Intent


class IntentClassifier:
    """
    Classify user intent using rule-based patterns.
    
    Two-tier classification:
    1. Rule-based patterns (fastest, ~90% accuracy)
    2. ML model (fallback) - TODO: Implement FastText model
    """
    
    # Intent patterns (regex)
    INTENT_PATTERNS = {
        # Informational
        Intent.PRICE_CHECK: [
            r"\b(price|cost|worth|value) of (\w+|ETH|BTC|USDC)",
            r"what('s| is) (\w+|ETH|BTC) (price|worth|trading at)",
            r"how much is (\w+|ETH|BTC)",
            r"(\w+|ETH|BTC) price",
        ],
        Intent.BALANCE_CHECK: [
            r"\b(my )?(balance|holdings|portfolio)\b",
            r"what do i (have|own)",
            r"show me my (assets|tokens)",
        ],
        Intent.GAS_CHECK: [
            r"\bgas (price|fee|cost)",
            r"current gas",
            r"how much gas",
        ],
        Intent.APY_CHECK: [
            r"\b(apy|yield|interest rate) (on|for)",
            r"what('s| is) the (apy|yield)",
            r"(earning|lending) rate",
        ],
        Intent.STATUS_CHECK: [
            r"is (\w+) (working|up|down|online)",
            r"(\w+) status",
            r"can i use (\w+)",
        ],
        
        # Educational
        Intent.EXPLAIN_CONCEPT: [
            r"what is (a |an )?(\w+)",
            r"explain (\w+)",
            r"(tell me about|define) (\w+)",
            r"how does (\w+) work",
        ],
        Intent.HOW_TO: [
            r"how (do i|to) (\w+)",
            r"(steps|guide) (to|for) (\w+)",
            r"how can i (\w+)",
        ],
        Intent.COMPARE: [
            r"(compare|difference between) (\w+) (and|vs) (\w+)",
            r"(\w+) vs (\w+)",
            r"which is better (\w+) or (\w+)",
        ],
        
        # Transactional
        Intent.SWAP_REQUEST: [
            r"\b(swap|exchange|trade|convert) \d+",
            r"buy (\w+) with (\w+)",
            r"sell \d+ (\w+)",
            r"trade (\w+) for (\w+)",
        ],
        Intent.STAKE_REQUEST: [
            r"\bstake \d+",
            r"stake my (\w+)",
            r"staking (\w+)",
        ],
        Intent.LEND_REQUEST: [
            r"\b(lend|deposit|supply) \d+",
            r"(lend|deposit) (\w+) (on|to|in)",
        ],
        Intent.BORROW_REQUEST: [
            r"\bborrow \d+",
            r"borrow (\w+) (against|using)",
            r"take (a )?loan",
        ],
        Intent.BRIDGE_REQUEST: [
            r"\bbridge (\w+) (to|from)",
            r"move (\w+) to (\w+) chain",
            r"transfer to (\w+) (network|chain)",
        ],
        
        # Analytical
        Intent.PORTFOLIO_ANALYSIS: [
            r"(analyze|review) my portfolio",
            r"portfolio (analysis|breakdown|performance)",
            r"how('s| is) my portfolio",
        ],
        Intent.RISK_ASSESSMENT: [
            r"(risk|risky|safe) (of|is)",
            r"(assess|check) (the )?risk",
            r"is this (safe|risky)",
        ],
        Intent.YIELD_OPTIMIZATION: [
            r"best (yield|apy) for",
            r"(optimize|maximize) (yield|returns)",
            r"where (to|should i) (put|deposit|lend)",
        ],
        Intent.STRATEGY_ADVICE: [
            r"(strategy|plan) for",
            r"should i (\w+)",
            r"(advice|recommend|suggest) (for|on)",
        ],
        
        # Administrative
        Intent.SETTINGS_CHANGE: [
            r"(change|update|set) (my )?(settings|preferences|slippage)",
            r"set (\w+) to",
        ],
        Intent.ALERT_SETUP: [
            r"(alert|notify|tell) me (when|if)",
            r"set (up )?(an )?alert",
        ],
        
        # Off-topic / Other
        Intent.GREETING: [
            r"^(hello|hi|hey|greetings|good (morning|afternoon|evening))",
        ],
        Intent.SMALL_TALK: [
            r"how are you",
            r"what('s| is) up",
            r"how('s| is) it going",
        ],
    }
    
    def classify(self, text: str) -> Tuple[Intent, float]:
        """
        Classify intent with confidence score.
        
        Args:
            text: User query text
            
        Returns:
            Tuple of (Intent, confidence)
        """
        # Normalize text
        text_lower = text.lower().strip()
        
        # Try rules first (fastest)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent, 0.95
        
        # TODO: Fall back to ML model
        # For now, return UNCLEAR with low confidence
        return Intent.UNCLEAR, 0.5
