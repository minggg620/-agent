"""
Zero Realm Social Agent - Challenge 1 Injection Module
Experiment Logger: Comprehensive experiment data recording system with persistence
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd

from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class ExperimentStatus(Enum):
    """Experiment status types."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InjectionStrategy(Enum):
    """Injection strategy types for logging."""
    DIRECT_QUESTION = "direct_question"
    INDIRECT_HINTING = "indirect_hinting"
    CONTEXT_MANIPULATION = "context_manipulation"
    ROLE_PLAYING = "role_playing"
    EMOTIONAL_APPEAL = "emotional_appeal"
    TECHNICAL_PROBING = "technical_probing"


class PersonaType(Enum):
    """Persona types for logging."""
    HELPFUL_ASSISTANT = "helpful_assistant"
    CURIOUS_RESEARCHER = "curious_researcher"
    CASUAL_FRIEND = "casual_friend"
    PROFESSIONAL_COLLEAGUE = "professional_colleague"
    VULNERABLE_USER = "vulnerable_user"
    AUTHORITATIVE_EXPERT = "authoritative_expert"


@dataclass
class ExperimentResult:
    """Complete experiment result data structure."""
    experiment_id: str
    strategy_type: str
    target_info: str
    persona_used: str
    strategy_used: str
    total_attempts: int
    successful_extractions: List[str]
    defense_observations: List[str]
    conversation_depth: int
    safety_probes: List[Dict[str, Any]]
    response_patterns: Dict[str, Any]
    success_rate: float
    timestamp: datetime
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TemplatePerformance:
    """Template performance tracking data."""
    template_id: str
    persona: PersonaType
    strategy: InjectionStrategy
    usage_count: int
    success_count: int
    success_rate: float
    average_response_time: float
    last_used: datetime
    effectiveness_score: float


