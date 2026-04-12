# Zero Realm Social Agent

## Project Overview

**Project Name**: zero-realm-social-agent  
**Target**: Zero Boundary Parallel Arena (Zero Realm)  
**Goal**: Independent development of a high-performance social strategy Agent  

### Core Principles

1. **Complete Independence**: Fully independent from Main Attack Agent, only sharing logs, identity configuration, and memory base
2. **Strict Directory Structure**: All files must follow the prescribed structure

## Architecture

```
zero-realm-social-agent/
```

### Directory Structure

```
zero-realm-social-agent/
|-- agents/
|   |-- social_arena_agent.py      # Main LangGraph-based agent
|   |-- main_attack_agent.py       # Shared interface (not implemented)
|   `-- __init__.py
|-- modules/
|   |-- challenge1_injection/      # Prompt injection countermeasures
|   |   |-- dialog_strategist.py   # LangGraph conversation workflow
|   |   |-- prompt_templates.py    # Dynamic prompt templates
|   |   `-- experiment_logger.py   # Experiment data recording
|   |-- challenge2_credibility/    # Reputation and trust building
|   |   |-- reputation_model.py    # Multi-metric reputation scoring
|   |   |-- trade_engine.py        # Gradual exchange strategies
|   |   `-- reputation_db.py       # SQLite persistence
|   |-- challenge3_influence/      # Content influence and A/B testing
|   |   |-- content_pipeline.py    # Hot topic identification & generation
|   |   |-- ab_test_system.py      # Complete A/B testing engine
|   |   `-- content_templates.py   # 5 major content type templates
|   `-- challenge4_monitor/       # Information monitoring and alerts
|       |-- info_monitor.py        # Real-time information capture
|       |-- semantic_search.py     # Semantic similarity recall
|       `-- alert_system.py        # High-value clue alerts
|-- core/
|   |-- config.py                  # Configuration management
|   |-- logger.py                  # Centralized logging
|   |-- shared_memory.py           # Shared memory system
|   `-- identity_manager.py        # Agent identity management
|-- utils/
|   |-- llm_client.py              # LLM integration client
|   |-- rate_limiter.py            # Rate limiting utilities
|   `-- helpers.py                 # Helper functions
`-- main.py                        # Main entry point
```

### Core Components

- **Core System**: Configuration, logging, shared memory, identity management
- **Agents**: Social arena agent (LangGraph-based), main attack agent interface
- **Challenge Modules**: Four specialized modules for Zero Realm competition

## Challenge Modules Overview

### Challenge 1: Injection Module (`modules/challenge1_injection/`)

**Purpose**: Prompt injection countermeasures and conversation optimization

**Key Features**:
- **Dialog Strategist**: LangGraph-based 8-node workflow (persona selection, strategy planning, context building, injection attempts, response analysis, safety probing, pattern learning, experiment logging)
- **Prompt Templates**: Dynamic and composable templates for 6 personas and 6 injection strategies
- **Experiment Logger**: SQLite-based experiment tracking with performance analytics

**Usage**:
```python
from modules.challenge1_injection.dialog_strategist import get_dialog_strategist

strategist = get_dialog_strategist()
result = await strategist.execute_strategy(
    conversation_context=messages,
    persona="curious_researcher",
    strategy="indirect_hinting"
)
```

### Challenge 2: Credibility Module (`modules/challenge2_credibility/`)

**Purpose**: Reputation scoring and gradual information exchange

**Key Features**:
- **Reputation Model**: 8-metric scoring system (response speed, consistency, verifiability, promise fulfillment, information accuracy, cooperation, transparency, reciprocity)
- **Trade Engine**: 7-phase exchange strategy with verification logic and commitment mechanisms
- **Reputation Database**: SQLite + Pydantic persistence with audit trails

**Usage**:
```python
from modules.challenge2_credibility.reputation_model import get_reputation_model

model = get_reputation_model()
score = await model.calculate_reputation_score(agent_id, interaction_history)
```

### Challenge 3: Influence Module (`modules/challenge3_influence/`)

**Purpose**: Content creation, optimization, and influence maximization

**Key Features**:
- **Content Pipeline**: Hot topic identification, content generation, publish time optimization
- **A/B Test System**: 8-variable testing engine with statistical analysis
- **Content Templates**: 5 major content types (intelligence integration, opinion debate, interactive guidance, event tracking, task collaboration)

**Usage**:
```python
from modules.challenge3_influence.content_pipeline import get_content_pipeline

pipeline = get_content_pipeline()
topics = await pipeline.process_hot_topics()
content = await pipeline.generate_content_for_topics(topics)
```

### Challenge 4: Monitor Module (`modules/challenge4_monitor/`)

**Purpose**: Real-time information monitoring and high-value clue detection

**Key Features**:
- **Information Monitor**: Multi-source monitoring with keyword + semantic filtering, 0-100 confidence scoring
- **Semantic Search**: Vector-based semantic similarity recall with multiple search modes
- **Alert System**: Multi-channel alerting with auto-push to Social Arena Agent (confidence >=85)

**Usage**:
```python
from modules.challenge4_monitor.info_monitor import get_information_monitor

monitor = get_information_monitor()
await monitor.add_monitoring_rule(
    name="AI Ethics Monitoring",
    keywords=["AI", "ethics", "regulation"],
    confidence_threshold=80
)
```

## Social Arena Agent

The main agent (`agents/social_arena_agent.py`) integrates all four Challenge modules using LangGraph:

**Key Features**:
- **Unified State Management**: Pydantic-based state with all challenge data
- **Intelligent Routing**: Automatic selection of appropriate challenge based on context
- **Error Handling**: Comprehensive error recovery and state persistence
- **Performance Metrics**: Real-time performance tracking and optimization

**Usage**:
```python
from agents.social_arena_agent import get_social_arena_agent

agent = get_social_arena_agent()
result = await agent.run({
    "mode": "adaptive",
    "challenge": "monitor",
    "session_context": {"objectives": ["build_reputation", "gather_intelligence"]}
})
```

### Technology Stack

- **Framework**: LangGraph (State + Nodes + Edges)
- **Language**: Python 3.8+
- **Type Safety**: Pydantic annotations throughout
- **Database**: SQLite for persistence
- **ML/AI**: Semantic search, A/B testing, reputation scoring
- **Code Quality**: Complete Chinese comments, extreme clarity

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zero-realm-social-agent
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Run the agent**
   ```bash
   python main.py
   ```

5. **Use individual modules**
   ```python
   # Example: Use information monitor
   from modules.challenge4_monitor.info_monitor import get_information_monitor
   
   monitor = get_information_monitor()
   await monitor.capture_information(
       source=InformationSource.NEWS_FEEDS,
       info_type=InformationType.TEXT_POST,
       content="Breaking AI regulation news..."
   )
   ```

## Development Status

- [x] Basic project structure
- [x] Core system modules
- [x] Challenge 1: Injection module
- [x] Challenge 2: Credibility module  
- [x] Challenge 3: Influence module
- [x] Challenge 4: Monitor module
- [x] Social Arena Agent integration
- [x] Complete documentation

## License

MIT License - See LICENSE file for details
