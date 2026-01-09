"""
Swap Handler v2.

Multi-turn conversational swap handler with full flow support.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.application.chat.services.conversation_memory import ConversationContext

logger = logging.getLogger(__name__)


# Supported tokens
SUPPORTED_TOKENS = [
    "ETH", "USDC", "USDT", "DAI", "WBTC", "WETH", "BTC", "SOL",
    "MATIC", "ARB", "OP", "LINK", "UNI", "AAVE", "CRV", "MKR",
]


@dataclass
class SwapInfo:
    """Information for a swap operation."""
    
    from_token: str | None = None
    to_token: str | None = None
    amount: str | None = None
    from_chain: str | None = None  # Source chain for cross-chain swaps
    to_chain: str | None = None  # Destination chain for cross-chain swaps
    
    @property
    def is_complete(self) -> bool:
        """Check if we have all required info."""
        return bool(self.from_token and self.to_token and self.amount)
    
    @property
    def next_step(self) -> str | None:
        """Get the next step needed."""
        if not self.from_token:
            return "from_token"
        if not self.to_token:
            return "to_token"
        if not self.amount:
            return "amount"
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "amount": self.amount,
            "from_chain": self.from_chain,
            "to_chain": self.to_chain,
            "is_complete": self.is_complete,
        }


@dataclass
class HandlerResult:
    """Result from a handler."""
    
    content: str
    pending_action: str | None = None
    requires_registration: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    enrichment: dict[str, Any] | None = None
    execute_data: dict[str, Any] | None = None  # Execute action data for /execute endpoint


class SwapHandlerV2:
    """
    Multi-turn conversational swap handler.
    
    Supports:
    - Single message complete swaps: "swap 100 USDC to ETH"
    - Multi-turn flows: "quiero swap" → "de USDC" → "a ETH" → "100"
    - Context-aware continuation
    """
    
    def __init__(self):
        # Popular tokens for quick selection
        self._popular_tokens = ["USDC", "ETH", "BTC", "USDT", "DAI", "WBTC"]
        
        self._messages = {
            "ask_from_token": {
                "en": "🔄 I can help you swap tokens!\n\nWhat token do you want to swap **from**?\n\n{options}",
                "es": "🔄 ¡Puedo ayudarte a intercambiar tokens!\n\n¿**De qué** token quieres hacer swap?\n\n{options}",
                "pt": "🔄 Posso ajudá-lo a trocar tokens!\n\n**De qual** token você quer fazer swap?\n\n{options}",
            },
            "ask_to_token": {
                "en": "Got it! You want to swap **{from_token}**.\n\nWhat token do you want to receive?\n\n{options}",
                "es": "¡Entendido! Quieres cambiar **{from_token}**.\n\n¿Qué token quieres recibir?\n\n{options}",
                "pt": "Entendi! Você quer trocar **{from_token}**.\n\nQual token você quer receber?\n\n{options}",
            },
            "ask_amount": {
                "en": "Perfect! Swapping **{from_token}** → **{to_token}**\n\nHow much {from_token} do you want to swap?\n\n{options}",
                "es": "¡Perfecto! Intercambio **{from_token}** → **{to_token}**\n\n¿Cuántos {from_token} quieres cambiar?\n\n{options}",
                "pt": "Perfeito! Troca **{from_token}** → **{to_token}**\n\nQuantos {from_token} você quer trocar?\n\n{options}",
            },
            "quote": {
                "en": """💱 **Swap Quote**

**From:** {amount} {from_token}
**To:** ~{output_amount} {to_token}

**Rate:** 1 {from_token} = {rate} {to_token}
**Price Impact:** {price_impact}%
**Network:** {network}

Ready to execute? Type **1** to confirm and proceed with the swap.""",
                "es": """💱 **Cotización de Swap**

**De:** {amount} {from_token}
**A:** ~{output_amount} {to_token}

**Tasa:** 1 {from_token} = {rate} {to_token}
**Impacto en precio:** {price_impact}%
**Red:** {network}

¿Listo para ejecutar? Escribe **1** para confirmar y proceder con el swap.""",
                "pt": """💱 **Cotação de Swap**

**De:** {amount} {from_token}
**Para:** ~{output_amount} {to_token}

