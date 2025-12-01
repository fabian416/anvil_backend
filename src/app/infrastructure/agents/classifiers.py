"""
DeFi intent classifiers for Agent Squad.
"""

from typing import Dict, List


class DeFiIntentClassifier:
    """
    Classifies user intents for DeFi operations.
    
    This classifier helps Agent Squad route messages to the appropriate
    specialized agent based on the user's intent.
    """
    
    # All supported intents
    INTENTS = [
        "trade_swap",           # "swap 100 USDC to ETH"
        "trade_perp_open",      # "open 10x long on BTC"
        "trade_perp_close",     # "close my ETH position"
        "lend_supply",          # "lend 1000 USDC on Aave"
        "lend_borrow",          # "borrow ETH against my USDC"
        "earn_stake",           # "stake ETH for yield"
        "portfolio_view",       # "show my portfolio"
        "market_info",          # "what's the funding rate on BTC?"
        "risk_analysis",        # "analyze my position risk"
        "save_schedule",        # "save $100 weekly to USDC"
        "general_question",     # "how does Aave work?"
    ]
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize DeFi intent classifier.
        
        Args:
            model: LLM model to use for classification
        """
        self.model = model
        self.examples = self._get_examples()
    
    def _get_examples(self) -> Dict[str, List[str]]:
        """
        Get training examples for each intent.
        
        Returns:
            Dictionary mapping intents to example phrases
        """
        return {
            "trade_swap": [
                "swap 100 USDC to ETH",
                "exchange my DAI for USDC",
                "convert 0.5 ETH to USDC",
                "trade USDC for ETH",
                "I want to swap tokens",
                "can you swap 50 DAI to WETH for me?",
            ],
            "trade_perp_open": [
                "open 10x long on BTC",
                "long ETH with 5x leverage",
                "short SOL 20x",
                "I want to open a position on BTC",
                "can I go long on ETH?",
                "open a 15x leveraged short on BTC",
                "start a perpetual position",
            ],
            "trade_perp_close": [
                "close my ETH position",
                "exit my BTC long",
                "close all my positions",
                "I want to close my short",
                "take profit on my ETH position",
                "stop loss on BTC",
            ],
            "lend_supply": [
                "lend 1000 USDC on Aave",
                "supply ETH to Aave",
                "deposit USDC for yield",
                "I want to earn interest on my USDC",
                "provide liquidity on Aave",
                "lend my tokens",
            ],
            "lend_borrow": [
                "borrow ETH against my USDC",
                "take out a loan on Aave",
                "borrow DAI using my ETH as collateral",
                "I need to borrow some USDC",
                "can I borrow against my holdings?",
            ],
            "earn_stake": [
                "stake ETH for yield",
                "earn rewards on my tokens",
                "what's the best staking option?",
                "I want to stake my ETH",
                "earn passive income",
            ],
            "portfolio_view": [
                "show my portfolio",
                "what's my balance?",
                "show all my positions",
                "how much do I have?",
                "display my holdings",
                "what's my net worth?",
                "show my assets",
            ],
            "market_info": [
                "what's the funding rate on BTC?",
                "current ETH price",
                "show me the market",
                "what's the price of SOL?",
                "funding rate for ETH perp",
                "market conditions",
                "TVL on Aave",
            ],
            "risk_analysis": [
                "analyze my position risk",
                "what's my liquidation price?",
                "how risky is this position?",
                "calculate my health factor",
                "am I at risk of liquidation?",
                "check my portfolio risk",
            ],
            "save_schedule": [
                "save $100 weekly to USDC",
                "set up automatic savings",
                "DCA into ETH every week",
                "I want to save regularly",
                "schedule weekly buys",
                "recurring investment",
            ],
            "general_question": [
                "how does Aave work?",
                "what is a perpetual future?",
                "explain funding rates",
                "what's DeFi?",
                "how do I use Hyperliquid?",
                "what are the risks?",
                "tell me about lending",
            ],
        }
    
    def get_intent_descriptions(self) -> Dict[str, str]:
        """
        Get human-readable descriptions for each intent.
        
        Returns:
            Dictionary mapping intents to descriptions
        """
        return {
            "trade_swap": "User wants to swap or exchange tokens on a DEX",
            "trade_perp_open": "User wants to open and trade a leveraged perpetual futures position",
            "trade_perp_close": "User wants to close and exit an existing perpetual position",
            "lend_supply": "User wants to supply or lend tokens to earn interest",
            "lend_borrow": "User wants to borrow tokens against collateral",
            "earn_stake": "User wants to stake tokens for yield/rewards",
            "portfolio_view": "User wants to view their portfolio/balances",
            "market_info": "User wants to get market data (prices, rates, TVL)",
            "risk_analysis": "User wants to analyze risk assessment of their positions",
            "save_schedule": "User wants to set up recurring buy/save schedule",
            "general_question": "User has a general question about DeFi concepts",
        }
    
    def get_intent_to_agent_mapping(self) -> Dict[str, str]:
        """
        Map intents to appropriate agent names.
        
        Returns:
            Dictionary mapping intents to agent names
        """
        return {
            "trade_swap": "SwapAgent",
            "trade_perp_open": "TradingAgent",
            "trade_perp_close": "TradingAgent",
            "lend_supply": "LendingAgent",
            "lend_borrow": "LendingAgent",
            "earn_stake": "EarnAgent",
            "portfolio_view": "PortfolioAgent",
            "market_info": "MarketDataAgent",
            "risk_analysis": "RiskAgent",
            "save_schedule": "SaveAgent",
            "general_question": "GeneralAgent",
        }


# Convenience function to get classifier instance
def get_defi_intent_classifier(model: str = "gpt-4-turbo") -> DeFiIntentClassifier:
    """
    Get a configured DeFi intent classifier.
    
    Args:
        model: LLM model to use
    
    Returns:
        DeFiIntentClassifier instance
    """
    return DeFiIntentClassifier(model=model)
