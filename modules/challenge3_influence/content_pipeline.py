"""
Zero Realm Social Agent - Challenge 3 Influence Module
Content Pipeline: Hot topic identification, topic generation, publish time optimization, A/B testing
"""

import asyncio
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, ClassVar
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import math

from pydantic import BaseModel, Field
from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class ContentType(Enum):
    """Content types for influence pipeline."""
    INTELLIGENCE_INTEGRATION = "intelligence_integration"
    OPINION_DEBATE = "opinion_debate"
    INTERACTIVE_GUIDANCE = "interactive_guidance"
    EVENT_TRACKING = "event_tracking"
    TASK_COLLABORATION = "task_collaboration"


class ContentStatus(Enum):
    """Content status in pipeline."""
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class HotTopicLevel(Enum):
    """Hot topic classification levels."""
    TRENDING = "trending"
    VIRAL = "viral"
    BREAKING = "breaking"
    EMERGING = "emerging"
    SUSTAINED = "sustained"
    DECLINING = "declining"


class EngagementType(Enum):
    """Types of user engagement."""
    VIEWS = "views"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    BOOKMARKS = "bookmarks"
    MENTIONS = "mentions"
    CLICKS = "clicks"


@dataclass
class HotTopic:
    """Hot topic data structure."""
    topic_id: str
    title: str
    description: str
    keywords: List[str]
    level: HotTopicLevel
    heat_score: float  # 0-1, higher is hotter
    trend_direction: str  # "rising", "stable", "falling"
    source_channels: List[str]
    engagement_metrics: Dict[EngagementType, int]
    discovery_time: datetime
    last_updated: datetime
    relevance_score: float  # 0-1, relevance to our goals
    content_potential: float  # 0-1, potential for content creation


@dataclass
class ContentItem:
    """Content item in the pipeline."""
    content_id: str
    topic_id: str
    content_type: ContentType
    title: str
    body: str
    status: ContentStatus
    created_at: datetime
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    target_audience: List[str]
    engagement_prediction: float  # 0-1, predicted engagement
    actual_engagement: Dict[EngagementType, int]
    ab_test_group: Optional[str] = None
    optimization_score: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class PublishTimeSlot:
    """Optimal publish time slot."""
    slot_id: str
    day_of_week: int  # 0-6, Monday=0
    hour: int  # 0-23
    minute: int  # 0-59
    expected_reach: float
    expected_engagement: float
    competition_level: float  # 0-1, how crowded the slot is
    historical_performance: float  # 0-1, historical performance score
    confidence: float  # 0-1, confidence in prediction


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    total_topics_processed: int
    total_content_generated: int
    total_content_published: int
    average_engagement_rate: float
    average_time_to_publish: float  # hours
    ab_test_success_rate: float
    hot_topic_accuracy: float
    pipeline_efficiency: float


