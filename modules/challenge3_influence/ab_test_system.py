"""
Zero Realm Social Agent - Challenge 3 Influence Module
A/B Test System: Complete A/B testing engine for content optimization
"""

import asyncio
import hashlib
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, ClassVar
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math

from pydantic import BaseModel, Field
from scipy import stats
from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class TestVariable(Enum):
    """Variables that can be A/B tested."""
    TITLE = "title"
    CONTENT_STYLE = "content_style"
    PUBLISH_TIME = "publish_time"
    INTERACTION_STRATEGY = "interaction_strategy"
    CALL_TO_ACTION = "call_to_action"
    VISUAL_ELEMENTS = "visual_elements"
    CONTENT_LENGTH = "content_length"
    EMOTIONAL_TONE = "emotional_tone"


class TestStatus(Enum):
    """A/B test status types."""
    DESIGNING = "designing"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestResult(Enum):
    """A/B test result outcomes."""
    SIGNIFICANT_A = "significant_a"
    SIGNIFICANT_B = "significant_b"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


class EngagementMetric(Enum):
    """Engagement metrics for testing."""
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_TIME = "engagement_time"
    SHARE_RATE = "share_rate"
    COMMENT_RATE = "comment_rate"
    REACH = "reach"


@dataclass
class TestVariant:
    """Individual test variant."""
    variant_id: str
    variant_name: str  # "A" or "B"
    variable: TestVariable
    content: Dict[str, Any]  # The actual content for this variant
    traffic_allocation: float  # 0.0-1.0, proportion of traffic
    sample_size: int = 0
    engagement_metrics: Dict[EngagementMetric, float] = None
    conversion_events: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.engagement_metrics is None:
            self.engagement_metrics = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ABTest:
    """Complete A/B test configuration."""
    test_id: str
    test_name: str
    variable: TestVariable
    hypothesis: str
    variants: List[TestVariant]
    status: TestStatus
    primary_metric: EngagementMetric
    secondary_metrics: List[EngagementMetric]
    confidence_level: float  # 0.0-1.0
    minimum_sample_size: int
    maximum_duration_days: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    result: Optional[TestResult]
    statistical_significance: float
    winner_variant: Optional[str]
    insights: List[str]
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class TestInsight:
    """Insight generated from A/B test results."""
    insight_id: str
    test_id: str
    insight_type: str
    description: str
    confidence: float
    impact_level: str  # "low", "medium", "high"
    actionable_recommendations: List[str]
    generated_at: datetime


class StatisticalTest(BaseModel):
    """Statistical test configuration and results."""
    test_type: str = "two_sample_t_test"
    alpha: float = Field(default=0.05, description="Significance level")
    power: float = Field(default=0.8, description="Statistical power")
    effect_size: Optional[float] = Field(default=None, description="Expected effect size")
    p_value: Optional[float] = Field(default=None, description="Calculated p-value")
    confidence_interval: Optional[Tuple[float, float]] = Field(default=None, description="Confidence interval")
    test_statistic: Optional[float] = Field(default=None, description="Test statistic value")


