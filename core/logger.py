"""
Logging configuration for Cascade Agent.
Provides structured logging with multiple handlers and levels.
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from .config import settings


class AgentLogger:
    """Centralized logging configuration for the agent."""
    
    def __init__(self):
        self.setup_logger()
    
    def setup_logger(self):
        """Configure loguru logger with custom settings."""
        # Remove default handler
        logger.remove()
        
        # Console handler with formatting
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler for persistent logs
        log_file_path = Path(settings.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} | "
                   "{message}",
            level=settings.log_level,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # Error file handler for errors and above
        error_log_path = log_file_path.parent / "error.log"
        logger.add(
            error_log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} | "
                   "{message}\n"
                   "{exception}",
            level="ERROR",
            rotation="5 MB",
            retention="90 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    def get_logger(self, name: Optional[str] = None):
        """Get a logger instance with optional name."""
        if name:
            return logger.bind(name=name)
        return logger


# Global logger instance
agent_logger = AgentLogger()


def get_logger(name: Optional[str] = None):
    """Convenience function to get a logger instance."""
    return agent_logger.get_logger(name)


# Export commonly used logger functions
__all__ = ["logger", "get_logger", "AgentLogger"]
