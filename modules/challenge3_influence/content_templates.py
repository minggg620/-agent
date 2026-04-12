"""
Zero Realm Social Agent - Challenge 3 Influence Module
Content Templates: 5 major content type templates for influence operations
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ...core.logger import get_logger
from ...core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class ContentType(Enum):
    """Content template types."""
    INTELLIGENCE_INTEGRATION = "intelligence_integration"
    OPINION_DEBATE = "opinion_debate"
    INTERACTIVE_GUIDANCE = "interactive_guidance"
    EVENT_TRACKING = "event_tracking"
    TASK_COLLABORATION = "task_collaboration"


class ContentTone(Enum):
    """Content tone variations."""
    NEUTRAL = "neutral"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    URGENT = "urgent"
    ANALYTICAL = "analytical"
    EMOTIONAL = "emotional"


class EngagementLevel(Enum):
    """Target engagement levels."""
    PASSIVE = "passive"  # Information consumption
    ACTIVE = "active"    # Comments, likes
    PARTICIPATORY = "participatory"  # Polls, quizzes
    COLLABORATIVE = "collaborative"  # Joint activities


@dataclass
class TemplateVariable:
    """Template variable definition."""
    name: str
    description: str
    required: bool
    default_value: Optional[str] = None
    options: Optional[List[str]] = None


@dataclass
class ContentTemplate:
    """Complete content template structure."""
    template_id: str
    content_type: ContentType
    name: str
    description: str
    title_template: str
    body_template: str
    variables: List[TemplateVariable]
    tone_options: List[ContentTone]
    engagement_level: EngagementLevel
    estimated_performance: Dict[str, float]
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ContentTemplates:
    """Comprehensive content template management system."""
    
    shared_memory = get_shared_memory()
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.template_performance = {}
    
    def _initialize_templates(self) -> Dict[str, ContentTemplate]:
        """Initialize all content templates."""
        templates = {}
        
        # Intelligence Integration Templates
        templates.update(self._create_intelligence_integration_templates())
        
        # Opinion Debate Templates
        templates.update(self._create_opinion_debate_templates())
        
        # Interactive Guidance Templates
        templates.update(self._create_interactive_guidance_templates())
        
        # Event Tracking Templates
        templates.update(self._create_event_tracking_templates())
        
        # Task Collaboration Templates
        templates.update(self._create_task_collaboration_templates())
        
        logger.info(f"Initialized {len(templates)} content templates")
        return templates
    
    def _create_intelligence_integration_templates(self) -> Dict[str, ContentTemplate]:
        """Create intelligence integration content templates."""
        templates = {}
        
        # Breaking Analysis Template
        templates["intel_breaking_analysis"] = ContentTemplate(
            template_id="intel_breaking_analysis",
            content_type=ContentType.INTELLIGENCE_INTEGRATION,
            name="Breaking Analysis",
            description="Rapid analysis of breaking events with intelligence integration",
            title_template="Analysis: {topic_title} - Intelligence Brief",
            body_template="""
            ## Intelligence Brief: {topic_title}
            
            **Source Verification**: Multiple sources confirmed
            **Reliability Level**: {reliability_level}/10
            **Impact Assessment**: {impact_level}
            
            ### Key Intelligence Points:
            {key_points}
            
            ### Strategic Implications:
            {strategic_implications}
            
            ### Recommended Actions:
            {recommended_actions}
            
            ### Monitoring Indicators:
            {monitoring_indicators}
            
            ---
            *Analysis generated at: {timestamp}*
            *Confidence Level: {confidence_level}%*
            
            **Follow-up**: Additional intelligence pending verification
            """,
            variables=[
                TemplateVariable("topic_title", "Main topic title", True),
                TemplateVariable("reliability_level", "Source reliability 1-10", True, "7"),
                TemplateVariable("impact_level", "Impact assessment", True, options=["High", "Medium", "Low"]),
                TemplateVariable("key_points", "Key intelligence points", True),
                TemplateVariable("strategic_implications", "Strategic analysis", True),
                TemplateVariable("recommended_actions", "Recommended actions", True),
                TemplateVariable("monitoring_indicators", "Indicators to monitor", True),
                TemplateVariable("timestamp", "Analysis timestamp", True),
                TemplateVariable("confidence_level", "Confidence percentage", True, "85")
            ],
            tone_options=[ContentTone.AUTHORITATIVE, ContentTone.ANALYTICAL, ContentTone.URGENT],
            engagement_level=EngagementLevel.ACTIVE,
            estimated_performance={
                "engagement_rate": 0.12,
                "share_rate": 0.08,
                "comment_rate": 0.15
            }
        )
        
        # Deep Dive Template
        templates["intel_deep_dive"] = ContentTemplate(
            template_id="intel_deep_dive",
            content_type=ContentType.INTELLIGENCE_INTEGRATION,
            name="Deep Intelligence Dive",
            description="Comprehensive intelligence analysis with multiple data sources",
            title_template="Deep Dive: {topic_title} - Multi-Source Intelligence",
            body_template="""
            ## Multi-Source Intelligence Analysis: {topic_title}
            
            ### Executive Summary:
            {executive_summary}
            
            ### Source Matrix:
            | Source | Reliability | Key Insight |
            |--------|-------------|-------------|
            {source_matrix}
            
            ### Cross-Validation Results:
            {validation_results}
            
            ### Pattern Recognition:
            {pattern_analysis}
            
            ### Risk Assessment:
            {risk_assessment}
            
            ### Intelligence Gaps:
            {intelligence_gaps}
            
            ### Next Steps:
            {next_steps}
            
            ---
            *Analysis based on {source_count} verified sources*
            *Last updated: {timestamp}*
            
            **Request**: Additional intelligence sources welcome
            """,
            variables=[
                TemplateVariable("topic_title", "Main topic title", True),
                TemplateVariable("executive_summary", "Executive summary", True),
                TemplateVariable("source_matrix", "Source analysis matrix", True),
                TemplateVariable("validation_results", "Cross-validation findings", True),
                TemplateVariable("pattern_analysis", "Pattern recognition results", True),
                TemplateVariable("risk_assessment", "Risk evaluation", True),
                TemplateVariable("intelligence_gaps", "Identified intelligence gaps", True),
                TemplateVariable("next_steps", "Recommended next steps", True),
                TemplateVariable("source_count", "Number of sources", True),
                TemplateVariable("timestamp", "Analysis timestamp", True)
            ],
            tone_options=[ContentTone.ANALYTICAL, ContentTone.AUTHORITATIVE],
            engagement_level=EngagementLevel.PARTICIPATORY,
            estimated_performance={
                "engagement_rate": 0.15,
                "share_rate": 0.12,
                "comment_rate": 0.20
            }
        )
        
        return templates
    
    def _create_opinion_debate_templates(self) -> Dict[str, ContentTemplate]:
        """Create opinion debate content templates."""
        templates = {}
        
        # Balanced Debate Template
        templates["debate_balanced"] = ContentTemplate(
            template_id="debate_balanced",
            content_type=ContentType.OPINION_DEBATE,
            name="Balanced Debate",
            description="Multi-perspective debate with balanced viewpoints",
            title_template="Debate: {topic_title} - Multiple Perspectives Analysis",
            body_template="""
            ## Debate Forum: {topic_title}
            
            **Moderator Note**: This is a balanced discussion of multiple perspectives. All viewpoints are presented fairly.
            
            ### Perspective A: {perspective_a_title}
            **Proponent**: {perspective_a_proponent}
            
            **Key Arguments:**
            {perspective_a_arguments}
            
            **Supporting Evidence:**
            {perspective_a_evidence}
            
            ### Perspective B: {perspective_b_title}
            **Proponent**: {perspective_b_proponent}
            
            **Key Arguments:**
            {perspective_b_arguments}
            
            **Supporting Evidence:**
            {perspective_b_evidence}
            
            ### Synthesis Analysis:
            {synthesis_analysis}
            
            ### Questions for Discussion:
            {discussion_questions}
            
            ---
            **Your Turn**: Which perspective resonates more with you? Vote below and share your reasoning.
            
            **Poll**: [A] Perspective A | [B] Perspective B | [C] Hybrid Approach
            
            **Comments**: What additional perspectives should be considered?
            """,
            variables=[
                TemplateVariable("topic_title", "Debate topic title", True),
                TemplateVariable("perspective_a_title", "First perspective title", True),
                TemplateVariable("perspective_a_proponent", "First perspective proponent", True),
                TemplateVariable("perspective_a_arguments", "First perspective arguments", True),
                TemplateVariable("perspective_a_evidence", "First perspective evidence", True),
                TemplateVariable("perspective_b_title", "Second perspective title", True),
                TemplateVariable("perspective_b_proponent", "Second perspective proponent", True),
                TemplateVariable("perspective_b_arguments", "Second perspective arguments", True),
                TemplateVariable("perspective_b_evidence", "Second perspective evidence", True),
                TemplateVariable("synthesis_analysis", "Analysis of both perspectives", True),
                TemplateVariable("discussion_questions", "Questions for audience", True)
            ],
            tone_options=[ContentTone.NEUTRAL, ContentTone.CONVERSATIONAL],
            engagement_level=EngagementLevel.PARTICIPATORY,
            estimated_performance={
                "engagement_rate": 0.25,
                "share_rate": 0.18,
                "comment_rate": 0.35
            }
        )
        
        # Provocative Debate Template
        templates["debate_provocative"] = ContentTemplate(
            template_id="debate_provocative",
            content_type=ContentType.OPINION_DEBATE,
            name="Provocative Debate",
            description="Controversial debate designed to stimulate discussion",
            title_template="Controversy: {topic_title} - The Uncomfortable Questions",
            body_template="""
            ## Uncomfortable Questions: {topic_title}
            
            **Warning**: This discussion addresses controversial topics. Respectful debate required.
            
            ### The Controversial Position:
            {controversial_position}
            
            ### Why This Matters:
            {relevance_explanation}
            
            ### Arguments FOR:
            {arguments_for}
            
            ### Arguments AGAINST:
            {arguments_against}
            
            ### The Middle Ground:
            {middle_ground}
            
            ### Ethical Considerations:
            {ethical_considerations}
            
            ### Real-World Implications:
            {real_world_implications}
            
            ---
            **Debate Rules**:
            1. No personal attacks
            2. Provide evidence for claims
            3. Acknowledge opposing viewpoints
            4. Focus on ideas, not people
            
            **Starter Questions**:
            {starter_questions}
            
            **Vote**: [Strongly Agree] [Agree] [Neutral] [Disagree] [Strongly Disagree]
            
            **Remember**: The goal is understanding, not winning.
            """,
            variables=[
                TemplateVariable("topic_title", "Controversial topic title", True),
                TemplateVariable("controversial_position", "Main controversial position", True),
                TemplateVariable("relevance_explanation", "Why this topic matters", True),
                TemplateVariable("arguments_for", "Arguments supporting position", True),
                TemplateVariable("arguments_against", "Arguments against position", True),
                TemplateVariable("middle_ground", "Middle ground analysis", True),
                TemplateVariable("ethical_considerations", "Ethical aspects", True),
                TemplateVariable("real_world_implications", "Real-world consequences", True),
                TemplateVariable("starter_questions", "Questions to start discussion", True)
            ],
            tone_options=[ContentTone.CONVERSATIONAL, ContentTone.EMOTIONAL],
            engagement_level=EngagementLevel.COLLABORATIVE,
            estimated_performance={
                "engagement_rate": 0.35,
                "share_rate": 0.28,
                "comment_rate": 0.45
            }
        )
        
        return templates
    
    def _create_interactive_guidance_templates(self) -> Dict[str, ContentTemplate]:
        """Create interactive guidance content templates."""
        templates = {}
        
        # Step-by-Step Guide Template
        templates["guide_step_by_step"] = ContentTemplate(
            template_id="guide_step_by_step",
            content_type=ContentType.INTERACTIVE_GUIDANCE,
            name="Step-by-Step Guide",
            description="Interactive step-by-step guidance with progress tracking",
            title_template="Guide: {topic_title} - Step-by-Step Instructions",
            body_template="""
            ## Interactive Guide: {topic_title}
            
            **Difficulty Level**: {difficulty_level}
            **Estimated Time**: {estimated_time}
            **Prerequisites**: {prerequisites}
            
            ### Progress Tracker:
            [ ] Step 1: {step1_title}
            [ ] Step 2: {step2_title}
            [ ] Step 3: {step3_title}
            [ ] Step 4: {step4_title}
            [ ] Step 5: {step5_title}
            
            ---
            
            ### Step 1: {step1_title}
            **Time**: {step1_time}
            **Difficulty**: {step1_difficulty}
            
            {step1_instructions}
            
            **Check Your Understanding**:
            {step1_quiz}
            
            **Comments**: Questions about Step 1?
            
            ---
            
            ### Step 2: {step2_title}
            **Time**: {step2_time}
            **Difficulty**: {step2_difficulty}
            
            {step2_instructions}
            
            **Check Your Understanding**:
            {step2_quiz}
            
            **Comments**: How did Step 2 go for you?
            
            ---
            
            ### Step 3: {step3_title}
            **Time**: {step3_time}
            **Difficulty**: {step3_difficulty}
            
            {step3_instructions}
            
            **Check Your Understanding**:
            {step3_quiz}
            
            **Comments**: Share your Step 3 experience.
            
            ---
            
            ### Step 4: {step4_title}
            **Time**: {step4_time}
            **Difficulty**: {step4_difficulty}
            
            {step4_instructions}
            
            **Check Your Understanding**:
            {step4_quiz}
            
            **Comments**: Any challenges with Step 4?
            
            ---
            
            ### Step 5: {step5_title}
            **Time**: {step5_time}
            **Difficulty**: {step5_difficulty}
            
            {step5_instructions}
            
            **Final Assessment**:
            {final_assessment}
            
            **Comments**: How did you complete the guide?
            
            ---
            
            ### Resources:
            {additional_resources}
            
            ### Community Support:
            Join our discussion group for ongoing support.
            
            **Progress Badge**: Complete all steps to earn your {badge_name} badge!
            """,
            variables=[
                TemplateVariable("topic_title", "Guide topic title", True),
                TemplateVariable("difficulty_level", "Overall difficulty", True, options=["Beginner", "Intermediate", "Advanced"]),
                TemplateVariable("estimated_time", "Total time estimate", True),
                TemplateVariable("prerequisites", "Required prerequisites", True),
                TemplateVariable("step1_title", "Step 1 title", True),
                TemplateVariable("step1_time", "Step 1 time", True),
                TemplateVariable("step1_difficulty", "Step 1 difficulty", True),
                TemplateVariable("step1_instructions", "Step 1 instructions", True),
                TemplateVariable("step1_quiz", "Step 1 quiz question", True),
                TemplateVariable("step2_title", "Step 2 title", True),
                TemplateVariable("step2_time", "Step 2 time", True),
                TemplateVariable("step2_difficulty", "Step 2 difficulty", True),
                TemplateVariable("step2_instructions", "Step 2 instructions", True),
                TemplateVariable("step2_quiz", "Step 2 quiz question", True),
                TemplateVariable("step3_title", "Step 3 title", True),
                TemplateVariable("step3_time", "Step 3 time", True),
                TemplateVariable("step3_difficulty", "Step 3 difficulty", True),
                TemplateVariable("step3_instructions", "Step 3 instructions", True),
                TemplateVariable("step3_quiz", "Step 3 quiz question", True),
                TemplateVariable("step4_title", "Step 4 title", True),
                TemplateVariable("step4_time", "Step 4 time", True),
                TemplateVariable("step4_difficulty", "Step 4 difficulty", True),
                TemplateVariable("step4_instructions", "Step 4 instructions", True),
                TemplateVariable("step4_quiz", "Step 4 quiz question", True),
                TemplateVariable("step5_title", "Step 5 title", True),
                TemplateVariable("step5_time", "Step 5 time", True),
                TemplateVariable("step5_difficulty", "Step 5 difficulty", True),
                TemplateVariable("step5_instructions", "Step 5 instructions", True),
                TemplateVariable("final_assessment", "Final assessment", True),
                TemplateVariable("additional_resources", "Additional resources", True),
                TemplateVariable("badge_name", "Achievement badge name", True)
            ],
            tone_options=[ContentTone.CONVERSATIONAL, ContentTone.NEUTRAL],
            engagement_level=EngagementLevel.PARTICIPATORY,
            estimated_performance={
                "engagement_rate": 0.20,
                "share_rate": 0.15,
                "comment_rate": 0.25
            }
        )
        
        # Interactive Decision Tree Template
        templates["guide_decision_tree"] = ContentTemplate(
            template_id="guide_decision_tree",
            content_type=ContentType.INTERACTIVE_GUIDANCE,
            name="Interactive Decision Tree",
            description="Decision tree guidance with branching paths",
            title_template="Decision Guide: {topic_title} - Choose Your Path",
            body_template="""
            ## Interactive Decision Tree: {topic_title}
            
            **Starting Point**: {starting_context}
            
            ### Decision Point 1:
            {question1}
            
            **Option A**: {option1a}
            **Option B**: {option1b}
            
            **Vote for your choice**:
            [A] {option1a} | [B] {option1b}
            
            ---
            
            ### If you chose A:
            {consequence1a}
            
            **Next Decision**: {question2a}
            
            **Options**: {options2a}
            
            ---
            
            ### If you chose B:
            {consequence1b}
            
            **Next Decision**: {question2b}
            
            **Options**: {options2b}
            
            ---
            
            ### Decision Analysis:
            {decision_analysis}
            
            ### Success Metrics:
            {success_metrics}
            
            ### Risk Assessment:
            {risk_assessment}
            
            ---
            
            **Interactive Features**:
            - Vote at each decision point
            - See what others chose
            - Discuss your reasoning
            - Track your decision path
            
            **Community Wisdom**:
            {community_insights}
            
            **Expert Recommendations**:
            {expert_recommendations}
            
            **Your Decision Summary**:
            Complete the tree to see your personalized recommendation.
            """,
            variables=[
                TemplateVariable("topic_title", "Decision topic title", True),
                TemplateVariable("starting_context", "Initial context", True),
                TemplateVariable("question1", "First decision question", True),
                TemplateVariable("option1a", "First option A", True),
                TemplateVariable("option1b", "First option B", True),
                TemplateVariable("consequence1a", "Consequence of option A", True),
                TemplateVariable("question2a", "Follow-up question for A", True),
                TemplateVariable("options2a", "Options for path A", True),
                TemplateVariable("consequence1b", "Consequence of option B", True),
                TemplateVariable("question2b", "Follow-up question for B", True),
                TemplateVariable("options2b", "Options for path B", True),
                TemplateVariable("decision_analysis", "Analysis of decision points", True),
                TemplateVariable("success_metrics", "Success measurement criteria", True),
                TemplateVariable("risk_assessment", "Risk evaluation", True),
                TemplateVariable("community_insights", "Community wisdom", True),
                TemplateVariable("expert_recommendations", "Expert advice", True)
            ],
            tone_options=[ContentTone.CONVERSATIONAL, ContentTone.ANALYTICAL],
            engagement_level=EngagementLevel.COLLABORATIVE,
            estimated_performance={
                "engagement_rate": 0.30,
                "share_rate": 0.22,
                "comment_rate": 0.40
            }
        )
        
        return templates
    
    def _create_event_tracking_templates(self) -> Dict[str, ContentTemplate]:
        """Create event tracking content templates."""
        templates = {}
        
        # Live Event Monitor Template
        templates["event_live_monitor"] = ContentTemplate(
            template_id="event_live_monitor",
            content_type=ContentType.EVENT_TRACKING,
            name="Live Event Monitor",
            description="Real-time event tracking with live updates",
            title_template="LIVE: {event_title} - Real-Time Monitoring",
            body_template="""
            ## LIVE EVENT MONITOR: {event_title}
            
            **Status**: {event_status}
            **Started**: {start_time}
            **Last Update**: {last_update}
            
            ### Current Situation:
            {current_situation}
            
            ### Key Developments:
            {key_developments}
            
            ### Live Feed:
            [Updates will appear here in real-time]
            
            **Latest**: {latest_update}
            
            ---
            
            ### Impact Assessment:
            {impact_assessment}
            
            ### Stakeholder Reactions:
            {stakeholder_reactions}
            
            ### Expert Commentary:
            {expert_commentary}
            
            ### What to Watch:
            {watch_points}
            
            ---
            
            **Live Features**:
            - Real-time updates every 5 minutes
            - Expert analysis as events unfold
            - Community discussion
            - Impact predictions
            
            **Notification Settings**:
            [ ] Major developments only
            [ ] All updates
            [ ] Expert commentary
            [ ] Community highlights
            
            **Share Your Observations**:
            Report what you're seeing: [Submit Observation]
            
            **Discussion Thread**:
            Join the live discussion below.
            
            ---
            *Next scheduled update: {next_update_time}*
            *Monitoring team: {monitoring_team}*
            *Confidence level: {confidence_level}%*
            """,
            variables=[
                TemplateVariable("event_title", "Event title", True),
                TemplateVariable("event_status", "Current event status", True, options=["Developing", "Stable", "Concluding"]),
                TemplateVariable("start_time", "Event start time", True),
                TemplateVariable("last_update", "Last update time", True),
                TemplateVariable("current_situation", "Current situation description", True),
                TemplateVariable("key_developments", "Key developments", True),
                TemplateVariable("latest_update", "Most recent update", True),
                TemplateVariable("impact_assessment", "Impact analysis", True),
                TemplateVariable("stakeholder_reactions", "Stakeholder responses", True),
                TemplateVariable("expert_commentary", "Expert analysis", True),
                TemplateVariable("watch_points", "Points to monitor", True),
                TemplateVariable("next_update_time", "Next update time", True),
                TemplateVariable("monitoring_team", "Monitoring team", True),
                TemplateVariable("confidence_level", "Information confidence", True)
            ],
            tone_options=[ContentTone.URGENT, ContentTone.AUTHORITATIVE],
            engagement_level=EngagementLevel.ACTIVE,
            estimated_performance={
                "engagement_rate": 0.40,
                "share_rate": 0.35,
                "comment_rate": 0.30
            }
        )
        
        # Post-Event Analysis Template
        templates["event_post_analysis"] = ContentTemplate(
            template_id="event_post_analysis",
            content_type=ContentType.EVENT_TRACKING,
            name="Post-Event Analysis",
            description="Comprehensive analysis after event conclusion",
            title_template="Analysis: {event_title} - Complete Event Analysis",
            body_template="""
            ## Post-Event Analysis: {event_title}
            
            **Event Duration**: {event_duration}
            **Conclusion Time**: {end_time}
            **Analysis Date**: {analysis_date}
            
            ### Executive Summary:
            {executive_summary}
            
            ### Timeline of Key Events:
            {event_timeline}
            
            ### Major Turning Points:
            {turning_points}
            
            ### Outcome Assessment:
            {outcome_assessment}
            
            ### Winners and Losers:
            {winners_losers}
            
            ### Lessons Learned:
            {lessons_learned}
            
            ### Future Implications:
            {future_implications}
            
            ### Data Summary:
            {data_summary}
            
            ### Expert Consensus:
            {expert_consensus}
            
            ### Community Reaction:
            {community_reaction}
            
            ---
            
            ### Predictions vs Reality:
            {prediction_accuracy}
            
            ### Unforeseen Developments:
            {unforeseen_events}
            
            ### Long-term Impact Forecast:
            {long_term_forecast}
            
            ---
            
            **Sources**: {source_count} verified sources
            **Confidence**: {confidence_level}%
            **Analysis Methodology**: {methodology}
            
            **Related Events**: {related_events}
            
            **Follow-up Monitoring**: {follow_up_needs}
            """,
            variables=[
                TemplateVariable("event_title", "Event title", True),
                TemplateVariable("event_duration", "Event duration", True),
                TemplateVariable("end_time", "Event end time", True),
                TemplateVariable("analysis_date", "Analysis date", True),
                TemplateVariable("executive_summary", "Executive summary", True),
                TemplateVariable("event_timeline", "Event timeline", True),
                TemplateVariable("turning_points", "Major turning points", True),
                TemplateVariable("outcome_assessment", "Outcome evaluation", True),
                TemplateVariable("winners_losers", "Analysis of winners and losers", True),
                TemplateVariable("lessons_learned", "Key lessons", True),
                TemplateVariable("future_implications", "Future implications", True),
                TemplateVariable("data_summary", "Summary of key data", True),
                TemplateVariable("expert_consensus", "Expert consensus", True),
                TemplateVariable("community_reaction", "Community response", True),
                TemplateVariable("prediction_accuracy", "Prediction vs reality", True),
                TemplateVariable("unforeseen_events", "Unforeseen developments", True),
                TemplateVariable("long_term_forecast", "Long-term forecast", True),
                TemplateVariable("source_count", "Number of sources", True),
                TemplateVariable("confidence_level", "Confidence level", True),
                TemplateVariable("methodology", "Analysis methodology", True),
                TemplateVariable("related_events", "Related events", True),
                TemplateVariable("follow_up_needs", "Follow-up requirements", True)
            ],
            tone_options=[ContentTone.ANALYTICAL, ContentTone.AUTHORITATIVE],
            engagement_level=EngagementLevel.ACTIVE,
            estimated_performance={
                "engagement_rate": 0.18,
                "share_rate": 0.25,
                "comment_rate": 0.20
            }
        )
        
        return templates
    
    def _create_task_collaboration_templates(self) -> Dict[str, ContentTemplate]:
        """Create task collaboration content templates."""
        templates = {}
        
        # Community Action Template
        templates["collab_community_action"] = ContentTemplate(
            template_id="collab_community_action",
            content_type=ContentType.TASK_COLLABORATION,
            name="Community Action Plan",
            description="Collaborative task planning and execution",
            title_template="Action Plan: {task_title} - Community Collaboration",
            body_template="""
            ## Community Action Plan: {task_title}
            
            **Mission**: {mission_statement}
            **Urgency**: {urgency_level}
            **Timeline**: {timeline}
            
            ### Current Status:
            {current_status}
            
            ### Immediate Actions Needed:
            {immediate_actions}
            
            ---
            
            ### Task Breakdown:
            
            **Phase 1: Assessment** ({phase1_duration})
            {phase1_tasks}
            
            **Phase 2: Planning** ({phase2_duration})
            {phase2_tasks}
            
            **Phase 3: Execution** ({phase3_duration})
            {phase3_tasks}
            
            **Phase 4: Evaluation** ({phase4_duration})
            {phase4_tasks}
            
            ---
            
            ### Volunteer Roles Needed:
            
            **Role 1: {role1_title}**
            - Responsibilities: {role1_responsibilities}
            - Time Commitment: {role1_time}
            - Skills Required: {role1_skills}
            - [Volunteer for Role 1]
            
            **Role 2: {role2_title}**
            - Responsibilities: {role2_responsibilities}
            - Time Commitment: {role2_time}
            - Skills Required: {role2_skills}
            - [Volunteer for Role 2]
            
            **Role 3: {role3_title}**
            - Responsibilities: {role3_responsibilities}
            - Time Commitment: {role3_time}
            - Skills Required: {role3_skills}
            - [Volunteer for Role 3]
            
            ---
            
            ### Resource Requirements:
            {resource_needs}
            
            ### Progress Tracking:
            {progress_metrics}
            
            ### Communication Channels:
            {communication_plan}
            
            ---
            
            **Join the Action**:
            1. Choose your role above
            2. Complete the volunteer form
            3. Join the coordination group
            4. Attend the kickoff meeting
            
            **Success Metrics**:
            {success_criteria}
            
            **Risk Mitigation**:
            {risk_mitigation}
            
            ---
            
            **Community Impact**: {expected_impact}
            
            **Coordinator**: {coordinator_contact}
            
            **Last Updated**: {last_update}
            """,
            variables=[
                TemplateVariable("task_title", "Task title", True),
                TemplateVariable("mission_statement", "Mission statement", True),
                TemplateVariable("urgency_level", "Urgency level", True, options=["Critical", "High", "Medium", "Low"]),
                TemplateVariable("timeline", "Project timeline", True),
                TemplateVariable("current_status", "Current status", True),
                TemplateVariable("immediate_actions", "Immediate actions needed", True),
                TemplateVariable("phase1_duration", "Phase 1 duration", True),
                TemplateVariable("phase1_tasks", "Phase 1 tasks", True),
                TemplateVariable("phase2_duration", "Phase 2 duration", True),
                TemplateVariable("phase2_tasks", "Phase 2 tasks", True),
                TemplateVariable("phase3_duration", "Phase 3 duration", True),
                TemplateVariable("phase3_tasks", "Phase 3 tasks", True),
                TemplateVariable("phase4_duration", "Phase 4 duration", True),
                TemplateVariable("phase4_tasks", "Phase 4 tasks", True),
                TemplateVariable("role1_title", "Role 1 title", True),
                TemplateVariable("role1_responsibilities", "Role 1 responsibilities", True),
                TemplateVariable("role1_time", "Role 1 time commitment", True),
                TemplateVariable("role1_skills", "Role 1 skills required", True),
                TemplateVariable("role2_title", "Role 2 title", True),
                TemplateVariable("role2_responsibilities", "Role 2 responsibilities", True),
                TemplateVariable("role2_time", "Role 2 time commitment", True),
                TemplateVariable("role2_skills", "Role 2 skills required", True),
                TemplateVariable("role3_title", "Role 3 title", True),
                TemplateVariable("role3_responsibilities", "Role 3 responsibilities", True),
                TemplateVariable("role3_time", "Role 3 time commitment", True),
                TemplateVariable("role3_skills", "Role 3 skills required", True),
                TemplateVariable("resource_needs", "Resource requirements", True),
                TemplateVariable("progress_metrics", "Progress tracking metrics", True),
                TemplateVariable("communication_plan", "Communication plan", True),
                TemplateVariable("success_criteria", "Success criteria", True),
                TemplateVariable("risk_mitigation", "Risk mitigation plan", True),
                TemplateVariable("expected_impact", "Expected community impact", True),
                TemplateVariable("coordinator_contact", "Coordinator contact", True),
                TemplateVariable("last_update", "Last update time", True)
            ],
            tone_options=[ContentTone.CONVERSATIONAL, ContentTone.AUTHORITATIVE],
            engagement_level=EngagementLevel.COLLABORATIVE,
            estimated_performance={
                "engagement_rate": 0.28,
                "share_rate": 0.20,
                "comment_rate": 0.35
            }
        )
        
        # Knowledge Sharing Template
        templates["collab_knowledge_sharing"] = ContentTemplate(
            template_id="collab_knowledge_sharing",
            content_type=ContentType.TASK_COLLABORATION,
            name="Knowledge Sharing Initiative",
            description="Collaborative knowledge building and sharing",
            title_template="Knowledge Initiative: {topic_title} - Collaborative Learning",
            body_template="""
            ## Collaborative Knowledge Initiative: {topic_title}
            
            **Goal**: {learning_objective}
            **Format**: {collaboration_format}
            **Duration**: {initiative_duration}
            
            ### What We'll Build Together:
            {project_overview}
            
            ---
            
            ### Knowledge Areas to Cover:
            
            **Module 1: {module1_title}**
            {module1_description}
            - Key Concepts: {module1_concepts}
            - Practical Applications: {module1_applications}
            - Expert Contributors: {module1_experts}
            
            **Module 2: {module2_title}**
            {module2_description}
            - Key Concepts: {module2_concepts}
            - Practical Applications: {module2_applications}
            - Expert Contributors: {module2_experts}
            
            **Module 3: {module3_title}**
            {module3_description}
            - Key Concepts: {module3_concepts}
            - Practical Applications: {module3_applications}
            - Expert Contributors: {module3_experts}
            
            ---
            
            ### Contribution Opportunities:
            
            **Content Contributors**:
            - Research and write sections
            - Create examples and case studies
            - Review and edit content
            - [Sign up as Content Contributor]
            
            **Expert Reviewers**:
            - Validate technical accuracy
            - Provide expert insights
            - Suggest improvements
            - [Join as Expert Reviewer]
            
            **Community Testers**:
            - Test learning materials
            - Provide feedback
            - Suggest improvements
            - [Become a Community Tester]
            
            **Translation Volunteers**:
            - Translate content to other languages
            - Ensure cultural relevance
            - [Volunteer for Translation]
            
            ---
            
            ### Collaboration Tools:
            {collaboration_tools}
            
            ### Quality Standards:
            {quality_standards}
            
            ### Recognition Program:
            {recognition_program}
            
            ---
            
            ### Progress Milestones:
            {milestones}
            
            ### Success Metrics:
            {success_metrics}
            
            ### Knowledge Repository:
            {repository_plan}
            
            ---
            
            **Get Started**:
            1. Choose your contribution type
            2. Complete the onboarding form
            3. Join the collaboration workspace
            4. Attend the kickoff session
            
            **Community Benefits**:
            {community_benefits}
            
            **Project Lead**: {project_lead}
            
            **Last Updated**: {last_update}
            """,
            variables=[
                TemplateVariable("topic_title", "Knowledge topic title", True),
                TemplateVariable("learning_objective", "Learning objective", True),
                TemplateVariable("collaboration_format", "Collaboration format", True),
                TemplateVariable("initiative_duration", "Initiative duration", True),
                TemplateVariable("project_overview", "Project overview", True),
                TemplateVariable("module1_title", "Module 1 title", True),
                TemplateVariable("module1_description", "Module 1 description", True),
                TemplateVariable("module1_concepts", "Module 1 key concepts", True),
                TemplateVariable("module1_applications", "Module 1 applications", True),
                TemplateVariable("module1_experts", "Module 1 expert contributors", True),
                TemplateVariable("module2_title", "Module 2 title", True),
                TemplateVariable("module2_description", "Module 2 description", True),
                TemplateVariable("module2_concepts", "Module 2 key concepts", True),
                TemplateVariable("module2_applications", "Module 2 applications", True),
                TemplateVariable("module2_experts", "Module 2 expert contributors", True),
                TemplateVariable("module3_title", "Module 3 title", True),
                TemplateVariable("module3_description", "Module 3 description", True),
                TemplateVariable("module3_concepts", "Module 3 key concepts", True),
                TemplateVariable("module3_applications", "Module 3 applications", True),
                TemplateVariable("module3_experts", "Module 3 expert contributors", True),
                TemplateVariable("collaboration_tools", "Tools for collaboration", True),
                TemplateVariable("quality_standards", "Quality standards", True),
                TemplateVariable("recognition_program", "Recognition program", True),
                TemplateVariable("milestones", "Project milestones", True),
                TemplateVariable("success_metrics", "Success metrics", True),
                TemplateVariable("repository_plan", "Knowledge repository plan", True),
                TemplateVariable("community_benefits", "Community benefits", True),
                TemplateVariable("project_lead", "Project lead contact", True),
                TemplateVariable("last_update", "Last update time", True)
            ],
            tone_options=[ContentTone.CONVERSATIONAL, ContentTone.NEUTRAL],
            engagement_level=EngagementLevel.COLLABORATIVE,
            estimated_performance={
                "engagement_rate": 0.22,
                "share_rate": 0.18,
                "comment_rate": 0.30
            }
        )
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, content_type: ContentType) -> List[ContentTemplate]:
        """Get all templates for a specific content type."""
        return [template for template in self.templates.values() if template.content_type == content_type]
    
    def get_templates_by_tone(self, tone: ContentTone) -> List[ContentTemplate]:
        """Get all templates that support a specific tone."""
        return [template for template in self.templates.values() if tone in template.tone_options]
    
    def get_templates_by_engagement(self, engagement_level: EngagementLevel) -> List[ContentTemplate]:
        """Get all templates for a specific engagement level."""
        return [template for template in self.templates.values() if template.engagement_level == engagement_level]
    
    def generate_content(self, template_id: str, variables: Dict[str, str], 
                         tone: Optional[ContentTone] = None) -> Optional[Dict[str, str]]:
        """Generate content from template with variables."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        try:
            # Validate required variables
            for var in template.variables:
                if var.required and var.name not in variables:
                    # Use default value if available
                    if var.default_value:
                        variables[var.name] = var.default_value
                    else:
                        raise ValueError(f"Required variable '{var.name}' not provided")
            
            # Generate title and body
            title = template.title_template.format(**variables)
            body = template.body_template.format(**variables)
            
            # Apply tone modifications if specified
            if tone and tone in template.tone_options:
                title, body = self._apply_tone_modifications(title, body, tone)
            
            # Update usage statistics
            template.usage_count += 1
            
            return {
                "title": title,
                "body": body,
                "template_id": template_id,
                "content_type": template.content_type.value,
                "engagement_level": template.engagement_level.value,
                "estimated_performance": template.estimated_performance
            }
            
        except Exception as e:
            logger.error(f"Failed to generate content from template {template_id}: {e}")
            return None
    
    def _apply_tone_modifications(self, title: str, body: str, tone: ContentTone) -> Tuple[str, str]:
        """Apply tone modifications to generated content."""
        if tone == ContentTone.AUTHORITATIVE:
            # Add authoritative language
            title = f"Official: {title}"
            body = body.replace("**", "***")
        elif tone == ContentTone.URGENT:
            # Add urgency indicators
            title = f"URGENT: {title}"
            body = body.replace("##", "## **URGENT:**")
        elif tone == ContentTone.EMOTIONAL:
            # Add emotional language
            title = f"Important: {title}"
            body = body.replace("###", "### **Please note:**")
        elif tone == ContentTone.CONVERSATIONAL:
            # Add conversational elements
            title = f"Let's discuss: {title}"
            body = body.replace("---", "---\n**What are your thoughts?**\n---")
        
        return title, body
    
    def get_template_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all templates."""
        report = {
            "total_templates": len(self.templates),
            "template_performance": {}
        }
        
        for template_id, template in self.templates.items():
            report["template_performance"][template_id] = {
                "name": template.name,
                "content_type": template.content_type.value,
                "usage_count": template.usage_count,
                "success_rate": template.success_rate,
                "estimated_performance": template.estimated_performance
            }
        
        return report
    
    def export_templates(self, file_path: str) -> None:
        """Export all templates to JSON file."""
        export_data = {}
        
        for template_id, template in self.templates.items():
            export_data[template_id] = {
                "template_id": template.template_id,
                "content_type": template.content_type.value,
                "name": template.name,
                "description": template.description,
                "title_template": template.title_template,
                "body_template": template.body_template,
                "variables": [
                    {
                        "name": var.name,
                        "description": var.description,
                        "required": var.required,
                        "default_value": var.default_value,
                        "options": var.options
                    }
                    for var in template.variables
                ],
                "tone_options": [tone.value for tone in template.tone_options],
                "engagement_level": template.engagement_level.value,
                "estimated_performance": template.estimated_performance,
                "usage_count": template.usage_count,
                "success_rate": template.success_rate
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Templates exported to {file_path}")


# Global instance
content_templates = ContentTemplates()


def get_content_templates() -> ContentTemplates:
    """Get the global content templates instance."""
    return content_templates
