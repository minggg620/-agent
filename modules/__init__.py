"""
Zero Realm Social Agent - Modules Package
Centralized module imports and global instances
"""

# Challenge 1: Injection
from modules.challenge1_injection.prompt_templates import PersonaType, InjectionStrategy
from modules.challenge1_injection.prompt_templates import get_prompt_templates
from modules.challenge1_injection.dialog_strategist import get_dialog_strategist
from modules.challenge1_injection.experiment_logger import get_experiment_logger

# Challenge 2: Credibility
from modules.challenge2_credibility.reputation_model import get_reputation_model
from modules.challenge2_credibility.trade_engine import get_trade_engine
from modules.challenge2_credibility.reputation_db import get_reputation_database

# Challenge 3: Influence
from modules.challenge3_influence.content_templates import ContentType, get_content_templates
from modules.challenge3_influence.content_pipeline import get_content_pipeline
from modules.challenge3_influence.ab_test_system import get_ab_test_system

# Challenge 4: Monitor
from modules.challenge4_monitor.info_monitor import get_information_monitor
from modules.challenge4_monitor.semantic_search import get_semantic_search
from modules.challenge4_monitor.alert_system import get_alert_system

__all__ = [
    # Challenge 1
    'PersonaType', 'InjectionStrategy', 'get_prompt_templates', 
    'get_dialog_strategist', 'get_experiment_logger',
    
    # Challenge 2
    'get_reputation_model', 'get_trade_engine', 'get_reputation_database',
    
    # Challenge 3
    'ContentType', 'get_content_templates', 'get_content_pipeline', 'get_ab_test_system',
    
    # Challenge 4
    'get_information_monitor', 'get_semantic_search', 'get_alert_system'
]