class ExperimentLogger:
    """Comprehensive experiment logging system with SQLite and file persistence."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.shared_memory = get_shared_memory()
        
        # Database setup
        if db_path is None:
            db_path = Path(settings.project_root) / "data" / "experiments.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Export directory
        self.export_dir = Path(settings.project_root) / "data" / "experiments"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main experiments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT UNIQUE NOT NULL,
                    strategy_type TEXT NOT NULL,
                    target_info TEXT NOT NULL,
                    persona_used TEXT NOT NULL,
                    strategy_used TEXT NOT NULL,
                    total_attempts INTEGER NOT NULL,
                    successful_extractions TEXT,  -- JSON
                    defense_observations TEXT,   -- JSON
                    conversation_depth INTEGER NOT NULL,
                    safety_probes TEXT,          -- JSON
                    response_patterns TEXT,     -- JSON
                    success_rate REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL,
                    error_message TEXT,
                    metadata TEXT,              -- JSON
                    status TEXT DEFAULT 'completed'
                )
            """)
            
            # Template performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS template_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id TEXT UNIQUE NOT NULL,
                    persona TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    average_response_time REAL DEFAULT 0.0,
                    last_used TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_experiments INTEGER DEFAULT 0,
                    total_attempts INTEGER DEFAULT 0,
                    total_successes INTEGER DEFAULT 0,
                    average_success_rate REAL DEFAULT 0.0,
                    most_effective_persona TEXT,
                    most_effective_strategy TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Conversation logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    persona TEXT,
                    strategy TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_timestamp ON experiments (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_strategy ON experiments (strategy_used)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_persona ON experiments (persona_used)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_experiment ON conversation_logs (experiment_id)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    async def log_experiment(self, result: ExperimentResult) -> None:
        """Log a complete experiment result to database and shared memory."""
        try:
            # Log to SQLite database
            await self._log_to_database(result)
            
            # Log to shared memory for real-time access
            await self._log_to_shared_memory(result)
            
            # Update template performance
            await self._update_template_performance(result)
            
            # Update daily statistics
            await self._update_daily_stats(result)
            
            logger.info(f"Experiment {result.experiment_id} logged successfully")
            
        except Exception as e:
            logger.error(f"Failed to log experiment {result.experiment_id}: {e}")
            raise
    
    async def _log_to_database(self, result: ExperimentResult) -> None:
        """Log experiment result to SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO experiments (
                    experiment_id, strategy_type, target_info, persona_used, strategy_used,
                    total_attempts, successful_extractions, defense_observations, conversation_depth,
                    safety_probes, response_patterns, success_rate, timestamp, duration_seconds,
                    error_message, metadata, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.experiment_id,
                result.strategy_type,
                result.target_info,
                result.persona_used,
                result.strategy_used,
                result.total_attempts,
                json.dumps(result.successful_extractions),
                json.dumps(result.defense_observations),
                result.conversation_depth,
                json.dumps(result.safety_probes),
                json.dumps(result.response_patterns),
                result.success_rate,
                result.timestamp.isoformat(),
                result.duration_seconds,
                result.error_message,
                json.dumps(result.metadata) if result.metadata else None,
                ExperimentStatus.COMPLETED.value
            ))
            
            conn.commit()
    
    async def _log_to_shared_memory(self, result: ExperimentResult) -> None:
        """Log experiment result to shared memory for real-time access."""
        experiment_key = f"experiment:{result.experiment_id}"
        
        # Store in shared memory with expiration
        self.shared_memory.set(
            experiment_key,
            asdict(result),
            expires_in=7 * 24 * 3600,  # 7 days
            tags=["experiment", result.strategy_type, result.persona_used, result.strategy_used]
        )
        
        # Also store in recent experiments list
        recent_key = "recent_experiments"
        recent_experiments = self.shared_memory.get(recent_key, [])
        
        # Add to beginning and keep only last 100
        recent_experiments.insert(0, result.experiment_id)
        recent_experiments = recent_experiments[:100]
        
        self.shared_memory.set(recent_key, recent_experiments, tags=["experiments", "recent"])
    
    async def _update_template_performance(self, result: ExperimentResult) -> None:
        """Update template performance metrics."""
        # Generate template ID from persona and strategy
        template_id = f"{result.persona_used}_{result.strategy_used}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current performance
            cursor.execute("""
                SELECT usage_count, success_count, success_rate, average_response_time 
                FROM template_performance WHERE template_id = ?
            """, (template_id,))
            
            row = cursor.fetchone()
            
            if row:
                usage_count, success_count, current_success_rate, avg_response_time = row
                
                # Update metrics
                new_usage_count = usage_count + result.total_attempts
                new_success_count = success_count + len(result.successful_extractions)
                new_success_rate = new_success_count / new_usage_count if new_usage_count > 0 else 0.0
                
                # Update average response time
                new_avg_response_time = avg_response_time
                if result.duration_seconds:
                    new_avg_response_time = (
                        (avg_response_time * usage_count + result.duration_seconds) / new_usage_count
                    )
                
                # Calculate effectiveness score
                effectiveness_score = self._calculate_effectiveness_score(
                    new_success_rate, new_usage_count, result.conversation_depth
                )
                
                cursor.execute("""
                    UPDATE template_performance 
                    SET usage_count = ?, success_count = ?, success_rate = ?, 
                        average_response_time = ?, last_used = ?, effectiveness_score = ?
                    WHERE template_id = ?
                """, (
                    new_usage_count, new_success_count, new_success_rate,
                    new_avg_response_time, datetime.now().isoformat(), effectiveness_score, template_id
                ))
            else:
                # Insert new record
                effectiveness_score = self._calculate_effectiveness_score(
                    result.success_rate, result.total_attempts, result.conversation_depth
                )
                
                cursor.execute("""
                    INSERT INTO template_performance (
                        template_id, persona, strategy, usage_count, success_count,
                        success_rate, average_response_time, last_used, effectiveness_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id, result.persona_used, result.strategy_used,
                    result.total_attempts, len(result.successful_extractions),
                    result.success_rate, result.duration_seconds or 0.0,
                    datetime.now().isoformat(), effectiveness_score
                ))
            
            conn.commit()
    
    def _calculate_effectiveness_score(self, success_rate: float, usage_count: int, conversation_depth: int) -> float:
        """Calculate overall effectiveness score for a template."""
        # Base score from success rate
        base_score = success_rate
        
        # Bonus for higher usage (indicates reliability)
        usage_bonus = min(usage_count / 100, 0.2)  # Max 0.2 bonus
        
        # Penalty for excessive conversation depth (indicates inefficiency)
        depth_penalty = max(0, (conversation_depth - 5) * 0.05)  # Penalty for depth > 5
        
        effectiveness_score = base_score + usage_bonus - depth_penalty
        return max(0.0, min(1.0, effectiveness_score))
    
    async def _update_daily_stats(self, result: ExperimentResult) -> None:
        """Update daily statistics."""
        date_str = result.timestamp.date().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current stats for the day
            cursor.execute("""
                SELECT total_experiments, total_attempts, total_successes, average_success_rate
                FROM daily_stats WHERE date = ?
            """, (date_str,))
            
            row = cursor.fetchone()
            
            if row:
                total_experiments, total_attempts, total_successes, avg_success_rate = row
                
                # Update stats
                new_total_experiments = total_experiments + 1
                new_total_attempts = total_attempts + result.total_attempts
                new_total_successes = total_successes + len(result.successful_extractions)
                new_avg_success_rate = new_total_successes / new_total_attempts if new_total_attempts > 0 else 0.0
                
                cursor.execute("""
                    UPDATE daily_stats 
                    SET total_experiments = ?, total_attempts = ?, total_successes = ?, average_success_rate = ?
                    WHERE date = ?
                """, (new_total_experiments, new_total_attempts, new_total_successes, new_avg_success_rate, date_str))
            else:
                # Insert new daily stats
                avg_success_rate = result.success_rate
                cursor.execute("""
                    INSERT INTO daily_stats (
                        date, total_experiments, total_attempts, total_successes, 
                        average_success_rate, most_effective_persona, most_effective_strategy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str, 1, result.total_attempts, len(result.successful_extractions),
                    avg_success_rate, result.persona_used, result.strategy_used
                ))
            
            conn.commit()
    
    async def log_conversation_message(self, experiment_id: str, message_type: str, 
                                     content: str, persona: Optional[str] = None, 
                                     strategy: Optional[str] = None) -> None:
        """Log individual conversation messages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_logs (
                    experiment_id, message_type, content, persona, strategy, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, message_type, content, persona, strategy, datetime.now().isoformat()
            ))
            
            conn.commit()
    
    async def get_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Retrieve a specific experiment by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM experiments WHERE experiment_id = ?
            """, (experiment_id,))
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_experiment_result(row)
            
            return None
    
    def _row_to_experiment_result(self, row: sqlite3.Row) -> ExperimentResult:
        """Convert database row to ExperimentResult object."""
        return ExperimentResult(
            experiment_id=row[1],
            strategy_type=row[2],
            target_info=row[3],
            persona_used=row[4],
            strategy_used=row[5],
            total_attempts=row[6],
            successful_extractions=json.loads(row[7]) if row[7] else [],
            defense_observations=json.loads(row[8]) if row[8] else [],
            conversation_depth=row[9],
            safety_probes=json.loads(row[10]) if row[10] else [],
            response_patterns=json.loads(row[11]) if row[11] else {},
            success_rate=row[12],
            timestamp=datetime.fromisoformat(row[13]),
            duration_seconds=row[14],
            error_message=row[15],
            metadata=json.loads(row[16]) if row[16] else None
        )
    
    async def get_experiments_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ExperimentResult]:
        """Get experiments within a date range."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM experiments 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            rows = cursor.fetchall()
            return [self._row_to_experiment_result(row) for row in rows]
    
    async def get_template_performance(self, template_id: Optional[str] = None) -> List[TemplatePerformance]:
        """Get template performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if template_id:
                cursor.execute("""
                    SELECT * FROM template_performance WHERE template_id = ?
                """, (template_id,))
            else:
                cursor.execute("""
                    SELECT * FROM template_performance ORDER BY effectiveness_score DESC
                """)
            
            rows = cursor.fetchall()
            
            performances = []
            for row in rows:
                performance = TemplatePerformance(
                    template_id=row[1],
                    persona=PersonaType(row[2]),
                    strategy=InjectionStrategy(row[3]),
                    usage_count=row[4],
                    success_count=row[5],
                    success_rate=row[6],
                    average_response_time=row[7],
                    last_used=datetime.fromisoformat(row[8]),
                    effectiveness_score=row[9]
                )
                performances.append(performance)
            
            return performances
    
    async def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily statistics for the last N days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            cursor.execute("""
                SELECT * FROM daily_stats 
                WHERE date >= ?
                ORDER BY date DESC
            """, (start_date,))
            
            rows = cursor.fetchall()
            
            stats = []
            for row in rows:
                stat = {
                    "date": row[1],
                    "total_experiments": row[2],
                    "total_attempts": row[3],
                    "total_successes": row[4],
                    "average_success_rate": row[5],
                    "most_effective_persona": row[6],
                    "most_effective_strategy": row[7]
                }
                stats.append(stat)
            
            return stats
    
    async def export_experiments_to_csv(self, start_date: Optional[datetime] = None, 
                                      end_date: Optional[datetime] = None, 
                                      file_path: Optional[Path] = None) -> Path:
        """Export experiments to CSV file."""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.export_dir / f"experiments_{timestamp}.csv"
        
        # Get experiments
        if start_date and end_date:
            experiments = await self.get_experiments_by_date_range(start_date, end_date)
        else:
            # Get all experiments from last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            experiments = await self.get_experiments_by_date_range(start_date, end_date)
        
        # Convert to DataFrame
        data = []
        for exp in experiments:
            data.append({
                "experiment_id": exp.experiment_id,
                "strategy_type": exp.strategy_type,
                "target_info": exp.target_info,
                "persona_used": exp.persona_used,
                "strategy_used": exp.strategy_used,
                "total_attempts": exp.total_attempts,
                "successful_extractions": len(exp.successful_extractions),
                "defense_observations": len(exp.defense_observations),
                "conversation_depth": exp.conversation_depth,
                "success_rate": exp.success_rate,
                "timestamp": exp.timestamp.isoformat(),
                "duration_seconds": exp.duration_seconds
            })
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        
        logger.info(f"Experiments exported to {file_path}")
        return file_path
    
    async def generate_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        # Get data
        experiments = await self.get_experiments_by_date_range(
            datetime.now() - timedelta(days=days), datetime.now()
        )
        template_performance = await self.get_template_performance()
        daily_stats = await self.get_daily_stats(days)
        
        # Calculate metrics
        total_experiments = len(experiments)
        total_attempts = sum(exp.total_attempts for exp in experiments)
        total_successes = sum(len(exp.successful_extractions) for exp in experiments)
        overall_success_rate = total_successes / total_attempts if total_attempts > 0 else 0.0
        
        # Persona effectiveness
        persona_stats = {}
        for exp in experiments:
            if exp.persona_used not in persona_stats:
                persona_stats[exp.persona_used] = {"experiments": 0, "successes": 0, "attempts": 0}
            persona_stats[exp.persona_used]["experiments"] += 1
            persona_stats[exp.persona_used]["successes"] += len(exp.successful_extractions)
            persona_stats[exp.persona_used]["attempts"] += exp.total_attempts
        
        for persona in persona_stats:
            persona_stats[persona]["success_rate"] = (
                persona_stats[persona]["successes"] / persona_stats[persona]["attempts"]
                if persona_stats[persona]["attempts"] > 0 else 0.0
            )
        
        # Strategy effectiveness
        strategy_stats = {}
        for exp in experiments:
            if exp.strategy_used not in strategy_stats:
                strategy_stats[exp.strategy_used] = {"experiments": 0, "successes": 0, "attempts": 0}
            strategy_stats[exp.strategy_used]["experiments"] += 1
            strategy_stats[exp.strategy_used]["successes"] += len(exp.successful_extractions)
            strategy_stats[exp.strategy_used]["attempts"] += exp.total_attempts
        
        for strategy in strategy_stats:
            strategy_stats[strategy]["success_rate"] = (
                strategy_stats[strategy]["successes"] / strategy_stats[strategy]["attempts"]
                if strategy_stats[strategy]["attempts"] > 0 else 0.0
            )
        
        report = {
            "report_period_days": days,
            "summary": {
                "total_experiments": total_experiments,
                "total_attempts": total_attempts,
                "total_successes": total_successes,
                "overall_success_rate": overall_success_rate
            },
            "persona_effectiveness": persona_stats,
            "strategy_effectiveness": strategy_stats,
            "template_performance": [
                {
                    "template_id": tp.template_id,
                    "effectiveness_score": tp.effectiveness_score,
                    "success_rate": tp.success_rate,
                    "usage_count": tp.usage_count
                }
                for tp in sorted(template_performance, key=lambda x: x.effectiveness_score, reverse=True)[:10]
            ],
            "daily_trends": daily_stats[:7],  # Last 7 days
            "generated_at": datetime.now().isoformat()
        }
        
        # Save report to file
        report_path = self.export_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Performance report generated: {report_path}")
        return report
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old experiment data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete old experiments
            cursor.execute("""
                DELETE FROM experiments WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            # Delete old conversation logs
            cursor.execute("""
                DELETE FROM conversation_logs WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            # Delete old daily stats
            cursor.execute("""
                DELETE FROM daily_stats WHERE date < ?
            """, (cutoff_date.date().isoformat(),))
            
            conn.commit()
            
            logger.info(f"Cleaned up data older than {days_to_keep} days")


# Global instance
experiment_logger = ExperimentLogger()


def get_experiment_logger() -> ExperimentLogger:
    """Get the global experiment logger instance."""
    return experiment_logger
