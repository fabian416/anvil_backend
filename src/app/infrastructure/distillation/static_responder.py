"""Static response system with template engine."""
from typing import Dict, Optional, Any
import re

from app.domain.ports.distillation_repository import StaticResponseRepository
from app.domain.value_objects.distillation import ExtractedEntities, Intent


class StaticResponder:
    """
    Generate static responses from templates.
    
    Supports:
    - Template variable injection
    - Dynamic data source integration
    - Variant selection based on conditions
    """
    
    def __init__(
        self,
        static_response_repo: StaticResponseRepository,
        data_sources: Optional[Dict[str, Any]] = None,
    ):
        self.static_response_repo = static_response_repo
        self.data_sources = data_sources or {}
    
    async def generate(
        self,
        intent: Intent,
        entities: ExtractedEntities,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Generate static response for intent.
        
        Args:
            intent: Classified intent
            entities: Extracted entities from query
            user_context: Optional user context (time of day, etc.)
            
        Returns:
            Generated response or None if not available
        """
        # Select appropriate variant
        variant = self._select_variant(intent, user_context or {})
        
        # Get static response template
        static_response = await self.static_response_repo.get_response(intent, variant)
        
        if not static_response or not static_response.is_active:
            return None
        
        # If no variables, return template as-is
        if not static_response.template_variables:
            return static_response.response_template
        
        # Fetch dynamic data if needed
        data = {}
        if static_response.data_source:
            data = await self._fetch_data(
                static_response.data_source,
                entities,
                user_context or {},
            )
        
        # Inject variables into template
        try:
            response = self._inject_variables(
                static_response.response_template,
                static_response.template_variables,
                entities,
                data,
            )
            return response
        except Exception:
            # If injection fails, return template as-is
            return static_response.response_template
    
    async def check_available(
        self,
        intent: Intent,
        entities: ExtractedEntities,
    ) -> bool:
        """
        Check if static response is available for intent.
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            True if static response can be generated
        """
        # Get default variant
        static_response = await self.static_response_repo.get_response(intent, "default")
        
        if not static_response or not static_response.is_active:
            return False
        
        # Check if required entities are present for data sources
        if static_response.data_source:
            return self._has_required_entities(
                static_response.data_source,
                entities,
            )
        
        return True
    
    def _select_variant(self, intent: Intent, context: Dict[str, Any]) -> str:
        """
        Select appropriate variant based on context.
        
        Args:
            intent: Intent type
            context: User context (time_of_day, etc.)
            
        Returns:
            Variant name
        """
        # Time-based variants for greetings
        if intent == Intent.GREETING:
            time_of_day = context.get("time_of_day", "").lower()
            
            if "morning" in time_of_day or context.get("hour", 12) < 12:
                return "morning"
            elif "evening" in time_of_day or context.get("hour", 12) >= 18:
                return "evening"
        
        # Default variant
        return "default"
    
    async def _fetch_data(
        self,
        data_source: str,
        entities: ExtractedEntities,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fetch dynamic data from external source.
        
        Args:
            data_source: Data source identifier
            entities: Extracted entities
            context: User context
            
        Returns:
            Data dictionary for template injection
        """
        # Get data fetcher for source
        fetcher = self.data_sources.get(data_source)
        
        if not fetcher:
            return {}
        
        try:
            # Call data fetcher
            data = await fetcher.fetch(entities, context)
            return data
        except Exception:
            # Return empty dict on error
            return {}
    
    def _inject_variables(
        self,
        template: str,
        variables: list,
        entities: ExtractedEntities,
        data: Dict[str, Any],
    ) -> str:
        """
        Inject variables into template.
        
        Args:
            template: Template string with {variable} placeholders
            variables: List of variable names
            entities: Extracted entities
            data: Data from external sources
            
        Returns:
            Template with variables replaced
        """
        replacements = {}
        
        for var in variables:
            # Try to get value from data first
            if var in data:
                replacements[var] = str(data[var])
                continue
            
            # Try to get from entities
            value = self._get_entity_value(var, entities)
            if value:
                replacements[var] = value
                continue
            
            # Default to placeholder
            replacements[var] = f"[{var}]"
        
        # Replace all variables in template
        result = template
        for var, value in replacements.items():
            result = result.replace(f"{{{var}}}", value)
        
        return result
    
    def _get_entity_value(self, var: str, entities: ExtractedEntities) -> Optional[str]:
        """
        Get entity value for variable name.
        
        Args:
            var: Variable name
            entities: Extracted entities
            
        Returns:
            Entity value or None
        """
        # Token variables
        if var == "token" and entities.tokens:
            return entities.tokens[0]
        
        # Protocol variables
        if var == "protocol" and entities.protocols:
            return entities.protocols[0]
        
        # Chain variables
        if var == "chain" and entities.chains:
            return entities.chains[0]
        
        # Amount variables
        if var == "amount" and entities.amounts:
            return str(entities.amounts[0])
        
        return None
    
    def _has_required_entities(
        self,
        data_source: str,
        entities: ExtractedEntities,
    ) -> bool:
        """
        Check if required entities are present for data source.
        
        Args:
            data_source: Data source identifier
            entities: Extracted entities
            
        Returns:
            True if all required entities present
        """
        # Define required entities per data source
        requirements = {
            "coingecko_api": ["tokens"],  # Needs at least one token
            "gas_api": [],  # No specific requirements
            "portfolio_service": [],  # Uses user_id from context
        }
        
        required = requirements.get(data_source, [])
        
        for req in required:
            if req == "tokens" and not entities.tokens:
                return False
            elif req == "protocols" and not entities.protocols:
                return False
            elif req == "chains" and not entities.chains:
                return False
        
        return True


class DataSourceFetcher:
    """Base class for data source fetchers."""
    
    async def fetch(
        self,
        entities: ExtractedEntities,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fetch data from source."""
        raise NotImplementedError


class CoinGeckoDataFetcher(DataSourceFetcher):
    """Fetch price data from CoinGecko API."""
    
    def __init__(self, api_client: Optional[Any] = None):
        self.api_client = api_client
    
    async def fetch(
        self,
        entities: ExtractedEntities,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fetch token price data.
        
        Returns:
            {
                "token": "ETH",
                "price": "2150.50",
                "change_24h": "+2.5"
            }
        """
        if not entities.tokens:
            return {}
        
        token = entities.tokens[0]
        
        # TODO: Integrate with actual CoinGecko API
        # For now, return mock data
        return {
            "token": token,
            "price": "2150.50",
            "change_24h": "+2.5",
        }


class GasDataFetcher(DataSourceFetcher):
    """Fetch gas price data."""
    
    def __init__(self, api_client: Optional[Any] = None):
        self.api_client = api_client
    
    async def fetch(
        self,
        entities: ExtractedEntities,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fetch gas prices.
        
        Returns:
            {
                "chain": "Ethereum",
                "low": "15",
                "avg": "20",
                "high": "30"
            }
        """
        chain = entities.chains[0] if entities.chains else "Ethereum"
        
        # TODO: Integrate with actual gas API
        # For now, return mock data
        return {
            "chain": chain,
            "low": "15",
            "avg": "20",
            "high": "30",
        }


class PortfolioDataFetcher(DataSourceFetcher):
    """Fetch user portfolio data."""
    
    def __init__(self, portfolio_service: Optional[Any] = None):
        self.portfolio_service = portfolio_service
    
    async def fetch(
        self,
        entities: ExtractedEntities,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Fetch user portfolio data.
        
        Returns:
            {
                "total_value": "50000.00",
                "holdings_list": "ETH: 10.5, USDC: 25000"
            }
        """
        user_id = context.get("user_id")
        
        if not user_id:
            return {}
        
        # TODO: Integrate with actual portfolio service
        # For now, return mock data
        return {
            "total_value": "50000.00",
            "holdings_list": "ETH: 10.5, USDC: 25000",
        }
