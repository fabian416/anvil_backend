# Admin Projects - Setup Examples

"""
Example code for setting up and managing Admin Projects.
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime


# =============================================================================
# DATA MODELS
# =============================================================================

class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Visibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"


@dataclass
class ProjectRiskConfig:
    """Risk parameters for a project."""
    max_slippage_bps: int = 100
    max_position_usd: float = 10000
    max_daily_volume_usd: float = 50000
    require_2fa_for_transactions: bool = True
    allowed_tokens: Optional[List[str]] = None
    blocked_tokens: List[str] = field(default_factory=list)
    require_simulation: bool = True
    min_health_factor: Optional[float] = None


@dataclass
class Project:
    """Admin-configured project definition."""
    id: UUID
    slug: str
    name: str
    description: str
    icon: str
    color: str
    
    status: ProjectStatus
    visibility: Visibility
    
    system_prompt: str
    welcome_message: str
    
    enabled_protocols: List[str]
    enabled_chains: List[str]
    enabled_tools: List[str]
    
    risk_config: ProjectRiskConfig
    
    created_by: UUID
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeDocument:
    """Knowledge base document."""
    id: UUID
    title: str
    content: str
    doc_type: str  # guide, faq, reference, data
    tags: List[str]
    priority: int = 1


# =============================================================================
# PROJECT MANAGER
# =============================================================================

class ProjectManager:
    """Manage admin-configured projects."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_project(
        self,
        slug: str,
        name: str,
        description: str,
        system_prompt: str,
        created_by: UUID,
        **kwargs
    ) -> Project:
        """
        Create a new project.
        
        Example:
            project = await manager.create_project(
                slug="defi-basics",
                name="DeFi Basics",
                description="Educational project for beginners",
                system_prompt="You are a DeFi educator...",
                created_by=admin_id,
                enabled_protocols=["uniswap", "aave"],
                enabled_chains=["ethereum"],
                risk_config=ProjectRiskConfig(max_position_usd=1000)
            )
        """
        project = Project(
            id=uuid4(),
            slug=slug,
            name=name,
            description=description,
            icon=kwargs.get("icon", "📌"),
            color=kwargs.get("color", "#6366F1"),
            status=ProjectStatus.DRAFT,
            visibility=Visibility(kwargs.get("visibility", "public")),
            system_prompt=system_prompt,
            welcome_message=kwargs.get("welcome_message", f"Welcome to {name}!"),
            enabled_protocols=kwargs.get("enabled_protocols", []),
            enabled_chains=kwargs.get("enabled_chains", ["ethereum"]),
            enabled_tools=kwargs.get("enabled_tools", []),
            risk_config=kwargs.get("risk_config", ProjectRiskConfig()),
            created_by=created_by
        )
        
        # Save to database
        await self._save_project(project)
        
        # Create associated knowledge base
        await self._create_knowledge_base(project.id)
        
        return project
    
    async def update_project(self, project_id: UUID, **updates) -> Project:
        """Update project configuration."""
        project = await self.get_project(project_id)
        
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.utcnow()
        await self._save_project(project)
        
        return project
    
    async def activate_project(self, project_id: UUID) -> Project:
        """Activate a draft project."""
        return await self.update_project(project_id, status=ProjectStatus.ACTIVE)
    
    async def get_project(self, project_id: UUID) -> Project:
        """Get project by ID."""
        # Database query
        pass
    
    async def _save_project(self, project: Project):
        """Save project to database."""
        pass
    
    async def _create_knowledge_base(self, project_id: UUID):
        """Create knowledge base for project."""
        pass


# =============================================================================
# KNOWLEDGE BASE MANAGER
# =============================================================================

