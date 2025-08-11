"""
Performance Analytics and Monitoring Module for RAG Chatbot
Provides comprehensive analytics, performance tracking, and monitoring capabilities.
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import psutil
import os
from enum import Enum

from .config import logger


class MetricType(Enum):
    """Types of metrics that can be tracked"""
    QUERY_PERFORMANCE = "query_performance"
    SYSTEM_PERFORMANCE = "system_performance"
    USER_ACTIVITY = "user_activity"
    DOCUMENT_PROCESSING = "document_processing"
    RERANKING_PERFORMANCE = "reranking_performance"
    CACHE_PERFORMANCE = "cache_performance"
    ERROR_TRACKING = "error_tracking"


@dataclass
class PerformanceMetric:
    """Base performance metric structure"""
    metric_type: str
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class QueryMetric:
    """Query-specific performance metrics"""
    query_id: str
    query_text: str
    processing_time: float
    response_time: float
    chunk_count: int
    reranking_time: float
    llm_time: float
    cache_hit: bool
    user_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SystemMetric:
    """System-level performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    queue_size: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class UserActivityMetric:
    """User activity tracking metrics"""
    user_id: str
    session_id: str
    action_type: str
    action_data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceAnalytics:
    """Comprehensive performance analytics and monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the analytics system.
        
        Args:
            config: Configuration dictionary with analytics settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Storage for metrics
        self.metrics_storage = defaultdict(deque)
        self.max_metrics_per_type = self.config.get('max_metrics_per_type', 10000)
        
        # Performance tracking
        self.query_metrics = deque(maxlen=self.max_metrics_per_type)
        self.system_metrics = deque(maxlen=self.max_metrics_per_type)
        self.user_activity = deque(maxlen=self.max_metrics_per_type)
        self.error_logs = deque(maxlen=self.max_metrics_per_type)
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = self.config.get('monitoring_interval', 30)  # seconds
        
        # Alert thresholds
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'response_time_ms': 5000,
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'error_rate_percent': 5
        })
        
        # Performance baselines
        self.performance_baselines = {}
        self.baseline_calculation_days = self.config.get('baseline_calculation_days', 7)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Start monitoring if enabled
        if self.config.get('auto_start_monitoring', True):
            self.start_monitoring()
    
    def track_query_performance(self, query_metric: QueryMetric):
        """Track query performance metrics"""
        with self.lock:
            self.query_metrics.append(query_metric)
            self._store_metric(MetricType.QUERY_PERFORMANCE, query_metric)
        
        # Check for performance alerts
        self._check_query_alerts(query_metric)
    
    def track_system_performance(self, system_metric: SystemMetric):
        """Track system performance metrics"""
        with self.lock:
            self.system_metrics.append(system_metric)
            self._store_metric(MetricType.SYSTEM_PERFORMANCE, system_metric)
        
        # Check for system alerts
        self._check_system_alerts(system_metric)
    
    def track_user_activity(self, activity_metric: UserActivityMetric):
        """Track user activity metrics"""
        with self.lock:
            self.user_activity.append(activity_metric)
            self._store_metric(MetricType.USER_ACTIVITY, activity_metric)
    
    def track_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Track error occurrences"""
        error_metric = {
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'timestamp': datetime.now(),
            'stack_trace': self._get_stack_trace()
        }
        
        with self.lock:
            self.error_logs.append(error_metric)
            self._store_metric(MetricType.ERROR_TRACKING, error_metric)
        
        # Check error rate alerts
        self._check_error_alerts()
    
    def get_performance_stats(self, metric_type: MetricType = None, 
                            time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get performance statistics for specified metric type and time range"""
        with self.lock:
            if metric_type:
                metrics = self._get_metrics_in_range(metric_type, time_range)
                return self._calculate_stats_for_metrics(metrics, metric_type.value)
            else:
                # Return overall stats
                return self._calculate_overall_stats(time_range)
    
    def get_query_analytics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get detailed query analytics"""
        with self.lock:
            queries = self._get_metrics_in_range(MetricType.QUERY_PERFORMANCE, time_range)
            
            if not queries:
                return {}
            
            # Calculate query statistics
            response_times = [q.response_time for q in queries]
            processing_times = [q.processing_time for q in queries]
            chunk_counts = [q.chunk_count for q in queries]
            cache_hits = sum(1 for q in queries if q.cache_hit)
            
            return {
                'total_queries': len(queries),
                'avg_response_time': sum(response_times) / len(response_times),
                'max_response_time': max(response_times),
                'min_response_time': min(response_times),
                'avg_processing_time': sum(processing_times) / len(processing_times),
                'avg_chunk_count': sum(chunk_counts) / len(chunk_counts),
                'cache_hit_rate': cache_hits / len(queries) if queries else 0,
                'query_volume_by_hour': self._calculate_hourly_volume(queries),
                'top_queries': self._get_top_queries(queries),
                'performance_trends': self._calculate_performance_trends(queries)
            }
    
    def get_system_analytics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get detailed system analytics"""
        with self.lock:
            system_metrics = self._get_metrics_in_range(MetricType.SYSTEM_PERFORMANCE, time_range)
            
            if not system_metrics:
                return {}
            
            # Calculate system statistics
            cpu_usage = [m.cpu_usage for m in system_metrics]
            memory_usage = [m.memory_usage for m in system_metrics]
            disk_usage = [m.disk_usage for m in system_metrics]
            
            return {
                'avg_cpu_usage': sum(cpu_usage) / len(cpu_usage),
                'max_cpu_usage': max(cpu_usage),
                'avg_memory_usage': sum(memory_usage) / len(memory_usage),
                'max_memory_usage': max(memory_usage),
                'avg_disk_usage': sum(disk_usage) / len(disk_usage),
                'max_disk_usage': max(disk_usage),
                'system_health_score': self._calculate_system_health_score(system_metrics),
                'resource_utilization_trends': self._calculate_resource_trends(system_metrics),
                'peak_usage_times': self._find_peak_usage_times(system_metrics)
            }
    
    def get_user_analytics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get user activity analytics"""
        with self.lock:
            activities = self._get_metrics_in_range(MetricType.USER_ACTIVITY, time_range)
            
            if not activities:
                return {}
            
            # Calculate user statistics
            unique_users = len(set(a.user_id for a in activities))
            unique_sessions = len(set(a.session_id for a in activities))
            action_counts = defaultdict(int)
            
            for activity in activities:
                action_counts[activity.action_type] += 1
            
            return {
                'total_activities': len(activities),
                'unique_users': unique_users,
                'unique_sessions': unique_sessions,
                'avg_activities_per_user': len(activities) / unique_users if unique_users > 0 else 0,
                'action_distribution': dict(action_counts),
                'user_engagement_score': self._calculate_user_engagement(activities),
                'peak_activity_times': self._find_peak_activity_times(activities),
                'user_retention_metrics': self._calculate_user_retention(activities)
            }
    
    def get_error_analytics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get error analytics"""
        with self.lock:
            errors = self._get_metrics_in_range(MetricType.ERROR_TRACKING, time_range)
            
            if not errors:
                return {}
            
            # Calculate error statistics
            error_types = defaultdict(int)
            for error in errors:
                error_types[error['error_type']] += 1
            
            total_queries = len(self._get_metrics_in_range(MetricType.QUERY_PERFORMANCE, time_range))
            error_rate = len(errors) / total_queries if total_queries > 0 else 0
            
            return {
                'total_errors': len(errors),
                'error_rate': error_rate,
                'error_types': dict(error_types),
                'most_common_errors': self._get_most_common_errors(errors),
                'error_trends': self._calculate_error_trends(errors),
                'error_impact_analysis': self._analyze_error_impact(errors)
            }
    
    def start_monitoring(self):
        """Start real-time system monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Performance monitoring stopped")
    
    def export_metrics(self, filepath: str, metric_types: List[MetricType] = None):
        """Export metrics to JSON file"""
        with self.lock:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': {}
            }
            
            if metric_types is None:
                metric_types = list(MetricType)
            
            for metric_type in metric_types:
                metrics = list(self.metrics_storage[metric_type.value])
                export_data['metrics'][metric_type.value] = [
                    asdict(m) if hasattr(m, '__dataclass_fields__') else m 
                    for m in metrics
                ]
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Metrics exported to {filepath}")
    
    def generate_performance_report(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            'report_timestamp': datetime.now().isoformat(),
            'time_range': {
                'start': time_range[0].isoformat() if time_range else None,
                'end': time_range[1].isoformat() if time_range else None
            },
            'query_analytics': self.get_query_analytics(time_range),
            'system_analytics': self.get_system_analytics(time_range),
            'user_analytics': self.get_user_analytics(time_range),
            'error_analytics': self.get_error_analytics(time_range),
            'performance_recommendations': self._generate_recommendations(time_range),
            'alerts': self._get_active_alerts()
        }
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metric = self._collect_system_metrics()
                self.track_system_performance(system_metric)
                
                # Wait for next monitoring interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(5)  # Brief pause on error
    
    def _collect_system_metrics(self) -> SystemMetric:
        """Collect current system metrics"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemMetric(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                active_connections=len(psutil.net_connections()),
                queue_size=0  # Placeholder - implement queue monitoring
            )
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")
            return SystemMetric(0, 0, 0, 0, 0)
    
    def _store_metric(self, metric_type: MetricType, metric: Any):
        """Store metric in appropriate storage"""
        self.metrics_storage[metric_type.value].append(metric)
        
        # Maintain storage limits
        if len(self.metrics_storage[metric_type.value]) > self.max_metrics_per_type:
            self.metrics_storage[metric_type.value].popleft()
    
    def _get_metrics_in_range(self, metric_type: MetricType, 
                            time_range: Optional[Tuple[datetime, datetime]]) -> List[Any]:
        """Get metrics within specified time range"""
        metrics = list(self.metrics_storage[metric_type.value])
        
        if not time_range:
            return metrics
        
        start_time, end_time = time_range
        return [
            m for m in metrics 
            if hasattr(m, 'timestamp') and start_time <= m.timestamp <= end_time
        ]
    
    def _calculate_stats_for_metrics(self, metrics: List[Any], metric_type: str) -> Dict[str, Any]:
        """Calculate basic statistics for a list of metrics"""
        if not metrics:
            return {}
        
        # Extract numeric values based on metric type
        if metric_type == MetricType.QUERY_PERFORMANCE.value:
            values = [m.response_time for m in metrics if hasattr(m, 'response_time')]
        elif metric_type == MetricType.SYSTEM_PERFORMANCE.value:
            values = [m.cpu_usage for m in metrics if hasattr(m, 'cpu_usage')]
        else:
            values = [getattr(m, 'value', 0) for m in metrics if hasattr(m, 'value')]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1] if values else 0
        }
    
    def _calculate_overall_stats(self, time_range: Optional[Tuple[datetime, datetime]]) -> Dict[str, Any]:
        """Calculate overall performance statistics"""
        return {
            'query_performance': self.get_query_analytics(time_range),
            'system_performance': self.get_system_analytics(time_range),
            'user_activity': self.get_user_analytics(time_range),
            'error_tracking': self.get_error_analytics(time_range)
        }
    
    def _check_query_alerts(self, query_metric: QueryMetric):
        """Check for query performance alerts"""
        threshold = self.alert_thresholds.get('response_time_ms', 5000)
        if query_metric.response_time > threshold / 1000:  # Convert to seconds
            self._trigger_alert('high_response_time', {
                'query_id': query_metric.query_id,
                'response_time': query_metric.response_time,
                'threshold': threshold / 1000
            })
    
    def _check_system_alerts(self, system_metric: SystemMetric):
        """Check for system performance alerts"""
        cpu_threshold = self.alert_thresholds.get('cpu_usage_percent', 80)
        memory_threshold = self.alert_thresholds.get('memory_usage_percent', 85)
        
        if system_metric.cpu_usage > cpu_threshold:
            self._trigger_alert('high_cpu_usage', {
                'cpu_usage': system_metric.cpu_usage,
                'threshold': cpu_threshold
            })
        
        if system_metric.memory_usage > memory_threshold:
            self._trigger_alert('high_memory_usage', {
                'memory_usage': system_metric.memory_usage,
                'threshold': memory_threshold
            })
    
    def _check_error_alerts(self):
        """Check for error rate alerts"""
        # Calculate error rate for last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = len(self._get_metrics_in_range(MetricType.ERROR_TRACKING, (one_hour_ago, datetime.now())))
        recent_queries = len(self._get_metrics_in_range(MetricType.QUERY_PERFORMANCE, (one_hour_ago, datetime.now())))
        
        if recent_queries > 0:
            error_rate = (recent_errors / recent_queries) * 100
            threshold = self.alert_thresholds.get('error_rate_percent', 5)
            
            if error_rate > threshold:
                self._trigger_alert('high_error_rate', {
                    'error_rate': error_rate,
                    'threshold': threshold,
                    'errors': recent_errors,
                    'queries': recent_queries
                })
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Trigger a performance alert"""
        alert = {
            'type': alert_type,
            'data': alert_data,
            'timestamp': datetime.now(),
            'severity': 'warning'
        }
        
        self.logger.warning(f"Performance alert: {alert_type} - {alert_data}")
        # TODO: Implement alert notification system (email, Slack, etc.)
    
    def _get_stack_trace(self) -> str:
        """Get current stack trace for error tracking"""
        import traceback
        return traceback.format_exc()
    
    # Additional helper methods for analytics calculations
    def _calculate_hourly_volume(self, queries: List[QueryMetric]) -> Dict[int, int]:
        """Calculate query volume by hour"""
        hourly_volume = defaultdict(int)
        for query in queries:
            hour = query.timestamp.hour
            hourly_volume[hour] += 1
        return dict(hourly_volume)
    
    def _get_top_queries(self, queries: List[QueryMetric], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top queries by frequency"""
        query_counts = defaultdict(int)
        for query in queries:
            query_counts[query.query_text] += 1
        
        return [
            {'query': query, 'count': count}
            for query, count in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    def _calculate_performance_trends(self, queries: List[QueryMetric]) -> Dict[str, List[float]]:
        """Calculate performance trends over time"""
        # Group queries by hour and calculate averages
        hourly_stats = defaultdict(list)
        for query in queries:
            hour = query.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_stats[hour].append(query.response_time)
        
        hours = sorted(hourly_stats.keys())
        avg_response_times = [sum(hourly_stats[hour]) / len(hourly_stats[hour]) for hour in hours]
        
        return {
            'hours': [h.isoformat() for h in hours],
            'avg_response_times': avg_response_times
        }
    
    def _calculate_system_health_score(self, system_metrics: List[SystemMetric]) -> float:
        """Calculate overall system health score (0-100)"""
        if not system_metrics:
            return 100.0
        
        # Calculate average resource usage
        avg_cpu = sum(m.cpu_usage for m in system_metrics) / len(system_metrics)
        avg_memory = sum(m.memory_usage for m in system_metrics) / len(system_metrics)
        avg_disk = sum(m.disk_usage for m in system_metrics) / len(system_metrics)
        
        # Health score is inverse of resource usage
        health_score = 100 - (avg_cpu + avg_memory + avg_disk) / 3
        return max(0, min(100, health_score))
    
    def _calculate_resource_trends(self, system_metrics: List[SystemMetric]) -> Dict[str, List[float]]:
        """Calculate resource utilization trends"""
        timestamps = [m.timestamp for m in system_metrics]
        cpu_usage = [m.cpu_usage for m in system_metrics]
        memory_usage = [m.memory_usage for m in system_metrics]
        disk_usage = [m.disk_usage for m in system_metrics]
        
        return {
            'timestamps': [t.isoformat() for t in timestamps],
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage
        }
    
    def _find_peak_usage_times(self, system_metrics: List[SystemMetric]) -> Dict[str, datetime]:
        """Find peak usage times for different resources"""
        if not system_metrics:
            return {}
        
        max_cpu_metric = max(system_metrics, key=lambda m: m.cpu_usage)
        max_memory_metric = max(system_metrics, key=lambda m: m.memory_usage)
        max_disk_metric = max(system_metrics, key=lambda m: m.disk_usage)
        
        return {
            'peak_cpu_time': max_cpu_metric.timestamp,
            'peak_memory_time': max_memory_metric.timestamp,
            'peak_disk_time': max_disk_metric.timestamp
        }
    
    def _calculate_user_engagement(self, activities: List[UserActivityMetric]) -> float:
        """Calculate user engagement score"""
        if not activities:
            return 0.0
        
        # Calculate engagement based on activity frequency and diversity
        user_activity_counts = defaultdict(int)
        for activity in activities:
            user_activity_counts[activity.user_id] += 1
        
        avg_activities_per_user = sum(user_activity_counts.values()) / len(user_activity_counts)
        return min(100, avg_activities_per_user * 10)  # Scale to 0-100
    
    def _find_peak_activity_times(self, activities: List[UserActivityMetric]) -> List[datetime]:
        """Find peak user activity times"""
        hourly_activity = defaultdict(int)
        for activity in activities:
            hour = activity.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_activity[hour] += 1
        
        # Find top 3 peak hours
        peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        return [hour for hour, count in peak_hours]
    
    def _calculate_user_retention(self, activities: List[UserActivityMetric]) -> Dict[str, float]:
        """Calculate user retention metrics"""
        if not activities:
            return {}
        
        # Group activities by user and calculate retention
        user_sessions = defaultdict(set)
        for activity in activities:
            user_sessions[activity.user_id].add(activity.session_id)
        
        total_users = len(user_sessions)
        multi_session_users = sum(1 for sessions in user_sessions.values() if len(sessions) > 1)
        
        return {
            'retention_rate': (multi_session_users / total_users) * 100 if total_users > 0 else 0,
            'avg_sessions_per_user': sum(len(sessions) for sessions in user_sessions.values()) / total_users if total_users > 0 else 0
        }
    
    def _get_most_common_errors(self, errors: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common error types"""
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error['error_type']] += 1
        
        return [
            {'error_type': error_type, 'count': count}
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    def _calculate_error_trends(self, errors: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """Calculate error trends over time"""
        hourly_errors = defaultdict(int)
        for error in errors:
            hour = error['timestamp'].replace(minute=0, second=0, microsecond=0)
            hourly_errors[hour] += 1
        
        hours = sorted(hourly_errors.keys())
        error_counts = [hourly_errors[hour] for hour in hours]
        
        return {
            'hours': [h.isoformat() for h in hours],
            'error_counts': error_counts
        }
    
    def _analyze_error_impact(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact of errors"""
        if not errors:
            return {}
        
        # Categorize errors by severity
        critical_errors = [e for e in errors if 'critical' in e.get('error_type', '').lower()]
        warning_errors = [e for e in errors if 'warning' in e.get('error_type', '').lower()]
        
        return {
            'total_errors': len(errors),
            'critical_errors': len(critical_errors),
            'warning_errors': len(warning_errors),
            'critical_error_rate': len(critical_errors) / len(errors) if errors else 0
        }
    
    def _generate_recommendations(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Get current analytics
        query_analytics = self.get_query_analytics(time_range)
        system_analytics = self.get_system_analytics(time_range)
        error_analytics = self.get_error_analytics(time_range)
        
        # Query performance recommendations
        if query_analytics.get('avg_response_time', 0) > 2.0:
            recommendations.append("Consider optimizing query processing or increasing system resources")
        
        if query_analytics.get('cache_hit_rate', 0) < 0.5:
            recommendations.append("Low cache hit rate detected. Consider expanding cache size or improving cache strategy")
        
        # System performance recommendations
        if system_analytics.get('avg_cpu_usage', 0) > 70:
            recommendations.append("High CPU usage detected. Consider scaling up or optimizing resource-intensive operations")
        
        if system_analytics.get('avg_memory_usage', 0) > 80:
            recommendations.append("High memory usage detected. Consider increasing memory or optimizing memory usage")
        
        # Error rate recommendations
        if error_analytics.get('error_rate', 0) > 0.05:
            recommendations.append("High error rate detected. Review error logs and implement error handling improvements")
        
        return recommendations
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        # This would be implemented with a proper alerting system
        # For now, return empty list
        return []


# Global analytics instance
_analytics_instance = None

def get_analytics(config: Dict[str, Any] = None) -> PerformanceAnalytics:
    """Get or create the global analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = PerformanceAnalytics(config)
    return _analytics_instance

