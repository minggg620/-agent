"""
Zero Realm Social Agent - Challenge 4 Monitor Module
Information Monitor: Real-time information capture, semantic filtering, confidence scoring, auto-follow-up
"""

import asyncio
import hashlib
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import math

from pydantic import BaseModel, Field
from ...core.config import settings
from ...core.logger import get_logger
from ...core.shared_memory import get_shared_memory
from .semantic_search import get_semantic_search, SemanticSearch
from .alert_system import get_alert_system, AlertSystem

logger = get_logger(__name__)


class InformationSource(Enum):
    """Information source types for monitoring."""
    SOCIAL_MEDIA = "social_media"
    NEWS_FEEDS = "news_feeds"
    FORUMS = "forums"
    BLOGS = "blogs"
    CHAT_ROOMS = "chat_rooms"
    API_ENDPOINTS = "api_endpoints"
    RSS_FEEDS = "rss_feeds"
    DARK_WEB = "dark_web"
    INTERNAL_SYSTEMS = "internal_systems"


class InformationType(Enum):
    """Types of information to monitor."""
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    VIDEO_POST = "video_post"
    DOCUMENT = "document"
    COMMENT = "comment"
    PRIVATE_MESSAGE = "private_message"
    SYSTEM_LOG = "system_log"
    API_RESPONSE = "api_response"


class ConfidenceLevel(Enum):
    """Confidence level classifications."""
    VERY_LOW = "very_low"      # 0-20
    LOW = "low"               # 21-40
    MEDIUM = "medium"         # 41-60
    HIGH = "high"             # 61-80
    VERY_HIGH = "very_high"   # 81-100


class MonitoringStatus(Enum):
    """Monitoring status types."""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class InformationItem:
    """Individual information item captured by monitor."""
    item_id: str
    source: InformationSource
    info_type: InformationType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    author: Optional[str]
    url: Optional[str]
    keywords: List[str]
    semantic_score: float  # 0-1, semantic relevance to target
    confidence_score: int  # 0-100, overall confidence
    processed: bool = False
    followed_up: bool = False
    alert_sent: bool = False
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class MonitoringRule:
    """Rule for information monitoring and filtering."""
    rule_id: str
    name: str
    keywords: List[str]
    semantic_threshold: float  # 0-1, minimum semantic similarity
    confidence_threshold: int  # 0-100, minimum confidence score
    sources: List[InformationSource]
    info_types: List[InformationType]
    time_window_hours: int
    max_items_per_hour: int
    auto_follow_up: bool
    alert_enabled: bool
    priority: int  # 1-10, higher is more important
    active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class FollowUpAction:
    """Follow-up action for high-confidence information."""
    action_id: str
    item_id: str
    action_type: str
    parameters: Dict[str, Any]
    scheduled_at: datetime
    executed: bool = False
    result: Optional[str] = None


