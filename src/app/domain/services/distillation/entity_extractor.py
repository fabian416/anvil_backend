"""Entity extraction service."""
import re
from decimal import Decimal
from typing import List

from app.domain.value_objects.distillation import ExtractedEntities


class EntityExtractor:
    """Extract DeFi-relevant entities from text."""
    
    # Known tokens
    KNOWN_TOKENS = {
        "eth", "ethereum", "btc", "bitcoin", "usdc", "usdt", "dai", "weth",
        "uni", "uniswap", "aave", "comp", "compound", "crv", "curve",
        "matic", "polygon", "arb", "arbitrum", "op", "optimism",
        "steth", "reth", "cbeth", "wsteth", "frax", "lusd", "mkr",
    }
    
    # Known protocols
    KNOWN_PROTOCOLS = {
        "uniswap", "aave", "compound", "curve", "balancer", "yearn",
        "lido", "rocket pool", "morpho", "euler", "convex", "beefy",
        "gmx", "dydx", "hyperliquid", "1inch", "paraswap",
        "stargate", "across", "hop", "synapse",
    }
    
    # Known chains
    KNOWN_CHAINS = {
        "ethereum", "arbitrum", "optimism", "polygon", "base",
        "bnb", "avalanche", "fantom", "mainnet", "l1", "l2",
    }
    
    def extract(self, text: str) -> ExtractedEntities:
        """
        Extract all relevant entities from text.
        
        Args:
            text: User query text
            
        Returns:
            ExtractedEntities with all extracted entities
        """
        text_lower = text.lower()
        
        return ExtractedEntities(
            tokens=self._extract_tokens(text_lower),
            protocols=self._extract_protocols(text_lower),
            chains=self._extract_chains(text_lower),
            amounts=self._extract_amounts(text),
            addresses=self._extract_addresses(text),
            time_references=self._extract_time_refs(text_lower),
        )
    
    def _extract_tokens(self, text: str) -> List[str]:
        """Extract token symbols from text."""
        tokens = []
        
        # Check against known tokens
        for token in self.KNOWN_TOKENS:
            if re.search(r"\b" + token + r"\b", text):
                tokens.append(token.upper())
        
        # Look for $ prefixed tokens (e.g., $ETH)
        dollar_tokens = re.findall(r"\$([A-Z]{2,6})\b", text.upper())
        tokens.extend(dollar_tokens)
        
        # Remove duplicates, preserve order
        return list(dict.fromkeys(tokens))
    
    def _extract_protocols(self, text: str) -> List[str]:
        """Extract protocol names from text."""
        protocols = []
        
        for protocol in self.KNOWN_PROTOCOLS:
            if protocol in text:
                protocols.append(protocol)
        
        return protocols
    
    def _extract_chains(self, text: str) -> List[str]:
        """Extract blockchain names from text."""
        chains = []
        
        for chain in self.KNOWN_CHAINS:
            if re.search(r"\b" + chain + r"\b", text):
                chains.append(chain)
        
        return chains
    
    def _extract_amounts(self, text: str) -> List[Decimal]:
        """Extract numeric amounts from text."""
        amounts = []
        
        # Match numbers (including decimals)
        # Patterns: 100, 100.5, 1,000, 1,000.50
        patterns = [
            r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b",  # 1,000.50
            r"\b(\d+\.\d+)\b",  # 100.5
            r"\b(\d+)\b",  # 100
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Remove commas
                    clean_num = match.replace(",", "")
                    amount = Decimal(clean_num)
                    
                    # Filter out unrealistic amounts (avoid extracting years, etc.)
                    if Decimal("0.000001") <= amount <= Decimal("1000000000"):
                        amounts.append(amount)
                except (ValueError, Decimal.InvalidOperation):
                    continue
        
        # Remove duplicates, preserve order
        return list(dict.fromkeys(amounts))
    
    def _extract_addresses(self, text: str) -> List[str]:
        """Extract Ethereum addresses from text."""
        # Match 0x followed by 40 hex characters
        pattern = r"\b(0x[a-fA-F0-9]{40})\b"
        addresses = re.findall(pattern, text)
        
        return addresses
    
    def _extract_time_refs(self, text: str) -> List[str]:
        """Extract time references from text."""
        time_patterns = [
            r"\btoday\b",
            r"\byesterday\b",
            r"\btomorrow\b",
            r"\blast (week|month|year|hour|day)\b",
            r"\bnext (week|month|year|hour|day)\b",
            r"\bthis (week|month|year)\b",
            r"\b(\d+) (days?|weeks?|months?|years?) ago\b",
            r"\bin the (last|past) (\d+) (days?|weeks?|months?)\b",
        ]
        
        time_refs = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    time_refs.append(" ".join(matches[0]))
                else:
                    time_refs.append(matches[0])
        
        return time_refs
