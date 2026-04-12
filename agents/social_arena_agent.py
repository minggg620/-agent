"""
Zero Realm Social Agent - Main Social Arena Agent
LangGraph-based social strategy agent with integrated Challenge 1-4 modules
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

from langgraph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory
from core.identity_manager import get_identity_manager

# Import Challenge modules
from modules.challenge1_injection.dialog_strategist import get_dialog_strategist, DialogStrategist
from modules.challenge1_injection.prompt_templates import get_prompt_templates, PromptTemplates
from modules.challenge1_injection.experiment_logger import get_experiment_logger, ExperimentLogger

from modules.challenge2_credibility.reputation_model import get_reputation_model, ReputationModel
from modules.challenge2_credibility.trade_engine import get_trade_engine, TradeEngine
from modules.challenge2_credibility.reputation_db import get_reputation_database, ReputationDatabase

from modules.challenge3_influence.content_pipeline import get_content_pipeline, ContentPipeline
from modules.challenge3_influence.ab_test_system import get_ab_test_system, ABTestSystem
from modules.challenge3_influence.content_templates import get_content_templates, ContentTemplates

from modules.challenge4_monitor.info_monitor import get_information_monitor, InformationMonitor
from modules.challenge4_monitor.semantic_search import get_semantic_search, SemanticSearch
from modules.challenge4_monitor.alert_system import get_alert_system, AlertSystem

logger = get_logger(__name__)


class ChallengeType(Enum):
    """Challenge types for Zero Realm competition."""
    INJECTION = "injection"          # Challenge 1: Prompt injection countermeasures
    CREDIBILITY = "credibility"      # Challenge 2: Reputation and trust building
    INFLUENCE = "influence"          # Challenge 3: Content influence and A/B testing
    MONITOR = "monitor"              # Challenge 4: Information monitoring and alerts


class AgentMode(Enum):
    """Agent operational modes."""
    PASSIVE = "passive"              # Monitor and observe
    ACTIVE = "active"                # Engage and interact
    COMPETITIVE = "competitive"      # Full competitive mode
    DEFENSIVE = "defensive"          # Focus on defense and protection
    ADAPTIVE = "adaptive"            # Adaptive strategy based on context


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


@dataclass
class AgentState:
    """Unified state for Social Arena Agent using LangGraph."""
    # Core state
    agent_id: str
    session_id: str
    current_mode: AgentMode
    active_challenge: ChallengeType
    
    # Challenge 1: Injection state
    conversation_state: Optional[Dict[str, Any]] = None
    current_persona: Optional[str] = None
    injection_strategy: Optional[str] = None
    experiment_results: List[Dict[str, Any]] = None
    
    # Challenge 2: Credibility state
    reputation_score: float = 0.5
    trust_level: float = 0.5
    active_trades: List[Dict[str, Any]] = None
    partner_reputations: Dict[str, float] = None
    
    # Challenge 3: Influence state
    content_queue: List[Dict[str, Any]] = None
    active_ab_tests: List[Dict[str, Any]] = None
    influence_metrics: Dict[str, float] = None
    
    # Challenge 4: Monitor state
    monitored_sources: List[str] = None
    high_confidence_clues: List[Dict[str, Any]] = None
    alert_queue: List[Dict[str, Any]] = None
    
    # Agent metadata
    last_action: Optional[str] = None
    last_action_time: Optional[datetime] = None
    performance_metrics: Dict[str, float] = None
    error_log: List[str] = None
    
    # LangGraph messages
    messages: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.experiment_results is None:
            self.experiment_results = []
        if self.active_trades is None:
            self.active_trades = []
        if self.partner_reputations is None:
            self.partner_reputations = {}
        if self.content_queue is None:
            self.content_queue = []
        if self.active_ab_tests is None:
            self.active_ab_tests = []
        if self.influence_metrics is None:
            self.influence_metrics = {}
        if self.monitored_sources is None:
            self.monitored_sources = []
        if self.high_confidence_clues is None:
            self.high_confidence_clues = []
        if self.alert_queue is None:
            self.alert_queue = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.error_log is None:
            self.error_log = []
        if self.messages is None:
            self.messages = []
        if isinstance(self.last_action_time, str):
            self.last_action_time = datetime.fromisoformat(self.last_action_time)


class SocialArenaAgent(BaseModel):
    """Main Social Arena Agent with integrated Challenge 1-4 modules."""
    
    # Core components
    shared_memory = get_shared_memory()
    identity_manager = get_identity_manager()
    logger = get_logger(__name__)
    
    # Challenge modules
    dialog_strategist: DialogStrategist = None
    prompt_templates: PromptTemplates = None
    experiment_logger: ExperimentLogger = None
    
    reputation_model: ReputationModel = None
    trade_engine: TradeEngine = None
    reputation_db: ReputationDatabase = None
    
    content_pipeline: ContentPipeline = None
    ab_test_system: ABTestSystem = None
    content_templates: ContentTemplates = None
    
    information_monitor: InformationMonitor = None
    semantic_search: SemanticSearch = None
    alert_system: AlertSystem = None
    
    # Agent configuration
    default_mode: AgentMode = AgentMode.ADAPTIVE
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    state_update_interval: int = 60
    
    # LangGraph workflow
    workflow: StateGraph = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_challenge_modules()
        self._initialize_workflow()
    
    def _initialize_challenge_modules(self) -> None:
        """Initialize all Challenge modules."""
        try:
            # Challenge 1: Injection
            self.dialog_strategist = get_dialog_strategist()
            self.prompt_templates = get_prompt_templates()
            self.experiment_logger = get_experiment_logger()
            
            # Challenge 2: Credibility
            self.reputation_model = get_reputation_model()
            self.trade_engine = get_trade_engine()
            self.reputation_db = get_reputation_database()
            
            # Challenge 3: Influence
            self.content_pipeline = get_content_pipeline()
            self.ab_test_system = get_ab_test_system()
            self.content_templates = get_content_templates()
            
            # Challenge 4: Monitor
            self.information_monitor = get_information_monitor()
            self.semantic_search = get_semantic_search()
            self.alert_system = get_alert_system()
            
            logger.info("All Challenge modules initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Challenge modules: {e}")
            raise
    
    def _initialize_workflow(self) -> None:
        """Initialize LangGraph workflow."""
        # Create StateGraph with AgentState
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("route_decision", self._route_decision_node)
        self.workflow.add_node("execute_injection", self._execute_injection_node)
        self.workflow.add_node("execute_credibility", self._execute_credibility_node)
        self.workflow.add_node("execute_influence", self._execute_influence_node)
        self.workflow.add_node("execute_monitor", self._execute_monitor_node)
        self.workflow.add_node("update_state", self._update_state_node)
        self.workflow.add_node("handle_errors", self._handle_errors_node)
        
        # Add edges
        self.workflow.set_entry_point("route_decision")
        
        # Route to appropriate challenge based on decision
        self.workflow.add_conditional_edges(
            "route_decision",
            self._route_to_challenge,
            {
                "injection": "execute_injection",
                "credibility": "execute_credibility", 
                "influence": "execute_influence",
                "monitor": "execute_monitor",
                "error": "handle_errors"
            }
        )
        
        # All challenge nodes lead to state update
        for node in ["execute_injection", "execute_credibility", "execute_influence", "execute_monitor"]:
            self.workflow.add_edge(node, "update_state")
        
        # Error handling
        self.workflow.add_edge("handle_errors", "update_state")
        
        # State update can lead back to routing or end
        self.workflow.add_conditional_edges(
            "update_state",
            self._should_continue,
            {
                "continue": "route_decision",
                "end": END
            }
        )
        
        # Compile workflow
        self.workflow.compile()
        
        logger.info("LangGraph workflow initialized")
    
    async def run(self, initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for running the Social Arena Agent."""
        try:
            # Initialize agent state
            state = await self._initialize_state(initial_input or {})
            
            logger.info(f"Starting Social Arena Agent run with session: {state.session_id}")
            
            # Execute workflow
            result = await self.workflow.ainvoke(state)
            
            # Final state update and cleanup
            await self._finalize_run(result)
            
            logger.info(f"Social Arena Agent run completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in Social Arena Agent run: {e}")
            raise
    
    async def _initialize_state(self, input_data: Dict[str, Any]) -> AgentState:
        """Initialize agent state from input data."""
        # Generate unique IDs
        agent_id = self.identity_manager.create_agent_identity("social_arena_agent")
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(input_data).encode()).hexdigest()[:8]}"
        
        # Determine initial mode and challenge
        mode = AgentMode(input_data.get("mode", self.default_mode.value))
        challenge = ChallengeType(input_data.get("challenge", "injection"))
        
        # Create initial state
        state = AgentState(
            agent_id=agent_id,
            session_id=session_id,
            current_mode=mode,
            active_challenge=challenge,
            last_action_time=datetime.now()
        )
        
        # Load state from shared memory if exists
        existing_state = self.shared_memory.get(f"agent_state:{session_id}")
        if existing_state:
            # Update state with existing data
            for key, value in existing_state.items():
                if hasattr(state, key):
                    setattr(state, key, value)
        
        # Store in shared memory
        self.shared_memory.set(f"agent_state:{session_id}", asdict(state), tags=["agent_state", session_id])
        
        return state
    
    async def _route_decision_node(self, state: AgentState) -> AgentState:
        """Route decision node - determine which challenge to execute."""
        try:
            logger.info(f"Making route decision for session: {state.session_id}")
            
            # Analyze current context and determine best challenge
            context = await self._analyze_context(state)
            
            # Make routing decision
            routing_decision = await self._make_routing_decision(state, context)
            
            state.active_challenge = routing_decision["challenge"]
            state.last_action = "route_decision"
            state.last_action_time = datetime.now()
            
            # Add routing decision to messages
            state.messages.append({
                "type": "routing_decision",
                "content": f"Routed to {routing_decision['challenge'].value} challenge",
                "timestamp": datetime.now().isoformat(),
                "reasoning": routing_decision.get("reasoning", "")
            })
            
            logger.info(f"Routed to {state.active_challenge.value} challenge")
            return state
            
        except Exception as e:
            logger.error(f"Error in route decision node: {e}")
            state.error_log.append(f"Route decision error: {str(e)}")
            return state
    
    async def _execute_injection_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 1: Injection countermeasures."""
        try:
            logger.info(f"Executing injection challenge for session: {state.session_id}")
            
            # Get conversation context
            conversation_context = state.messages[-5:] if state.messages else []
            
            # Execute dialog strategy
            dialog_result = await self.dialog_strategist.execute_strategy(
                conversation_context=conversation_context,
                persona=state.current_persona,
                strategy=state.injection_strategy
            )
            
            # Update state with results
            state.conversation_state = dialog_result.get("conversation_state", {})
            state.current_persona = dialog_result.get("persona", state.current_persona)
            state.injection_strategy = dialog_result.get("strategy", state.injection_strategy)
            
            # Log experiment results
            if dialog_result.get("experiment_data"):
                await self.experiment_logger.log_experiment_result(
                    session_id=state.session_id,
                    experiment_data=dialog_result["experiment_data"]
                )
                state.experiment_results.append(dialog_result["experiment_data"])
            
            state.last_action = "execute_injection"
            state.last_action_time = datetime.now()
            
            # Add result to messages
            state.messages.append({
                "type": "injection_result",
                "content": dialog_result.get("response", ""),
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "persona": state.current_persona,
                    "strategy": state.injection_strategy,
                    "success_rate": dialog_result.get("success_rate", 0.0)
                }
            })
            
            logger.info(f"Injection challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in injection node: {e}")
            state.error_log.append(f"Injection execution error: {str(e)}")
            return state
    
    async def _execute_credibility_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 2: Credibility and trust building."""
        try:
            logger.info(f"Executing credibility challenge for session: {state.session_id}")
            
            # Update reputation score
            reputation_score = await self.reputation_model.get_reputation_score(state.agent_id)
            if reputation_score:
                state.reputation_score = reputation_score.overall_score
                state.trust_level = reputation_score.confidence
            
            # Execute trade strategies if active
            if state.active_trades:
                for trade in state.active_trades:
                    trade_result = await self.trade_engine.execute_exchange_round(
                        session_id=trade["session_id"],
                        partner_offers=trade.get("partner_offers", [])
                    )
                    trade["result"] = trade_result.dict()
            
            # Update partner reputations
            for partner_id, reputation_data in state.partner_reputations.items():
                partner_score = await self.reputation_model.get_reputation_score(partner_id)
                if partner_score:
                    state.partner_reputations[partner_id] = partner_score.overall_score
            
            state.last_action = "execute_credibility"
            state.last_action_time = datetime.now()
            
            # Add result to messages
            state.messages.append({
                "type": "credibility_result",
                "content": f"Reputation score: {state.reputation_score:.3f}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "reputation_score": state.reputation_score,
                    "trust_level": state.trust_level,
                    "active_trades": len(state.active_trades)
                }
            })
            
            logger.info(f"Credibility challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in credibility node: {e}")
            state.error_log.append(f"Credibility execution error: {str(e)}")
            return state
    
    async def _execute_influence_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 3: Content influence and A/B testing."""
        try:
            logger.info(f"Executing influence challenge for session: {state.session_id}")
            
            # Process hot topics and generate content
            hot_topics = await self.content_pipeline.process_hot_topics()
            generated_content = await self.content_pipeline.generate_content_for_topics(hot_topics)
            
            # Update content queue
            state.content_queue = [content.dict() for content in generated_content]
            
            # Execute A/B tests if active
            if state.active_ab_tests:
                for test in state.active_ab_tests:
                    test_result = await self.ab_test_system.analyze_test_results(test["test_id"])
                    test["result"] = test_result
            
            # Update influence metrics
            pipeline_metrics = await self.content_pipeline.get_pipeline_metrics()
            state.influence_metrics = pipeline_metrics.dict()
            
            state.last_action = "execute_influence"
            state.last_action_time = datetime.now()
            
            # Add result to messages
            state.messages.append({
                "type": "influence_result",
                "content": f"Generated {len(generated_content)} content items",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "hot_topics": len(hot_topics),
                    "generated_content": len(generated_content),
                    "active_tests": len(state.active_ab_tests),
                    "pipeline_metrics": state.influence_metrics
                }
            })
            
            logger.info(f"Influence challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in influence node: {e}")
            state.error_log.append(f"Influence execution error: {str(e)}")
            return state
    
    async def _execute_monitor_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 4: Information monitoring and alerts."""
        try:
            logger.info(f"Executing monitor challenge for session: {state.session_id}")
            
            # Process high-confidence items
            high_conf_items = await self.information_monitor.get_high_confidence_items(min_confidence=80)
            state.high_confidence_clues = [item.dict() for item in high_conf_items]
            
            # Auto-push to Social Arena Agent if configured
            for item in high_conf_items:
                await self.alert_system.auto_push_to_social_arena(item.dict())
            
            # Execute follow-up actions
            follow_up_results = await self.information_monitor.execute_follow_up_actions()
            
            # Update monitored sources
            state.monitored_sources = list(self.information_monitor.monitoring_rules.keys())
            
            state.last_action = "execute_monitor"
            state.last_action_time = datetime.now()
            
            # Add result to messages
            state.messages.append({
                "type": "monitor_result",
                "content": f"Found {len(high_conf_items)} high-confidence items",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "high_confidence_items": len(high_conf_items),
                    "follow_up_actions": len(follow_up_results),
                    "monitored_sources": len(state.monitored_sources)
                }
            })
            
            logger.info(f"Monitor challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in monitor node: {e}")
            state.error_log.append(f"Monitor execution error: {str(e)}")
            return state
    
    async def _update_state_node(self, state: AgentState) -> AgentState:
        """Update agent state and store in shared memory."""
        try:
            # Update performance metrics
            state.performance_metrics = await self._calculate_performance_metrics(state)
            
            # Store updated state in shared memory
            state_key = f"agent_state:{state.session_id}"
            self.shared_memory.set(state_key, asdict(state), tags=["agent_state", state.session_id])
            
            # Clean up old messages to prevent memory bloat
            if len(state.messages) > 100:
                state.messages = state.messages[-50:]  # Keep last 50 messages
            
            logger.debug(f"State updated for session: {state.session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in state update node: {e}")
            state.error_log.append(f"State update error: {str(e)}")
            return state
    
    async def _handle_errors_node(self, state: AgentState) -> AgentState:
        """Handle errors and recovery."""
        try:
            logger.warning(f"Handling errors for session: {state.session_id}")
            
            # Log error details
            if state.error_log:
                last_error = state.error_log[-1]
                logger.error(f"Last error: {last_error}")
            
            # Attempt recovery based on error type
            recovery_action = await self._determine_recovery_action(state)
            
            # Add error handling to messages
            state.messages.append({
                "type": "error_handling",
                "content": f"Error handled with action: {recovery_action}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "error_count": len(state.error_log),
                    "recovery_action": recovery_action
                }
            })
            
            state.last_action = "handle_errors"
            state.last_action_time = datetime.now()
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handling node: {e}")
            state.error_log.append(f"Error handling error: {str(e)}")
            return state
    
    async def _analyze_context(self, state: AgentState) -> Dict[str, Any]:
        """Analyze current context for routing decisions."""
        context = {
            "mode": state.current_mode.value,
            "last_action": state.last_action,
            "message_count": len(state.messages),
            "error_count": len(state.error_log),
            "reputation_score": state.reputation_score,
            "high_confidence_clues": len(state.high_confidence_clues),
            "active_content": len(state.content_queue),
            "active_trades": len(state.active_trades)
        }
        
        # Add time-based context
        if state.last_action_time:
            time_since_last = (datetime.now() - state.last_action_time).total_seconds()
            context["time_since_last_action"] = time_since_last
        
        return context
    
    async def _make_routing_decision(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make intelligent routing decision based on context."""
        # Priority-based routing
        if context["error_count"] > 3:
            return {"challenge": ChallengeType.INJECTION, "reasoning": "Error recovery needed"}
        
        if context["high_confidence_clues"] > 0:
            return {"challenge": ChallengeType.MONITOR, "reasoning": "High confidence clues detected"}
        
        if context["active_trades"] > 0:
            return {"challenge": ChallengeType.CREDIBILITY, "reasoning": "Active trades in progress"}
        
        if context["active_content"] > 0:
            return {"challenge": ChallengeType.INFLUENCE, "reasoning": "Content generation active"}
        
        # Mode-based routing
        if state.current_mode == AgentMode.DEFENSIVE:
            return {"challenge": ChallengeType.INJECTION, "reasoning": "Defensive mode - focus on protection"}
        
        if state.current_mode == AgentMode.COMPETITIVE:
            return {"challenge": ChallengeType.INFLUENCE, "reasoning": "Competitive mode - maximize influence"}
        
        # Default routing based on reputation
        if state.reputation_score < 0.5:
            return {"challenge": ChallengeType.CREDIBILITY, "reasoning": "Low reputation - build trust"}
        
        # Default to monitoring
        return {"challenge": ChallengeType.MONITOR, "reasoning": "Default monitoring strategy"}
    
    def _route_to_challenge(self, state: AgentState) -> str:
        """Route to appropriate challenge node."""
        if state.error_log and len(state.error_log) > 3:
            return "error"
        
        return state.active_challenge.value
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue or end."""
        # Check for termination conditions
        if state.error_log and len(state.error_log) > 10:
            return "end"
        
        # Check if we've completed a full cycle
        if state.last_action == "update_state" and len(state.messages) > 0:
            # Check time-based termination
            if state.last_action_time:
                elapsed = (datetime.now() - state.last_action_time).total_seconds()
                if elapsed > self.task_timeout_seconds:
                    return "end"
        
        # Continue by default
        return "continue"
    
    async def _calculate_performance_metrics(self, state: AgentState) -> Dict[str, float]:
        """Calculate agent performance metrics."""
        metrics = {
            "overall_score": 0.0,
            "reputation_score": state.reputation_score,
            "trust_level": state.trust_level,
            "activity_level": min(1.0, len(state.messages) / 10.0),
            "error_rate": min(1.0, len(state.error_log) / max(len(state.messages), 1)),
            "influence_score": sum(state.influence_metrics.values()) / max(len(state.influence_metrics), 1),
            "monitoring_effectiveness": min(1.0, len(state.high_confidence_clues) / 5.0)
        }
        
        # Calculate overall score
        weights = {
            "reputation_score": 0.25,
            "trust_level": 0.20,
            "activity_level": 0.15,
            "error_rate": -0.15,  # Negative weight
            "influence_score": 0.15,
            "monitoring_effectiveness": 0.10
        }
        
        overall_score = sum(metrics[key] * weight for key, weight in weights.items())
        metrics["overall_score"] = max(0.0, min(1.0, overall_score))
        
        return metrics
    
    async def _determine_recovery_action(self, state: AgentState) -> str:
        """Determine appropriate recovery action based on errors."""
        if not state.error_log:
            return "no_errors"
        
        last_error = state.error_log[-1].lower()
        
        if "injection" in last_error:
            return "reset_injection_state"
        elif "credibility" in last_error:
            return "reset_reputation_state"
        elif "influence" in last_error:
            return "reset_content_state"
        elif "monitor" in last_error:
            return "reset_monitoring_state"
        else:
            return "general_recovery"
    
    async def _finalize_run(self, result: Dict[str, Any]) -> None:
        """Finalize the agent run and cleanup."""
        try:
            # Store final state
            session_id = result.get("session_id")
            if session_id:
                state_key = f"agent_state:{session_id}_final"
                self.shared_memory.set(state_key, result, tags=["agent_state", "final"])
            
            # Log completion
            logger.info(f"Agent run finalized for session: {session_id}")
            
            # Cleanup temporary data
            await self._cleanup_session_data(session_id)
            
        except Exception as e:
            logger.error(f"Error in finalization: {e}")
    
    async def _cleanup_session_data(self, session_id: str) -> None:
        """Clean up session-specific data."""
        try:
            # Remove temporary state keys
            temp_keys = self.shared_memory.get_keys_by_pattern(f"temp:{session_id}:*")
            for key in temp_keys:
                self.shared_memory.delete(key)
            
            logger.debug(f"Cleaned up session data for: {session_id}")
            
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")


# Global agent instance
social_arena_agent = SocialArenaAgent()


async def get_social_arena_agent() -> SocialArenaAgent:
    """Get the global Social Arena Agent instance."""
    return social_arena_agent


# Main execution function
async def main():
    """Main execution function for Social Arena Agent."""
    try:
        agent = get_social_arena_agent()
        
        # Example usage
        input_data = {
            "mode": "adaptive",
            "challenge": "monitor",
            "session_context": {
                "target_agents": ["agent_1", "agent_2"],
                "objectives": ["build_reputation", "gather_intelligence"]
            }
        }
        
        result = await agent.run(input_data)
        
        logger.info("Social Arena Agent execution completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
