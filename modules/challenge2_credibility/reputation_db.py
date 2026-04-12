"""
Zero Realm Social Agent - Challenge 2 Credibility Module
Reputation Database: SQLite + Pydantic persistent storage for reputation data
"""

import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
from enum import Enum
import json

from pydantic import BaseModel, Field
from ...core.config import settings
from ...core.logger import get_logger
from ...core.shared_memory import get_shared_memory
from .reputation_model import ReputationScore, ReputationLevel, MetricType

logger = get_logger(__name__)


class DatabaseOperation(Enum):
    """Database operation types for logging."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SELECT = "select"
    BACKUP = "backup"
    RESTORE = "restore"


class ReputationRecord(BaseModel):
    """Complete reputation record for database storage."""
    agent_id: str = Field(description="Unique agent identifier")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall reputation score")
    metric_scores: Dict[str, float] = Field(description="Individual metric scores")
    level: str = Field(description="Reputation level")
    confidence: float = Field(ge=0.0, le=1.0, description="Score confidence")
    last_updated: datetime = Field(description="Last update timestamp")
    total_interactions: int = Field(ge=0, description="Total interactions count")
    trend_direction: str = Field(description="Trend direction")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    strengths: List[str] = Field(default_factory=list, description="Strengths")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ReputationHistory(BaseModel):
    """Historical reputation data point."""
    id: Optional[int] = Field(default=None, description="Database ID")
    agent_id: str = Field(description="Agent identifier")
    timestamp: datetime = Field(description="Timestamp of record")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall score at timestamp")
    level: str = Field(description="Reputation level at timestamp")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence at timestamp")
    significant_events: List[str] = Field(default_factory=list, description="Significant events")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Context information")


class ReputationDatabase(BaseModel):
    """SQLite database for persistent reputation storage with Pydantic models."""
    
    shared_memory = get_shared_memory()
    
    # Database configuration
    db_path: Path = Field(default_factory=lambda: Path(settings.project_root) / "data" / "reputation.db")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    max_history_days: int = Field(default=365, description="Maximum history retention in days")
    
    # Performance settings
    connection_pool_size: int = Field(default=5, description="Connection pool size")
    query_timeout_seconds: int = Field(default=30, description="Query timeout")
    batch_size: int = Field(default=1000, description="Batch operation size")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database with required tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main reputation table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reputation_records (
                    agent_id TEXT PRIMARY KEY,
                    overall_score REAL NOT NULL CHECK (overall_score >= 0.0 AND overall_score <= 1.0),
                    metric_scores TEXT NOT NULL,  -- JSON
                    level TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                    last_updated TEXT NOT NULL,
                    total_interactions INTEGER NOT NULL CHECK (total_interactions >= 0),
                    trend_direction TEXT NOT NULL,
                    risk_factors TEXT,  -- JSON
                    strengths TEXT,  -- JSON
                    metadata TEXT,  -- JSON
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reputation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reputation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    overall_score REAL NOT NULL CHECK (overall_score >= 0.0 AND overall_score <= 1.0),
                    level TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                    significant_events TEXT,  -- JSON
                    context_data TEXT,  -- JSON
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES reputation_records (agent_id) ON DELETE CASCADE
                )
            """)
            
            # Interaction log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    interaction_data TEXT NOT NULL,  -- JSON
                    timestamp TEXT NOT NULL,
                    reputation_impact REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES reputation_records (agent_id) ON DELETE CASCADE
                )
            """)
            
            # Verification records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    verification_type TEXT NOT NULL,
                    verification_result BOOLEAN NOT NULL,
                    evidence TEXT,
                    confidence_score REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES reputation_records (agent_id) ON DELETE CASCADE
                )
            """)
            
            # Database operation log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    operation_data TEXT,  -- JSON
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reputation_level ON reputation_records (level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reputation_updated ON reputation_records (last_updated)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_agent_timestamp ON reputation_history (agent_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interaction_agent_timestamp ON interaction_logs (agent_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_verification_agent_timestamp ON verification_records (agent_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation_timestamp ON operation_logs (timestamp)")
            
            # Create triggers for automatic timestamp updates
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_reputation_timestamp 
                AFTER UPDATE ON reputation_records
                BEGIN
                    UPDATE reputation_records SET updated_at = CURRENT_TIMESTAMP WHERE agent_id = NEW.agent_id;
                END
            """)
            
            conn.commit()
            logger.info("Reputation database initialized successfully")
    
    async def store_reputation_record(self, record: ReputationRecord) -> bool:
        """Store or update a reputation record in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert to JSON for storage
                metric_scores_json = json.dumps(record.metric_scores)
                risk_factors_json = json.dumps(record.risk_factors)
                strengths_json = json.dumps(record.strengths)
                metadata_json = json.dumps(record.metadata) if record.metadata else None
                
                # Insert or replace record
                cursor.execute("""
                    INSERT OR REPLACE INTO reputation_records (
                        agent_id, overall_score, metric_scores, level, confidence,
                        last_updated, total_interactions, trend_direction,
                        risk_factors, strengths, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.agent_id,
                    record.overall_score,
                    metric_scores_json,
                    record.level,
                    record.confidence,
                    record.last_updated.isoformat(),
                    record.total_interactions,
                    record.trend_direction,
                    risk_factors_json,
                    strengths_json,
                    metadata_json
                ))
                
                conn.commit()
                
                # Log operation
                await self._log_operation(DatabaseOperation.INSERT, "reputation_records", record.agent_id, record.dict())
                
                # Store in shared memory for quick access
                memory_key = f"reputation_record:{record.agent_id}"
                self.shared_memory.set(memory_key, record.dict(), tags=["reputation", "record"])
                
                logger.info(f"Reputation record stored for agent: {record.agent_id}")
                return True
                
        except Exception as e:
            await self._log_operation(DatabaseOperation.INSERT, "reputation_records", record.agent_id, {"error": str(e)}, success=False)
            logger.error(f"Failed to store reputation record for {record.agent_id}: {e}")
            return False
    
    async def get_reputation_record(self, agent_id: str) -> Optional[ReputationRecord]:
        """Retrieve a reputation record by agent ID."""
        try:
            # First check shared memory
            memory_key = f"reputation_record:{agent_id}"
            cached_record = self.shared_memory.get(memory_key)
            
            if cached_record:
                return ReputationRecord(**cached_record)
            
            # Query database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM reputation_records WHERE agent_id = ?
                """, (agent_id,))
                
                row = cursor.fetchone()
                
                if row:
                    record = self._row_to_reputation_record(row)
                    
                    # Cache in shared memory
                    self.shared_memory.set(memory_key, record.dict(), tags=["reputation", "record"])
                    
                    return record
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve reputation record for {agent_id}: {e}")
            return None
    
    def _row_to_reputation_record(self, row: sqlite3.Row) -> ReputationRecord:
        """Convert database row to ReputationRecord."""
        return ReputationRecord(
            agent_id=row[0],
            overall_score=row[1],
            metric_scores=json.loads(row[2]),
            level=row[3],
            confidence=row[4],
            last_updated=datetime.fromisoformat(row[5]),
            total_interactions=row[6],
            trend_direction=row[7],
            risk_factors=json.loads(row[8]) if row[8] else [],
            strengths=json.loads(row[9]) if row[9] else [],
            metadata=json.loads(row[10]) if row[10] else None
        )
    
    async def add_reputation_history(self, history: ReputationHistory) -> bool:
        """Add a historical reputation data point."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                significant_events_json = json.dumps(history.significant_events)
                context_data_json = json.dumps(history.context_data) if history.context_data else None
                
                cursor.execute("""
                    INSERT INTO reputation_history (
                        agent_id, timestamp, overall_score, level, confidence,
                        significant_events, context_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    history.agent_id,
                    history.timestamp.isoformat(),
                    history.overall_score,
                    history.level,
                    history.confidence,
                    significant_events_json,
                    context_data_json
                ))
                
                conn.commit()
                
                # Log operation
                await self._log_operation(DatabaseOperation.INSERT, "reputation_history", history.agent_id, history.dict())
                
                logger.debug(f"Reputation history added for agent: {history.agent_id}")
                return True
                
        except Exception as e:
            await self._log_operation(DatabaseOperation.INSERT, "reputation_history", history.agent_id, {"error": str(e)}, success=False)
            logger.error(f"Failed to add reputation history for {history.agent_id}: {e}")
            return False
    
    async def get_reputation_history(self, agent_id: str, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   limit: int = 100) -> List[ReputationHistory]:
        """Get reputation history for an agent within date range."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM reputation_history WHERE agent_id = ?"
                params = [agent_id]
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                history_list = []
                for row in rows:
                    history = ReputationHistory(
                        id=row[0],
                        agent_id=row[1],
                        timestamp=datetime.fromisoformat(row[2]),
                        overall_score=row[3],
                        level=row[4],
                        confidence=row[5],
                        significant_events=json.loads(row[6]) if row[6] else [],
                        context_data=json.loads(row[7]) if row[7] else None
                    )
                    history_list.append(history)
                
                return history_list
                
        except Exception as e:
            logger.error(f"Failed to get reputation history for {agent_id}: {e}")
            return []
    
    async def log_interaction(self, agent_id: str, interaction_type: str, 
                           interaction_data: Dict[str, Any], 
                           reputation_impact: Optional[float] = None) -> bool:
        """Log an interaction with reputation impact."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                interaction_data_json = json.dumps(interaction_data)
                
                cursor.execute("""
                    INSERT INTO interaction_logs (
                        agent_id, interaction_type, interaction_data, 
                        timestamp, reputation_impact
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    agent_id,
                    interaction_type,
                    interaction_data_json,
                    datetime.now().isoformat(),
                    reputation_impact
                ))
                
                conn.commit()
                
                # Log operation
                await self._log_operation(DatabaseOperation.INSERT, "interaction_logs", agent_id, {
                    "interaction_type": interaction_type,
                    "reputation_impact": reputation_impact
                })
                
                logger.debug(f"Interaction logged for agent: {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log interaction for {agent_id}: {e}")
            return False
    
    async def log_verification(self, agent_id: str, verification_type: str, 
                             verification_result: bool, evidence: Optional[str] = None,
                             confidence_score: Optional[float] = None) -> bool:
        """Log a verification result."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO verification_records (
                        agent_id, verification_type, verification_result,
                        evidence, confidence_score, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    agent_id,
                    verification_type,
                    verification_result,
                    evidence,
                    confidence_score,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                # Log operation
                await self._log_operation(DatabaseOperation.INSERT, "verification_records", agent_id, {
                    "verification_type": verification_type,
                    "verification_result": verification_result
                })
                
                logger.debug(f"Verification logged for agent: {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log verification for {agent_id}: {e}")
            return False
    
    async def get_agents_by_reputation_level(self, level: ReputationLevel, 
                                           limit: int = 50) -> List[ReputationRecord]:
        """Get agents filtered by reputation level."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM reputation_records 
                    WHERE level = ? 
                    ORDER BY overall_score DESC, last_updated DESC 
                    LIMIT ?
                """, (level.value, limit))
                
                rows = cursor.fetchall()
                
                return [self._row_to_reputation_record(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get agents by reputation level {level.value}: {e}")
            return []
    
    async def get_top_reputations(self, limit: int = 100, 
                                minimum_interactions: int = 10) -> List[ReputationRecord]:
        """Get top reputation records with minimum interaction threshold."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM reputation_records 
                    WHERE total_interactions >= ?
                    ORDER BY overall_score DESC, confidence DESC
                    LIMIT ?
                """, (minimum_interactions, limit))
                
                rows = cursor.fetchall()
                
                return [self._row_to_reputation_record(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get top reputations: {e}")
            return []
    
    async def get_reputation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive reputation database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM reputation_records")
                total_records = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM reputation_history")
                total_history = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM interaction_logs")
                total_interactions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM verification_records")
                total_verifications = cursor.fetchone()[0]
                
                # Level distribution
                cursor.execute("""
                    SELECT level, COUNT(*) FROM reputation_records 
                    GROUP BY level ORDER BY COUNT(*) DESC
                """)
                level_distribution = dict(cursor.fetchall())
                
                # Average scores
                cursor.execute("""
                    SELECT AVG(overall_score), AVG(confidence), AVG(total_interactions)
                    FROM reputation_records
                """)
                avg_scores = cursor.fetchone()
                
                # Recent activity (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM interaction_logs 
                    WHERE timestamp >= ?
                """, (week_ago,))
                recent_interactions = cursor.fetchone()[0]
                
                statistics = {
                    "total_records": total_records,
                    "total_history_points": total_history,
                    "total_interactions": total_interactions,
                    "total_verifications": total_verifications,
                    "level_distribution": level_distribution,
                    "average_overall_score": avg_scores[0] or 0.0,
                    "average_confidence": avg_scores[1] or 0.0,
                    "average_interactions": avg_scores[2] or 0.0,
                    "recent_interactions_7_days": recent_interactions,
                    "database_size_mb": self.db_path.stat().st_size / (1024 * 1024),
                    "last_updated": datetime.now().isoformat()
                }
                
                return statistics
                
        except Exception as e:
            logger.error(f"Failed to get reputation statistics: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = None) -> int:
        """Clean up old historical data."""
        if days_to_keep is None:
            days_to_keep = self.max_history_days
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean old history
                cursor.execute("""
                    DELETE FROM reputation_history WHERE timestamp < ?
                """, (cutoff_date,))
                history_deleted = cursor.rowcount
                
                # Clean old interaction logs
                cursor.execute("""
                    DELETE FROM interaction_logs WHERE timestamp < ?
                """, (cutoff_date,))
                interactions_deleted = cursor.rowcount
                
                # Clean old verification records
                cursor.execute("""
                    DELETE FROM verification_records WHERE timestamp < ?
                """, (cutoff_date,))
                verifications_deleted = cursor.rowcount
                
                # Clean old operation logs
                cursor.execute("""
                    DELETE FROM operation_logs WHERE timestamp < ?
                """, (cutoff_date,))
                operations_deleted = cursor.rowcount
                
                conn.commit()
                
                total_deleted = history_deleted + interactions_deleted + verifications_deleted + operations_deleted
                
                if total_deleted > 0:
                    logger.info(f"Cleaned up {total_deleted} old records older than {days_to_keep} days")
                
                return total_deleted
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    async def backup_database(self, backup_path: Optional[Path] = None) -> bool:
        """Create a backup of the database."""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"reputation_backup_{timestamp}.db"
        
        try:
            # Use SQLite backup API
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)
            
            source.backup(backup)
            
            backup.close()
            source.close()
            
            await self._log_operation(DatabaseOperation.BACKUP, "database", str(backup_path), {"backup_size": backup_path.stat().st_size})
            
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            await self._log_operation(DatabaseOperation.BACKUP, "database", str(backup_path), {"error": str(e)}, success=False)
            logger.error(f"Failed to backup database: {e}")
            return False
    
    async def _log_operation(self, operation: DatabaseOperation, table_name: str, 
                           record_id: Optional[str], operation_data: Dict[str, Any],
                           success: bool = True) -> None:
        """Log database operation for audit trail."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                operation_data_json = json.dumps(operation_data)
                error_message = None if success else operation_data.get("error")
                
                cursor.execute("""
                    INSERT INTO operation_logs (
                        operation_type, table_name, record_id, operation_data,
                        timestamp, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation.value,
                    table_name,
                    record_id,
                    operation_data_json,
                    datetime.now().isoformat(),
                    success,
                    error_message
                ))
                
                conn.commit()
                
        except Exception as e:
            # Don't let logging failures break main operations
            logger.error(f"Failed to log database operation: {e}")
    
    async def export_data(self, export_path: Path, 
                         include_history: bool = True,
                         include_interactions: bool = True,
                         include_verifications: bool = True) -> bool:
        """Export database data to JSON file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "reputation_records": [],
                "reputation_history": [],
                "interaction_logs": [],
                "verification_records": []
            }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Export reputation records
                cursor.execute("SELECT * FROM reputation_records")
                for row in cursor.fetchall():
                    record = self._row_to_reputation_record(row)
                    export_data["reputation_records"].append(record.dict())
                
                # Export history if requested
                if include_history:
                    cursor.execute("SELECT * FROM reputation_history ORDER BY timestamp")
                    for row in cursor.fetchall():
                        history = {
                            "id": row[0],
                            "agent_id": row[1],
                            "timestamp": row[2],
                            "overall_score": row[3],
                            "level": row[4],
                            "confidence": row[5],
                            "significant_events": json.loads(row[6]) if row[6] else [],
                            "context_data": json.loads(row[7]) if row[7] else None
                        }
                        export_data["reputation_history"].append(history)
                
                # Export interactions if requested
                if include_interactions:
                    cursor.execute("SELECT * FROM interaction_logs ORDER BY timestamp")
                    for row in cursor.fetchall():
                        interaction = {
                            "id": row[0],
                            "agent_id": row[1],
                            "interaction_type": row[2],
                            "interaction_data": json.loads(row[3]),
                            "timestamp": row[4],
                            "reputation_impact": row[5]
                        }
                        export_data["interaction_logs"].append(interaction)
                
                # Export verifications if requested
                if include_verifications:
                    cursor.execute("SELECT * FROM verification_records ORDER BY timestamp")
                    for row in cursor.fetchall():
                        verification = {
                            "id": row[0],
                            "agent_id": row[1],
                            "verification_type": row[2],
                            "verification_result": bool(row[3]),
                            "evidence": row[4],
                            "confidence_score": row[5],
                            "timestamp": row[6]
                        }
                        export_data["verification_records"].append(verification)
            
            # Write to file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False


# Global instance
reputation_db = ReputationDatabase()


async def get_reputation_database() -> ReputationDatabase:
    """Get the global reputation database instance."""
    return reputation_db
