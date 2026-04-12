"""
Identity management for Cascade Agent.
Handles agent identity, authentication, and session management.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .config import settings
from .logger import get_logger
from .shared_memory import get_shared_memory

logger = get_logger(__name__)


@dataclass
class AgentIdentity:
    """Agent identity information."""
    agent_id: str
    name: str
    version: str
    created_at: datetime
    last_active: datetime
    capabilities: List[str]
    status: str = "active"
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.last_active, str):
            self.last_active = datetime.fromisoformat(self.last_active)


@dataclass
class Session:
    """Agent session information."""
    session_id: str
    agent_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    context: Dict = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.expires_at, str):
            self.expires_at = datetime.fromisoformat(self.expires_at)


class IdentityManager:
    """Manages agent identity and sessions."""
    
    def __init__(self):
        self.shared_memory = get_shared_memory()
        self.current_identity: Optional[AgentIdentity] = None
        self.current_session: Optional[Session] = None
        self._load_or_create_identity()
    
    def _load_or_create_identity(self) -> None:
        """Load existing identity or create a new one."""
        identity_key = f"identity:{settings.agent_name}"
        identity_data = self.shared_memory.get(identity_key)
        
        if identity_data:
            self.current_identity = AgentIdentity(**identity_data)
            logger.info(f"Loaded existing identity: {self.current_identity.agent_id}")
        else:
            self.current_identity = self._create_identity()
            self.shared_memory.set(identity_key, asdict(self.current_identity), tags=["identity"])
            logger.info(f"Created new identity: {self.current_identity.agent_id}")
    
    def _create_identity(self) -> AgentIdentity:
        """Create a new agent identity."""
        return AgentIdentity(
            agent_id=str(uuid.uuid4()),
            name=settings.agent_name,
            version="0.1.0",
            created_at=datetime.now(),
            last_active=datetime.now(),
            capabilities=[
                "social_strategy",
                "parallel_arena",
                "memory_management",
                "adaptive_learning",
                "multi_agent_coordination"
            ],
            metadata={
                "mode": settings.agent_mode,
                "project_root": str(settings.project_root),
                "initialization_time": datetime.now().isoformat()
            }
        )
    
    def create_session(self, context: Optional[Dict] = None, 
                      expires_in_hours: int = 24) -> Session:
        """Create a new session for the agent."""
        if not self.current_identity:
            raise RuntimeError("No identity available")
        
        session_id = secrets.token_urlsafe(32)
        session = Session(
            session_id=session_id,
            agent_id=self.current_identity.agent_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=expires_in_hours),
            context=context or {}
        )
        
        # Store session in shared memory
        session_key = f"session:{session_id}"
        self.shared_memory.set(
            session_key, 
            asdict(session), 
            expires_in=expires_in_hours * 3600,
            tags=["session"]
        )
        
        self.current_session = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        session_key = f"session:{session_id}"
        session_data = self.shared_memory.get(session_key)
        
        if not session_data:
            return None
        
        session = Session(**session_data)
        
        # Check if session is expired
        if datetime.now() > session.expires_at:
            self.invalidate_session(session_id)
            return None
        
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        session_key = f"session:{session_id}"
        success = self.shared_memory.delete(session_key)
        
        if success:
            logger.info(f"Invalidated session: {session_id}")
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
        
        return success
    
    def update_identity(self, **kwargs) -> None:
        """Update agent identity information."""
        if not self.current_identity:
            raise RuntimeError("No identity available")
        
        for key, value in kwargs.items():
            if hasattr(self.current_identity, key):
                setattr(self.current_identity, key, value)
        
        self.current_identity.last_active = datetime.now()
        
        # Update in shared memory
        identity_key = f"identity:{settings.agent_name}"
        self.shared_memory.set(identity_key, asdict(self.current_identity), tags=["identity"])
        
        logger.info(f"Updated identity: {self.current_identity.agent_id}")
    
    def add_capability(self, capability: str) -> None:
        """Add a new capability to the agent."""
        if not self.current_identity:
            raise RuntimeError("No identity available")
        
        if capability not in self.current_identity.capabilities:
            self.current_identity.capabilities.append(capability)
            self.update_identity()
            logger.info(f"Added capability: {capability}")
    
    def remove_capability(self, capability: str) -> None:
        """Remove a capability from the agent."""
        if not self.current_identity:
            raise RuntimeError("No identity available")
        
        if capability in self.current_identity.capabilities:
            self.current_identity.capabilities.remove(capability)
            self.update_identity()
            logger.info(f"Removed capability: {capability}")
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions for this agent."""
        if not self.current_identity:
            return []
        
        session_keys = self.shared_memory.get_keys_by_pattern(r"session:.*")
        active_sessions = []
        
        for session_key in session_keys:
            session_data = self.shared_memory.get(session_key)
            if session_data and session_data.get("agent_id") == self.current_identity.agent_id:
                session = Session(**session_data)
                if session.is_active and datetime.now() <= session.expires_at:
                    active_sessions.append(session)
                else:
                    # Clean up expired sessions
                    self.invalidate_session(session.session_id)
        
        return active_sessions
    
    def generate_auth_token(self) -> str:
        """Generate an authentication token for the agent."""
        if not self.current_identity:
            raise RuntimeError("No identity available")
        
        # Create token with agent ID and timestamp
        token_data = f"{self.current_identity.agent_id}:{datetime.now().timestamp()}"
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Store token in shared memory with expiration
        token_key = f"token:{token_hash}"
        self.shared_memory.set(
            token_key,
            {
                "agent_id": self.current_identity.agent_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            },
            expires_in=3600,
            tags=["auth_token"]
        )
        
        return token_hash
    
    def validate_auth_token(self, token: str) -> bool:
        """Validate an authentication token."""
        token_key = f"token:{token}"
        token_data = self.shared_memory.get(token_key)
        
        if not token_data:
            return False
        
        # Check if token belongs to this agent
        if token_data.get("agent_id") != self.current_identity.agent_id:
            return False
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() > expires_at:
            self.shared_memory.delete(token_key)
            return False
        
        return True
    
    def get_identity_info(self) -> Dict:
        """Get current identity information as a dictionary."""
        if not self.current_identity:
            return {}
        
        return {
            "agent_id": self.current_identity.agent_id,
            "name": self.current_identity.name,
            "version": self.current_identity.version,
            "created_at": self.current_identity.created_at.isoformat(),
            "last_active": self.current_identity.last_active.isoformat(),
            "capabilities": self.current_identity.capabilities,
            "status": self.current_identity.status,
            "metadata": self.current_identity.metadata
        }
    
    def export_identity(self, file_path: Optional[Path] = None) -> None:
        """Export identity information to file."""
        if file_path is None:
            file_path = Path(settings.project_root) / "data" / "identity.json"
        
        if not self.current_identity:
            raise RuntimeError("No identity to export")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        identity_data = {
            "identity": asdict(self.current_identity),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(identity_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Identity exported to {file_path}")
    
    def get_stats(self) -> Dict:
        """Get identity and session statistics."""
        active_sessions = self.get_active_sessions()
        
        return {
            "agent_id": self.current_identity.agent_id if self.current_identity else None,
            "agent_name": self.current_identity.name if self.current_identity else None,
            "total_capabilities": len(self.current_identity.capabilities) if self.current_identity else 0,
            "active_sessions": len(active_sessions),
            "last_active": self.current_identity.last_active.isoformat() if self.current_identity else None,
            "identity_age_days": (datetime.now() - self.current_identity.created_at).days if self.current_identity else 0
        }


# Global identity manager instance
identity_manager = IdentityManager()


def get_identity_manager() -> IdentityManager:
    """Get the global identity manager instance."""
    return identity_manager
