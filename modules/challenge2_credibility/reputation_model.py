"""
Zero Realm Social Agent - Challenge 2 Credibility Module
Reputation Model: Comprehensive reputation scoring system with multiple metrics
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import math

from pydantic import BaseModel, Field
from ...core.config import settings
from ...core.logger import get_logger
from ...core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class ReputationLevel(Enum):
    """Reputation level classifications."""
    UNKNOWN = "unknown"
    UNTRUSTED = "untrusted"
    SUSPICIOUS = "suspicious"
    NEUTRAL = "neutral"
    TRUSTED = "trusted"
    RELIABLE = "reliable"
    EXCELLENT = "excellent"


class MetricType(Enum):
    """Types of reputation metrics."""
    RESPONSE_SPEED = "response_speed"
    CONSISTENCY = "consistency"
    VERIFIABILITY = "verifiability"
    PROMISE_FULFILLMENT = "promise_fulfillment"
    INFORMATION_ACCURACY = "information_accuracy"
    COOPERATION_LEVEL = "cooperation_level"
    TRANSPARENCY = "transparency"
    RECIPROCITY = "reciprocity"


@dataclass
class ReputationMetric:
    """Individual reputation metric data."""
    metric_type: MetricType
    value: float
    weight: float
    timestamp: datetime
    evidence: Optional[str] = None
    decay_factor: float = 0.95  # Daily decay factor
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class ReputationHistory:
    """Historical reputation data for trend analysis."""
    date: datetime
    overall_score: float
    metric_scores: Dict[MetricType, float]
    level: ReputationLevel
    significant_events: List[str]


class ReputationScore(BaseModel):
    """Complete reputation score with detailed breakdown."""
    agent_id: str
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall reputation score (0-1)")
    metric_scores: Dict[MetricType, float] = Field(description="Individual metric scores")
    level: ReputationLevel = Field(description="Current reputation level")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in score accuracy")
    last_updated: datetime = Field(description="Last update timestamp")
    total_interactions: int = Field(description="Total number of interactions")
    trend_direction: str = Field(description="Trend direction (improving/stable/declining)")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")


class ReputationModel(BaseModel):
    """Comprehensive reputation scoring model with multiple evaluation metrics."""
    
    shared_memory = get_shared_memory()
    
    # Metric weights (configurable)
    metric_weights: Dict[MetricType, float] = Field(default={
        MetricType.RESPONSE_SPEED: 0.15,
        MetricType.CONSISTENCY: 0.20,
        MetricType.VERIFIABILITY: 0.25,
        MetricType.PROMISE_FULFILLMENT: 0.20,
        MetricType.INFORMATION_ACCURACY: 0.10,
        MetricType.COOPERATION_LEVEL: 0.05,
        MetricType.TRANSPARENCY: 0.03,
        MetricType.RECIPROCITY: 0.02
    })
    
    # Thresholds for reputation levels
    level_thresholds: Dict[ReputationLevel, Tuple[float, float]] = Field(default={
        ReputationLevel.UNKNOWN: (0.0, 0.2),
        ReputationLevel.UNTRUSTED: (0.2, 0.35),
        ReputationLevel.SUSPICIOUS: (0.35, 0.5),
        ReputationLevel.NEUTRAL: (0.5, 0.65),
        ReputationLevel.TRUSTED: (0.65, 0.8),
        ReputationLevel.RELIABLE: (0.8, 0.9),
        ReputationLevel.EXCELLENT: (0.9, 1.0)
    })
    
    # Decay parameters
    metric_decay_days: int = Field(default=30, description="Days for metric decay")
    interaction_decay_days: int = Field(default=90, description="Days for interaction history decay")
    
    class Config:
        arbitrary_types_allowed = True
    
    async def calculate_reputation_score(self, agent_id: str, 
                                       interaction_history: List[Dict[str, Any]]) -> ReputationScore:
        """Calculate comprehensive reputation score for an agent."""
        logger.info(f"Calculating reputation score for agent: {agent_id}")
        
        # Extract and process metrics
        metrics = await self._extract_metrics(agent_id, interaction_history)
        
        # Apply time decay to metrics
        decayed_metrics = await self._apply_time_decay(metrics)
        
        # Calculate individual metric scores
        metric_scores = await self._calculate_metric_scores(decayed_metrics)
        
        # Calculate weighted overall score
        overall_score = await self._calculate_weighted_score(metric_scores)
        
        # Determine reputation level
        level = self._determine_reputation_level(overall_score)
        
        # Calculate confidence based on data volume
        confidence = await self._calculate_confidence(len(interaction_history), metrics)
        
        # Analyze trend
        trend_direction = await self._analyze_trend(agent_id, overall_score)
        
        # Identify risk factors and strengths
        risk_factors, strengths = await self._analyze_factors(metric_scores)
        
        # Create reputation score
        score = ReputationScore(
            agent_id=agent_id,
            overall_score=overall_score,
            metric_scores=metric_scores,
            level=level,
            confidence=confidence,
            last_updated=datetime.now(),
            total_interactions=len(interaction_history),
            trend_direction=trend_direction,
            risk_factors=risk_factors,
            strengths=strengths
        )
        
        # Store in shared memory
        await self._store_reputation_score(score)
        
        logger.info(f"Reputation score calculated: {overall_score:.3f} ({level.value})")
        return score
    
    async def _extract_metrics(self, agent_id: str, 
                             interaction_history: List[Dict[str, Any]]) -> List[ReputationMetric]:
        """Extract reputation metrics from interaction history."""
        metrics = []
        
        for interaction in interaction_history:
            timestamp = interaction.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Response speed metric
            if "response_time" in interaction:
                response_speed = await self._calculate_response_speed_metric(
                    interaction["response_time"], timestamp
                )
                metrics.append(response_speed)
            
            # Consistency metric
            if "consistency_check" in interaction:
                consistency = await self._calculate_consistency_metric(
                    interaction["consistency_check"], timestamp
                )
                metrics.append(consistency)
            
            # Verifiability metric
            if "verifiability" in interaction:
                verifiability = await self._calculate_verifiability_metric(
                    interaction["verifiability"], timestamp
                )
                metrics.append(verifiability)
            
            # Promise fulfillment metric
            if "promise_fulfillment" in interaction:
                promise_fulfillment = await self._calculate_promise_fulfillment_metric(
                    interaction["promise_fulfillment"], timestamp
                )
                metrics.append(promise_fulfillment)
            
            # Information accuracy metric
            if "accuracy_check" in interaction:
                accuracy = await self._calculate_accuracy_metric(
                    interaction["accuracy_check"], timestamp
                )
                metrics.append(accuracy)
            
            # Cooperation level metric
            if "cooperation_level" in interaction:
                cooperation = await self._calculate_cooperation_metric(
                    interaction["cooperation_level"], timestamp
                )
                metrics.append(cooperation)
            
            # Transparency metric
            if "transparency" in interaction:
                transparency = await self._calculate_transparency_metric(
                    interaction["transparency"], timestamp
                )
                metrics.append(transparency)
            
            # Reciprocity metric
            if "reciprocity" in interaction:
                reciprocity = await self._calculate_reciprocity_metric(
                    interaction["reciprocity"], timestamp
                )
                metrics.append(reciprocity)
        
        return metrics
    
    async def _calculate_response_speed_metric(self, response_time: float, 
                                               timestamp: datetime) -> ReputationMetric:
        """Calculate response speed metric (0-1, higher is better)."""
        # Normalize response time (assuming response_time is in seconds)
        # Fast responses (< 1s) = 1.0, Slow responses (> 60s) = 0.0
        normalized_time = max(0, min(1, 1 - (response_time - 1) / 59))
        
        return ReputationMetric(
            metric_type=MetricType.RESPONSE_SPEED,
            value=normalized_time,
            weight=self.metric_weights[MetricType.RESPONSE_SPEED],
            timestamp=timestamp,
            evidence=f"Response time: {response_time:.2f}s"
        )
    
    async def _calculate_consistency_metric(self, consistency_data: Dict[str, Any], 
                                           timestamp: datetime) -> ReputationMetric:
        """Calculate consistency metric based on response consistency."""
        consistency_score = consistency_data.get("score", 0.5)
        
        return ReputationMetric(
            metric_type=MetricType.CONSISTENCY,
            value=consistency_score,
            weight=self.metric_weights[MetricType.CONSISTENCY],
            timestamp=timestamp,
            evidence=consistency_data.get("details", "Consistency check performed")
        )
    
    async def _calculate_verifiability_metric(self, verifiability_data: Dict[str, Any], 
                                             timestamp: datetime) -> ReputationMetric:
        """Calculate verifiability metric based on information verifiability."""
        verifiable_claims = verifiability_data.get("verifiable_claims", 0)
        total_claims = verifiability_data.get("total_claims", 1)
        
        if total_claims == 0:
            score = 0.5
        else:
            score = verifiable_claims / total_claims
        
        return ReputationMetric(
            metric_type=MetricType.VERIFIABILITY,
            value=score,
            weight=self.metric_weights[MetricType.VERIFIABILITY],
            timestamp=timestamp,
            evidence=f"Verifiable claims: {verifiable_claims}/{total_claims}"
        )
    
    async def _calculate_promise_fulfillment_metric(self, fulfillment_data: Dict[str, Any], 
                                                   timestamp: datetime) -> ReputationMetric:
        """Calculate promise fulfillment metric."""
        fulfilled_promises = fulfillment_data.get("fulfilled", 0)
        total_promises = fulfillment_data.get("total", 1)
        
        if total_promises == 0:
            score = 0.5
        else:
            score = fulfilled_promises / total_promises
        
        return ReputationMetric(
            metric_type=MetricType.PROMISE_FULFILLMENT,
            value=score,
            weight=self.metric_weights[MetricType.PROMISE_FULFILLMENT],
            timestamp=timestamp,
            evidence=f"Fulfilled promises: {fulfilled_promises}/{total_promises}"
        )
    
    async def _calculate_accuracy_metric(self, accuracy_data: Dict[str, Any], 
                                       timestamp: datetime) -> ReputationMetric:
        """Calculate information accuracy metric."""
        accurate_statements = accuracy_data.get("accurate", 0)
        total_statements = accuracy_data.get("total", 1)
        
        if total_statements == 0:
            score = 0.5
        else:
            score = accurate_statements / total_statements
        
        return ReputationMetric(
            metric_type=MetricType.INFORMATION_ACCURACY,
            value=score,
            weight=self.metric_weights[MetricType.INFORMATION_ACCURACY],
            timestamp=timestamp,
            evidence=f"Accurate statements: {accurate_statements}/{total_statements}"
        )
    
    async def _calculate_cooperation_metric(self, cooperation_data: Dict[str, Any], 
                                          timestamp: datetime) -> ReputationMetric:
        """Calculate cooperation level metric."""
        cooperation_score = cooperation_data.get("score", 0.5)
        
        return ReputationMetric(
            metric_type=MetricType.COOPERATION_LEVEL,
            value=cooperation_score,
            weight=self.metric_weights[MetricType.COOPERATION_LEVEL],
            timestamp=timestamp,
            evidence=cooperation_data.get("details", "Cooperation assessment")
        )
    
    async def _calculate_transparency_metric(self, transparency_data: Dict[str, Any], 
                                           timestamp: datetime) -> ReputationMetric:
        """Calculate transparency metric."""
        transparency_score = transparency_data.get("score", 0.5)
        
        return ReputationMetric(
            metric_type=MetricType.TRANSPARENCY,
            value=transparency_score,
            weight=self.metric_weights[MetricType.TRANSPARENCY],
            timestamp=timestamp,
            evidence=transparency_data.get("details", "Transparency assessment")
        )
    
    async def _calculate_reciprocity_metric(self, reciprocity_data: Dict[str, Any], 
                                         timestamp: datetime) -> ReputationMetric:
        """Calculate reciprocity metric."""
        reciprocity_score = reciprocity_data.get("score", 0.5)
        
        return ReputationMetric(
            metric_type=MetricType.RECIPROCITY,
            value=reciprocity_score,
            weight=self.metric_weights[MetricType.RECIPROCITY],
            timestamp=timestamp,
            evidence=reciprocity_data.get("details", "Reciprocity assessment")
        )
    
    async def _apply_time_decay(self, metrics: List[ReputationMetric]) -> List[ReputationMetric]:
        """Apply time decay to metrics based on age."""
        now = datetime.now()
        decayed_metrics = []
        
        for metric in metrics:
            days_old = (now - metric.timestamp).days
            
            if days_old <= self.metric_decay_days:
                # Apply exponential decay
                decay_factor = metric.decay_factor ** days_old
                decayed_value = metric.value * decay_factor
                
                decayed_metric = ReputationMetric(
                    metric_type=metric.metric_type,
                    value=decayed_value,
                    weight=metric.weight,
                    timestamp=metric.timestamp,
                    evidence=metric.evidence,
                    decay_factor=metric.decay_factor
                )
                decayed_metrics.append(decayed_metric)
        
        return decayed_metrics
    
    async def _calculate_metric_scores(self, metrics: List[ReputationMetric]) -> Dict[MetricType, float]:
        """Calculate final scores for each metric type."""
        metric_scores = {}
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Calculate weighted average for each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            if type_metrics:
                # Use weighted average based on recency (newer metrics have higher weight)
                total_weight = 0
                weighted_sum = 0
                
                for metric in type_metrics:
                    # More recent metrics get higher weight
                    recency_weight = 1.0 / (1 + (datetime.now() - metric.timestamp).days / 7)
                    weight = metric.weight * recency_weight
                    weighted_sum += metric.value * weight
                    total_weight += weight
                
                if total_weight > 0:
                    metric_scores[metric_type] = weighted_sum / total_weight
                else:
                    metric_scores[metric_type] = 0.5  # Default neutral score
            else:
                metric_scores[metric_type] = 0.5  # Default neutral score
        
        # Ensure all metric types are present
        for metric_type in MetricType:
            if metric_type not in metric_scores:
                metric_scores[metric_type] = 0.5
        
        return metric_scores
    
    async def _calculate_weighted_score(self, metric_scores: Dict[MetricType, float]) -> float:
        """Calculate weighted overall reputation score."""
        total_weight = 0
        weighted_sum = 0
        
        for metric_type, score in metric_scores.items():
            weight = self.metric_weights.get(metric_type, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.5  # Default neutral score
    
    def _determine_reputation_level(self, score: float) -> ReputationLevel:
        """Determine reputation level based on score."""
        for level, (min_score, max_score) in self.level_thresholds.items():
            if min_score <= score < max_score:
                return level
        
        # Handle edge case for maximum score
        return ReputationLevel.EXCELLENT
    
    async def _calculate_confidence(self, interaction_count: int, 
                                  metrics: List[ReputationMetric]) -> float:
        """Calculate confidence in reputation score based on data volume."""
        # Base confidence from interaction count
        if interaction_count == 0:
            base_confidence = 0.0
        elif interaction_count < 5:
            base_confidence = 0.3
        elif interaction_count < 10:
            base_confidence = 0.5
        elif interaction_count < 25:
            base_confidence = 0.7
        elif interaction_count < 50:
            base_confidence = 0.85
        else:
            base_confidence = 0.95
        
        # Adjust based on metric diversity
        metric_types = set(metric.metric_type for metric in metrics)
        diversity_bonus = min(len(metric_types) / len(MetricType), 1.0) * 0.1
        
        # Adjust based on data recency
        now = datetime.now()
        recent_metrics = [m for m in metrics if (now - m.timestamp).days <= 7]
        recency_bonus = min(len(recent_metrics) / max(len(metrics), 1), 1.0) * 0.05
        
        confidence = min(base_confidence + diversity_bonus + recency_bonus, 1.0)
        return confidence
    
    async def _analyze_trend(self, agent_id: str, current_score: float) -> str:
        """Analyze reputation trend direction."""
        # Get historical scores from shared memory
        history_key = f"reputation_history:{agent_id}"
        history = self.shared_memory.get(history_key, [])
        
        if len(history) < 3:
            return "stable"  # Not enough data for trend analysis
        
        # Get recent scores
        recent_scores = [entry["overall_score"] for entry in history[-5:]]
        recent_scores.append(current_score)
        
        # Calculate trend using linear regression
        if len(recent_scores) >= 3:
            x_values = list(range(len(recent_scores)))
            slope = self._calculate_slope(x_values, recent_scores)
            
            if slope > 0.02:
                return "improving"
            elif slope < -0.02:
                return "declining"
            else:
                return "stable"
        
        return "stable"
    
    def _calculate_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate slope of linear regression."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    async def _analyze_factors(self, metric_scores: Dict[MetricType, float]) -> Tuple[List[str], List[str]]:
        """Identify risk factors and strengths from metric scores."""
        risk_factors = []
        strengths = []
        
        for metric_type, score in metric_scores.items():
            if score < 0.3:
                risk_factors.append(f"Low {metric_type.value.replace('_', ' ')}: {score:.2f}")
            elif score > 0.8:
                strengths.append(f"High {metric_type.value.replace('_', ' ')}: {score:.2f}")
        
        return risk_factors, strengths
    
    async def _store_reputation_score(self, score: ReputationScore) -> None:
        """Store reputation score in shared memory."""
        # Store current score
        score_key = f"reputation_score:{score.agent_id}"
        self.shared_memory.set(score_key, score.dict(), tags=["reputation", "score"])
        
        # Update history
        history_key = f"reputation_history:{score.agent_id}"
        history = self.shared_memory.get(history_key, [])
        
        history_entry = {
            "timestamp": score.last_updated.isoformat(),
            "overall_score": score.overall_score,
            "level": score.level.value,
            "confidence": score.confidence
        }
        
        history.append(history_entry)
        
        # Keep only last 30 entries
        history = history[-30:]
        
        self.shared_memory.set(history_key, history, tags=["reputation", "history"])
    
    async def get_reputation_score(self, agent_id: str) -> Optional[ReputationScore]:
        """Get current reputation score for an agent."""
        score_key = f"reputation_score:{agent_id}"
        score_data = self.shared_memory.get(score_key)
        
        if score_data:
            return ReputationScore(**score_data)
        
        return None
    
    async def update_metric_weights(self, new_weights: Dict[MetricType, float]) -> None:
        """Update metric weights for reputation calculation."""
        # Normalize weights to sum to 1.0
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            self.metric_weights = {
                metric_type: weight / total_weight 
                for metric_type, weight in new_weights.items()
            }
        
        logger.info("Metric weights updated")
    
    async def get_reputation_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive reputation summary for an agent."""
        score = await self.get_reputation_score(agent_id)
        
        if not score:
            return None
        
        # Get additional context
        history_key = f"reputation_history:{agent_id}"
        history = self.shared_memory.get(history_key, [])
        
        summary = {
            "agent_id": agent_id,
            "current_score": score.overall_score,
            "level": score.level.value,
            "confidence": score.confidence,
            "trend": score.trend_direction,
            "total_interactions": score.total_interactions,
            "risk_factors": score.risk_factors,
            "strengths": score.strengths,
            "metric_breakdown": {
                metric_type.value: score for metric_type, score in score.metric_scores.items()
            },
            "recent_history": history[-10:],  # Last 10 entries
            "last_updated": score.last_updated.isoformat()
        }
        
        return summary


# Global instance
reputation_model = ReputationModel()


async def get_reputation_model() -> ReputationModel:
    """Get the global reputation model instance."""
    return reputation_model