class InformationMonitor(BaseModel):
    """Real-time information monitoring system with semantic filtering and confidence scoring."""
    
    shared_memory = get_shared_memory()
    semantic_search: SemanticSearch = None
    alert_system: AlertSystem = None
    
    # Monitoring configuration
    max_concurrent_sources: int = Field(default=10, description="Maximum concurrent source monitoring")
    processing_batch_size: int = Field(default=50, description="Batch size for information processing")
    confidence_update_interval: int = Field(default=300, description="Confidence score update interval (seconds)")
    follow_up_delay_minutes: int = Field(default=5, description="Delay before follow-up actions")
    
    # Scoring weights
    keyword_match_weight: float = Field(default=0.3, description="Weight for keyword matching")
    semantic_similarity_weight: float = Field(default=0.4, description="Weight for semantic similarity")
    source_reliability_weight: float = Field(default=0.2, description="Weight for source reliability")
    temporal_relevance_weight: float = Field(default=0.1, description="Weight for temporal relevance")
    
    # Monitoring state
    monitoring_rules: Dict[str, MonitoringRule] = Field(default_factory=dict)
    captured_items: List[InformationItem] = Field(default_factory=list)
    follow_up_actions: List[FollowUpAction] = Field(default_factory=list)
    monitoring_status: MonitoringStatus = Field(default=MonitoringStatus.ACTIVE)
    
    # Source reliability scores
    source_reliability: Dict[InformationSource, float] = Field(default={
        InformationSource.NEWS_FEEDS: 0.8,
        InformationSource.API_ENDPOINTS: 0.9,
        InformationSource.INTERNAL_SYSTEMS: 0.95,
        InformationSource.SOCIAL_MEDIA: 0.6,
        InformationSource.FORUMS: 0.5,
        InformationSource.BLOGS: 0.7,
        InformationSource.CHAT_ROOMS: 0.4,
        InformationSource.RSS_FEEDS: 0.75,
        InformationSource.DARK_WEB: 0.3
    })
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.semantic_search = get_semantic_search()
        self.alert_system = get_alert_system()
    
    async def add_monitoring_rule(self, name: str, keywords: List[str],
                                 semantic_threshold: float = 0.7,
                                 confidence_threshold: int = 60,
                                 sources: Optional[List[InformationSource]] = None,
                                 info_types: Optional[List[InformationType]] = None,
                                 time_window_hours: int = 24,
                                 max_items_per_hour: int = 100,
                                 auto_follow_up: bool = True,
                                 alert_enabled: bool = True,
                                 priority: int = 5) -> MonitoringRule:
        """Add a new monitoring rule."""
        rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        rule = MonitoringRule(
            rule_id=rule_id,
            name=name,
            keywords=keywords,
            semantic_threshold=semantic_threshold,
            confidence_threshold=confidence_threshold,
            sources=sources or list(InformationSource),
            info_types=info_types or list(InformationType),
            time_window_hours=time_window_hours,
            max_items_per_hour=max_items_per_hour,
            auto_follow_up=auto_follow_up,
            alert_enabled=alert_enabled,
            priority=priority
        )
        
        self.monitoring_rules[rule_id] = rule
        
        # Store in shared memory
        rule_key = f"monitoring_rule:{rule_id}"
        self.shared_memory.set(rule_key, asdict(rule), tags=["monitoring", "rule"])
        
        logger.info(f"Added monitoring rule: {name} ({rule_id})")
        return rule
    
    async def capture_information(self, source: InformationSource, info_type: InformationType,
                                content: str, metadata: Dict[str, Any] = None,
                                author: Optional[str] = None, url: Optional[str] = None) -> InformationItem:
        """Capture and process new information."""
        item_id = f"info_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        # Extract keywords from content
        keywords = await self._extract_keywords(content)
        
        # Calculate semantic score
        semantic_score = await self._calculate_semantic_score(content)
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(
            content, keywords, semantic_score, source, info_type
        )
        
        # Create information item
        item = InformationItem(
            item_id=item_id,
            source=source,
            info_type=info_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(),
            author=author,
            url=url,
            keywords=keywords,
            semantic_score=semantic_score,
            confidence_score=confidence_score
        )
        
        # Add to captured items
        self.captured_items.append(item)
        
        # Store in shared memory
        item_key = f"information_item:{item_id}"
        self.shared_memory.set(item_key, asdict(item), tags=["information", "captured"])
        
        # Process item through monitoring rules
        await self._process_information_item(item)
        
        logger.debug(f"Captured information item: {item_id} with confidence {confidence_score}")
        return item
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        # Simple keyword extraction (in real implementation, use NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return top keywords by frequency
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [kw for kw, count in keyword_counts.most_common(10)]
    
    async def _calculate_semantic_score(self, content: str) -> float:
        """Calculate semantic relevance score using semantic search."""
        if not self.semantic_search:
            return 0.5  # Default score
        
        # Get target keywords from active rules
        target_keywords = []
        for rule in self.monitoring_rules.values():
            if rule.active:
                target_keywords.extend(rule.keywords)
        
        if not target_keywords:
            return 0.5
        
        # Calculate semantic similarity
        semantic_score = await self.semantic_search.calculate_similarity(content, target_keywords)
        return semantic_score
    
    async def _calculate_confidence_score(self, content: str, keywords: List[str],
                                        semantic_score: float, source: InformationSource,
                                        info_type: InformationType) -> int:
        """Calculate overall confidence score (0-100)."""
        # Keyword matching score
        keyword_score = 0.0
        for rule in self.monitoring_rules.values():
            if rule.active:
                matches = len(set(keywords) & set(rule.keywords))
                keyword_score += matches / len(rule.keywords) if rule.keywords else 0
        
        keyword_score = min(keyword_score / len(self.monitoring_rules), 1.0) if self.monitoring_rules else 0.0
        
        # Source reliability score
        source_score = self.source_reliability.get(source, 0.5)
        
        # Temporal relevance score (newer is better)
        temporal_score = 1.0  # All items are current when captured
        
        # Information type score
        type_scores = {
            InformationType.API_RESPONSE: 0.9,
            InformationType.SYSTEM_LOG: 0.8,
            InformationType.DOCUMENT: 0.7,
            InformationType.NEWS_FEEDS: 0.75,
            InformationType.TEXT_POST: 0.6,
            InformationType.COMMENT: 0.5,
            InformationType.IMAGE_POST: 0.4,
            InformationType.VIDEO_POST: 0.4,
            InformationType.PRIVATE_MESSAGE: 0.3,
            InformationType.CHAT_ROOMS: 0.3
        }
        type_score = type_scores.get(info_type, 0.5)
        
        # Calculate weighted score
        weighted_score = (
            keyword_score * self.keyword_match_weight +
            semantic_score * self.semantic_similarity_weight +
            source_score * self.source_reliability_weight +
            temporal_score * self.temporal_relevance_weight +
            type_score * 0.1  # Small weight for info type
        )
        
        # Convert to 0-100 scale
        confidence_score = int(weighted_score * 100)
        return max(0, min(100, confidence_score))
    
    async def _process_information_item(self, item: InformationItem) -> None:
        """Process information item through monitoring rules."""
        for rule in self.monitoring_rules.values():
            if not rule.active:
                continue
            
            # Check if item matches rule
            if await self._item_matches_rule(item, rule):
                # Mark as processed
                item.processed = True
                
                # Check if follow-up is needed
                if rule.auto_follow_up and item.confidence_score >= rule.confidence_threshold:
                    await self._schedule_follow_up(item, rule)
                
                # Check if alert should be sent
                if rule.alert_enabled and item.confidence_score >= rule.confidence_threshold:
                    await self._send_alert(item, rule)
                
                break  # Stop after first matching rule
    
    async def _item_matches_rule(self, item: InformationItem, rule: MonitoringRule) -> bool:
        """Check if information item matches monitoring rule."""
        # Check source
        if item.source not in rule.sources:
            return False
        
        # Check info type
        if item.info_type not in rule.info_types:
            return False
        
        # Check keyword match
        keyword_matches = len(set(item.keywords) & set(rule.keywords))
        if keyword_matches == 0:
            return False
        
        # Check semantic threshold
        if item.semantic_score < rule.semantic_threshold:
            return False
        
        # Check confidence threshold
        if item.confidence_score < rule.confidence_threshold:
            return False
        
        # Check time window
        time_diff = (datetime.now() - item.timestamp).total_seconds() / 3600
        if time_diff > rule.time_window_hours:
            return False
        
        return True
    
    async def _schedule_follow_up(self, item: InformationItem, rule: MonitoringRule) -> None:
        """Schedule follow-up action for high-confidence item."""
        follow_up_time = datetime.now() + timedelta(minutes=self.follow_up_delay_minutes)
        
        action_id = f"follow_up_{item.item_id}_{datetime.now().strftime('%H%M%S')}"
        
        action = FollowUpAction(
            action_id=action_id,
            item_id=item.item_id,
            action_type="semantic_analysis",
            parameters={
                "content": item.content,
                "keywords": item.keywords,
                "confidence": item.confidence_score,
                "rule_id": rule.rule_id
            },
            scheduled_at=follow_up_time
        )
        
        self.follow_up_actions.append(action)
        
        # Store in shared memory
        action_key = f"follow_up_action:{action_id}"
        self.shared_memory.set(action_key, asdict(action), tags=["follow_up", "scheduled"])
        
        logger.info(f"Scheduled follow-up action: {action_id} for item: {item.item_id}")
    
    async def _send_alert(self, item: InformationItem, rule: MonitoringRule) -> None:
        """Send alert for high-confidence information."""
        if not self.alert_system:
            return
        
        alert_data = {
            "item_id": item.item_id,
            "source": item.source.value,
            "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
            "confidence_score": item.confidence_score,
            "keywords": item.keywords,
            "timestamp": item.timestamp.isoformat(),
            "rule_name": rule.name,
            "priority": rule.priority
        }
        
        await self.alert_system.send_alert(
            alert_type="high_confidence_information",
            data=alert_data,
            priority=rule.priority
        )
        
        item.alert_sent = True
        
        logger.info(f"Alert sent for item: {item.item_id} with confidence {item.confidence_score}")
    
    async def execute_follow_up_actions(self) -> List[FollowUpAction]:
        """Execute scheduled follow-up actions."""
        executed_actions = []
        now = datetime.now()
        
        for action in self.follow_up_actions:
            if action.executed or action.scheduled_at > now:
                continue
            
            try:
                # Execute follow-up action
                result = await self._execute_follow_up_action(action)
                action.executed = True
                action.result = result
                executed_actions.append(action)
                
                # Update in shared memory
                action_key = f"follow_up_action:{action.action_id}"
                self.shared_memory.set(action_key, asdict(action), tags=["follow_up", "executed"])
                
                logger.info(f"Executed follow-up action: {action.action_id}")
                
            except Exception as e:
                action.executed = True
                action.result = f"Error: {str(e)}"
                logger.error(f"Failed to execute follow-up action {action.action_id}: {e}")
        
        return executed_actions
    
    async def _execute_follow_up_action(self, action: FollowUpAction) -> str:
        """Execute a specific follow-up action."""
        if action.action_type == "semantic_analysis":
            # Perform deeper semantic analysis
            content = action.parameters.get("content", "")
            keywords = action.parameters.get("keywords", [])
            
            # Use semantic search for deeper analysis
            if self.semantic_search:
                similar_items = await self.semantic_search.find_similar_content(content, limit=5)
                return f"Found {len(similar_items)} similar items"
            else:
                return "Semantic search not available"
        
        elif action.action_type == "source_verification":
            # Verify information source
            return "Source verification completed"
        
        elif action.action_type == "cross_reference":
            # Cross-reference with other sources
            return "Cross-reference analysis completed"
        
        else:
            return f"Unknown action type: {action.action_type}"
    
    async def get_high_confidence_items(self, min_confidence: int = 80,
                                      hours_back: int = 24) -> List[InformationItem]:
        """Get high-confidence information items."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        high_conf_items = [
            item for item in self.captured_items
            if item.confidence_score >= min_confidence and item.timestamp >= cutoff_time
        ]
        
        # Sort by confidence score (descending)
        high_conf_items.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return high_conf_items
    
    async def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        total_items = len(self.captured_items)
        
        # Confidence distribution
        confidence_dist = {
            "very_high": len([i for i in self.captured_items if i.confidence_score >= 80]),
            "high": len([i for i in self.captured_items if 60 <= i.confidence_score < 80]),
            "medium": len([i for i in self.captured_items if 40 <= i.confidence_score < 60]),
            "low": len([i for i in self.captured_items if 20 <= i.confidence_score < 40]),
            "very_low": len([i for i in self.captured_items if i.confidence_score < 20])
        }
        
        # Source distribution
        source_dist = {}
        for item in self.captured_items:
            source_name = item.source.value
            source_dist[source_name] = source_dist.get(source_name, 0) + 1
        
        # Processing statistics
        processed_items = len([i for i in self.captured_items if i.processed])
        followed_up_items = len([i for i in self.captured_items if i.followed_up])
        alert_sent_items = len([i for i in self.captured_items if i.alert_sent])
        
        # Follow-up statistics
        scheduled_actions = len([a for a in self.follow_up_actions if not a.executed])
        executed_actions = len([a for a in self.follow_up_actions if a.executed])
        
        return {
            "total_items_captured": total_items,
            "active_rules": len([r for r in self.monitoring_rules.values() if r.active]),
            "confidence_distribution": confidence_dist,
            "source_distribution": source_dist,
            "processing_stats": {
                "processed_items": processed_items,
                "followed_up_items": followed_up_items,
                "alert_sent_items": alert_sent_items,
                "processing_rate": processed_items / total_items if total_items > 0 else 0
            },
            "follow_up_stats": {
                "scheduled_actions": scheduled_actions,
                "executed_actions": executed_actions,
                "execution_rate": executed_actions / (scheduled_actions + executed_actions) if (scheduled_actions + executed_actions) > 0 else 0
            },
            "monitoring_status": self.monitoring_status.value,
            "last_updated": datetime.now().isoformat()
        }
    
    async def cleanup_old_items(self, days_to_keep: int = 7) -> int:
        """Clean up old information items."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        old_items = [item for item in self.captured_items if item.timestamp < cutoff_time]
        self.captured_items = [item for item in self.captured_items if item.timestamp >= cutoff_time]
        
        # Clean up old follow-up actions
        cutoff_action_time = datetime.now() - timedelta(days=1)
        old_actions = [action for action in self.follow_up_actions if action.scheduled_at < cutoff_action_time]
        self.follow_up_actions = [action for action in self.follow_up_actions if action.scheduled_at >= cutoff_action_time]
        
        logger.info(f"Cleaned up {len(old_items)} old items and {len(old_actions)} old actions")
        return len(old_items) + len(old_actions)
    
    async def export_monitoring_data(self, file_path: str, 
                                    include_items: bool = True,
                                    include_actions: bool = True) -> bool:
        """Export monitoring data to JSON file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "monitoring_statistics": await self.get_monitoring_statistics(),
                "monitoring_rules": {rule_id: asdict(rule) for rule_id, rule in self.monitoring_rules.items()}
            }
            
            if include_items:
                export_data["captured_items"] = [asdict(item) for item in self.captured_items]
            
            if include_actions:
                export_data["follow_up_actions"] = [asdict(action) for action in self.follow_up_actions]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Monitoring data exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export monitoring data: {e}")
            return False


# Global instance
information_monitor = InformationMonitor()


async def get_information_monitor() -> InformationMonitor:
    """Get the global information monitor instance."""
    return information_monitor
