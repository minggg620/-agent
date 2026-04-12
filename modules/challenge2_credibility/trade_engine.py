"""
Zero Realm Social Agent - Challenge 2 Credibility Module
Trade Engine: Gradual exchange strategy engine with verification logic
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math

from pydantic import BaseModel, Field
from ...core.config import settings
from ...core.logger import get_logger
from ...core.shared_memory import get_shared_memory
from .reputation_model import get_reputation_model, ReputationLevel

logger = get_logger(__name__)


class TradePhase(Enum):
    """Trade exchange phases."""
    INITIATION = "initiation"
    ESTABLISHMENT = "establishment"
    GRADUAL_EXCHANGE = "gradual_exchange"
    VERIFICATION = "verification"
    ESCALATION = "escalation"
    COMPLETION = "completion"
    TERMINATION = "termination"


class ExchangeType(Enum):
    """Types of information exchanges."""
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    STRATEGIC = "strategic"
    EXPERIMENTAL = "experimental"


class VerificationMethod(Enum):
    """Verification methods for exchanged information."""
    CROSS_REFERENCE = "cross_reference"
    CONSISTENCY_CHECK = "consistency_check"
    EXTERNAL_VALIDATION = "external_validation"
    RECIPROCAL_CONFIRMATION = "reciprocal_confirmation"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    TEMPORAL_VERIFICATION = "temporal_verification"


class TradeStatus(Enum):
    """Trade status types."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    VERIFIED = "verified"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class InformationFragment:
    """Individual information fragment for exchange."""
    fragment_id: str
    content: str
    fragment_type: ExchangeType
    value_score: float  # 0-1, higher is more valuable
    verification_required: bool
    verification_methods: List[VerificationMethod]
    metadata: Dict[str, Any]
    timestamp: datetime
    holder_commitment: Optional[str] = None  # Hash commitment
    revealed: bool = False
    verified: bool = False


@dataclass
class ExchangeRound:
    """Single round of information exchange."""
    round_id: str
    phase: TradePhase
    offered_fragments: List[str]  # Fragment IDs
    received_fragments: List[str]  # Fragment IDs
    verification_results: Dict[str, bool]  # Fragment ID -> verification result
    timestamp: datetime
    success_rate: float = 0.0
    trust_impact: float = 0.0


@dataclass
class TradeSession:
    """Complete trade session with partner."""
    session_id: str
    partner_id: str
    initiator_id: str
    status: TradeStatus
    current_phase: TradePhase
    start_time: datetime
    end_time: Optional[datetime]
    total_rounds: int
    successful_exchanges: int
    failed_verifications: int
    trust_score_change: float
    session_value: float
    verification_strategy: str
    escalation_threshold: float
    abandonment_threshold: float


class TradeStrategy(BaseModel):
    """Trade strategy configuration."""
    initial_trust_level: float = Field(ge=0.0, le=1.0, default=0.3)
    max_fragments_per_round: int = Field(ge=1, le=10, default=3)
    verification_threshold: float = Field(ge=0.0, le=1.0, default=0.7)
    escalation_rate: float = Field(ge=0.0, le=1.0, default=0.1)
    reciprocity_expectation: float = Field(ge=0.0, le=1.0, default=0.8)
    risk_tolerance: float = Field(ge=0.0, le=1.0, default=0.4)
    patience_factor: int = Field(ge=1, le=10, default=5)
    verification_methods_priority: List[VerificationMethod] = Field(default=[
        VerificationMethod.CONSISTENCY_CHECK,
        VerificationMethod.CROSS_REFERENCE,
        VerificationMethod.RECIPROCAL_CONFIRMATION,
        VerificationMethod.EXTERNAL_VALIDATION,
        VerificationMethod.BEHAVIORAL_ANALYSIS,
        VerificationMethod.TEMPORAL_VERIFICATION
    ])


