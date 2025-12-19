"""
Project entity.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class Project:
    """
    Project entity representing an admin-configured DeFi assistant project.
    
    Each project has:
    - Custom branding and identity
    - Specialized system prompt
    - Configured protocols, chains, and tools
    - Knowledge base for RAG
    - User assignments
    """
    
    def __init__(
        self,
        id: UUID,
        slug: str,
        name: str,
        description: Optional[str],
        icon: Optional[str],
        color: Optional[str],
        banner_url: Optional[str],
        status: str,
        visibility: str,
        system_prompt: str,
        welcome_message: Optional[str],
        enabled_protocols: List[str],
        enabled_chains: List[str],
        enabled_tools: List[str],
        risk_config: Dict[str, Any],
        max_users: Optional[int],
        display_order: int,
        is_featured: bool,
        created_by: UUID,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize project.
        
        Args:
            id: Project identifier
            slug: URL-friendly identifier
            name: Display name
            description: Project description
            icon: Icon/emoji
            color: Hex color
            banner_url: Banner image URL
            status: Project status (draft, active, paused, archived)
            visibility: Visibility (public, private, invite_only)
            system_prompt: System prompt for AI
            welcome_message: Welcome message for users
            enabled_protocols: Allowed DeFi protocols
            enabled_chains: Allowed blockchain networks
            enabled_tools: Allowed tool functions
            risk_config: Risk configuration
            max_users: Maximum user limit
            display_order: Display order
            is_featured: Featured flag
            created_by: Creator user ID
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = id
        self.slug = slug
        self.name = name
        self.description = description
        self.icon = icon
        self.color = color
        self.banner_url = banner_url
        self.status = status
        self.visibility = visibility
        self.system_prompt = system_prompt
        self.welcome_message = welcome_message
        self.enabled_protocols = enabled_protocols
        self.enabled_chains = enabled_chains
        self.enabled_tools = enabled_tools
        self.risk_config = risk_config
        self.max_users = max_users
        self.display_order = display_order
        self.is_featured = is_featured
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        slug: str,
        name: str,
        system_prompt: str,
        created_by: UUID,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        status: str = "draft",
        visibility: str = "public",
        welcome_message: Optional[str] = None,
        enabled_protocols: Optional[List[str]] = None,
        enabled_chains: Optional[List[str]] = None,
        enabled_tools: Optional[List[str]] = None,
        risk_config: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None,
        display_order: int = 0,
        is_featured: bool = False,
    ) -> "Project":
        """
        Create a new project.
        
        Args:
            slug: URL-friendly identifier
            name: Display name
            system_prompt: System prompt for AI
            created_by: Creator user ID
            description: Optional description
            icon: Optional icon/emoji
            color: Optional hex color
            status: Status (default: draft)
            visibility: Visibility (default: public)
            welcome_message: Optional welcome message
            enabled_protocols: Allowed protocols
            enabled_chains: Allowed chains
            enabled_tools: Allowed tools
            risk_config: Risk configuration
            max_users: Maximum users allowed (None = unlimited)
            display_order: Display order for sorting
            is_featured: Featured flag

        Returns:
            New project instance
        """
        return cls(
            id=uuid4(),
            slug=slug,
            name=name,
            description=description,
            icon=icon,
            color=color,
            banner_url=None,
            status=status,
            visibility=visibility,
            system_prompt=system_prompt,
            welcome_message=welcome_message,
            enabled_protocols=enabled_protocols or [],
            enabled_chains=enabled_chains or [],
            enabled_tools=enabled_tools or [],
            risk_config=risk_config or {},
            max_users=max_users,
            display_order=display_order,
            is_featured=is_featured,
            created_by=created_by,
        )
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        banner_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        welcome_message: Optional[str] = None,
        enabled_protocols: Optional[List[str]] = None,
        enabled_chains: Optional[List[str]] = None,
        enabled_tools: Optional[List[str]] = None,
        risk_config: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None,
        display_order: Optional[int] = None,
        is_featured: Optional[bool] = None,
    ) -> None:
        """
        Update project details.
        
        Args:
            name: New name
            description: New description
            icon: New icon
            color: New color
            banner_url: New banner URL
            system_prompt: New system prompt
            welcome_message: New welcome message
            enabled_protocols: New protocols list
            enabled_chains: New chains list
            enabled_tools: New tools list
            risk_config: New risk config
            max_users: New max users
            display_order: New display order
            is_featured: New featured flag
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if icon is not None:
            self.icon = icon
        if color is not None:
            self.color = color
        if banner_url is not None:
            self.banner_url = banner_url
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if welcome_message is not None:
            self.welcome_message = welcome_message
        if enabled_protocols is not None:
            self.enabled_protocols = enabled_protocols
        if enabled_chains is not None:
            self.enabled_chains = enabled_chains
        if enabled_tools is not None:
            self.enabled_tools = enabled_tools
        if risk_config is not None:
            self.risk_config = risk_config
        if max_users is not None:
            self.max_users = max_users
        if display_order is not None:
            self.display_order = display_order
        if is_featured is not None:
            self.is_featured = is_featured
        
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the project."""
        self.status = "active"
        self.updated_at = datetime.utcnow()
    
    def pause(self) -> None:
        """Pause the project."""
        self.status = "paused"
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the project."""
        self.status = "archived"
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status == "active"
    
    def is_public(self) -> bool:
        """Check if project is public."""
        return self.visibility == "public"
    
    def can_accept_users(self, current_user_count: int) -> bool:
        """
        Check if project can accept more users.
        
        Args:
            current_user_count: Current number of users
        
        Returns:
            True if project can accept more users
        """
        if self.max_users is None:
            return True
        return current_user_count < self.max_users
    
    def has_protocol(self, protocol: str) -> bool:
        """Check if protocol is enabled."""
        return protocol in self.enabled_protocols
    
    def has_chain(self, chain: str) -> bool:
        """Check if chain is enabled."""
        return chain in self.enabled_chains
    
    def has_tool(self, tool: str) -> bool:
        """Check if tool is enabled."""
        return tool in self.enabled_tools
    
    @property
    def hunter_tools_enabled(self) -> List[str]:
        """
        Get enabled Hunter AI tools.
        
        Returns:
            List of Hunter AI tool names enabled for this project
        """
        return [
            tool for tool in self.enabled_tools
            if tool.startswith("hunter_")
        ]
    
    @property
    def ultra_tools_enabled(self) -> List[str]:
        """
        Get enabled ULTRA Arbitrage tools.
        
        Returns:
            List of ULTRA tool names enabled for this project
        """
        return [
            tool for tool in self.enabled_tools
            if tool.startswith("ultra_")
        ]
    
    def can_use_hunter_tool(self, tool_name: str) -> bool:
        """
        Check if Hunter AI tool is enabled for this project.
        
        Args:
            tool_name: Hunter AI tool name (e.g., "hunter_sentiment_analysis")
        
        Returns:
            True if tool is enabled
        """
        return tool_name in self.enabled_tools
    
    def can_use_ultra_tool(self, tool_name: str) -> bool:
        """
        Check if ULTRA tool is enabled for this project.
        
        Args:
            tool_name: ULTRA tool name (e.g., "ultra_flash_loans")
        
        Returns:
            True if tool is enabled
        """
        return tool_name in self.enabled_tools
