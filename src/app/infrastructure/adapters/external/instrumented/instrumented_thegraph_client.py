"""
Instrumented TheGraph Client with Full Telemetry.

Provides complete observability for The Graph API calls:
- Request timing and latency tracking
- Query complexity tracking
- Error categorization
- Distributed tracing with span propagation
- Subgraph-specific metrics
"""

from typing import Any, Optional

from app.infrastructure.telemetry.api_telemetry import (
    APITelemetry,
    APIStatus,
    get_api_telemetry,
)
from app.infrastructure.telemetry.tracing import (
    TracingService,
    SpanKind,
    SpanStatus,
    get_tracing_service,
)


class InstrumentedTheGraphClient:
    """
    The Graph client with full telemetry instrumentation.
    
    Usage:
        client = InstrumentedTheGraphClient(api_key="your_key")
        
        # All calls automatically instrumented
        result = await client.query(subgraph, query, variables)
        
        # Get metrics
        telemetry = get_api_telemetry()
        metrics = telemetry.get_metrics("thegraph")
    """
    
    API_NAME = "thegraph"
    BASE_URL = "https://gateway.thegraph.com/api"
    
    def __init__(
        self,
        api_key: str | None = None,
        telemetry: Optional[APITelemetry] = None,
        tracing: Optional[TracingService] = None,
    ):
        """
        Initialize instrumented The Graph client.
        
        Args:
            api_key: The Graph API key
            telemetry: API telemetry instance
            tracing: Tracing service instance
        """
        import httpx
        
        self._api_key = api_key
        self._telemetry = telemetry or get_api_telemetry()
        self._tracing = tracing or get_tracing_service()
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=60.0,  # Graph queries can be slow
            headers=headers,
        )
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
    
    async def query(
        self,
        subgraph_id: str,
        query: str,
        variables: Optional[dict] = None,
        operation_name: str = "",
    ) -> dict[str, Any]:
        """
        Execute GraphQL query with telemetry.
        
        Args:
            subgraph_id: Subgraph ID or deployment ID
            query: GraphQL query string
            variables: Query variables
            operation_name: Operation name for telemetry
            
        Returns:
            Query result data
        """
        op_name = operation_name or self._extract_operation_name(query)
        
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation=op_name,
            subgraph_id=subgraph_id[:20] if subgraph_id else "",
        )
        
        with self._tracing.start_span(
            name=f"{self.API_NAME}.{op_name}",
            kind=SpanKind.CLIENT,
            attributes={
                "api.name": self.API_NAME,
                "api.operation": op_name,
                "graphql.subgraph_id": subgraph_id,
                "graphql.query_length": len(query),
            },
        ) as span:
            try:
                url = f"/{self._api_key}/subgraphs/id/{subgraph_id}" if self._api_key else f"/subgraphs/id/{subgraph_id}"
                
                response = await self._client.post(
                    url,
                    json={
                        "query": query,
                        "variables": variables or {},
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for GraphQL errors
                if "errors" in data:
                    error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
                    ctx.complete(
                        status=APIStatus.ERROR,
                        status_code=response.status_code,
                        error_message="; ".join(error_messages),
                        error_type="graphql_error",
                    )
                    span.set_status(SpanStatus.ERROR, "; ".join(error_messages))
                else:
                    ctx.complete(status=APIStatus.SUCCESS, status_code=response.status_code)
                    span.set_status(SpanStatus.OK)
                
                span.set_attribute("graphql.has_errors", "errors" in data)
                
                return data.get("data", {})
                
            except Exception as e:
                error_type = self._classify_error(e)
                ctx.complete(
                    status=error_type,
                    error_message=str(e),
                    error_type=type(e).__name__,
                )
                span.set_status(SpanStatus.ERROR, str(e))
                raise
                
            finally:
                await self._telemetry.record(ctx)
    
    async def query_uniswap_v3(
        self,
        query: str,
        variables: Optional[dict] = None,
        chain: str = "ethereum",
    ) -> dict[str, Any]:
        """Query Uniswap V3 subgraph with telemetry."""
        # Subgraph IDs for different chains
        subgraph_ids = {
            "ethereum": "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV",
            "polygon": "3hCPRGf4z88VC5rsBKU5AA9FBBq5nF3jbKJG7VZCbhjm",
            "arbitrum": "FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM",
        }
        
        subgraph_id = subgraph_ids.get(chain, subgraph_ids["ethereum"])
        
        return await self.query(
            subgraph_id=subgraph_id,
            query=query,
            variables=variables,
            operation_name="uniswap_v3_query",
        )
    
    async def query_aave_v3(
        self,
        query: str,
        variables: Optional[dict] = None,
        chain: str = "ethereum",
    ) -> dict[str, Any]:
        """Query Aave V3 subgraph with telemetry."""
        subgraph_ids = {
            "ethereum": "GQFbb95cE6d8mV989mL5figjaGaKCQB3xqYrr1bRyXqF",
            "polygon": "Co2URyXjnxaw8WqxKyVHdirq9Ahhm5vcTs4pKwRNm1CV",
            "arbitrum": "DLuE98AEBBKjmSj3jSHpXmZdoAcjBBjbk2bCR9vpqWsS",
        }
        
        subgraph_id = subgraph_ids.get(chain, subgraph_ids["ethereum"])
        
        return await self.query(
            subgraph_id=subgraph_id,
            query=query,
            variables=variables,
            operation_name="aave_v3_query",
        )
    
    def _extract_operation_name(self, query: str) -> str:
        """Extract operation name from GraphQL query."""
        import re
        
        # Try to extract operation name from query
        match = re.search(r'(query|mutation|subscription)\s+(\w+)', query)
        if match:
            return match.group(2)
        
        # Try to get first field
        match = re.search(r'{\s*(\w+)', query)
        if match:
            return match.group(1)
        
        return "graphql_query"
    
    def _classify_error(self, error: Exception) -> APIStatus:
        """Classify error type for telemetry."""
        import httpx
        
        if isinstance(error, httpx.TimeoutException):
            return APIStatus.TIMEOUT
        
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                return APIStatus.RATE_LIMITED
            if error.response.status_code in (401, 403):
                return APIStatus.AUTH_FAILURE
        
        return APIStatus.ERROR
