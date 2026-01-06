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


class SwapHandlerV2:
    """
    Multi-turn conversational swap handler.
    
    Supports:
    - Single message complete swaps: "swap 100 USDC to ETH"
    - Multi-turn flows: "quiero swap" → "de USDC" → "a ETH" → "100"
    - Context-aware continuation
    """
    
    def __init__(self):
        self._messages = {
            "ask_from_token": {
                "en": "🔄 I can help you swap tokens!\n\nWhat token do you want to swap **from**?\n(e.g., USDC, ETH, BTC)",
                "es": "🔄 ¡Puedo ayudarte a intercambiar tokens!\n\n¿**De qué** token quieres hacer swap?\n(ej: USDC, ETH, BTC)",
                "pt": "🔄 Posso ajudá-lo a trocar tokens!\n\n**De qual** token você quer fazer swap?\n(ex: USDC, ETH, BTC)",
            },
            "ask_to_token": {
                "en": "Got it! You want to swap **{from_token}**.\n\nWhat token do you want to receive?\n(e.g., ETH, USDC, BTC)",
                "es": "¡Entendido! Quieres cambiar **{from_token}**.\n\n¿Qué token quieres recibir?\n(ej: ETH, USDC, BTC)",
                "pt": "Entendi! Você quer trocar **{from_token}**.\n\nQual token você quer receber?\n(ex: ETH, USDC, BTC)",
            },
            "ask_amount": {
                "en": "Perfect! Swapping **{from_token}** → **{to_token}**\n\nHow much {from_token} do you want to swap?",
                "es": "¡Perfecto! Intercambio **{from_token}** → **{to_token}**\n\n¿Cuántos {from_token} quieres cambiar?",
                "pt": "Perfeito! Troca **{from_token}** → **{to_token}**\n\nQuantos {from_token} você quer trocar?",
            },
            "quote": {
                "en": """💱 **Swap Quote**

**From:** {amount} {from_token}
**To:** ~{output_amount} {to_token}

**Rate:** 1 {from_token} = {rate} {to_token}
**Price Impact:** {price_impact}%
**Network:** Ethereum

⚠️ **Demo Mode** - Sign up to execute real swaps!

👉 [Sign Up Free](/signup) to:
• Execute swaps with best rates
• Track your transactions
• Access portfolio management""",
                "es": """💱 **Cotización de Swap**

**De:** {amount} {from_token}
**A:** ~{output_amount} {to_token}

**Tasa:** 1 {from_token} = {rate} {to_token}
**Impacto en precio:** {price_impact}%
**Red:** Ethereum

⚠️ **Modo Demo** - ¡Regístrate para ejecutar swaps reales!

👉 [Regístrate Gratis](/signup) para:
• Ejecutar swaps con las mejores tasas
• Seguir tus transacciones
• Acceder a gestión de portafolio""",
                "pt": """💱 **Cotação de Swap**

**De:** {amount} {from_token}
**Para:** ~{output_amount} {to_token}

**Taxa:** 1 {from_token} = {rate} {to_token}
**Impacto no preço:** {price_impact}%
**Rede:** Ethereum

⚠️ **Modo Demo** - Cadastre-se para executar swaps reais!

👉 [Cadastre-se Grátis](/signup) para:
• Executar swaps com as melhores taxas
• Acompanhar suas transações
• Acessar gestão de portfólio""",
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
        # Initialize swap_info from previous state if available
        if previous_swap_info:
            swap_info = SwapInfo(
                from_token=previous_swap_info.get("from_token"),
                to_token=previous_swap_info.get("to_token"),
                amount=previous_swap_info.get("amount"),
            )
        else:
            # Extract swap info from message and context
            swap_info = self._extract_swap_info(message, context)
        
        # Handle continuation of pending flow
        if continuation_step:
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
            return HandlerResult(
                content=self._get_message("ask_from_token", language),
                pending_action="swap_awaiting_from_token",
                metadata=swap_info.to_dict(),
            )
        
        # Ask for to_token
        if not swap_info.to_token:
            return HandlerResult(
                content=self._get_message("ask_to_token", language).format(
                    from_token=swap_info.from_token
                ),
                pending_action="swap_awaiting_to_token",
                metadata=swap_info.to_dict(),
            )
        
        # Ask for amount
        if not swap_info.amount:
            return HandlerResult(
                content=self._get_message("ask_amount", language).format(
                    from_token=swap_info.from_token,
                    to_token=swap_info.to_token,
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
        
        # Format quote
        content = self._get_message("quote", language).format(
            amount=swap_info.amount,
            from_token=swap_info.from_token,
            to_token=swap_info.to_token,
            output_amount=f"{output_amount:.6f}",
            rate=f"{rate:.6f}",
            price_impact="0.05",
        )
        
        return HandlerResult(
            content=content,
            pending_action=None,
            requires_registration=True,
            metadata=swap_info.to_dict(),
            enrichment={
                "swap_quote": {
                    "from_token": swap_info.from_token,
                    "to_token": swap_info.to_token,
                    "from_amount": swap_info.amount,
                    "to_amount": f"{output_amount:.6f}",
                    "rate": rate,
                    "price_impact": 0.05,
                    "network": "ethereum",
                    "is_demo": True,
                },
            },
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
        
        # Extract tokens mentioned
        found_tokens = []
        for token in SUPPORTED_TOKENS:
            if token.lower() in combined:
                found_tokens.append(token)
        
        # Try to extract source token with patterns
        from_patterns = [
            r"(?:swap|cambiar|trocar|exchange)\s+(?:\d+\.?\d*\s*)?(\w+)",
            r"(?:de|from|del)\s+(\w+)",
        ]
        for pattern in from_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                if token in SUPPORTED_TOKENS:
                    swap_info.from_token = token
                    break
        
        # Try to extract target token
        to_patterns = [
            r"(?:to|a|hacia|por|for|para)\s+(\w+)",
        ]
        for pattern in to_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                token = match.group(1).upper()
                if token in SUPPORTED_TOKENS and token != swap_info.from_token:
                    swap_info.to_token = token
                    break
        
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
        if found_tokens and not swap_info.from_token and not swap_info.to_token:
            if len(found_tokens) >= 1:
                swap_info.from_token = found_tokens[0]
            if len(found_tokens) >= 2:
                swap_info.to_token = found_tokens[1]
        
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

