"""
Network Analysis Interactors

Application services for advanced graph algorithms.
"""

from typing import List, Optional
from uuid import UUID

from app.domain.ml.services.network_analysis_service import (
    NetworkAnalysisService,
    PageRankResult,
    CommunityDetectionResult,
    CentralityResult,
    ContagionSimulation,
)


class CalculatePageRankInteractor:
    """Calculate PageRank for protocols"""

    def __init__(
        self,
        network_service: NetworkAnalysisService,
    ):
        """Initialize interactor"""
        self._network_service = network_service

    async def execute(
        self,
        damping_factor: float = 0.85,
        max_iterations: int = 100,
    ) -> List[PageRankResult]:
        """
        Calculate PageRank importance scores.

        Args:
            damping_factor: PageRank damping factor
            max_iterations: Maximum iterations

        Returns:
            List of protocols ranked by importance
        """
        return await self._network_service.calculate_pagerank(
            damping_factor=damping_factor,
            max_iterations=max_iterations,
        )


class DetectCommunitiesInteractor:
    """Detect protocol communities"""

    def __init__(
        self,
        network_service: NetworkAnalysisService,
    ):
        """Initialize interactor"""
        self._network_service = network_service

    async def execute(
        self,
        algorithm: str = "label_propagation",
    ) -> List[CommunityDetectionResult]:
        """
        Detect communities in protocol network.

        Args:
            algorithm: Detection algorithm

        Returns:
            List of detected communities
        """
        return await self._network_service.detect_communities(algorithm)


class CalculateCentralityInteractor:
    """Calculate centrality metrics"""

    def __init__(
        self,
        network_service: NetworkAnalysisService,
    ):
        """Initialize interactor"""
        self._network_service = network_service

    async def execute(
        self,
        protocol_id: Optional[UUID] = None,
    ) -> List[CentralityResult]:
        """
        Calculate centrality metrics.

        Args:
            protocol_id: Specific protocol (optional)

        Returns:
            List of centrality results
        """
        return await self._network_service.calculate_centrality(protocol_id)


class SimulateContagionInteractor:
    """Simulate cascade risk"""

    def __init__(
        self,
        network_service: NetworkAnalysisService,
    ):
        """Initialize interactor"""
        self._network_service = network_service

    async def execute(
        self,
        origin_protocol_id: UUID,
        propagation_probability: float = 0.8,
        max_depth: int = 5,
    ) -> ContagionSimulation:
        """
        Simulate contagion cascade from protocol failure.

        Args:
            origin_protocol_id: Origin of failure
            propagation_probability: Cascade probability
            max_depth: Maximum cascade depth

        Returns:
            Contagion simulation result
        """
        return await self._network_service.simulate_contagion(
            origin_protocol_id=origin_protocol_id,
            propagation_probability=propagation_probability,
            max_depth=max_depth,
        )
