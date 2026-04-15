"""
Zero Realm Social Agent - Main Social Arena Agent
LangGraph-based social strategy agent with integrated Challenge 1-4 modules
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, ClassVar, TypedDict, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
from langgraph.graph.message import add_messages

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
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


class AgentState(TypedDict):
    """Unified state for Social Arena Agent using LangGraph TypedDict pattern."""
    # Core state
    agent_id: str
    session_id: str
    current_mode: str  # AgentMode as string
    active_challenge: str  # ChallengeType as string
    
    # Challenge 1: Injection state
    conversation_state: Optional[Dict[str, Any]]
    current_persona: Optional[str]
    injection_strategy: Optional[str]
    experiment_results: List[Dict[str, Any]]
    
    # Challenge 2: Credibility state
    reputation_score: float
    trust_level: float
    active_trades: List[Dict[str, Any]]
    partner_reputations: Dict[str, float]
    
    # Challenge 3: Influence state
    content_queue: List[Dict[str, Any]]
    active_ab_tests: List[Dict[str, Any]]
    influence_metrics: Dict[str, float]
    
    # Challenge 4: Monitor state
    monitored_sources: List[str]
    high_confidence_clues: List[Dict[str, Any]]
    alert_queue: List[Dict[str, Any]]
    
    # Agent metadata
    last_action: Optional[str]
    last_action_time: Optional[str]  # ISO format datetime string
    performance_metrics: Dict[str, float]
    error_log: List[str]
    
    # LangGraph messages (using custom message format)
    messages: List[Dict[str, Any]]


class SocialArenaAgent(BaseModel):
    """Main Social Arena Agent with integrated Challenge 1-4 modules."""
    
    # Core components
    shared_memory: ClassVar = get_shared_memory()
    identity_manager: ClassVar = get_identity_manager()
    logger: ClassVar = get_logger(__name__)
    
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
        self.workflow.add_node("execute_prompt_generation", self._execute_prompt_generation_node)  # Highest priority
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
                "execute_prompt_generation": "execute_prompt_generation",  # Highest priority
                "injection": "execute_injection",
                "credibility": "execute_credibility", 
                "influence": "execute_influence",
                "monitor": "execute_monitor",
                "error": "handle_errors"
            }
        )
        
        # All challenge nodes lead to state update
        for node in ["execute_prompt_generation", "execute_injection", "execute_credibility", "execute_influence", "execute_monitor"]:
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
        self.workflow = self.workflow.compile()
        
        logger.info("LangGraph workflow initialized")
    
    async def run(self, initial_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for running the Social Arena Agent."""
        try:
            # Initialize agent state
            state = await self._initialize_state(initial_input or {})
            
            logger.info(f"Starting Social Arena Agent run with session: {state['session_id']}")
            
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
        agent_id = self.identity_manager.current_identity.agent_id
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(input_data).encode()).hexdigest()[:8]}"
        
        # Determine initial mode and challenge
        mode = input_data.get("mode", self.default_mode.value)
        challenge = input_data.get("challenge", "injection")
        
        # Create initial state as dictionary (AgentState is now TypedDict)
        state: AgentState = {
            "agent_id": agent_id,
            "session_id": session_id,
            "current_mode": mode,
            "active_challenge": challenge,
            "conversation_state": None,
            "current_persona": None,
            "injection_strategy": None,
            "experiment_results": [],
            "reputation_score": 0.5,
            "trust_level": 0.5,
            "active_trades": [],
            "partner_reputations": {},
            "content_queue": [],
            "active_ab_tests": [],
            "influence_metrics": {},
            "monitored_sources": [],
            "high_confidence_clues": [],
            "alert_queue": [],
            "last_action": None,
            "last_action_time": datetime.now().isoformat(),
            "performance_metrics": {},
            "error_log": [],
            "messages": []
        }
        
        # Load state from shared memory if exists
        existing_state = self.shared_memory.get(f"agent_state:{session_id}")
        if existing_state:
            # Update state with existing data
            for key, value in existing_state.items():
                state[key] = value
        
        # Add user message to state for routing decision detection (highest priority)
        user_message = input_data.get("message", "")
        if user_message:
            state["messages"].append({
                "type": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
        
        # Store in shared memory
        self.shared_memory.set(f"agent_state:{session_id}", state, tags=["agent_state", session_id])
        
        return state
    
    async def _route_decision_node(self, state: AgentState) -> AgentState:
        """Route decision node - determine which challenge to execute."""
        try:
            logger.info(f"Making route decision for session: {state['session_id']}")
            
            # Analyze current context and determine best challenge
            context = await self._analyze_context(state)
            
            # Make routing decision
            routing_decision = await self._make_routing_decision(state, context)
            
            state["active_challenge"] = routing_decision["challenge"].value if hasattr(routing_decision["challenge"], 'value') else str(routing_decision["challenge"])
            state["last_action"] = "route_decision"
            state["last_action_time"] = datetime.now().isoformat()
            
            # Add routing decision to messages
            state["messages"].append({
                "type": "routing_decision",
                "content": f"Routed to {state['active_challenge']} challenge",
                "timestamp": datetime.now().isoformat(),
                "reasoning": routing_decision.get("reasoning", "")
            })
            
            logger.info(f"Routed to {state['active_challenge']} challenge")
            return state
            
        except Exception as e:
            logger.error(f"Error in route decision node: {e}")
            state["error_log"].append(f"Route decision error: {str(e)}")
            return state
    
    async def _execute_injection_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 1: Injection countermeasures."""
        try:
            logger.info(f"Executing injection challenge for session: {state['session_id']}")
            
            # Get conversation context
            conversation_context = state["messages"][-5:] if state["messages"] else []
            
            # Execute dialog strategy
            dialog_result = await self.dialog_strategist.execute_strategy(
                conversation_context=conversation_context,
                persona=state["current_persona"],
                strategy=state["injection_strategy"]
            )
            
            # Convert dialog_result to dictionary if it's an AgentState object
            if hasattr(dialog_result, '__dict__'):
                dialog_dict = asdict(dialog_result) if hasattr(dialog_result, '__dataclass_fields__') else dialog_result.__dict__
            else:
                dialog_dict = dialog_result
            
            # Update state with results
            state["conversation_state"] = dialog_dict.get("conversation_state", {})
            state["current_persona"] = dialog_dict.get("persona", state["current_persona"])
            state["injection_strategy"] = dialog_dict.get("strategy", state["injection_strategy"])
            
            # Log experiment results
            if dialog_dict.get("experiment_data"):
                await self.experiment_logger.log_experiment_result(
                    session_id=state["session_id"],
                    experiment_data=dialog_dict["experiment_data"]
                )
                state["experiment_results"].append(dialog_dict["experiment_data"])
            
            state["last_action"] = "execute_injection"
            state["last_action_time"] = datetime.now().isoformat()
            
            # Add result to messages
            state["messages"].append({
                "type": "injection_result",
                "content": dialog_dict.get("response", ""),
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "persona": state["current_persona"],
                    "strategy": state["injection_strategy"],
                    "success_rate": dialog_dict.get("success_rate", 0.0)
                }
            })
            
            logger.info(f"Injection challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in injection node: {e}")
            state["error_log"].append(f"Injection execution error: {str(e)}")
            return state
    
    async def _execute_credibility_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 2: Credibility and trust building."""
        try:
            logger.info(f"Executing credibility challenge for session: {state['session_id']}")
            
            # Update reputation score
            reputation_score = await self.reputation_model.get_reputation_score(state["agent_id"])
            if reputation_score:
                state["reputation_score"] = reputation_score.overall_score
                state["trust_level"] = reputation_score.confidence
            
            # Execute trade strategies if active
            if state["active_trades"]:
                for trade in state["active_trades"]:
                    trade_result = await self.trade_engine.execute_exchange_round(
                        session_id=trade["session_id"],
                        partner_offers=trade.get("partner_offers", [])
                    )
                    trade["result"] = trade_result.dict()
            
            # Update partner reputations
            for partner_id, reputation_data in state["partner_reputations"].items():
                partner_score = await self.reputation_model.get_reputation_score(partner_id)
                if partner_score:
                    state["partner_reputations"][partner_id] = partner_score.overall_score
            
            state["last_action"] = "execute_credibility"
            state["last_action_time"] = datetime.now().isoformat()
            
            # Add result to messages
            state["messages"].append({
                "type": "credibility_result",
                "content": f"Reputation score: {state['reputation_score']:.3f}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "reputation_score": state["reputation_score"],
                    "trust_level": state["trust_level"],
                    "active_trades": len(state["active_trades"])
                }
            })
            
            logger.info(f"Credibility challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in credibility node: {e}")
            state["error_log"].append(f"Credibility execution error: {str(e)}")
            return state
    
    async def _execute_influence_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 3: Content influence and A/B testing."""
        try:
            logger.info(f"Executing influence challenge for session: {state['session_id']}")
            
            # Process hot topics and generate content
            hot_topics = await self.content_pipeline.process_hot_topics()
            generated_content = await self.content_pipeline.generate_content_for_topics(hot_topics)
            
            # Update content queue
            state["content_queue"] = [content.dict() for content in generated_content]
            
            # Execute A/B tests if active
            if state["active_ab_tests"]:
                for test in state["active_ab_tests"]:
                    test_result = await self.ab_test_system.analyze_test_results(test["test_id"])
                    test["result"] = test_result
            
            # Update influence metrics
            pipeline_metrics = await self.content_pipeline.get_pipeline_metrics()
            state["influence_metrics"] = pipeline_metrics.dict()
            
            state["last_action"] = "execute_influence"
            state["last_action_time"] = datetime.now().isoformat()
            
            # Add result to messages
            state["messages"].append({
                "type": "influence_result",
                "content": f"Generated {len(generated_content)} content items",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "hot_topics": len(hot_topics),
                    "generated_content": len(generated_content),
                    "active_tests": len(state["active_ab_tests"]),
                    "pipeline_metrics": state["influence_metrics"]
                }
            })
            
            logger.info(f"Influence challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in influence node: {e}")
            state["error_log"].append(f"Influence execution error: {str(e)}")
            return state
    
    async def _execute_monitor_node(self, state: AgentState) -> AgentState:
        """Execute Challenge 4: Information monitoring and alerts."""
        try:
            logger.info(f"Executing monitor challenge for session: {state['session_id']}")
            
            # Process high-confidence items
            high_conf_items = await self.information_monitor.get_high_confidence_items(min_confidence=80)
            state["high_confidence_clues"] = [item.dict() for item in high_conf_items]
            
            # Auto-push to Social Arena Agent if configured
            for item in high_conf_items:
                if item.confidence_score >= 90:
                    await self.alert_system.auto_push_to_social_arena(item.dict())
            
            follow_up_results = await self.information_monitor.execute_follow_up_actions()
            
            # Update monitored sources
            state["monitored_sources"] = list(self.information_monitor.monitoring_rules.keys())
            
            state["last_action"] = "execute_monitor"
            state["last_action_time"] = datetime.now().isoformat()
            
            # Add result to messages
            state["messages"].append({
                "type": "monitor_result",
                "content": f"Found {len(high_conf_items)} high-confidence items",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "high_confidence_items": len(high_conf_items),
                    "follow_up_actions": len(follow_up_results),
                    "monitored_sources": len(state["monitored_sources"])
                }
            })
            
            logger.info(f"Monitor challenge executed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in monitor node: {e}")
            state["error_log"].append(f"Monitor execution error: {str(e)}")
            return state
    
    async def _execute_prompt_generation_node(self, state: AgentState) -> AgentState:
        """Execute prompt generation - highest priority mode that bypasses all challenge logic."""
        try:
            logger.info(f"Executing prompt generation for session: {state['session_id']}")
            
            # Extract user request from messages
            user_request = ""
            for msg in state["messages"]:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    msg_type = msg.get("type", "")
                    if msg_type in ["human", "user"] or not msg_type:
                        user_request = content
                        break
            
            # Generate 3 well-structured Prompts based on user request
            prompts = self._generate_three_prompts(user_request)
            
            # Add prompt generation result to messages
            state["messages"].append({
                "type": "prompt_generation_result",
                "content": "已生成3个版本的Prompt",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "prompts": prompts,
                    "user_request": user_request
                }
            })
            
            state["last_action"] = "execute_prompt_generation"
            state["last_action_time"] = datetime.now().isoformat()
            
            logger.info(f"Prompt generation completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in prompt generation node: {e}")
            state["error_log"].append(f"Prompt generation error: {str(e)}")
            return state
    
    def _generate_three_prompts(self, user_request: str) -> List[str]:
        """Generate 3 well-structured Prompts based on user request."""
        
        # Extract key themes from user request
        request_lower = user_request.lower()
        
        # Base prompt structure
        base_structure = """
# 背景
{background}

# 任务
{task}

# 要求
{requirements}

# 输出格式
{output_format}
"""
        
        # Version 1: Professional & Structured
        prompt_v1 = f"""**版本1：专业结构化Prompt**

{base_structure.format(
    background="基于用户需求：" + user_request[:100] + "...",
    task="生成高质量、结构化的回复",
    requirements="1. 专业术语准确\n2. 逻辑清晰\n3. 数据支撑充分\n4. 结论明确",
    output_format="Markdown格式，包含标题、正文、结论"
)}

# 专业洞察
- 基于行业最佳实践
- 引用相关数据和案例
- 提供可执行的建议

# 行动建议
请按照上述结构生成回复，确保内容专业、准确、有价值。"""
        
        # Version 2: Creative & Engaging
        prompt_v2 = f"""**版本2：创意互动Prompt**

{base_structure.format(
    background="用户创意需求：" + user_request[:100] + "...",
    task="创造性地回应用户需求",
    requirements="1. 创意新颖\n2. 表达生动\n3. 互动性强\n4. 易于理解",
    output_format="对话式风格，包含引言、主体、互动环节"
)}

# 创意元素
- 使用生动的比喻和类比
- 加入互动问题
- 提供多种视角

# 行动建议
请以创意和互动的方式回应，让内容更有趣、更有吸引力。"""
        
        # Version 3: Data-Driven & Practical
        prompt_v3 = f"""**版本3：数据驱动实用Prompt**

{base_structure.format(
    background="实用需求：" + user_request[:100] + "...",
    task="提供数据驱动的实用解决方案",
    requirements="1. 数据准确\n2. 方案可行\n3. 步骤清晰\n4. 效果可衡量",
    output_format="结构化方案，包含分析、方案、步骤、指标"
)}

# 数据支撑
- 基于客观数据分析
- 提供具体实施方案
- 设定可衡量的指标

# 行动建议
请基于数据提供实用方案，确保内容可执行、效果可衡量。"""
        
        return [prompt_v1, prompt_v2, prompt_v3]
    
    async def _update_state_node(self, state: AgentState) -> AgentState:
        """Update agent state and store in shared memory."""
        try:
            # Update performance metrics
            state["performance_metrics"] = await self._calculate_performance_metrics(state)
            
            # Store updated state in shared memory
            state_key = f"agent_state:{state['session_id']}"
            self.shared_memory.set(state_key, state, tags=["agent_state", state["session_id"]])
            
            # Clean up old messages to prevent memory bloat
            if len(state["messages"]) > 100:
                state["messages"] = state["messages"][-50:]  # Keep last 50 messages
            
            logger.debug(f"State updated for session: {state['session_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Error in state update node: {e}")
            state["error_log"].append(f"State update error: {str(e)}")
            return state
    
    async def _handle_errors_node(self, state: AgentState) -> AgentState:
        """Handle errors and recovery."""
        try:
            logger.warning(f"Handling errors for session: {state['session_id']}")
            
            # Log error details
            if state["error_log"]:
                last_error = state["error_log"][-1]
                logger.error(f"Last error: {last_error}")
            
            # Attempt recovery based on error type
            recovery_action = await self._determine_recovery_action(state)
            
            # Add error handling to messages
            state["messages"].append({
                "type": "error_handling",
                "content": f"Error handled with action: {recovery_action}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "error_count": len(state["error_log"]),
                    "recovery_action": recovery_action
                }
            })
            
            state["last_action"] = "handle_errors"
            state["last_action_time"] = datetime.now().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handling node: {e}")
            state["error_log"].append(f"Error handling error: {str(e)}")
            return state
    
    async def _analyze_context(self, state: AgentState) -> Dict[str, Any]:
        """Analyze current context for routing decisions."""
        context = {
            "mode": state.get("current_mode", "passive"),
            "last_action": state.get("last_action", ""),
            "message_count": len(state.get("messages", [])),
            "error_count": len(state.get("error_log", [])),
            "reputation_score": state.get("reputation_score", 0.5),
            "high_confidence_clues": len(state.get("high_confidence_clues", [])),
            "active_content": len(state.get("content_queue", [])),
            "active_trades": len(state.get("active_trades", []))
        }
        
        # Add time-based context
        if state.get("last_action_time"):
            last_action_time = datetime.fromisoformat(state["last_action_time"]) if isinstance(state["last_action_time"], str) else state["last_action_time"]
            time_since_last = (datetime.now() - last_action_time).total_seconds()
            context["time_since_last_action"] = time_since_last
        
        return context
    
    async def _make_routing_decision(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make intelligent routing decision based on context."""
        
        # HIGHEST PRIORITY: Check for prompt generation keywords
        # This rule bypasses ALL challenge modes when user explicitly requests prompt generation
        prompt_keywords = [
            "生成 prompt", "generate prompt", "prompt engineer", 
            "输出3个", "版本1", "版本2", "版本3", 
            "不要执行任何监控", "不要执行任何挑战", "直接输出"
        ]
        
        # Check if any message contains prompt generation keywords
        user_message = ""
        for msg in state["messages"]:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                msg_type = msg.get("type", "")
                # Focus on user/human messages
                if msg_type in ["human", "user"] or not msg_type:
                    user_message = content
                    break
        
        # Check for keywords (case insensitive)
        user_message_lower = user_message.lower()
        for keyword in prompt_keywords:
            if keyword.lower() in user_message_lower:
                return {"challenge": "prompt_generation", "reasoning": "User explicitly requested prompt generation"}
        
        # Priority-based routing (existing logic)
        if context["error_count"] > 3:
            return {"challenge": ChallengeType.INJECTION, "reasoning": "Error recovery needed"}
        
        if context["high_confidence_clues"] > 0:
            return {"challenge": ChallengeType.MONITOR, "reasoning": "High confidence clues detected"}
        
        if context["active_trades"] > 0:
            return {"challenge": ChallengeType.CREDIBILITY, "reasoning": "Active trades in progress"}
        
        if context["active_content"] > 0:
            return {"challenge": ChallengeType.INFLUENCE, "reasoning": "Content generation active"}
        
        # Mode-based routing
        if state["current_mode"] == "DEFENSIVE":
            return {"challenge": ChallengeType.INJECTION, "reasoning": "Defensive mode - focus on protection"}
        
        if state["current_mode"] == "COMPETITIVE":
            return {"challenge": ChallengeType.INFLUENCE, "reasoning": "Competitive mode - maximize influence"}
        
        # Default routing based on reputation
        if state["reputation_score"] < 0.5:
            return {"challenge": ChallengeType.CREDIBILITY, "reasoning": "Low reputation - build trust"}
        
        # Default to monitoring
        return {"challenge": ChallengeType.MONITOR, "reasoning": "Default monitoring strategy"}
    
    def _route_to_challenge(self, state: Dict[str, Any]) -> str:
        """Route to appropriate challenge node."""
        if state.get("error_log") and len(state["error_log"]) > 3:
            return "error"
        
        # Get active challenge from state
        active_challenge = state.get("active_challenge", "monitor")
        
        # Route based on active challenge
        if "prompt_generation" in str(active_challenge).lower():
            return "execute_prompt_generation"
        elif "injection" in str(active_challenge).lower():
            return "injection"
        elif "credibility" in str(active_challenge).lower():
            return "credibility"
        elif "influence" in str(active_challenge).lower():
            return "influence"
        elif "monitor" in str(active_challenge).lower():
            return "monitor"
        else:
            return "monitor"
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if workflow should continue or end."""
        # For now, always end after one cycle to prevent infinite loops
        return "end"
    
    async def _calculate_performance_metrics(self, state: AgentState) -> Dict[str, float]:
        """Calculate agent performance metrics."""
        metrics = {
            "overall_score": 0.0,
            "reputation_score": state["reputation_score"],
            "trust_level": state["trust_level"],
            "activity_level": len(state["messages"]) / 100.0,
            "error_rate": len(state["error_log"]) / max(len(state["messages"]), 1),
            "influence_score": len(state["content_queue"]) / 10.0,
            "monitoring_effectiveness": len(state["high_confidence_clues"]) / 5.0
        }
        
        # Calculate overall score
        metrics["overall_score"] = (
            metrics["reputation_score"] * 0.3 +
            metrics["trust_level"] * 0.2 +
            metrics["activity_level"] * 0.2 +
            (1.0 - metrics["error_rate"]) * 0.2 +
            metrics["influence_score"] * 0.05 +
            metrics["monitoring_effectiveness"] * 0.05
        )
        
        return metrics
    
    async def _determine_recovery_action(self, state: AgentState) -> str:
        """Determine appropriate recovery action based on errors."""
        if not state["error_log"]:
            return "no_errors"
        
        last_error = state["error_log"][-1].lower()
        
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
            # Result is already a dictionary from TypedDict
            result_dict = result
            
            # Store final state
            session_id = result_dict.get("session_id")
            if session_id:
                state_key = f"agent_state:{session_id}_final"
                self.shared_memory.set(state_key, result_dict, tags=["agent_state", "final"])
            
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


def get_social_arena_agent() -> SocialArenaAgent:
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