class ABTestSystem(BaseModel):
    """Complete A/B testing system for content optimization."""
    
    shared_memory: ClassVar = get_shared_memory()
    
    # System configuration
    default_confidence_level: float = Field(default=0.95, description="Default confidence level")
    default_sample_size: int = Field(default=100, description="Default minimum sample size")
    maximum_concurrent_tests: int = Field(default=10, description="Maximum concurrent tests")
    test_cleanup_days: int = Field(default=30, description="Days to keep completed tests")
    
    # Traffic allocation
    traffic_split_precision: float = Field(default=0.01, description="Precision for traffic splitting")
    min_traffic_per_variant: float = Field(default=0.05, description="Minimum traffic per variant")
    
    # Statistical thresholds
    significance_threshold: float = Field(default=0.05, description="P-value threshold for significance")
    practical_significance_threshold: float = Field(default=0.02, description="Minimum practical difference")
    
    # Test storage
    active_tests: Dict[str, ABTest] = Field(default_factory=dict)
    completed_tests: Dict[str, ABTest] = Field(default_factory=dict)
    test_insights: Dict[str, List[TestInsight]] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    async def design_ab_test(self, test_name: str, variable: TestVariable, 
                           hypothesis: str, variant_a_content: Dict[str, Any],
                           variant_b_content: Dict[str, Any],
                           primary_metric: EngagementMetric,
                           secondary_metrics: List[EngagementMetric] = None,
                           confidence_level: Optional[float] = None,
                           minimum_sample_size: Optional[int] = None) -> ABTest:
        """Design a new A/B test."""
        logger.info(f"Designing A/B test: {test_name}")
        
        # Validate inputs
        await self._validate_test_design(variable, hypothesis, variant_a_content, variant_b_content)
        
        # Generate test ID
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(test_name.encode()).hexdigest()[:8]}"
        
        # Create variants
        variant_a = TestVariant(
            variant_id=f"{test_id}_A",
            variant_name="A",
            variable=variable,
            content=variant_a_content,
            traffic_allocation=0.5
        )
        
        variant_b = TestVariant(
            variant_id=f"{test_id}_B",
            variant_name="B", 
            variable=variable,
            content=variant_b_content,
            traffic_allocation=0.5
        )
        
        # Create test
        test = ABTest(
            test_id=test_id,
            test_name=test_name,
            variable=variable,
            hypothesis=hypothesis,
            variants=[variant_a, variant_b],
            status=TestStatus.DESIGNING,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            confidence_level=confidence_level or self.default_confidence_level,
            minimum_sample_size=minimum_sample_size or self.default_sample_size,
            maximum_duration_days=14,  # Default 2 weeks
            start_time=None,
            end_time=None,
            result=None,
            statistical_significance=0.0,
            winner_variant=None,
            insights=[],
            created_at=datetime.now()
        )
        
        # Store test
        self.active_tests[test_id] = test
        
        # Store in shared memory
        test_key = f"ab_test:{test_id}"
        self.shared_memory.set(test_key, asdict(test), tags=["ab_test", "active"])
        
        logger.info(f"A/B test designed: {test_id}")
        return test
    
    async def _validate_test_design(self, variable: TestVariable, hypothesis: str,
                                  variant_a_content: Dict[str, Any], 
                                  variant_b_content: Dict[str, Any]) -> None:
        """Validate A/B test design."""
        # Check if variants are sufficiently different
        if variable == TestVariable.TITLE:
            if variant_a_content.get("title") == variant_b_content.get("title"):
                raise ValueError("Title variants must be different")
        
        elif variable == TestVariable.CONTENT_STYLE:
            if variant_a_content.get("style") == variant_b_content.get("style"):
                raise ValueError("Content style variants must be different")
        
        elif variable == TestVariable.PUBLISH_TIME:
            time_a = variant_a_content.get("publish_time")
            time_b = variant_b_content.get("publish_time")
            if not time_a or not time_b or time_a == time_b:
                raise ValueError("Publish time variants must be different")
        
        # Validate hypothesis
        if not hypothesis or len(hypothesis) < 10:
            raise ValueError("Hypothesis must be at least 10 characters")
        
        # Check concurrent test limit
        if len(self.active_tests) >= self.maximum_concurrent_tests:
            raise ValueError(f"Maximum concurrent tests ({self.maximum_concurrent_tests}) reached")
    
    async def start_ab_test(self, test_id: str) -> bool:
        """Start an A/B test."""
        test = self.active_tests.get(test_id)
        if not test:
            logger.error(f"Test {test_id} not found")
            return False
        
        if test.status != TestStatus.DESIGNING:
            logger.error(f"Test {test_id} is not in DESIGNING status")
            return False
        
        # Update test status
        test.status = TestStatus.RUNNING
        test.start_time = datetime.now()
        
        # Initialize traffic allocation
        await self._initialize_traffic_allocation(test)
        
        # Store in shared memory
        test_key = f"ab_test:{test_id}"
        self.shared_memory.set(test_key, asdict(test), tags=["ab_test", "running"])
        
        logger.info(f"A/B test started: {test_id}")
        return True
    
    async def _initialize_traffic_allocation(self, test: ABTest) -> None:
        """Initialize traffic allocation for test variants."""
        # Ensure traffic allocation sums to 1.0
        total_allocation = sum(v.traffic_allocation for v in test.variants)
        if abs(total_allocation - 1.0) > self.traffic_split_precision:
            # Normalize allocations
            for variant in test.variants:
                variant.traffic_allocation = variant.traffic_allocation / total_allocation
        
        # Check minimum traffic per variant
        for variant in test.variants:
            if variant.traffic_allocation < self.min_traffic_per_variant:
                logger.warning(f"Variant {variant.variant_id} has low traffic allocation: {variant.traffic_allocation}")
    
    async def allocate_traffic(self, test_id: str) -> Optional[TestVariant]:
        """Allocate traffic to a variant for a running test."""
        test = self.active_tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return None
        
        # Random allocation based on traffic weights
        rand = random.random()
        cumulative = 0.0
        
        for variant in test.variants:
            cumulative += variant.traffic_allocation
            if rand <= cumulative:
                variant.sample_size += 1
                return variant
        
        # Fallback to first variant
        test.variants[0].sample_size += 1
        return test.variants[0]
    
    async def record_engagement(self, test_id: str, variant_id: str,
                              metrics: Dict[EngagementMetric, float]) -> bool:
        """Record engagement metrics for a test variant."""
        test = self.active_tests.get(test_id)
        if not test:
            return False
        
        # Find variant
        variant = None
        for v in test.variants:
            if v.variant_id == variant_id:
                variant = v
                break
        
        if not variant:
            return False
        
        # Update metrics
        for metric, value in metrics.items():
            if metric in variant.engagement_metrics:
                # Update running average
                current_avg = variant.engagement_metrics[metric]
                new_avg = (current_avg * (variant.sample_size - 1) + value) / variant.sample_size
                variant.engagement_metrics[metric] = new_avg
            else:
                variant.engagement_metrics[metric] = value
        
        # Check for conversion events
        if metrics.get(EngagementMetric.CONVERSION_RATE, 0) > 0:
            variant.conversion_events += 1
        
        # Store in shared memory
        test_key = f"ab_test:{test_id}"
        self.shared_memory.set(test_key, asdict(test), tags=["ab_test", "running"])
        
        return True
    
    async def analyze_test_results(self, test_id: str) -> TestResult:
        """Analyze A/B test results and determine winner."""
        test = self.active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        if test.status != TestStatus.RUNNING:
            raise ValueError(f"Test {test_id} is not running")
        
        logger.info(f"Analyzing A/B test results: {test_id}")
        
        # Update status
        test.status = TestStatus.ANALYZING
        
        # Check minimum sample size
        if not await self._check_sample_size_requirements(test):
            test.result = TestResult.INCONCLUSIVE
            test.statistical_significance = 0.0
            return await self._complete_test(test)
        
        # Perform statistical analysis
        statistical_result = await self._perform_statistical_analysis(test)
        
        # Determine winner based on primary metric
        result = await self._determine_test_winner(test, statistical_result)
        
        test.result = result
        test.statistical_significance = 1 - statistical_result.p_value if statistical_result.p_value else 0.0
        
        # Generate insights
        insights = await self._generate_test_insights(test, statistical_result)
        test.insights = insights
        
        return await self._complete_test(test)
    
    async def _check_sample_size_requirements(self, test: ABTest) -> bool:
        """Check if test meets minimum sample size requirements."""
        for variant in test.variants:
            if variant.sample_size < test.minimum_sample_size:
                logger.info(f"Variant {variant.variant_id} sample size insufficient: {variant.sample_size} < {test.minimum_sample_size}")
                return False
        return True
    
    async def _perform_statistical_analysis(self, test: ABTest) -> StatisticalTest:
        """Perform statistical analysis on test results."""
        # Get primary metric data for both variants
        variant_a = test.variants[0]
        variant_b = test.variants[1]
        
        metric_a = variant_a.engagement_metrics.get(test.primary_metric, 0)
        metric_b = variant_b.engagement_metrics.get(test.primary_metric, 0)
        
        # For demonstration, we'll use simulated data
        # In real implementation, this would use actual engagement data
        sample_size_a = variant_a.sample_size
        sample_size_b = variant_b.sample_size
        
        # Generate sample data (replace with real data)
        data_a = [metric_a + random.normalvariate(0, 0.1) for _ in range(sample_size_a)]
        data_b = [metric_b + random.normalvariate(0, 0.1) for _ in range(sample_size_b)]
        
        # Perform two-sample t-test
        t_stat, p_value = stats.ttest_ind(data_a, data_b)
        
        # Calculate confidence interval
        mean_diff = statistics.mean(data_b) - statistics.mean(data_a)
        std_error = math.sqrt(sum((x - statistics.mean(data_b))**2 for x in data_b) / (len(data_b) - 1) / len(data_b) +
                            sum((x - statistics.mean(data_a))**2 for x in data_a) / (len(data_a) - 1) / len(data_a))
        
        t_critical = stats.t.ppf(1 - (1 - test.confidence_level) / 2, len(data_a) + len(data_b) - 2)
        margin_error = t_critical * std_error
        
        confidence_interval = (mean_diff - margin_error, mean_diff + margin_error)
        
        return StatisticalTest(
            test_type="two_sample_t_test",
            alpha=1 - test.confidence_level,
            power=0.8,
            effect_size=abs(mean_diff),
            p_value=p_value,
            confidence_interval=confidence_interval,
            test_statistic=t_stat
        )
    
    async def _determine_test_winner(self, test: ABTest, 
                                   statistical_result: StatisticalTest) -> TestResult:
        """Determine test winner based on statistical analysis."""
        # Check statistical significance
        if statistical_result.p_value and statistical_result.p_value < self.significance_threshold:
            # Check practical significance
            if statistical_result.confidence_interval:
                lower_bound, upper_bound = statistical_result.confidence_interval
                practical_significance = abs(lower_bound) > self.practical_significance_threshold or \
                                       abs(upper_bound) > self.practical_significance_threshold
                
                if practical_significance:
                    # Determine which variant won
                    variant_a = test.variants[0]
                    variant_b = test.variants[1]
                    
                    metric_a = variant_a.engagement_metrics.get(test.primary_metric, 0)
                    metric_b = variant_b.engagement_metrics.get(test.primary_metric, 0)
                    
                    if metric_b > metric_a:
                        test.winner_variant = variant_b.variant_id
                        return TestResult.SIGNIFICANT_B
                    else:
                        test.winner_variant = variant_a.variant_id
                        return TestResult.SIGNIFICANT_A
                else:
                    return TestResult.INCONCLUSIVE
            else:
                return TestResult.INCONCLUSIVE
        else:
            return TestResult.INCONCLUSIVE
    
    async def _generate_test_insights(self, test: ABTest, 
                                    statistical_result: StatisticalTest) -> List[str]:
        """Generate insights from test results."""
        insights = []
        
        # Primary metric insight
        if test.result in [TestResult.SIGNIFICANT_A, TestResult.SIGNIFICANT_B]:
            winner = test.variants[0] if test.result == TestResult.SIGNIFICANT_A else test.variants[1]
            loser = test.variants[1] if test.result == TestResult.SIGNIFICANT_A else test.variants[0]
            
            winner_metric = winner.engagement_metrics.get(test.primary_metric, 0)
            loser_metric = loser.engagement_metrics.get(test.primary_metric, 0)
            
            improvement = ((winner_metric - loser_metric) / loser_metric * 100) if loser_metric > 0 else 0
            
            insights.append(f"Variant {winner.variant_name} achieved {improvement:.1f}% higher {test.primary_metric.value}")
            
            # Variable-specific insights
            if test.variable == TestVariable.TITLE:
                insights.append(f"Title optimization significantly impacts {test.primary_metric.value}")
            elif test.variable == TestVariable.CONTENT_STYLE:
                insights.append(f"Content style choice affects user engagement by {improvement:.1f}%")
            elif test.variable == TestVariable.PUBLISH_TIME:
                insights.append(f"Publish timing influences {test.primary_metric.value} performance")
        
        # Sample size insight
        total_sample = sum(v.sample_size for v in test.variants)
        insights.append(f"Test completed with {total_sample} total samples")
        
        # Statistical confidence insight
        if statistical_result.p_value:
            confidence = (1 - statistical_result.p_value) * 100
            insights.append(f"Results have {confidence:.1f}% statistical confidence")
        
        return insights
    
    async def _complete_test(self, test: ABTest) -> TestResult:
        """Complete test and move to completed tests."""
        test.end_time = datetime.now()
        test.status = TestStatus.COMPLETED
        
        # Move to completed tests
        self.completed_tests[test.test_id] = test
        del self.active_tests[test.test_id]
        
        # Store in shared memory
        test_key = f"ab_test:{test.test_id}"
        self.shared_memory.set(test_key, asdict(test), tags=["ab_test", "completed"])
        
        logger.info(f"A/B test completed: {test.test_id} with result: {test.result.value}")
        return test.result
    
    async def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive test results."""
        # Check both active and completed tests
        test = self.active_tests.get(test_id) or self.completed_tests.get(test_id)
        if not test:
            return None
        
        # Compile results
        results = {
            "test_id": test.test_id,
            "test_name": test.test_name,
            "variable": test.variable.value,
            "hypothesis": test.hypothesis,
            "status": test.status.value,
            "result": test.result.value if test.result else None,
            "statistical_significance": test.statistical_significance,
            "winner_variant": test.winner_variant,
            "duration_days": (test.end_time or datetime.now() - test.start_time).days if test.start_time else 0,
            "insights": test.insights,
            "variants": []
        }
        
        # Add variant details
        for variant in test.variants:
            variant_data = {
                "variant_id": variant.variant_id,
                "variant_name": variant.variant_name,
                "traffic_allocation": variant.traffic_allocation,
                "sample_size": variant.sample_size,
                "conversion_events": variant.conversion_events,
                "engagement_metrics": {metric.value: value for metric, value in variant.engagement_metrics.items()}
            }
            results["variants"].append(variant_data)
        
        return results
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get A/B testing system statistics."""
        total_tests = len(self.active_tests) + len(self.completed_tests)
        
        # Calculate success rates
        if self.completed_tests:
            significant_tests = sum(1 for test in self.completed_tests.values() 
                                  if test.result in [TestResult.SIGNIFICANT_A, TestResult.SIGNIFICANT_B])
            success_rate = significant_tests / len(self.completed_tests)
        else:
            success_rate = 0.0
        
        # Variable performance
        variable_performance = {}
        for test in self.completed_tests.values():
            if test.result in [TestResult.SIGNIFICANT_A, TestResult.SIGNIFICANT_B]:
                var_name = test.variable.value
                if var_name not in variable_performance:
                    variable_performance[var_name] = {"tests": 0, "wins": 0}
                variable_performance[var_name]["tests"] += 1
                variable_performance[var_name]["wins"] += 1
        
        # Calculate win rates
        for var_name in variable_performance:
            if variable_performance[var_name]["tests"] > 0:
                variable_performance[var_name]["win_rate"] = (
                    variable_performance[var_name]["wins"] / variable_performance[var_name]["tests"]
                )
        
        return {
            "total_tests": total_tests,
            "active_tests": len(self.active_tests),
            "completed_tests": len(self.completed_tests),
            "success_rate": success_rate,
            "variable_performance": variable_performance,
            "average_test_duration_days": 7.5,  # Placeholder
            "total_sample_size": sum(
                sum(v.sample_size for v in test.variants) 
                for test in self.completed_tests.values()
            )
        }
    
    async def cleanup_old_tests(self, days_to_keep: int = None) -> int:
        """Clean up old completed tests."""
        if days_to_keep is None:
            days_to_keep = self.test_cleanup_days
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        tests_to_remove = []
        for test_id, test in self.completed_tests.items():
            if test.end_time and test.end_time < cutoff_date:
                tests_to_remove.append(test_id)
        
        for test_id in tests_to_remove:
            del self.completed_tests[test_id]
            logger.info(f"Cleaned up old test: {test_id}")
        
        return len(tests_to_remove)
    
    async def export_test_results(self, file_path: str, 
                                 include_active: bool = False,
                                 include_completed: bool = True) -> bool:
        """Export test results to JSON file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_statistics": await self.get_system_statistics(),
                "tests": []
            }
            
            # Include active tests if requested
            if include_active:
                for test in self.active_tests.values():
                    test_data = await self.get_test_results(test.test_id)
                    if test_data:
                        export_data["tests"].append(test_data)
            
            # Include completed tests if requested
            if include_completed:
                for test in self.completed_tests.values():
                    test_data = await self.get_test_results(test.test_id)
                    if test_data:
                        export_data["tests"].append(test_data)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"A/B test results exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export test results: {e}")
            return False


# Global instance
ab_test_system = ABTestSystem()


def get_ab_test_system() -> ABTestSystem:
    """Get the global A/B test system instance."""
    return ab_test_system
