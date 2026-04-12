"""
Shared memory management for Cascade Agent.
Handles persistent storage and retrieval of agent state, strategies, and data.
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryEntry:
    """Individual memory entry with metadata."""
    key: str
    value: Any
    timestamp: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None
    priority: int = 0  # Higher priority = less likely to be evicted
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.expires_at, str):
            self.expires_at = datetime.fromisoformat(self.expires_at)


class SharedMemory(BaseModel):
    """Shared memory system for agent state management."""
    
    storage: Dict[str, MemoryEntry] = Field(default_factory=dict)
    max_size: int = Field(default=settings.shared_memory_size)
    retention_days: int = Field(default=settings.memory_retention_days)
    
    class Config:
        arbitrary_types_allowed = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from shared memory."""
        if key not in self.storage:
            return default
        
        entry = self.storage[key]
        
        # Check if entry has expired
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.storage[key]
            logger.debug(f"Expired entry removed: {key}")
            return default
        
        return entry.value
    
    def set(self, key: str, value: Any, expires_in: Optional[int] = None, 
            tags: Optional[List[str]] = None, priority: int = 0) -> None:
        """Store a value in shared memory."""
        # Check memory limit and evict if necessary
        if len(self.storage) >= self.max_size and key not in self.storage:
            self._evict_low_priority()
        
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        entry = MemoryEntry(
            key=key,
            value=value,
            timestamp=datetime.now(),
            expires_at=expires_at,
            tags=tags or [],
            priority=priority
        )
        
        self.storage[key] = entry
        logger.debug(f"Stored entry: {key} with tags: {tags}")
    
    def delete(self, key: str) -> bool:
        """Remove a value from shared memory."""
        if key in self.storage:
            del self.storage[key]
            logger.debug(f"Deleted entry: {key}")
            return True
        return False
    
    def clear_expired(self) -> int:
        """Remove all expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.storage.items()
            if entry.expires_at and now > entry.expires_at
        ]
        
        for key in expired_keys:
            del self.storage[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def clear_old(self) -> int:
        """Remove entries older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        old_keys = [
            key for key, entry in self.storage.items()
            if entry.timestamp < cutoff_date
        ]
        
        for key in old_keys:
            del self.storage[key]
        
        if old_keys:
            logger.info(f"Cleared {len(old_keys)} old entries")
        
        return len(old_keys)
    
    def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get all entries with a specific tag."""
        return {
            key: entry.value
            for key, entry in self.storage.items()
            if tag in entry.tags
        }
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching a pattern."""
        import re
        regex = re.compile(pattern)
        return [key for key in self.storage.keys() if regex.match(key)]
    
    def _evict_low_priority(self) -> None:
        """Evict entries with lowest priority to make space."""
        if not self.storage:
            return
        
        # Sort by priority (ascending) and timestamp (ascending)
        sorted_entries = sorted(
            self.storage.items(),
            key=lambda x: (x[1].priority, x[1].timestamp)
        )
        
        # Remove the lowest priority entry
        key_to_remove = sorted_entries[0][0]
        del self.storage[key_to_remove]
        logger.debug(f"Evicted low priority entry: {key_to_remove}")
    
    def save_to_file(self, file_path: Optional[Path] = None) -> None:
        """Save shared memory to file."""
        if file_path is None:
            file_path = Path(settings.project_root) / "data" / "shared_memory.json"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        serializable_data = {}
        for key, entry in self.storage.items():
            serializable_data[key] = {
                "key": entry.key,
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
                "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                "tags": entry.tags,
                "priority": entry.priority
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Shared memory saved to {file_path}")
    
    def load_from_file(self, file_path: Optional[Path] = None) -> None:
        """Load shared memory from file."""
        if file_path is None:
            file_path = Path(settings.project_root) / "data" / "shared_memory.json"
        
        if not file_path.exists():
            logger.debug(f"Shared memory file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                serializable_data = json.load(f)
            
            # Convert back to MemoryEntry objects
            for key, data in serializable_data.items():
                entry = MemoryEntry(
                    key=data["key"],
                    value=data["value"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
                    tags=data["tags"],
                    priority=data["priority"]
                )
                self.storage[key] = entry
            
            logger.info(f"Shared memory loaded from {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to load shared memory from {file_path}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_entries = len(self.storage)
        expired_count = sum(
            1 for entry in self.storage.values()
            if entry.expires_at and datetime.now() > entry.expires_at
        )
        
        tag_counts = {}
        for entry in self.storage.values():
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "max_size": self.max_size,
            "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
            "tag_distribution": tag_counts
        }


# Global shared memory instance
shared_memory = SharedMemory()


def get_shared_memory() -> SharedMemory:
    """Get the global shared memory instance."""
    return shared_memory


# Auto-save and cleanup tasks
async def cleanup_task():
    """Periodic cleanup of expired and old entries."""
    while True:
        try:
            expired_count = shared_memory.clear_expired()
            old_count = shared_memory.clear_old()
            
            if expired_count > 0 or old_count > 0:
                logger.info(f"Cleanup completed: {expired_count} expired, {old_count} old entries removed")
            
            # Save to file after cleanup
            shared_memory.save_to_file()
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
        
        # Run cleanup every hour
        await asyncio.sleep(3600)
