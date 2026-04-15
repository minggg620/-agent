"""
Zero Realm Social Agent - Challenge 4 Monitor Module
Alert System: High-value clue alert and automatic push system
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, ClassVar
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pydantic import BaseModel, Field
from core.config import settings
from core.logger import get_logger
from core.shared_memory import get_shared_memory

logger = get_logger(__name__)


class AlertType(Enum):
    """Alert type classifications."""
    HIGH_CONFIDENCE_INFORMATION = "high_confidence_information"
    CRITICAL_THREAT = "critical_threat"
    EMERGING_PATTERN = "emerging_pattern"
    SOURCE_VERIFICATION = "source_verification"
    SYSTEM_ANOMALY = "system_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_INCIDENT = "security_incident"
    DATA_BREACH = "data_breach"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class AlertStatus(Enum):
    """Alert status types."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FAILED = "failed"


class DeliveryMethod(Enum):
    """Alert delivery methods."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    PUSH_NOTIFICATION = "push_notification"
    SYSTEM_LOG = "system_log"


@dataclass
class AlertChannel:
    """Alert channel configuration."""
    channel_id: str
    name: str
    method: DeliveryMethod
    enabled: bool
    priority_threshold: AlertPriority  # Minimum priority to send
    recipients: List[str]  # Email addresses, phone numbers, webhook URLs, etc.
    configuration: Dict[str, Any]  # Channel-specific configuration
    rate_limit_per_hour: int
    last_sent: Optional[datetime] = None
    sent_count: int = 0
    
    def __post_init__(self):
        if isinstance(self.last_sent, str):
            self.last_sent = datetime.fromisoformat(self.last_sent)


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    alert_type: AlertType
    conditions: Dict[str, Any]
    priority: AlertPriority
    channels: List[str]  # Channel IDs
    enabled: bool
    auto_escalate: bool
    escalation_delay_minutes: int
    max_escalations: int
    created_at: datetime
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: Dict[str, Any]
    rule_id: Optional[str]
    channels: List[str]  # Channel IDs to send through
    status: AlertStatus
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    delivery_attempts: Dict[str, int]  # channel_id -> attempts
    escalation_level: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.sent_at, str) and self.sent_at:
            self.sent_at = datetime.fromisoformat(self.sent_at)
        if isinstance(self.delivered_at, str) and self.delivered_at:
            self.delivered_at = datetime.fromisoformat(self.delivered_at)
        if isinstance(self.acknowledged_at, str) and self.acknowledged_at:
            self.acknowledged_at = datetime.fromisoformat(self.acknowledged_at)
        if isinstance(self.resolved_at, str) and self.resolved_at:
            self.resolved_at = datetime.fromisoformat(self.resolved_at)


@dataclass
class AlertDelivery:
    """Alert delivery attempt."""
    delivery_id: str
    alert_id: str
    channel_id: str
    status: str
    sent_at: datetime
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    response_data: Optional[Dict[str, Any]]


class AlertSystem(BaseModel):
    """High-value clue alert and automatic push system."""
    
    shared_memory: ClassVar = get_shared_memory()
    
    # Alert configuration
    default_priority: AlertPriority = Field(default=AlertPriority.MEDIUM, description="Default alert priority")
    max_delivery_attempts: int = Field(default=3, description="Maximum delivery attempts per channel")
    escalation_check_interval: int = Field(default=300, description="Escalation check interval (seconds)")
    alert_retention_days: int = Field(default=30, description="Days to retain alert history")
    
    # Rate limiting
    global_rate_limit_per_hour: int = Field(default=100, description="Global rate limit per hour")
    channel_rate_limit_per_hour: int = Field(default=10, description="Per-channel rate limit per hour")
    
    # Alert state
    alert_channels: Dict[str, AlertChannel] = Field(default_factory=dict)
    alert_rules: Dict[str, AlertRule] = Field(default_factory=dict)
    active_alerts: Dict[str, Alert] = Field(default_factory=dict)
    alert_history: List[Alert] = Field(default_factory=list)
    delivery_log: List[AlertDelivery] = Field(default_factory=list)
    
    # Social Arena Agent integration
    social_arena_agent_webhook: Optional[str] = Field(default=None, description="Webhook URL for Social Arena Agent")
    auto_push_threshold: int = Field(default=85, description="Confidence threshold for auto-push to Social Arena Agent")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_default_channels()
        self._initialize_default_rules()
    
    def _initialize_default_channels(self) -> None:
        """Initialize default alert channels."""
        # Email channel
        email_channel = AlertChannel(
            channel_id="email_default",
            name="Default Email Channel",
            method=DeliveryMethod.EMAIL,
            enabled=True,
            priority_threshold=AlertPriority.MEDIUM,
            recipients=["admin@zero-realm.com"],
            configuration={
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "alerts@zero-realm.com",
                "password": "app_password",
                "use_tls": True
            },
            rate_limit_per_hour=50
        )
        self.alert_channels[email_channel.channel_id] = email_channel
        
        # System log channel
        log_channel = AlertChannel(
            channel_id="system_log",
            name="System Log Channel",
            method=DeliveryMethod.SYSTEM_LOG,
            enabled=True,
            priority_threshold=AlertPriority.LOW,
            recipients=[],
            configuration={
                "log_level": "INFO",
                "log_file": "alerts.log"
            },
            rate_limit_per_hour=1000
        )
        self.alert_channels[log_channel.channel_id] = log_channel
        
        # Webhook channel for Social Arena Agent
        if self.social_arena_agent_webhook:
            webhook_channel = AlertChannel(
                channel_id="social_arena_webhook",
                name="Social Arena Agent Webhook",
                method=DeliveryMethod.WEBHOOK,
                enabled=True,
                priority_threshold=AlertPriority.HIGH,
                recipients=[self.social_arena_agent_webhook],
                configuration={
                    "timeout": 30,
                    "retry_attempts": 3,
                    "headers": {
                        "Content-Type": "application/json",
                        "User-Agent": "ZeroRealmAlertSystem/1.0"
                    }
                },
                rate_limit_per_hour=20
            )
            self.alert_channels[webhook_channel.channel_id] = webhook_channel
        
        logger.info(f"Initialized {len(self.alert_channels)} default alert channels")
    
    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules."""
        # High confidence information rule
        high_conf_rule = AlertRule(
            rule_id="high_confidence_info",
            name="High Confidence Information Alert",
            alert_type=AlertType.HIGH_CONFIDENCE_INFORMATION,
            conditions={
                "confidence_score": {"min": 85},
                "semantic_similarity": {"min": 0.8},
                "source_reliability": {"min": 0.7}
            },
            priority=AlertPriority.HIGH,
            channels=["email_default", "social_arena_webhook"],
            enabled=True,
            auto_escalate=True,
            escalation_delay_minutes=15,
            max_escalations=3,
            created_at=datetime.now()
        )
        self.alert_rules[high_conf_rule.rule_id] = high_conf_rule
        
        # Critical threat rule
        threat_rule = AlertRule(
            rule_id="critical_threat",
            name="Critical Threat Alert",
            alert_type=AlertType.CRITICAL_THREAT,
            conditions={
                "threat_level": {"min": 8},
                "impact_score": {"min": 0.8},
                "urgency": {"equals": "high"}
            },
            priority=AlertPriority.CRITICAL,
            channels=["email_default", "social_arena_webhook"],
            enabled=True,
            auto_escalate=True,
            escalation_delay_minutes=5,
            max_escalations=5,
            created_at=datetime.now()
        )
        self.alert_rules[threat_rule.rule_id] = threat_rule
        
        logger.info(f"Initialized {len(self.alert_rules)} default alert rules")
    
    async def send_alert(self, alert_type: AlertType, data: Dict[str, Any],
                        priority: AlertPriority = None, title: str = None,
                        message: str = None, rule_id: str = None,
                        channels: List[str] = None) -> Alert:
        """Send an alert through configured channels."""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(data).encode()).hexdigest()[:8]}"
        
        # Set defaults
        priority = priority or self.default_priority
        
        # Generate title and message if not provided
        if not title:
            title = f"Alert: {alert_type.value.replace('_', ' ').title()}"
        
        if not message:
            message = self._generate_alert_message(alert_type, data)
        
        # Determine channels
        if not channels:
            if rule_id and rule_id in self.alert_rules:
                channels = self.alert_rules[rule_id].channels
            else:
                channels = self._get_channels_for_priority(priority)
        
        # Create alert
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            data=data,
            rule_id=rule_id,
            channels=channels,
            status=AlertStatus.PENDING,
            created_at=datetime.now(),
            sent_at=None,
            delivered_at=None,
            acknowledged_at=None,
            resolved_at=None,
            delivery_attempts={channel: 0 for channel in channels},
            escalation_level=0,
            metadata={"auto_generated": title is None or message is None}
        )
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Store in shared memory
        alert_key = f"alert:{alert_id}"
        self.shared_memory.set(alert_key, asdict(alert), tags=["alert", "active"])
        
        # Process alert delivery
        await self._process_alert_delivery(alert)
        
        logger.info(f"Alert created and queued for delivery: {alert_id}")
        return alert
    
    def _generate_alert_message(self, alert_type: AlertType, data: Dict[str, Any]) -> str:
        """Generate alert message based on type and data."""
        base_message = f"Alert Type: {alert_type.value.replace('_', ' ').title()}\n"
        base_message += f"Timestamp: {datetime.now().isoformat()}\n\n"
        
        if alert_type == AlertType.HIGH_CONFIDENCE_INFORMATION:
            confidence = data.get("confidence_score", 0)
            source = data.get("source", "Unknown")
            keywords = data.get("keywords", [])
            content = data.get("content", "")[:200] + "..." if len(data.get("content", "")) > 200 else data.get("content", "")
            
            message = base_message
            message += f"High confidence information detected!\n\n"
            message += f"Confidence Score: {confidence}/100\n"
            message += f"Source: {source}\n"
            message += f"Keywords: {', '.join(keywords)}\n\n"
            message += f"Content Preview:\n{content}\n"
            
        elif alert_type == AlertType.CRITICAL_THREAT:
            threat_level = data.get("threat_level", 0)
            impact = data.get("impact_score", 0)
            description = data.get("description", "No description available")
            
            message = base_message
            message += f"CRITICAL THREAT DETECTED!\n\n"
            message += f"Threat Level: {threat_level}/10\n"
            message += f"Impact Score: {impact:.2f}\n"
            message += f"Description: {description}\n"
            
        elif alert_type == AlertType.EMERGING_PATTERN:
            pattern_type = data.get("pattern_type", "Unknown")
            occurrences = data.get("occurrences", 0)
            significance = data.get("significance", 0)
            
            message = base_message
            message += f"Emerging pattern identified!\n\n"
            message += f"Pattern Type: {pattern_type}\n"
            message += f"Occurrences: {occurrences}\n"
            message += f"Significance: {significance:.2f}\n"
            
        else:
            message = base_message
            message += f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}\n"
        
        return message
    
    def _get_channels_for_priority(self, priority: AlertPriority) -> List[str]:
        """Get appropriate channels for alert priority."""
        channels = []
        
        for channel_id, channel in self.alert_channels.items():
            if channel.enabled and priority.value >= channel.priority_threshold.value:
                channels.append(channel_id)
        
        return channels
    
    async def _process_alert_delivery(self, alert: Alert) -> None:
        """Process alert delivery through all channels."""
        alert.status = AlertStatus.SENT
        alert.sent_at = datetime.now()
        
        delivery_tasks = []
        for channel_id in alert.channels:
            if channel_id in self.alert_channels:
                task = asyncio.create_task(self._send_alert_to_channel(alert, channel_id))
                delivery_tasks.append(task)
        
        # Wait for all delivery attempts
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Check if any delivery was successful
        successful_deliveries = sum(1 for result in results if not isinstance(result, Exception))
        
        if successful_deliveries > 0:
            alert.status = AlertStatus.DELIVERED
            alert.delivered_at = datetime.now()
        else:
            alert.status = AlertStatus.FAILED
        
        # Update in shared memory
        alert_key = f"alert:{alert.alert_id}"
        self.shared_memory.set(alert_key, asdict(alert), tags=["alert", "processed"])
        
        logger.info(f"Alert delivery completed: {alert.alert_id} - Status: {alert.status.value}")
    
    async def _send_alert_to_channel(self, alert: Alert, channel_id: str) -> bool:
        """Send alert to specific channel."""
        channel = self.alert_channels.get(channel_id)
        if not channel or not channel.enabled:
            return False
        
        # Check rate limiting
        if not await self._check_rate_limit(channel):
            logger.warning(f"Rate limit exceeded for channel: {channel_id}")
            return False
        
        # Update delivery attempts
        alert.delivery_attempts[channel_id] = alert.delivery_attempts.get(channel_id, 0) + 1
        
        # Check max attempts
        if alert.delivery_attempts[channel_id] > self.max_delivery_attempts:
            logger.error(f"Max delivery attempts exceeded for channel: {channel_id}")
            return False
        
        # Create delivery record
        delivery_id = f"delivery_{alert.alert_id}_{channel_id}_{alert.delivery_attempts[channel_id]}"
        delivery = AlertDelivery(
            delivery_id=delivery_id,
            alert_id=alert.alert_id,
            channel_id=channel_id,
            status="pending",
            sent_at=datetime.now(),
            delivered_at=None,
            error_message=None,
            response_data=None
        )
        
        try:
            # Send based on channel method
            success = False
            if channel.method == DeliveryMethod.EMAIL:
                success = await self._send_email_alert(alert, channel)
            elif channel.method == DeliveryMethod.WEBHOOK:
                success = await self._send_webhook_alert(alert, channel)
            elif channel.method == DeliveryMethod.SYSTEM_LOG:
                success = await self._send_log_alert(alert, channel)
            else:
                logger.warning(f"Unsupported delivery method: {channel.method.value}")
                success = False
            
            # Update delivery record
            delivery.status = "sent" if success else "failed"
            delivery.delivered_at = datetime.now() if success else None
            
            if success:
                channel.last_sent = datetime.now()
                channel.sent_count += 1
            
            self.delivery_log.append(delivery)
            
            return success
            
        except Exception as e:
            delivery.status = "error"
            delivery.error_message = str(e)
            self.delivery_log.append(delivery)
            
            logger.error(f"Failed to send alert to channel {channel_id}: {e}")
            return False
    
    async def _check_rate_limit(self, channel: AlertChannel) -> bool:
        """Check if channel is within rate limits."""
        now = datetime.now()
        
        # Check hourly rate limit
        if channel.last_sent:
            hours_since_last = (now - channel.last_sent).total_seconds() / 3600
            if hours_since_last < 1 and channel.sent_count >= channel.rate_limit_per_hour:
                return False
        
        # Reset counter if hour has passed
        if channel.last_sent and (now - channel.last_sent).total_seconds() >= 3600:
            channel.sent_count = 0
        
        return True
    
    async def _send_email_alert(self, alert: Alert, channel: AlertChannel) -> bool:
        """Send alert via email."""
        try:
            config = channel.configuration
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config.get("username", "alerts@zero-realm.com")
            msg['To'] = ", ".join(channel.recipients)
            msg['Subject'] = f"[ZERO REALM ALERT] {alert.title}"
            
            # Email body
            body = f"""
            Alert ID: {alert.alert_id}
            Priority: {alert.priority.name}
            Type: {alert.alert_type.value}
            Created: {alert.created_at.isoformat()}
            
            {alert.message}
            
            ---
            Zero Realm Social Agent Alert System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (simulation - in real implementation, use smtplib)
            logger.info(f"Email alert sent to {len(channel.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def _send_webhook_alert(self, alert: Alert, channel: AlertChannel) -> bool:
        """Send alert via webhook."""
        try:
            config = channel.configuration
            
            # Prepare webhook payload
            payload = {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "priority": alert.priority.name,
                "title": alert.title,
                "message": alert.message,
                "data": alert.data,
                "created_at": alert.created_at.isoformat(),
                "source": "zero_realm_monitor"
            }
            
            # Send webhook (simulation - in real implementation, use aiohttp)
            for recipient in channel.recipients:
                logger.info(f"Webhook alert sent to: {recipient}")
                logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    async def _send_log_alert(self, alert: Alert, channel: AlertChannel) -> bool:
        """Send alert to system log."""
        try:
            config = channel.configuration
            log_level = config.get("log_level", "INFO")
            
            log_message = f"ALERT [{alert.priority.name}] {alert.title}: {alert.message}"
            
            if log_level == "INFO":
                logger.info(log_message)
            elif log_level == "WARNING":
                logger.warning(log_message)
            elif log_level == "ERROR":
                logger.error(log_message)
            elif log_level == "CRITICAL":
                logger.critical(log_message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send log alert: {e}")
            return False
    
    async def auto_push_to_social_arena(self, information_item: Dict[str, Any]) -> bool:
        """Automatically push high-confidence information to Social Arena Agent."""
        confidence_score = information_item.get("confidence_score", 0)
        
        if confidence_score >= self.auto_push_threshold:
            # Create alert for Social Arena Agent
            alert_data = {
                "item_id": information_item.get("item_id"),
                "source": information_item.get("source"),
                "content": information_item.get("content"),
                "confidence_score": confidence_score,
                "keywords": information_item.get("keywords", []),
                "timestamp": information_item.get("timestamp"),
                "auto_push": True
            }
            
            await self.send_alert(
                alert_type=AlertType.HIGH_CONFIDENCE_INFORMATION,
                data=alert_data,
                priority=AlertPriority.HIGH,
                title=f"Auto-Push: High Confidence Information ({confidence_score}/100)",
                channels=["social_arena_webhook"]
            )
            
            logger.info(f"Auto-pushed information to Social Arena Agent: {information_item.get('item_id')}")
            return True
        
        return False
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False
        
        alert.acknowledged_at = datetime.now()
        alert.status = AlertStatus.ACKNOWLEDGED
        
        # Update in shared memory
        alert_key = f"alert:{alert_id}"
        self.shared_memory.set(alert_key, asdict(alert), tags=["alert", "acknowledged"])
        
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Resolve an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False
        
        alert.resolved_at = datetime.now()
        alert.status = AlertStatus.RESOLVED
        
        if resolution_note:
            alert.metadata = alert.metadata or {}
            alert.metadata["resolution_note"] = resolution_note
        
        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]
        
        # Update in shared memory
        alert_key = f"alert:{alert_id}"
        self.shared_memory.set(alert_key, asdict(alert), tags=["alert", "resolved"])
        
        logger.info(f"Alert resolved: {alert_id}")
        return True
    
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get comprehensive alert statistics."""
        total_alerts = len(self.active_alerts) + len(self.alert_history)
        
        # Status distribution
        status_dist = {
            "pending": len([a for a in self.active_alerts.values() if a.status == AlertStatus.PENDING]),
            "sent": len([a for a in self.active_alerts.values() if a.status == AlertStatus.SENT]),
            "delivered": len([a for a in self.active_alerts.values() if a.status == AlertStatus.DELIVERED]),
            "acknowledged": len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACKNOWLEDGED]),
            "resolved": len(self.alert_history)
        }
        
        # Priority distribution
        priority_dist = {}
        for alert in list(self.active_alerts.values()) + self.alert_history:
            priority_name = alert.priority.name
            priority_dist[priority_name] = priority_dist.get(priority_name, 0) + 1
        
        # Type distribution
        type_dist = {}
        for alert in list(self.active_alerts.values()) + self.alert_history:
            type_name = alert.alert_type.value
            type_dist[type_name] = type_dist.get(type_name, 0) + 1
        
        # Channel performance
        channel_performance = {}
        for channel_id, channel in self.alert_channels.items():
            channel_performance[channel_id] = {
                "enabled": channel.enabled,
                "sent_count": channel.sent_count,
                "last_sent": channel.last_sent.isoformat() if channel.last_sent else None,
                "rate_limit": channel.rate_limit_per_hour
            }
        
        # Delivery statistics
        delivery_stats = {
            "total_deliveries": len(self.delivery_log),
            "successful_deliveries": len([d for d in self.delivery_log if d.status == "sent"]),
            "failed_deliveries": len([d for d in self.delivery_log if d.status in ["failed", "error"]]),
            "average_delivery_time": 0.0  # Would calculate from delivery logs
        }
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": len(self.active_alerts),
            "resolved_alerts": len(self.alert_history),
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "type_distribution": type_dist,
            "channel_performance": channel_performance,
            "delivery_statistics": delivery_stats,
            "auto_push_threshold": self.auto_push_threshold,
            "last_updated": datetime.now().isoformat()
        }
    
    async def cleanup_old_alerts(self, days_to_keep: int = None) -> int:
        """Clean up old resolved alerts."""
        if days_to_keep is None:
            days_to_keep = self.alert_retention_days
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        old_alerts = [
            alert for alert in self.alert_history
            if alert.resolved_at and alert.resolved_at < cutoff_time
        ]
        
        # Remove old alerts
        for alert in old_alerts:
            self.alert_history.remove(alert)
        
        # Clean up old delivery logs
        cutoff_delivery_time = datetime.now() - timedelta(days=7)
        old_deliveries = [
            delivery for delivery in self.delivery_log
            if delivery.sent_at < cutoff_delivery_time
        ]
        
        for delivery in old_deliveries:
            self.delivery_log.remove(delivery)
        
        logger.info(f"Cleaned up {len(old_alerts)} old alerts and {len(old_deliveries)} old delivery logs")
        return len(old_alerts) + len(old_deliveries)


# Global instance
alert_system = AlertSystem()


def get_alert_system() -> AlertSystem:
    """Get the global alert system instance."""
    return alert_system