class KnowledgeBaseManager:
    """Manage project knowledge bases."""
    
    def __init__(self, db_session, embedding_service):
        self.db = db_session
        self.embeddings = embedding_service
    
    async def add_document(
        self,
        project_id: UUID,
        title: str,
        content: str,
        doc_type: str,
        tags: List[str] = None,
        priority: int = 1
    ) -> KnowledgeDocument:
        """
        Add document to project knowledge base.
        
        Example:
            doc = await kb_manager.add_document(
                project_id=aave_project.id,
                title="Health Factor Guide",
                content="# Understanding Health Factor...",
                doc_type="guide",
                tags=["health-factor", "liquidation"],
                priority=1
            )
        """
        doc = KnowledgeDocument(
            id=uuid4(),
            title=title,
            content=content,
            doc_type=doc_type,
            tags=tags or [],
            priority=priority
        )
        
        # Save document
        await self._save_document(project_id, doc)
        
        # Process and embed chunks
        await self._process_document(project_id, doc)
        
        return doc
    
    async def search(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search knowledge base using semantic similarity.
        
        Example:
            results = await kb_manager.search(
                project_id=aave_project.id,
                query="How do I avoid liquidation?",
                top_k=3
            )
        """
        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)
        
        # Search vector store
        results = await self._vector_search(project_id, query_embedding, top_k)
        
        return results
    
    async def _save_document(self, project_id: UUID, doc: KnowledgeDocument):
        """Save document to database."""
        pass
    
    async def _process_document(self, project_id: UUID, doc: KnowledgeDocument):
        """Process document into chunks and generate embeddings."""
        # Split into chunks
        chunks = self._split_into_chunks(doc.content)
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            embedding = await self.embeddings.embed(chunk)
            await self._save_chunk(project_id, doc.id, i, chunk, embedding)
    
    def _split_into_chunks(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split content into overlapping chunks."""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    async def _vector_search(self, project_id: UUID, embedding: List[float], top_k: int) -> List[Dict]:
        """Search vector store for similar chunks."""
        pass
    
    async def _save_chunk(self, project_id: UUID, doc_id: UUID, index: int, text: str, embedding: List[float]):
        """Save chunk with embedding."""
        pass


# =============================================================================
# USER ASSIGNMENT MANAGER
# =============================================================================

class UserAssignmentManager:
    """Manage user-project assignments."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def assign_user(
        self,
        user_id: UUID,
        project_id: UUID,
        assignment_type: str = "manual",
        assigned_by: UUID = None,
        reason: str = None
    ):
        """
        Assign user to project.
        
        Example:
            await assignment_manager.assign_user(
                user_id=user.id,
                project_id=aave_project.id,
                assignment_type="manual",
                assigned_by=admin.id,
                reason="Premium user with Aave positions"
            )
        """
        pass
    
    async def set_active_project(self, user_id: UUID, project_id: UUID):
        """
        Set user's currently active project.
        
        Example:
            await assignment_manager.set_active_project(
                user_id=user.id,
                project_id=savings_project.id
            )
        """
        pass
    
    async def get_user_projects(self, user_id: UUID) -> List[Project]:
        """Get all projects assigned to user."""
        pass
    
    async def get_active_project(self, user_id: UUID) -> Optional[Project]:
        """Get user's currently active project."""
        pass
    
    async def run_auto_assignment(self, user_id: UUID) -> List[UUID]:
        """
        Run auto-assignment rules for a user.
        
        Returns list of newly assigned project IDs.
        """
        pass


# =============================================================================
# PROJECT CONTEXT BUILDER
# =============================================================================

class ProjectContextBuilder:
    """Build context for LLM from project configuration."""
    
    def __init__(self, knowledge_manager: KnowledgeBaseManager):
        self.knowledge = knowledge_manager
    
    async def build_context(
        self,
        project: Project,
        user_message: str,
        user_portfolio: Dict = None
    ) -> Dict:
        """
        Build full context for LLM request.
        
        Returns context dict with:
        - system_message: Full system prompt with knowledge
        - tools: Available tools for this project
        - risk_config: Risk parameters to enforce
        """
        # Retrieve relevant knowledge
        knowledge_results = await self.knowledge.search(
            project_id=project.id,
            query=user_message,
            top_k=5
        )
        
        # Build knowledge context
        knowledge_context = self._format_knowledge(knowledge_results)
        
        # Build system message
        system_message = self._build_system_message(
            project=project,
            knowledge=knowledge_context,
            user_portfolio=user_portfolio
        )
        
        return {
            "system_message": system_message,
            "tools": project.enabled_tools,
            "risk_config": project.risk_config,
            "enabled_chains": project.enabled_chains,
            "enabled_protocols": project.enabled_protocols
        }
    
    def _format_knowledge(self, results: List[Dict]) -> str:
        """Format knowledge results for context."""
        if not results:
            return ""
        
        formatted = "## Relevant Knowledge\n\n"
        for result in results:
            formatted += f"### {result.get('title', 'Reference')}\n"
            formatted += f"{result.get('text', '')}\n\n"
        
        return formatted
    
    def _build_system_message(
        self,
        project: Project,
        knowledge: str,
        user_portfolio: Dict = None
    ) -> str:
        """Build complete system message."""
        
        message = project.system_prompt
        
        if knowledge:
            message += f"\n\n{knowledge}"
        
        if user_portfolio:
            portfolio_summary = self._format_portfolio(user_portfolio)
            message += f"\n\n## User Portfolio\n{portfolio_summary}"
        
        # Add risk guidelines
        message += f"\n\n## Risk Guidelines\n"
        message += f"- Max slippage: {project.risk_config.max_slippage_bps / 100}%\n"
        message += f"- Max position: ${project.risk_config.max_position_usd:,.0f}\n"
        
        if project.risk_config.min_health_factor:
            message += f"- Min health factor: {project.risk_config.min_health_factor}\n"
        
        return message
    
    def _format_portfolio(self, portfolio: Dict) -> str:
        """Format portfolio for context."""
        return f"Total value: ${portfolio.get('total_value_usd', 0):,.2f}"


# =============================================================================
# EXAMPLE: CREATING THE AAVE PROJECT
# =============================================================================

async def create_aave_project_example():
    """Example: Create and configure the Aave project."""
    
    # Initialize managers (mock)
    db_session = None
    embedding_service = None
    
    project_manager = ProjectManager(db_session)
    kb_manager = KnowledgeBaseManager(db_session, embedding_service)
    assignment_manager = UserAssignmentManager(db_session)
    
    admin_id = uuid4()
    
    # Create project
    aave_project = await project_manager.create_project(
        slug="aave",
        name="Aave Lending",
        description="Complete Aave lending and borrowing assistance",
        icon="🏦",
        color="#B6509E",
        
        system_prompt="""You are Anvil's Aave Specialist, an expert in the Aave 
lending protocol across all supported chains.

Your expertise includes:
- Supply and borrow optimization on Aave V3
- Health factor management and liquidation prevention
- E-mode strategies for correlated assets
- GHO stablecoin mechanics

Guidelines:
- Always check health factor before borrowing
- Warn about liquidation risks clearly
- Explain interest rate models
- Consider gas costs for small positions
- Recommend appropriate LTV ratios""",
        
        welcome_message="""Welcome to Aave Lending! 🏦

I'm your dedicated Aave assistant, here to help you lend, borrow, and manage positions.

I can help you with:
• Depositing assets to earn yield
• Borrowing against your collateral safely
• Managing your health factor
• Understanding E-mode opportunities

What would you like to do with Aave today?""",
        
        enabled_protocols=["aave"],
        enabled_chains=["ethereum", "arbitrum", "polygon", "optimism", "base"],
        enabled_tools=["lend", "borrow", "check_health", "swap"],
        
        risk_config=ProjectRiskConfig(
            max_slippage_bps=50,
            max_position_usd=100000,
            min_health_factor=1.5,
            require_simulation=True,
            require_2fa_for_transactions=True
        ),
        
        created_by=admin_id
    )
    
    print(f"Created project: {aave_project.name} ({aave_project.slug})")
    
    # Add knowledge documents
    await kb_manager.add_document(
        project_id=aave_project.id,
        title="Aave V3 Overview",
        content="""# Aave V3 Overview

Aave is a decentralized non-custodial liquidity protocol where users can 
participate as suppliers or borrowers.

## Key Features
- Supply assets to earn interest
- Borrow assets using collateral
- Flash loans for advanced strategies
- E-mode for correlated asset efficiency

## Supported Assets
Aave V3 supports various assets including ETH, WBTC, USDC, USDT, DAI, and more.
Each asset has specific risk parameters and interest rate models.""",
        doc_type="guide",
        tags=["overview", "basics"],
        priority=1
    )
    
    await kb_manager.add_document(
        project_id=aave_project.id,
        title="Health Factor Explained",
        content="""# Understanding Health Factor

The Health Factor (HF) is a numeric representation of the safety of your 
deposited assets against the borrowed assets.

## Formula
HF = (Total Collateral × Liquidation Threshold) / Total Borrows

## Risk Levels
- HF > 2.0: Safe zone
- 1.5 < HF < 2.0: Moderate risk
- 1.0 < HF < 1.5: High risk
- HF < 1.0: Liquidation triggered

## Preventing Liquidation
1. Monitor your HF regularly
2. Set up alerts for low HF
3. Maintain buffer above 1.5
4. Repay debt or add collateral when HF drops""",
        doc_type="guide",
        tags=["health-factor", "liquidation", "risk"],
        priority=1
    )
    
    await kb_manager.add_document(
        project_id=aave_project.id,
        title="E-Mode FAQ",
        content="""# E-Mode Frequently Asked Questions

## What is E-mode?
E-mode (Efficiency Mode) allows borrowers to extract higher borrowing power 
when collateral and borrowed assets are correlated in price.

## Available E-modes
- ETH correlated: ETH, wstETH, rETH
- Stablecoins: USDC, USDT, DAI

## Benefits
- Higher LTV (up to 97%)
- Higher liquidation threshold
- Lower liquidation penalty

## Risks
- Still subject to liquidation
- Limited to correlated assets
- Price divergence risk""",
        doc_type="faq",
        tags=["e-mode", "efficiency", "advanced"],
        priority=2
    )
    
    print(f"Added 3 knowledge documents")
    
    # Activate project
    aave_project = await project_manager.activate_project(aave_project.id)
    print(f"Project status: {aave_project.status.value}")
    
    return aave_project


# =============================================================================
# EXAMPLE: USING PROJECTS IN CHAT
# =============================================================================

async def chat_with_project_example():
    """Example: Process a chat message within project context."""
    
    # Mock setup
    project = Project(
        id=uuid4(),
        slug="aave",
        name="Aave Lending",
        description="Aave assistance",
        icon="🏦",
        color="#B6509E",
        status=ProjectStatus.ACTIVE,
        visibility=Visibility.PUBLIC,
        system_prompt="You are an Aave expert...",
        welcome_message="Welcome!",
        enabled_protocols=["aave"],
        enabled_chains=["ethereum"],
        enabled_tools=["lend", "borrow"],
        risk_config=ProjectRiskConfig(),
        created_by=uuid4()
    )
    
    user_message = "How do I avoid liquidation on my ETH loan?"
    
    # Build context (would use real managers)
    context = {
        "system_message": f"""{project.system_prompt}

## Relevant Knowledge

### Health Factor Explained
The Health Factor (HF) is a numeric representation of the safety...

## Risk Guidelines
- Max slippage: 0.5%
- Min health factor: 1.5
""",
        "tools": project.enabled_tools,
        "risk_config": project.risk_config
    }
    
    print("=" * 60)
    print("PROJECT CHAT EXAMPLE")
    print("=" * 60)
    print(f"\nProject: {project.name}")
    print(f"User: {user_message}")
    print(f"\nContext built with:")
    print(f"  - System prompt length: {len(context['system_message'])} chars")
    print(f"  - Available tools: {context['tools']}")
    print(f"  - Risk config applied: min_health_factor={project.risk_config.min_health_factor}")


# =============================================================================
# RUN EXAMPLES
# =============================================================================

async def main():
    """Run all examples."""
    
    print("=" * 60)
    print("ADMIN PROJECTS - SETUP EXAMPLES")
    print("=" * 60)
    
    # Note: These would work with real database connections
    # For demonstration, we just show the structure
    
    print("\n1. Creating Aave Project (demo)...")
    # await create_aave_project_example()
    
    print("\n2. Chat with Project Context (demo)...")
    await chat_with_project_example()
    
    print("\n" + "=" * 60)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