**Taxa:** 1 {from_token} = {rate} {to_token}
**Impacto no preço:** {price_impact}%
**Rede:** {network}

Pronto para executar? Digite **1** para confirmar e prosseguir com o swap.""",
            },
        }
        
        # Demo exchange rates
        self._demo_rates = {
            ("USDC", "ETH"): 0.0003,
            ("ETH", "USDC"): 3333.33,
            ("USDC", "WBTC"): 0.000015,
            ("WBTC", "USDC"): 66666.67,
            ("ETH", "WBTC"): 0.05,
            ("WBTC", "ETH"): 20.0,
            ("USDC", "USDT"): 1.0,
            ("USDT", "USDC"): 1.0,
            ("DAI", "USDC"): 1.0,
            ("USDC", "DAI"): 1.0,
        }
    
    async def handle(
        self,
        message: str,
        context: ConversationContext | None = None,
        language: str = "en",
        continuation_step: str | None = None,
        continuation_value: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> HandlerResult:
        """
        Handle swap request with multi-turn support.
        
        Args:
            message: User message
            context: Conversation context
            language: Language code
            continuation_step: If continuing a flow, which step
            continuation_value: Value for the continuation step
            previous_swap_info: Previous swap info for continuation
            
        Returns:
            HandlerResult with response and pending action
        """
        # Check if user is confirming execution after seeing quote
        # If previous_swap_info exists and is complete, and user says "1" or "confirm", return the same quote with execute_data
        message_lower = message.lower().strip()
        if previous_swap_info and previous_swap_info.get("is_complete"):
            # Check if user is confirming (says "1", "confirm", "yes", "execute", etc.)
            confirmation_keywords = ["1", "confirm", "yes", "sí", "sim", "execute", "ejecutar", "executar", "proceed", "proceder"]
            if any(keyword in message_lower for keyword in confirmation_keywords):
                # User confirmed, return the same quote with execute_data
                swap_info = SwapInfo(
                    from_token=previous_swap_info.get("from_token"),
                    to_token=previous_swap_info.get("to_token"),
                    amount=previous_swap_info.get("amount"),
                    from_chain=previous_swap_info.get("from_chain"),
                    to_chain=previous_swap_info.get("to_chain"),
                )
                # Return the quote again, but this time it will have execute_data
                return await self._generate_quote(swap_info, language)
        
        # Initialize swap_info from previous state if available
        if previous_swap_info:
            swap_info = SwapInfo(
                from_token=previous_swap_info.get("from_token"),
                to_token=previous_swap_info.get("to_token"),
                amount=previous_swap_info.get("amount"),
                from_chain=previous_swap_info.get("from_chain"),
                to_chain=previous_swap_info.get("to_chain"),
            )
        else:
            # Extract swap info from message and context
            swap_info = self._extract_swap_info(message, context)
            # Store message for rate query detection
            self._last_message = message
        
        # Handle continuation of pending flow
        if continuation_step:
            # Special handling for confirmation step
            if continuation_step == "confirm_execution":
                # User confirmed execution, return quote with execute_data
                if swap_info.from_token and swap_info.to_token and swap_info.amount:
                    return await self._generate_quote(swap_info, language)
                else:
                    # Missing info, ask for it
                    return await self._process_swap_flow(swap_info, language)
            else:
                # Regular continuation (from_token, to_token, amount)
                swap_info = self._apply_continuation(
                    swap_info,
                    continuation_step,
                    continuation_value or message,
                )
        
        # Determine next step
        return await self._process_swap_flow(swap_info, language)
    
    async def _process_swap_flow(
        self,
        swap_info: SwapInfo,
        language: str,
    ) -> HandlerResult:
        """Process swap flow based on current info."""
        
        # Ask for from_token
        if not swap_info.from_token:
            options = self._format_token_options(self._popular_tokens, language)
            return HandlerResult(
                content=self._get_message("ask_from_token", language).format(options=options),
                pending_action="swap_awaiting_from_token",
                metadata=swap_info.to_dict(),
            )
        
        # Ask for to_token
        if not swap_info.to_token:
            # Exclude from_token from options
            available_tokens = [t for t in self._popular_tokens if t != swap_info.from_token]
            options = self._format_token_options(available_tokens, language)
            return HandlerResult(
                content=self._get_message("ask_to_token", language).format(
                    from_token=swap_info.from_token,
                    options=options
                ),
                pending_action="swap_awaiting_to_token",
                metadata=swap_info.to_dict(),
            )
        
        # Ask for amount
        if not swap_info.amount:
            # For "best rate" queries, show rate info with default amount (1 token)
            # Check if message contains "rate" or "best" keywords
            message_lower = getattr(self, '_last_message', '').lower()
            if any(keyword in message_lower for keyword in ["rate", "best", "top", "highest", "mejor", "melhor"]):
                # Use default amount of 1 for rate display
                swap_info.amount = "1"
                return await self._generate_quote(swap_info, language)
            
            # Regular flow: ask for amount
            options = self._format_amount_options(language)
            return HandlerResult(
                content=self._get_message("ask_amount", language).format(
                    from_token=swap_info.from_token,
                    to_token=swap_info.to_token,
                    options=options
                ),
                pending_action="swap_awaiting_amount",
                metadata=swap_info.to_dict(),
            )
        
        # Generate quote
        return await self._generate_quote(swap_info, language)
    
    async def _generate_quote(
        self,
        swap_info: SwapInfo,
        language: str,
    ) -> HandlerResult:
        """Generate a demo swap quote."""
        # Get rate
        rate = self._get_rate(swap_info.from_token, swap_info.to_token)
        
        # Calculate output
        try:
            amount = float(swap_info.amount)
        except (ValueError, TypeError):
            amount = 100.0
        
        output_amount = amount * rate
        
        # Extract chain information from swap_info or default to ethereum
        chain = swap_info.from_chain or "ethereum"  # Default to ethereum
        to_chain = swap_info.to_chain
        
        # Format quote
        content = self._get_message("quote", language).format(
            amount=swap_info.amount,
            from_token=swap_info.from_token,
            to_token=swap_info.to_token,
            output_amount=f"{output_amount:.6f}",
            rate=f"{rate:.6f}",
            price_impact="0.05",
            network=chain.title(),  # Capitalize chain name
        )
        
        # Build execute data for when swap is complete and ready
        execute_data = {
            "action_type": "swap",
            "chain": chain,
            "from_token": swap_info.from_token,
            "to_token": swap_info.to_token,
            "amount": swap_info.amount,
            "slippage": 1.0,
            "to_chain": to_chain,
        }
        
        # Mark swap as complete in metadata so it can be detected for confirmation
        swap_metadata = swap_info.to_dict()
        swap_metadata["is_complete"] = True  # Mark as complete so confirmation can be detected
        
        return HandlerResult(
            content=content,
            pending_action=None,
            requires_registration=True,
            metadata=swap_metadata,
            enrichment={
                "swap_quote": {
                    "from_token": swap_info.from_token,
                    "to_token": swap_info.to_token,
                    "from_amount": swap_info.amount,
                    "to_amount": f"{output_amount:.6f}",
                    "rate": rate,
                    "price_impact": 0.05,
                    "network": chain,
                    "is_demo": True,
                },
            },
            execute_data=execute_data,  # Include execute data when swap is ready
        )
    
    def _extract_swap_info(
        self,
        message: str,
        context: ConversationContext | None,
    ) -> SwapInfo:
        """Extract swap information from message and context."""
        swap_info = SwapInfo()
        message_lower = message.lower()
        
        # Build combined text for parsing
        combined = message_lower
        if context and context.summary:
            combined = f"{context.summary.lower()}\n{message_lower}"
        
        # Supported chains
        SUPPORTED_CHAINS = {
            "ethereum": "ethereum",
            "eth": "ethereum",
            "base": "base",
            "arbitrum": "arbitrum",
            "arb": "arbitrum",
            "optimism": "optimism",
            "op": "optimism",
            "polygon": "polygon",
            "matic": "polygon",
            "avalanche": "avalanche",
            "avax": "avalanche",
            "bsc": "bsc",
            "binance": "bsc",
            "solana": "solana",
            "sol": "solana",
        }
        
        # Extract chains for cross-chain swaps
        # Pattern: "from Ethereum to Base", "desde Ethereum a Base"
        chain_patterns = [
            r"(?:from|desde|de)\s+(\w+)\s+(?:to|a|para|hacia)\s+(\w+)",
            r"on\s+(\w+)\s+(?:to|a|para|hacia)\s+(\w+)",
        ]
        for pattern in chain_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                from_chain_name = match.group(1).lower()
                to_chain_name = match.group(2).lower()
                if from_chain_name in SUPPORTED_CHAINS:
                    swap_info.from_chain = SUPPORTED_CHAINS[from_chain_name]
                if to_chain_name in SUPPORTED_CHAINS:
                    swap_info.to_chain = SUPPORTED_CHAINS[to_chain_name]
                break
        
        # Extract tokens mentioned (avoid chains that were already extracted)
        excluded_words = set()
        if swap_info.from_chain:
            excluded_words.add(swap_info.from_chain.lower())
        if swap_info.to_chain:
            excluded_words.add(swap_info.to_chain.lower())
        # Also exclude chain aliases
        for chain_alias in ["ethereum", "eth", "base", "arbitrum", "arb", "optimism", "op", "polygon", "matic", "avalanche", "avax", "bsc", "binance", "solana", "sol"]:
            excluded_words.add(chain_alias)
        
        # Find all tokens mentioned in the message
        found_tokens = []
        for token in SUPPORTED_TOKENS:
            if token.lower() in combined and token.lower() not in excluded_words:
                found_tokens.append(token)
        
        # Try to extract source token with patterns
        # Pattern 1: "Swap USDC from Ethereum" -> USDC is the token (before "from chain")
        # Pattern 2: "Swap 100 USDC to ETH" -> USDC is the token (before "to token")
        # Pattern 3: "Swap USDC" -> USDC is the token
        from_token_patterns = [
            r"(?:swap|cambiar|trocar|exchange|bridge)\s+(?:\d+\.?\d*\s*)?(\w+)",
            r"(\w+)\s+(?:from|desde|de)\s+(?:ethereum|base|arbitrum|optimism|polygon|avalanche|bsc|binance|solana)",
        ]
        for pattern in from_token_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                if token in SUPPORTED_TOKENS and token.lower() not in excluded_words:
                    swap_info.from_token = token
                    break
        
        # Try to extract target token (after "to" but not if it's a chain)
        # Pattern: "to ETH" or "a ETH" (not "to Base" which is a chain)
        # Only extract if we haven't already identified it as a chain
        to_token_patterns = [
            r"(?:to|a|hacia|por|for|para)\s+(\w+)",
        ]
        for pattern in to_token_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                # Check if it's a token (not a chain that was already extracted)
                if token in SUPPORTED_TOKENS and token.lower() not in excluded_words and token != swap_info.from_token:
                    # Only set if we haven't already set to_chain (cross-chain swaps don't need different to_token)
                    # For cross-chain, to_token will be set to from_token later
                    if not swap_info.to_chain:
                        swap_info.to_token = token
                    break
        
        # For cross-chain swaps (when we have chains but no to_token), 
        # the to_token is the same as from_token (bridging the same token)
        if swap_info.from_chain and swap_info.to_chain and not swap_info.to_token:
            swap_info.to_token = swap_info.from_token
        
        # Try to extract amount
        amount_patterns = [
            r"(\d+\.?\d*)\s*(?:tokens?)?",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, combined)
            if match:
                swap_info.amount = match.group(1)
                break
        
        # If we found tokens but couldn't determine source/target, use order
        # But only if we don't have chains (for cross-chain, we handle it differently)
        if found_tokens and not swap_info.from_token and not swap_info.to_token and not swap_info.from_chain:
            if len(found_tokens) >= 1:
                swap_info.from_token = found_tokens[0]
            if len(found_tokens) >= 2:
                swap_info.to_token = found_tokens[1]
        
        # For cross-chain swaps (when we have chains but no to_token), 
        # the to_token is the same as from_token (bridging the same token)
        if swap_info.from_chain and swap_info.to_chain and not swap_info.to_token and swap_info.from_token:
            swap_info.to_token = swap_info.from_token
        
        # Use context entities if available
        if context and context.detected_entities:
            entities = context.detected_entities
            if entities.get("tokens"):
                context_tokens = entities["tokens"]
                if not swap_info.from_token and len(context_tokens) >= 1:
                    swap_info.from_token = context_tokens[0]
                if not swap_info.to_token and len(context_tokens) >= 2:
                    swap_info.to_token = context_tokens[1]
            if entities.get("amounts") and not swap_info.amount:
                swap_info.amount = str(entities["amounts"][0])
        
        return swap_info
    
    def _apply_continuation(
        self,
        swap_info: SwapInfo,
        step: str,
        value: str,
    ) -> SwapInfo:
        """Apply continuation value to swap info."""
        value_upper = value.upper().strip()
        value_lower = value.lower().strip()
        
        # Check if user selected a numbered option (1, 2, 3, etc.)
        number_match = re.search(r"^(\d+)", value_lower)
        if number_match:
            option_num = int(number_match.group(1))
            # Map number to token/amount based on step
            if step == "from_token":
                if 1 <= option_num <= len(self._popular_tokens):
                    swap_info.from_token = self._popular_tokens[option_num - 1]
                    return swap_info
            elif step == "to_token":
                # Exclude from_token from options
                available_tokens = [t for t in self._popular_tokens if t != swap_info.from_token]
                if 1 <= option_num <= len(available_tokens):
                    swap_info.to_token = available_tokens[option_num - 1]
                    return swap_info
            elif step == "amount":
                # Common amounts for quick selection
                common_amounts = ["10", "50", "100", "500", "1000"]
                if 1 <= option_num <= len(common_amounts):
                    swap_info.amount = common_amounts[option_num - 1]
                    return swap_info
        
        # Fallback to original logic for text-based responses
        if step == "from_token":
            # Extract token from value
            for token in SUPPORTED_TOKENS:
                if token in value_upper:
                    swap_info.from_token = token
                    break
            else:
                # Maybe just the token name
                if value_upper in SUPPORTED_TOKENS:
                    swap_info.from_token = value_upper
        
        elif step == "to_token":
            for token in SUPPORTED_TOKENS:
                if token in value_upper:
                    swap_info.to_token = token
                    break
            else:
                if value_upper in SUPPORTED_TOKENS:
                    swap_info.to_token = value_upper
        
        elif step == "amount":
            # Extract number
            match = re.search(r"(\d+\.?\d*)", value)
            if match:
                swap_info.amount = match.group(1)
            else:
                swap_info.amount = value.strip()
        
        return swap_info
    
    def _get_rate(self, from_token: str, to_token: str) -> float:
        """Get exchange rate for token pair."""
        key = (from_token, to_token)
        if key in self._demo_rates:
            return self._demo_rates[key]
        
        # Fallback calculation
        reverse_key = (to_token, from_token)
        if reverse_key in self._demo_rates:
            return 1.0 / self._demo_rates[reverse_key]
        
        # Default to 1:1 for unknown pairs
        return 1.0
    
    def _get_message(self, key: str, language: str) -> str:
        """Get localized message."""
        messages = self._messages.get(key, {})
        return messages.get(language, messages.get("en", ""))
    
    def _format_token_options(self, tokens: list[str], language: str) -> str:
        """Format token options as numbered list."""
        options_text = {
            "en": "Select a token:",
            "es": "Selecciona un token:",
            "pt": "Selecione um token:",
        }
        header = options_text.get(language, options_text["en"])
        
        options = []
        for i, token in enumerate(tokens[:6], 1):  # Limit to 6 options
            options.append(f"{i}. {token}")
        
        return f"{header}\n" + "\n".join(options)
    
    def _format_amount_options(self, language: str) -> str:
        """Format amount options as numbered list."""
        common_amounts = ["10", "50", "100", "500", "1000"]
        options_text = {
            "en": "Select an amount:",
            "es": "Selecciona una cantidad:",
            "pt": "Selecione uma quantidade:",
        }
        header = options_text.get(language, options_text["en"])
        
        options = []
        for i, amount in enumerate(common_amounts, 1):
            options.append(f"{i}. {amount}")
        
        return f"{header}\n" + "\n".join(options) + "\n\nOr type a custom amount."