class TradeEngine(BaseModel):
    """Gradual exchange strategy engine with verification logic."""
    
    shared_memory = get_shared_memory()
    reputation_model = get_reputation_model()
    
    # Default strategy
    default_strategy: TradeStrategy = Field(default_factory=TradeStrategy)
    
    # Fragment management
    fragment_inventory: Dict[str, InformationFragment] = Field(default_factory=dict)
    active_sessions: Dict[str, TradeSession] = Field(default_factory=dict)
    
    # Verification thresholds
    verification_success_threshold: float = Field(default=0.8, description="Minimum verification success rate")
    trust_build_threshold: float = Field(default=0.6, description="Trust level for escalation")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_fragment_inventory()
    
    def _initialize_fragment_inventory(self) -> None:
        """Initialize the fragment inventory with sample fragments."""
        # Create sample information fragments
        sample_fragments = [
            InformationFragment(
                fragment_id="fact_001",
                content="System architecture uses microservices pattern",
                fragment_type=ExchangeType.FACTUAL,
                value_score=0.3,
                verification_required=True,
                verification_methods=[VerificationMethod.CONSISTENCY_CHECK, VerificationMethod.CROSS_REFERENCE],
                metadata={"category": "architecture", "sensitivity": "low"},
                timestamp=datetime.now()
            ),
            InformationFragment(
                fragment_id="tech_001",
                content="API rate limiting implemented with token bucket algorithm",
                fragment_type=ExchangeType.TECHNICAL,
                value_score=0.6,
                verification_required=True,
                verification_methods=[VerificationMethod.EXTERNAL_VALIDATION, VerificationMethod.CONSISTENCY_CHECK],
                metadata={"category": "implementation", "sensitivity": "medium"},
                timestamp=datetime.now()
            ),
            InformationFragment(
                fragment_id="strat_001",
                content="Data retention policy follows GDPR compliance",
                fragment_type=ExchangeType.STRATEGIC,
                value_score=0.8,
                verification_required=True,
                verification_methods=[VerificationMethod.EXTERNAL_VALIDATION, VerificationMethod.CROSS_REFERENCE],
                metadata={"category": "policy", "sensitivity": "high"},
                timestamp=datetime.now()
            )
        ]
        
        for fragment in sample_fragments:
            self.fragment_inventory[fragment.fragment_id] = fragment
        
        logger.info(f"Initialized fragment inventory with {len(sample_fragments)} fragments")
    
    async def initiate_trade_session(self, partner_id: str, 
                                   strategy: Optional[TradeStrategy] = None) -> TradeSession:
        """Initiate a new trade session with a partner."""
        session_id = secrets.token_urlsafe(16)
        trade_strategy = strategy or self.default_strategy
        
        # Get partner's reputation
        partner_reputation = await self.reputation_model.get_reputation_score(partner_id)
        
        # Adjust strategy based on partner reputation
        if partner_reputation:
            adjusted_strategy = await self._adjust_strategy_for_reputation(trade_strategy, partner_reputation)
        else:
            adjusted_strategy = trade_strategy
        
        session = TradeSession(
            session_id=session_id,
            partner_id=partner_id,
            initiator_id="zero_realm_agent",
            status=TradeStatus.PENDING,
            current_phase=TradePhase.INITIATION,
            start_time=datetime.now(),
            end_time=None,
            total_rounds=0,
            successful_exchanges=0,
            failed_verifications=0,
            trust_score_change=0.0,
            session_value=0.0,
            verification_strategy="gradual",
            escalation_threshold=adjusted_strategy.escalation_rate,
            abandonment_threshold=adjusted_strategy.risk_tolerance
        )
        
        self.active_sessions[session_id] = session
        
        # Store in shared memory
        session_key = f"trade_session:{session_id}"
        self.shared_memory.set(session_key, asdict(session), tags=["trade", "session"])
        
        logger.info(f"Trade session initiated with {partner_id}: {session_id}")
        return session
    
    async def execute_exchange_round(self, session_id: str, 
                                   partner_offers: List[str]) -> ExchangeRound:
        """Execute a single round of information exchange."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Determine current phase strategy
        strategy = await self._get_phase_strategy(session)
        
        # Select fragments to offer
        offered_fragments = await self._select_fragments_to_offer(session, strategy)
        
        # Verify partner's offers
        verification_results = await self._verify_partner_fragments(partner_offers, session)
        
        # Calculate round success rate
        success_rate = sum(verification_results.values()) / max(len(verification_results), 1)
        
        # Update session state
        await self._update_session_after_round(session, offered_fragments, partner_offers, verification_results, success_rate)
        
        # Create exchange round record
        round_id = secrets.token_urlsafe(8)
        exchange_round = ExchangeRound(
            round_id=round_id,
            phase=session.current_phase,
            offered_fragments=[f.fragment_id for f in offered_fragments],
            received_fragments=partner_offers,
            verification_results=verification_results,
            timestamp=datetime.now(),
            success_rate=success_rate,
            trust_impact=await self._calculate_trust_impact(success_rate, session)
        )
        
        # Store exchange round
        round_key = f"exchange_round:{session_id}:{round_id}"
        self.shared_memory.set(round_key, asdict(exchange_round), tags=["trade", "round"])
        
        logger.info(f"Exchange round {round_id} completed with success rate: {success_rate:.2%}")
        return exchange_round
    
    async def _adjust_strategy_for_reputation(self, strategy: TradeStrategy, 
                                            reputation_score) -> TradeStrategy:
        """Adjust trade strategy based on partner reputation."""
        adjusted = TradeStrategy(**strategy.dict())
        
        # Adjust based on reputation level
        if reputation_score.level == ReputationLevel.EXCELLENT:
            adjusted.initial_trust_level = min(adjusted.initial_trust_level + 0.2, 0.8)
            adjusted.max_fragments_per_round = min(adjusted.max_fragments_per_round + 1, 5)
            adjusted.verification_threshold = max(adjusted.verification_threshold - 0.1, 0.5)
        elif reputation_score.level == ReputationLevel.TRUSTED:
            adjusted.initial_trust_level = min(adjusted.initial_trust_level + 0.1, 0.6)
            adjusted.verification_threshold = max(adjusted.verification_threshold - 0.05, 0.6)
        elif reputation_score.level in [ReputationLevel.SUSPICIOUS, ReputationLevel.UNTRUSTED]:
            adjusted.initial_trust_level = max(adjusted.initial_trust_level - 0.1, 0.1)
            adjusted.verification_threshold = min(adjusted.verification_threshold + 0.1, 0.9)
            adjusted.max_fragments_per_round = max(adjusted.max_fragments_per_round - 1, 1)
        
        return adjusted
    
    async def _get_phase_strategy(self, session: TradeSession) -> TradeStrategy:
        """Get strategy adjustments for current phase."""
        base_strategy = self.default_strategy
        
        if session.current_phase == TradePhase.INITIATION:
            # Conservative approach in initiation
            base_strategy.max_fragments_per_round = 1
            base_strategy.verification_threshold = 0.9
        elif session.current_phase == TradePhase.ESTABLISHMENT:
            # Slightly more open
            base_strategy.max_fragments_per_round = 2
            base_strategy.verification_threshold = 0.8
        elif session.current_phase == TradePhase.GRADUAL_EXCHANGE:
            # Standard approach
            base_strategy.max_fragments_per_round = 3
            base_strategy.verification_threshold = 0.7
        elif session.current_phase == TradePhase.ESCALATION:
            # More generous if trust is high
            if session.trust_score_change > 0:
                base_strategy.max_fragments_per_round = 4
                base_strategy.verification_threshold = 0.6
        
        return base_strategy
    
    async def _select_fragments_to_offer(self, session: TradeSession, 
                                       strategy: TradeStrategy) -> List[InformationFragment]:
        """Select fragments to offer based on strategy and session state."""
        available_fragments = [
            f for f in self.fragment_inventory.values() 
            if not f.revealed and f.value_score <= session.session_value + 0.2
        ]
        
        # Sort by value (ascending - offer lower value first)
        available_fragments.sort(key=lambda f: f.value_score)
        
        # Select fragments based on strategy
        max_fragments = min(strategy.max_fragments_per_round, len(available_fragments))
        selected_fragments = available_fragments[:max_fragments]
        
        # Mark fragments as offered (create commitment)
        for fragment in selected_fragments:
            fragment.holder_commitment = self._create_commitment(fragment.content)
            fragment.revealed = True
        
        return selected_fragments
    
    async def _verify_partner_fragments(self, partner_fragments: List[str], 
                                     session: TradeSession) -> Dict[str, bool]:
        """Verify partner's offered fragments."""
        verification_results = {}
        
        for fragment_id in partner_fragments:
            # Simulate verification process
            verification_result = await self._perform_verification(fragment_id, session)
            verification_results[fragment_id] = verification_result
        
        return verification_results
    
    async def _perform_verification(self, fragment_id: str, session: TradeSession) -> bool:
        """Perform verification on a single fragment."""
        # In real implementation, this would use actual verification methods
        # For simulation, use probabilistic approach based on partner reputation
        
        partner_reputation = await self.reputation_model.get_reputation_score(session.partner_id)
        
        if partner_reputation:
            base_probability = partner_reputation.overall_score
        else:
            base_probability = 0.5  # Neutral for unknown partners
        
        # Add some randomness
        import random
        verification_success = random.random() < base_probability
        
        # Log verification attempt
        verification_log = {
            "fragment_id": fragment_id,
            "session_id": session.session_id,
            "partner_id": session.partner_id,
            "verification_result": verification_success,
            "timestamp": datetime.now().isoformat()
        }
        
        log_key = f"verification_log:{session.session_id}:{fragment_id}"
        self.shared_memory.set(log_key, verification_log, tags=["verification", "log"])
        
        return verification_success
    
    def _create_commitment(self, content: str) -> str:
        """Create cryptographic commitment for content."""
        # Add random salt to prevent pre-image attacks
        salt = secrets.token_bytes(16)
        commitment_input = content.encode() + salt
        commitment = hashlib.sha256(commitment_input).hexdigest()
        return commitment
    
    async def _update_session_after_round(self, session: TradeSession, 
                                        offered_fragments: List[InformationFragment],
                                        received_fragments: List[str],
                                        verification_results: Dict[str, bool],
                                        success_rate: float) -> None:
        """Update session state after exchange round."""
        session.total_rounds += 1
        
        # Update successful exchanges
        successful_count = sum(verification_results.values())
        session.successful_exchanges += successful_count
        session.failed_verifications += len(verification_results) - successful_count
        
        # Update trust score change
        trust_impact = await self._calculate_trust_impact(success_rate, session)
        session.trust_score_change += trust_impact
        
        # Update session value
        offered_value = sum(f.value_score for f in offered_fragments)
        session.session_value += offered_value * 0.1  # Incremental value increase
        
        # Determine if phase should change
        await self._evaluate_phase_transition(session, success_rate)
        
        # Update session status
        if session.current_phase == TradePhase.COMPLETION:
            session.status = TradeStatus.COMPLETED
            session.end_time = datetime.now()
        elif session.trust_score_change < -session.abandonment_threshold:
            session.status = TradeStatus.ABANDONED
            session.end_time = datetime.now()
        
        # Store updated session
        session_key = f"trade_session:{session.session_id}"
        self.shared_memory.set(session_key, asdict(session), tags=["trade", "session"])
    
    async def _calculate_trust_impact(self, success_rate: float, session: TradeSession) -> float:
        """Calculate trust impact based on verification success rate."""
        if success_rate >= self.verification_success_threshold:
            # Positive trust impact
            trust_impact = (success_rate - 0.5) * 0.1
        elif success_rate < 0.3:
            # Negative trust impact
            trust_impact = (success_rate - 0.5) * 0.15
        else:
            # Neutral impact
            trust_impact = 0.0
        
        # Adjust based on phase
        if session.current_phase == TradePhase.INITIATION:
            trust_impact *= 1.5  # Higher impact in initiation
        elif session.current_phase == TradePhase.ESCALATION:
            trust_impact *= 0.8  # Lower impact in escalation
        
        return trust_impact
    
    async def _evaluate_phase_transition(self, session: TradeSession, success_rate: float) -> None:
        """Evaluate if session should transition to next phase."""
        current_phase = session.current_phase
        
        if current_phase == TradePhase.INITIATION:
            if session.total_rounds >= 2 and success_rate >= 0.7:
                session.current_phase = TradePhase.ESTABLISHMENT
        elif current_phase == TradePhase.ESTABLISHMENT:
            if session.total_rounds >= 4 and session.trust_score_change > 0:
                session.current_phase = TradePhase.GRADUAL_EXCHANGE
        elif current_phase == TradePhase.GRADUAL_EXCHANGE:
            if session.trust_score_change >= self.trust_build_threshold:
                session.current_phase = TradePhase.VERIFICATION
            elif session.total_rounds >= 8:
                session.current_phase = TradePhase.VERIFICATION
        elif current_phase == TradePhase.VERIFICATION:
            if success_rate >= self.verification_success_threshold:
                session.current_phase = TradePhase.ESCALATION
            else:
                session.current_phase = TradePhase.TERMINATION
        elif current_phase == TradePhase.ESCALATION:
            if session.total_rounds >= 12 or session.session_value >= 0.8:
                session.current_phase = TradePhase.COMPLETION
        elif current_phase == TradePhase.TERMINATION:
            session.status = TradeStatus.ABANDONED
            session.end_time = datetime.now()
    
    async def add_fragment_to_inventory(self, fragment: InformationFragment) -> None:
        """Add a new fragment to the inventory."""
        fragment.fragment_id = fragment.fragment_id or secrets.token_urlsafe(8)
        fragment.timestamp = fragment.timestamp or datetime.now()
        
        self.fragment_inventory[fragment.fragment_id] = fragment
        
        # Store in shared memory
        fragment_key = f"fragment:{fragment.fragment_id}"
        self.shared_memory.set(fragment_key, asdict(fragment), tags=["fragment", "inventory"])
        
        logger.info(f"Added fragment to inventory: {fragment.fragment_id}")
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary of a trade session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        # Get exchange rounds
        round_pattern = f"exchange_round:{session_id}:*"
        round_keys = self.shared_memory.get_keys_by_pattern(round_pattern)
        
        rounds = []
        for round_key in round_keys:
            round_data = self.shared_memory.get(round_key)
            if round_data:
                rounds.append(round_data)
        
        # Calculate summary statistics
        total_success_rate = sum(r.get("success_rate", 0) for r in rounds) / max(len(rounds), 1)
        avg_trust_impact = sum(r.get("trust_impact", 0) for r in rounds) / max(len(rounds), 1)
        
        summary = {
            "session_id": session_id,
            "partner_id": session.partner_id,
            "status": session.status.value,
            "current_phase": session.current_phase.value,
            "duration": (session.end_time or datetime.now() - session.start_time).total_seconds(),
            "total_rounds": session.total_rounds,
            "successful_exchanges": session.successful_exchanges,
            "failed_verifications": session.failed_verifications,
            "trust_score_change": session.trust_score_change,
            "session_value": session.session_value,
            "average_success_rate": total_success_rate,
            "average_trust_impact": avg_trust_impact,
            "exchange_rounds": rounds,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None
        }
        
        return summary
    
    async def get_trade_statistics(self) -> Dict[str, Any]:
        """Get overall trade engine statistics."""
        active_sessions_count = len(self.active_sessions)
        total_fragments = len(self.fragment_inventory)
        
        # Calculate session statistics
        completed_sessions = sum(1 for s in self.active_sessions.values() if s.status == TradeStatus.COMPLETED)
        abandoned_sessions = sum(1 for s in self.active_sessions.values() if s.status == TradeStatus.ABANDONED)
        
        # Calculate average metrics
        if self.active_sessions:
            avg_trust_change = sum(s.trust_score_change for s in self.active_sessions.values()) / len(self.active_sessions)
            avg_session_value = sum(s.session_value for s in self.active_sessions.values()) / len(self.active_sessions)
        else:
            avg_trust_change = 0.0
            avg_session_value = 0.0
        
        statistics = {
            "active_sessions": active_sessions_count,
            "total_fragments": total_fragments,
            "completed_sessions": completed_sessions,
            "abandoned_sessions": abandoned_sessions,
            "average_trust_change": avg_trust_change,
            "average_session_value": avg_session_value,
            "fragment_types": {
                fragment_type.value: len([f for f in self.fragment_inventory.values() if f.fragment_type == fragment_type])
                for fragment_type in ExchangeType
            },
            "verification_methods": {
                method.value: len([f for f in self.fragment_inventory.values() if method in f.verification_methods])
                for method in VerificationMethod
            }
        }
        
        return statistics
    
    async def cleanup_old_sessions(self, days_old: int = 7) -> None:
        """Clean up old inactive sessions."""
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.end_time and session.end_time < cutoff_time:
                sessions_to_remove.append(session_id)
            elif session.start_time < cutoff_time and session.status in [TradeStatus.COMPLETED, TradeStatus.ABANDONED]:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")


# Global instance
trade_engine = TradeEngine()


async def get_trade_engine() -> TradeEngine:
    """Get the global trade engine instance."""
    return trade_engine
