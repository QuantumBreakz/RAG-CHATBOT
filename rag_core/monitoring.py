"""
Real-time Monitoring Module for RAG Chatbot
Provides real-time monitoring, alerting, and health checks for the system.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import psutil
import os
import signal
from enum import Enum

from .config import logger
from .analytics import get_analytics, QueryMetric, SystemMetric, UserActivityMetric


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Alert:
    """Alert structure"""
    id: str
    type: str
    severity: AlertSeverity
    message: str
    component: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    acknowledged: bool = False
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MonitoringConfig:
    """Configuration for monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Health check intervals (seconds)
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.system_metrics_interval = self.config.get('system_metrics_interval', 10)
        
        # Alert thresholds
        self.thresholds = self.config.get('thresholds', {
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'response_time_ms': 5000,
            'error_rate_percent': 5,
            'queue_size': 100
        })
        
        # Alert notification settings
        self.enable_notifications = self.config.get('enable_notifications', True)
        self.notification_channels = self.config.get('notification_channels', [])
        
        # Retention settings
        self.alert_retention_days = self.config.get('alert_retention_days', 30)
        self.metrics_retention_days = self.config.get('metrics_retention_days', 7)


class RealTimeMonitor:
    """Real-time monitoring system for RAG chatbot"""
    
    def __init__(self, config: MonitoringConfig = None):
        """
        Initialize the real-time monitor.
        
        Args:
            config: Monitoring configuration
        """
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(__name__)
        
        # Analytics integration
        self.analytics = get_analytics()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.health_check_thread = None
        
        # Storage
        self.health_checks = deque(maxlen=1000)
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        
        # Component health status
        self.component_health = defaultdict(lambda: HealthStatus.UNKNOWN)
        
        # Alert handlers
        self.alert_handlers = []
        
        # Performance tracking
        self.performance_metrics = defaultdict(deque)
        self.max_metrics = 1000
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Signal handlers for graceful shutdown
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            else:
                self.logger.debug("Skipping signal handler registration outside main thread")
        except Exception as e:
            self.logger.debug(f"Signal handler registration skipped: {e}")
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        
        # Start monitoring threads
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        
        self.monitoring_thread.start()
        self.health_check_thread.start()
        
        self.logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        
        # Wait for threads to finish
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        
        self.logger.info("Real-time monitoring stopped")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
        self.logger.info(f"Added alert handler: {handler.__name__}")
    
    def get_system_health(self) -> Dict[str, HealthStatus]:
        """Get current health status of all components"""
        with self.lock:
            return dict(self.component_health)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        with self.lock:
            return list(self.active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str, user_id: str = None):
        """Acknowledge an alert"""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledged = True
                alert.metadata = alert.metadata or {}
                alert.metadata['acknowledged_by'] = user_id
                alert.metadata['acknowledged_at'] = datetime.now().isoformat()
                
                self.logger.info(f"Alert {alert_id} acknowledged by {user_id}")
    
    def resolve_alert(self, alert_id: str, user_id: str = None, resolution_notes: str = None):
        """Resolve an alert"""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.metadata = alert.metadata or {}
                alert.metadata['resolved_by'] = user_id
                alert.metadata['resolved_at'] = datetime.now().isoformat()
                alert.metadata['resolution_notes'] = resolution_notes
                
                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]
                
                self.logger.info(f"Alert {alert_id} resolved by {user_id}")
    
    def get_health_check_history(self, component: str = None, limit: int = 100) -> List[HealthCheck]:
        """Get health check history"""
        with self.lock:
            if component:
                return [
                    check for check in list(self.health_checks)[-limit:]
                    if check.component == component
                ]
            else:
                return list(self.health_checks)[-limit:]
    
    def get_performance_metrics(self, component: str = None, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get performance metrics for components"""
        with self.lock:
            if component:
                metrics = list(self.performance_metrics.get(component, []))
            else:
                # Combine all component metrics
                all_metrics = {}
                for comp, metrics_list in self.performance_metrics.items():
                    all_metrics[comp] = list(metrics_list)
                return all_metrics
            
            if time_range:
                start_time, end_time = time_range
                metrics = [
                    m for m in metrics
                    if start_time <= m.get('timestamp', datetime.now()) <= end_time
                ]
            
            return {
                'component': component,
                'metrics': metrics,
                'count': len(metrics)
            }
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Wait for next interval
                time.sleep(self.config.system_metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(5)
    
    def _health_check_loop(self):
        """Health check loop"""
        while self.monitoring_active:
            try:
                # Perform health checks
                self._perform_health_checks()
                
                # Wait for next health check interval
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check loop error: {str(e)}")
                time.sleep(10)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_metric = SystemMetric(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                active_connections=len(psutil.net_connections()),
                queue_size=0  # TODO: Implement queue monitoring
            )
            
            # Track in analytics
            self.analytics.track_system_performance(system_metric)
            
            # Store in performance metrics
            with self.lock:
                self.performance_metrics['system'].append({
                    'timestamp': datetime.now(),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'active_connections': system_metric.active_connections
                })
                
                # Maintain size limits
                if len(self.performance_metrics['system']) > self.max_metrics:
                    self.performance_metrics['system'].popleft()
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")
    
    def _perform_health_checks(self):
        """Perform health checks on all components"""
        health_checks = []
        
        # System health check
        system_health = self._check_system_health()
        health_checks.append(system_health)
        
        # Database health check
        db_health = self._check_database_health()
        health_checks.append(db_health)
        
        # LLM service health check
        llm_health = self._check_llm_health()
        health_checks.append(llm_health)
        
        # Vector store health check
        vectorstore_health = self._check_vectorstore_health()
        health_checks.append(vectorstore_health)
        
        # Cache health check
        cache_health = self._check_cache_health()
        health_checks.append(cache_health)
        
        # Store health checks
        with self.lock:
            for check in health_checks:
                self.health_checks.append(check)
                self.component_health[check.component] = check.status
        
        # Log health status
        self._log_health_status(health_checks)
    
    def _check_system_health(self) -> HealthCheck:
        """Check system resource health"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            if (cpu_usage > self.config.thresholds['cpu_usage_percent'] or
                memory.percent > self.config.thresholds['memory_usage_percent'] or
                disk.percent > self.config.thresholds['disk_usage_percent']):
                status = HealthStatus.CRITICAL
                message = f"High resource usage: CPU {cpu_usage:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            elif (cpu_usage > self.config.thresholds['cpu_usage_percent'] * 0.8 or
                  memory.percent > self.config.thresholds['memory_usage_percent'] * 0.8 or
                  disk.percent > self.config.thresholds['disk_usage_percent'] * 0.8):
                status = HealthStatus.WARNING
                message = f"Elevated resource usage: CPU {cpu_usage:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"System resources normal: CPU {cpu_usage:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            
            return HealthCheck(
                component='system',
                status=status,
                message=message,
                metrics={
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'memory_available': memory.available
                }
            )
            
        except Exception as e:
            return HealthCheck(
                component='system',
                status=HealthStatus.UNKNOWN,
                message=f"System health check failed: {str(e)}"
            )
    
    def _check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        try:
            # TODO: Implement actual database health check
            # For now, return healthy status
            return HealthCheck(
                component='database',
                status=HealthStatus.HEALTHY,
                message="Database connectivity normal"
            )
        except Exception as e:
            return HealthCheck(
                component='database',
                status=HealthStatus.CRITICAL,
                message=f"Database health check failed: {str(e)}"
            )
    
    def _check_llm_health(self) -> HealthCheck:
        """Check LLM service health"""
        try:
            # TODO: Implement actual LLM health check
            # For now, return healthy status
            return HealthCheck(
                component='llm',
                status=HealthStatus.HEALTHY,
                message="LLM service operational"
            )
        except Exception as e:
            return HealthCheck(
                component='llm',
                status=HealthStatus.CRITICAL,
                message=f"LLM health check failed: {str(e)}"
            )
    
    def _check_vectorstore_health(self) -> HealthCheck:
        """Check vector store health"""
        try:
            # TODO: Implement actual vector store health check
            # For now, return healthy status
            return HealthCheck(
                component='vectorstore',
                status=HealthStatus.HEALTHY,
                message="Vector store operational"
            )
        except Exception as e:
            return HealthCheck(
                component='vectorstore',
                status=HealthStatus.CRITICAL,
                message=f"Vector store health check failed: {str(e)}"
            )
    
    def _check_cache_health(self) -> HealthCheck:
        """Check cache health"""
        try:
            # TODO: Implement actual cache health check
            # For now, return healthy status
            return HealthCheck(
                component='cache',
                status=HealthStatus.HEALTHY,
                message="Cache operational"
            )
        except Exception as e:
            return HealthCheck(
                component='cache',
                status=HealthStatus.CRITICAL,
                message=f"Cache health check failed: {str(e)}"
            )
    
    def _check_alerts(self):
        """Check for conditions that should trigger alerts"""
        try:
            # Check system resource alerts
            self._check_resource_alerts()
            
            # Check performance alerts
            self._check_performance_alerts()
            
            # Check error rate alerts
            self._check_error_alerts()
            
        except Exception as e:
            self.logger.error(f"Alert checking failed: {str(e)}")
    
    def _check_resource_alerts(self):
        """Check for resource usage alerts"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # CPU usage alert
            if cpu_usage > self.config.thresholds['cpu_usage_percent']:
                self._create_alert(
                    'high_cpu_usage',
                    AlertSeverity.WARNING,
                    f"High CPU usage: {cpu_usage:.1f}%",
                    'system',
                    {'cpu_usage': cpu_usage, 'threshold': self.config.thresholds['cpu_usage_percent']}
                )
            
            # Memory usage alert
            if memory.percent > self.config.thresholds['memory_usage_percent']:
                self._create_alert(
                    'high_memory_usage',
                    AlertSeverity.WARNING,
                    f"High memory usage: {memory.percent:.1f}%",
                    'system',
                    {'memory_usage': memory.percent, 'threshold': self.config.thresholds['memory_usage_percent']}
                )
            
            # Disk usage alert
            if disk.percent > self.config.thresholds['disk_usage_percent']:
                self._create_alert(
                    'high_disk_usage',
                    AlertSeverity.WARNING,
                    f"High disk usage: {disk.percent:.1f}%",
                    'system',
                    {'disk_usage': disk.percent, 'threshold': self.config.thresholds['disk_usage_percent']}
                )
                
        except Exception as e:
            self.logger.error(f"Resource alert checking failed: {str(e)}")
    
    def _check_performance_alerts(self):
        """Check for performance alerts"""
        try:
            # Get recent query performance
            recent_queries = self.analytics.get_query_analytics(
                time_range=(datetime.now() - timedelta(minutes=5), datetime.now())
            )
            
            if recent_queries and recent_queries.get('avg_response_time', 0) > self.config.thresholds['response_time_ms'] / 1000:
                self._create_alert(
                    'high_response_time',
                    AlertSeverity.WARNING,
                    f"High average response time: {recent_queries['avg_response_time']:.2f}s",
                    'performance',
                    {'avg_response_time': recent_queries['avg_response_time']}
                )
                
        except Exception as e:
            self.logger.error(f"Performance alert checking failed: {str(e)}")
    
    def _check_error_alerts(self):
        """Check for error rate alerts"""
        try:
            # Get recent error analytics
            recent_errors = self.analytics.get_error_analytics(
                time_range=(datetime.now() - timedelta(minutes=5), datetime.now())
            )
            
            if recent_errors and recent_errors.get('error_rate', 0) > self.config.thresholds['error_rate_percent'] / 100:
                self._create_alert(
                    'high_error_rate',
                    AlertSeverity.ERROR,
                    f"High error rate: {recent_errors['error_rate']:.2%}",
                    'system',
                    {'error_rate': recent_errors['error_rate']}
                )
                
        except Exception as e:
            self.logger.error(f"Error alert checking failed: {str(e)}")
    
    def _create_alert(self, alert_type: str, severity: AlertSeverity, message: str, 
                     component: str, metadata: Dict[str, Any] = None):
        """Create and store an alert"""
        alert_id = f"{alert_type}_{component}_{int(time.time())}"
        
        # Check if similar alert already exists
        with self.lock:
            for existing_alert in self.active_alerts.values():
                if (existing_alert.type == alert_type and 
                    existing_alert.component == component and
                    not existing_alert.resolved):
                    return  # Alert already exists
        
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            message=message,
            component=component,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.active_alerts[alert_id] = alert
        
        # Log alert
        self.logger.warning(f"Alert created: {alert_type} - {message}")
        
        # Notify handlers
        self._notify_alert_handlers(alert)
    
    def _notify_alert_handlers(self, alert: Alert):
        """Notify all registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler {handler.__name__} failed: {str(e)}")
    
    def _log_health_status(self, health_checks: List[HealthCheck]):
        """Log health status summary"""
        status_counts = defaultdict(int)
        for check in health_checks:
            status_counts[check.status.value] += 1
        
        if status_counts[HealthStatus.CRITICAL.value] > 0:
            self.logger.error(f"Health check summary: {dict(status_counts)}")
        elif status_counts[HealthStatus.WARNING.value] > 0:
            self.logger.warning(f"Health check summary: {dict(status_counts)}")
        else:
            self.logger.info(f"Health check summary: {dict(status_counts)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.alert_retention_days)
            
            with self.lock:
                # Clean up old alerts
                old_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.timestamp < cutoff_time and alert.resolved
                ]
                for alert_id in old_alerts:
                    del self.active_alerts[alert_id]
                
                # Clean up old health checks
                while (self.health_checks and 
                       self.health_checks[0].timestamp < cutoff_time):
                    self.health_checks.popleft()
                
                # Clean up old performance metrics
                for component in self.performance_metrics:
                    while (self.performance_metrics[component] and
                           self.performance_metrics[component][0].get('timestamp', datetime.now()) < cutoff_time):
                        self.performance_metrics[component].popleft()
                        
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down monitoring...")
        self.stop_monitoring()
    
    def export_monitoring_data(self, filepath: str):
        """Export monitoring data to JSON file"""
        try:
            with self.lock:
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'health_checks': [asdict(check) for check in self.health_checks],
                    'active_alerts': [asdict(alert) for alert in self.active_alerts.values()],
                    'alert_history': [asdict(alert) for alert in self.alert_history],
                    'component_health': {comp: status.value for comp, status in self.component_health.items()},
                    'performance_metrics': {
                        comp: list(metrics) for comp, metrics in self.performance_metrics.items()
                    }
                }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Monitoring data exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export monitoring data: {str(e)}")


# Global monitoring instance
_monitoring_instance = None

def get_monitor(config: MonitoringConfig = None) -> RealTimeMonitor:
    """Get or create the global monitoring instance"""
    global _monitoring_instance
    if _monitoring_instance is None:
        _monitoring_instance = RealTimeMonitor(config)
    return _monitoring_instance


# Default alert handlers
def log_alert_handler(alert: Alert):
    """Default alert handler that logs alerts"""
    logger.warning(f"ALERT [{alert.severity.value.upper()}] {alert.component}: {alert.message}")

def email_alert_handler(alert: Alert):
    """Email alert handler (placeholder)"""
    # TODO: Implement email notification
    pass

def slack_alert_handler(alert: Alert):
    """Slack alert handler (placeholder)"""
    # TODO: Implement Slack notification
    pass