class ContentPipeline(BaseModel):
    """Complete content pipeline for influence operations."""
    
    shared_memory: ClassVar = get_shared_memory()
    
    # Pipeline configuration
    max_topics_per_batch: int = Field(default=10, description="Maximum topics to process per batch")
    content_generation_timeout: int = Field(default=300, description="Content generation timeout in seconds")
    publish_ahead_hours: int = Field(default=24, description="Hours ahead to schedule content")
    min_engagement_threshold: float = Field(default=0.05, description="Minimum engagement rate to consider success")
    
    # Hot topic detection thresholds
    hot_topic_min_engagement: int = Field(default=1000, description="Minimum engagement for hot topic")
    trend_detection_window_hours: int = Field(default=6, description="Window for trend detection")
    
    # A/B testing configuration
    ab_test_sample_size: int = Field(default=100, description="Sample size for A/B testing")
    ab_test_confidence_threshold: float = Field(default=0.95, description="Confidence threshold for A/B test results")
    
    # Pipeline state
    hot_topics: Dict[str, HotTopic] = Field(default_factory=dict)
    content_queue: List[ContentItem] = Field(default_factory=list)
    published_content: List[ContentItem] = Field(default_factory=list)
    time_slots: List[PublishTimeSlot] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_time_slots()
    
    def _initialize_time_slots(self) -> None:
        """Initialize optimal publish time slots."""
        # Generate time slots for the next week
        for day in range(7):
            for hour in [8, 12, 18, 20]:  # Prime engagement hours
                slot_id = f"slot_{day}_{hour}"
                
                # Calculate expected metrics based on historical data
                expected_reach = self._calculate_expected_reach(day, hour)
                expected_engagement = self._calculate_expected_engagement(day, hour)
                competition_level = self._calculate_competition_level(day, hour)
                historical_performance = self._get_historical_performance(day, hour)
                confidence = min(0.8, (expected_reach + expected_engagement) / 2)
                
                time_slot = PublishTimeSlot(
                    slot_id=slot_id,
                    day_of_week=day,
                    hour=hour,
                    minute=0,
                    expected_reach=expected_reach,
                    expected_engagement=expected_engagement,
                    competition_level=competition_level,
                    historical_performance=historical_performance,
                    confidence=confidence
                )
                
                self.time_slots.append(time_slot)
        
        logger.info(f"Initialized {len(self.time_slots)} publish time slots")
    
    async def process_hot_topics(self) -> List[HotTopic]:
        """Process and identify hot topics from various sources."""
        logger.info("Processing hot topics...")
        
        # Simulate hot topic detection from various sources
        detected_topics = await self._detect_hot_topics()
        
        # Filter and rank topics
        filtered_topics = await self._filter_and_rank_topics(detected_topics)
        
        # Update hot topics storage
        for topic in filtered_topics:
            self.hot_topics[topic.topic_id] = topic
        
        # Store in shared memory
        topics_key = "hot_topics"
        topics_data = {tid: asdict(topic) for tid, topic in self.hot_topics.items()}
        self.shared_memory.set(topics_key, topics_data, tags=["content", "topics"])
        
        logger.info(f"Processed {len(filtered_topics)} hot topics")
        return filtered_topics
    
    async def _detect_hot_topics(self) -> List[HotTopic]:
        """Detect hot topics from various sources."""
        # Simulate detection from multiple sources
        sources = [
            "social_media_trends",
            "news_feeds", 
            "forum_discussions",
            "search_trends",
            "internal_analytics"
        ]
        
        detected_topics = []
        
        for source in sources:
            source_topics = await self._extract_topics_from_source(source)
            detected_topics.extend(source_topics)
        
        return detected_topics
    
    async def _extract_topics_from_source(self, source: str) -> List[HotTopic]:
        """Extract topics from a specific source."""
        # Simulate topic extraction
        topics = []
        
        # Generate sample topics based on source
        if source == "social_media_trends":
            sample_topics = [
                {
                    "title": "AI Ethics Debate Intensifies",
                    "keywords": ["AI", "ethics", "debate", "regulation"],
                    "engagement": 5000,
                    "trend": "rising"
                },
                {
                    "title": "New Cybersecurity Threats Discovered",
                    "keywords": ["cybersecurity", "threats", "vulnerability"],
                    "engagement": 3500,
                    "trend": "rising"
                }
            ]
        elif source == "news_feeds":
            sample_topics = [
                {
                    "title": "Tech Giants Face New Regulations",
                    "keywords": ["tech", "regulation", "antitrust"],
                    "engagement": 8000,
                    "trend": "stable"
                }
            ]
        else:
            sample_topics = []
        
        for i, topic_data in enumerate(sample_topics):
            topic_id = f"{source}_{i}_{datetime.now().strftime('%Y%m%d')}"
            
            # Calculate heat score based on engagement and trend
            base_heat = min(1.0, topic_data["engagement"] / 10000)
            trend_multiplier = 1.2 if topic_data["trend"] == "rising" else 1.0
            heat_score = min(1.0, base_heat * trend_multiplier)
            
            # Determine level based on heat score
            if heat_score >= 0.8:
                level = HotTopicLevel.VIRAL
            elif heat_score >= 0.6:
                level = HotTopicLevel.TRENDING
            elif heat_score >= 0.4:
                level = HotTopicLevel.EMERGING
            else:
                level = HotTopicLevel.SUSTAINED
            
            topic = HotTopic(
                topic_id=topic_id,
                title=topic_data["title"],
                description=f"Discussion about {topic_data['title']} in {source}",
                keywords=topic_data["keywords"],
                level=level,
                heat_score=heat_score,
                trend_direction=topic_data["trend"],
                source_channels=[source],
                engagement_metrics={
                    EngagementType.VIEWS: topic_data["engagement"],
                    EngagementType.LIKES: int(topic_data["engagement"] * 0.1),
                    EngagementType.COMMENTS: int(topic_data["engagement"] * 0.05),
                    EngagementType.SHARES: int(topic_data["engagement"] * 0.02)
                },
                discovery_time=datetime.now(),
                last_updated=datetime.now(),
                relevance_score=random.uniform(0.3, 0.9),
                content_potential=random.uniform(0.4, 0.8)
            )
            
            topics.append(topic)
        
        return topics
    
    async def _filter_and_rank_topics(self, topics: List[HotTopic]) -> List[HotTopic]:
        """Filter and rank topics by relevance and potential."""
        # Filter by minimum heat score
        filtered = [t for t in topics if t.heat_score >= 0.3]
        
        # Sort by combined score (heat + relevance + potential)
        def combined_score(topic):
            return (topic.heat_score * 0.4 + 
                   topic.relevance_score * 0.3 + 
                   topic.content_potential * 0.3)
        
        filtered.sort(key=combined_score, reverse=True)
        
        # Return top topics
        return filtered[:self.max_topics_per_batch]
    
    async def generate_content_for_topics(self, topics: List[HotTopic]) -> List[ContentItem]:
        """Generate content items for hot topics."""
        logger.info(f"Generating content for {len(topics)} topics...")
        
        generated_content = []
        
        for topic in topics:
            # Generate multiple content types for each topic
            content_types = [
                ContentType.INTELLIGENCE_INTEGRATION,
                ContentType.OPINION_DEBATE,
                ContentType.INTERACTIVE_GUIDANCE,
                ContentType.EVENT_TRACKING,
                ContentType.TASK_COLLABORATION
            ]
            
            for content_type in content_types[:2]:  # Generate 2 content types per topic
                content_item = await self._generate_single_content(topic, content_type)
                if content_item:
                    generated_content.append(content_item)
        
        # Add to queue
        self.content_queue.extend(generated_content)
        
        # Store in shared memory
        queue_key = "content_queue"
        queue_data = [asdict(item) for item in self.content_queue]
        self.shared_memory.set(queue_key, queue_data, tags=["content", "queue"])
        
        logger.info(f"Generated {len(generated_content)} content items")
        return generated_content
    
    async def _generate_single_content(self, topic: HotTopic, 
                                     content_type: ContentType) -> Optional[ContentItem]:
        """Generate a single content item."""
        try:
            content_id = f"content_{topic.topic_id}_{content_type.value}_{datetime.now().strftime('%H%M%S')}"
            
            # Generate title and body based on content type
            title, body = await self._create_content_for_type(topic, content_type)
            
            # Predict engagement
            engagement_prediction = await self._predict_engagement(topic, content_type, title, body)
            
            content_item = ContentItem(
                content_id=content_id,
                topic_id=topic.topic_id,
                content_type=content_type,
                title=title,
                body=body,
                status=ContentStatus.READY,
                created_at=datetime.now(),
                scheduled_at=None,
                published_at=None,
                target_audience=self._determine_target_audience(topic, content_type),
                engagement_prediction=engagement_prediction,
                actual_engagement={},
                optimization_score=random.uniform(0.6, 0.9),
                metadata={
                    "topic_heat": topic.heat_score,
                    "generation_time": datetime.now().isoformat()
                }
            )
            
            return content_item
            
        except Exception as e:
            logger.error(f"Failed to generate content for topic {topic.topic_id}: {e}")
            return None
    
    async def _create_content_for_type(self, topic: HotTopic, 
                                     content_type: ContentType) -> Tuple[str, str]:
        """Create title and body for specific content type."""
        if content_type == ContentType.INTELLIGENCE_INTEGRATION:
            title = f"Analysis: {topic.title} - Key Insights and Implications"
            body = f"""
            Breaking down the latest developments in {topic.title}:
            
            Key Points:
            - Recent events have significant implications
            - Multiple perspectives are emerging
            - Expert analysis suggests important trends
            
            Our intelligence integration reveals:
            1. Strategic implications for stakeholders
            2. Potential impact on future developments
            3. Recommended monitoring points
            
            Keywords: {', '.join(topic.keywords)}
            """
        elif content_type == ContentType.OPINION_DEBATE:
            title = f"Debate: {topic.title} - Multiple Perspectives Analysis"
            body = f"""
            The discussion around {topic.title} has intensified. Here's our analysis:
            
            Perspective A: Traditional approach
            - Emphasizes established methodologies
            - Cites historical precedents
            
            Perspective B: Innovative approach  
            - Proposes new frameworks
            - Challenges conventional wisdom
            
            Our take: Both perspectives have merit, but context matters.
            
            What's your view on this developing situation?
            """
        elif content_type == ContentType.INTERACTIVE_GUIDANCE:
            title = f"Guide: Navigating {topic.title} - Practical Steps"
            body = f"""
            With the recent developments in {topic.title}, here's how to navigate:
            
            Step 1: Assess your current position
            Step 2: Identify key decision points
            Step 3: Evaluate options and risks
            Step 4: Implement monitoring strategy
            Step 5: Prepare for contingencies
            
            Interactive elements:
            - Share your experience in comments
            - Vote on most critical factors
            - Join our discussion group
            
            Keywords: {', '.join(topic.keywords)}
            """
        elif content_type == ContentType.EVENT_TRACKING:
            title = f"Live: {topic.title} - Real-time Updates"
            body = f"""
            Tracking ongoing developments in {topic.title}:
            
            Timeline of Key Events:
            [Latest updates will appear here]
            
            Current Status: Actively monitoring
            Next Update: Within 2 hours
            
            Stay tuned for real-time updates and analysis.
            
            Follow for instant notifications on major developments.
            """
        else:  # TASK_COLLABORATION
            title = f"Collaboration: {topic.title} - Community Action Plan"
            body = f"""
            Addressing {topic.title} requires collective action:
            
            Immediate Actions Needed:
            1. Information gathering and verification
            2. Resource coordination
            3. Strategy development
            
            How you can help:
            - Share relevant information
            - Volunteer expertise
            - Support community initiatives
            
            Collaboration channels opening soon.
            
            Keywords: {', '.join(topic.keywords)}
            """
        
        return title, body
    
    async def _predict_engagement(self, topic: HotTopic, content_type: ContentType,
                                title: str, body: str) -> float:
        """Predict engagement rate for content."""
        # Base prediction from topic heat
        base_prediction = topic.heat_score * 0.7
        
        # Adjust for content type
        type_multipliers = {
            ContentType.INTELLIGENCE_INTEGRATION: 1.1,
            ContentType.OPINION_DEBATE: 1.3,
            ContentType.INTERACTIVE_GUIDANCE: 1.2,
            ContentType.EVENT_TRACKING: 1.4,
            ContentType.TASK_COLLABORATION: 0.9
        }
        
        type_multiplier = type_multipliers.get(content_type, 1.0)
        
        # Adjust for content characteristics
        title_factor = min(1.2, len(title.split()) / 10)  # Longer titles tend to perform better
        body_factor = min(1.1, len(body.split()) / 200)  # Moderate length is optimal
        
        # Calculate final prediction
        final_prediction = base_prediction * type_multiplier * title_factor * body_factor
        return min(1.0, final_prediction)
    
    def _determine_target_audience(self, topic: HotTopic, 
                                 content_type: ContentType) -> List[str]:
        """Determine target audience for content."""
        base_audience = ["general_public"]
        
        # Add specific audiences based on topic keywords
        if "tech" in topic.keywords or "AI" in topic.keywords:
            base_audience.extend(["tech_enthusiasts", "developers", "researchers"])
        
        if "security" in topic.keywords:
            base_audience.extend(["security_professionals", "it_administrators"])
        
        # Adjust based on content type
        if content_type == ContentType.INTELLIGENCE_INTEGRATION:
            base_audience.append("analysts")
        elif content_type == ContentType.TASK_COLLABORATION:
            base_audience.append("activists")
        elif content_type == ContentType.OPINION_DEBATE:
            base_audience.append("debate_community")
        
        return list(set(base_audience))  # Remove duplicates
    
    async def optimize_publish_times(self, content_items: List[ContentItem]) -> Dict[str, datetime]:
        """Optimize publish times for content items."""
        logger.info(f"Optimizing publish times for {len(content_items)} items...")
        
        scheduled_times = {}
        
        # Sort content by optimization score
        sorted_content = sorted(content_items, key=lambda x: x.optimization_score, reverse=True)
        
        # Get available time slots
        available_slots = self._get_available_time_slots()
        
        for content in sorted_content:
            # Find best slot for this content
            best_slot = await self._find_best_time_slot(content, available_slots)
            
            if best_slot:
                # Calculate actual publish time
                publish_time = self._calculate_publish_time(best_slot)
                
                content.scheduled_at = publish_time
                content.status = ContentStatus.SCHEDULED
                
                scheduled_times[content.content_id] = publish_time
                
                # Remove slot from availability
                available_slots.remove(best_slot)
        
        logger.info(f"Scheduled {len(scheduled_times)} content items")
        return scheduled_times
    
    def _get_available_time_slots(self) -> List[PublishTimeSlot]:
        """Get available time slots for scheduling."""
        now = datetime.now()
        
        # Filter slots that are in the future and within scheduling window
        available = []
        
        for slot in self.time_slots:
            slot_time = self._calculate_publish_time(slot)
            
            if (now < slot_time <= now + timedelta(hours=self.publish_ahead_hours)):
                available.append(slot)
        
        # Sort by expected performance
        available.sort(key=lambda x: x.expected_engagement, reverse=True)
        
        return available
    
    async def _find_best_time_slot(self, content: ContentItem, 
                                 available_slots: List[PublishTimeSlot]) -> Optional[PublishTimeSlot]:
        """Find the best time slot for a content item."""
        if not available_slots:
            return None
        
        # Score each slot for this content
        slot_scores = []
        
        for slot in available_slots:
            score = await self._calculate_slot_score(content, slot)
            slot_scores.append((slot, score))
        
        # Return best slot
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        return slot_scores[0][0]
    
    async def _calculate_slot_score(self, content: ContentItem, 
                                  slot: PublishTimeSlot) -> float:
        """Calculate how well a slot fits a content item."""
        base_score = slot.expected_engagement * 0.4
        base_score += slot.historical_performance * 0.3
        base_score += slot.confidence * 0.2
        base_score += (1 - slot.competition_level) * 0.1  # Lower competition is better
        
        # Adjust for content type and timing
        if content.content_type == ContentType.EVENT_TRACKING:
            # Breaking news should be published ASAP
            time_factor = max(0, 1 - (slot.hour - datetime.now().hour) / 24)
            base_score *= time_factor
        
        return base_score
    
    def _calculate_publish_time(self, slot: PublishTimeSlot) -> datetime:
        """Calculate actual publish datetime for a time slot."""
        now = datetime.now()
        
        # Find the next occurrence of this slot
        days_ahead = (slot.day_of_week - now.weekday()) % 7
        if days_ahead == 0 and (slot.hour < now.hour or (slot.hour == now.hour and now.minute > 0)):
            days_ahead = 7  # Next week if time has passed
        
        publish_time = now + timedelta(days=days_ahead)
        publish_time = publish_time.replace(hour=slot.hour, minute=slot.minute, second=0, microsecond=0)
        
        return publish_time
    
    def _calculate_expected_reach(self, day: int, hour: int) -> float:
        """Calculate expected reach for a time slot."""
        # Base reach patterns (higher on weekends, during prime hours)
        day_multiplier = 1.2 if day in [5, 6] else 1.0  # Weekend boost
        hour_multiplier = {
            8: 0.8,   # Morning commute
            12: 1.1,  # Lunch break
            18: 1.3,  # Evening
            20: 1.2   # Prime time
        }.get(hour, 0.6)
        
        base_reach = 1000  # Base reach number
        return base_reach * day_multiplier * hour_multiplier
    
    def _calculate_expected_engagement(self, day: int, hour: int) -> float:
        """Calculate expected engagement rate for a time slot."""
        # Engagement patterns
        base_engagement = 0.05  # 5% base engagement rate
        
        # Time-based adjustments
        if hour in [12, 18, 20]:  # Prime engagement hours
            time_multiplier = 1.5
        elif hour in [8, 14, 22]:  # Secondary hours
            time_multiplier = 1.2
        else:
            time_multiplier = 0.8
        
        # Day-based adjustments
        if day in [5, 6]:  # Weekend
            day_multiplier = 1.3
        elif day in [0, 6]:  # Sunday/Saturday
            day_multiplier = 1.2
        else:
            day_multiplier = 1.0
        
        return base_engagement * time_multiplier * day_multiplier
    
    def _calculate_competition_level(self, day: int, hour: int) -> float:
        """Calculate competition level for a time slot."""
        # Higher competition during prime hours
        if hour in [12, 18, 20]:
            return 0.8
        elif hour in [8, 14, 22]:
            return 0.6
        else:
            return 0.3
    
    def _get_historical_performance(self, day: int, hour: int) -> float:
        """Get historical performance for a time slot."""
        # Simulate historical performance data
        # In real implementation, this would come from actual analytics
        base_performance = 0.6
        
        # Adjust based on day and hour patterns
        if hour in [18, 20]:  # Best performing hours
            base_performance += 0.2
        elif hour in [12, 8]:  # Good hours
            base_performance += 0.1
        
        if day in [5, 6]:  # Weekend performance
            base_performance += 0.1
        
        return min(1.0, base_performance)
    
    async def get_pipeline_metrics(self) -> PipelineMetrics:
        """Get comprehensive pipeline performance metrics."""
        total_topics = len(self.hot_topics)
        total_generated = len(self.content_queue) + len(self.published_content)
        total_published = len(self.published_content)
        
        # Calculate average engagement rate
        if self.published_content:
            engagement_rates = []
            for content in self.published_content:
                total_engagement = sum(content.actual_engagement.values())
                # Assuming we have reach data somewhere
                estimated_reach = 1000  # Placeholder
                rate = total_engagement / estimated_reach if estimated_reach > 0 else 0
                engagement_rates.append(rate)
            
            avg_engagement = statistics.mean(engagement_rates) if engagement_rates else 0
        else:
            avg_engagement = 0
        
        # Calculate average time to publish
        if self.published_content:
            publish_times = []
            for content in self.published_content:
                if content.created_at and content.published_at:
                    time_diff = (content.published_at - content.created_at).total_seconds() / 3600
                    publish_times.append(time_diff)
            
            avg_time = statistics.mean(publish_times) if publish_times else 0
        else:
            avg_time = 0
        
        return PipelineMetrics(
            total_topics_processed=total_topics,
            total_content_generated=total_generated,
            total_content_published=total_published,
            average_engagement_rate=avg_engagement,
            average_time_to_publish=avg_time,
            ab_test_success_rate=0.85,  # Placeholder
            hot_topic_accuracy=0.78,   # Placeholder
            pipeline_efficiency=0.82   # Placeholder
        )


# Global instance
content_pipeline = ContentPipeline()


def get_content_pipeline() -> ContentPipeline:
    """Get the global content pipeline instance."""
    return content_pipeline
