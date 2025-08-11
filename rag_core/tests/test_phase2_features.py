"""
Test suite for Phase 2 features: Advanced Reranking and Performance Monitoring
"""

import unittest
import time
import tempfile
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rag_core.reranker import (
    AdvancedReranker, RerankingStrategy, RerankingResult, 
    get_advanced_reranker, RerankingMetrics
)
from rag_core.analytics import (
    PerformanceAnalytics, QueryMetric, SystemMetric, UserActivityMetric,
    get_analytics, MetricType
)
from rag_core.monitoring import (
    RealTimeMonitor, MonitoringConfig, HealthStatus, AlertSeverity,
    get_monitor, HealthCheck, Alert
)


class TestAdvancedReranking(unittest.TestCase):
    """Test advanced reranking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = {
            'cross_encoder_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
            'semantic_model': 'all-MiniLM-L6-v2'
        }
        self.reranker = AdvancedReranker(self.config)
        
        # Sample chunks for testing
        self.sample_chunks = [
            {
                'page_content': 'Machine learning is a subset of artificial intelligence.',
                'metadata': {'filename': 'ai_doc.pdf', 'chunk_index': 0, 'domain': 'technology'},
                'id': 'chunk_1'
            },
            {
                'page_content': 'Deep learning uses neural networks with multiple layers.',
                'metadata': {'filename': 'ai_doc.pdf', 'chunk_index': 1, 'domain': 'technology'},
                'id': 'chunk_2'
            },
            {
                'page_content': 'Natural language processing helps computers understand human language.',
                'metadata': {'filename': 'nlp_doc.pdf', 'chunk_index': 0, 'domain': 'technology'},
                'id': 'chunk_3'
            }
        ]
    
    def test_reranker_initialization(self):
        """Test reranker initialization"""
        self.assertIsNotNone(self.reranker)
        self.assertTrue(hasattr(self.reranker, 'cross_encoder'))
        self.assertTrue(hasattr(self.reranker, 'semantic_model'))
        self.assertTrue(hasattr(self.reranker, 'tfidf_vectorizer'))
    
    def test_cross_encoder_reranking(self):
        """Test cross-encoder reranking strategy"""
        if not self.reranker.cross_encoder:
            self.skipTest("Cross-encoder not available")
        
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.CROSS_ENCODER, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(len(result.chunks), 2)
        self.assertEqual(result.strategy_used, 'cross_encoder')
        self.assertTrue(all('rerank_score' in chunk for chunk in result.chunks))
    
    def test_semantic_similarity_reranking(self):
        """Test semantic similarity reranking strategy"""
        if not self.reranker.semantic_model:
            self.skipTest("Semantic model not available")
        
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.SEMANTIC_SIMILARITY, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(len(result.chunks), 2)
        self.assertEqual(result.strategy_used, 'semantic_similarity')
        self.assertTrue(all('rerank_score' in chunk for chunk in result.chunks))
    
    def test_tfidf_keyword_reranking(self):
        """Test TF-IDF keyword reranking strategy"""
        if not self.reranker.tfidf_vectorizer:
            self.skipTest("TF-IDF vectorizer not available")
        
        query = "machine learning"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.TFIDF_KEYWORD, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(len(result.chunks), 2)
        self.assertEqual(result.strategy_used, 'tfidf_keyword')
        self.assertTrue(all('rerank_score' in chunk for chunk in result.chunks))
    
    def test_hybrid_reranking(self):
        """Test hybrid reranking strategy"""
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.HYBRID, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(len(result.strategy_used), 'hybrid')
        self.assertTrue(all('rerank_score' in chunk for chunk in result.chunks))
    
    def test_context_aware_reranking(self):
        """Test context-aware reranking strategy"""
        query = "What is machine learning?"
        context = [
            {'role': 'user', 'content': 'Tell me about AI'},
            {'role': 'assistant', 'content': 'AI includes machine learning and deep learning'}
        ]
        
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.CONTEXT_AWARE, 
            top_k=2, context=context
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(result.strategy_used, 'context_aware')
    
    def test_personalized_reranking(self):
        """Test personalized reranking strategy"""
        # Set user preferences
        user_id = "test_user"
        preferences = {
            'preferred_domains': ['technology'],
            'preferred_file_types': ['pdf']
        }
        self.reranker.update_user_preferences(user_id, preferences)
        
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.PERSONALIZED, 
            top_k=2, user_id=user_id
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(result.strategy_used, 'personalized')
    
    def test_diversity_reranking(self):
        """Test diversity-aware reranking strategy"""
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.DIVERSITY, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(result.strategy_used, 'diversity')
    
    def test_temporal_reranking(self):
        """Test temporal reranking strategy"""
        # Add timestamps to chunks
        chunks_with_timestamps = []
        for i, chunk in enumerate(self.sample_chunks):
            chunk_copy = chunk.copy()
            chunk_copy['metadata'] = chunk_copy['metadata'].copy()
            chunk_copy['metadata']['timestamp'] = datetime.now() - timedelta(days=i)
            chunks_with_timestamps.append(chunk_copy)
        
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, chunks_with_timestamps, RerankingStrategy.TEMPORAL, top_k=2
        )
        
        self.assertIsInstance(result, RerankingResult)
        self.assertEqual(result.strategy_used, 'temporal')
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        query = "What is machine learning?"
        result = self.reranker.rerank(
            query, self.sample_chunks, RerankingStrategy.HYBRID, top_k=2
        )
        
        self.assertIsInstance(result.metrics, RerankingMetrics)
        self.assertGreater(result.metrics.processing_time, 0)
        self.assertEqual(result.metrics.input_chunks, 3)
        self.assertEqual(result.metrics.output_chunks, 2)
        self.assertIsInstance(result.metrics.diversity_score, float)
        self.assertIsInstance(result.metrics.confidence_score, float)
    
    def test_performance_stats(self):
        """Test performance statistics retrieval"""
        # Run multiple reranking operations
        for i in range(3):
            query = f"Test query {i}"
            self.reranker.rerank(query, self.sample_chunks, RerankingStrategy.HYBRID, top_k=2)
        
        stats = self.reranker.get_performance_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_operations', stats)
        self.assertIn('avg_processing_time', stats)
        self.assertIn('avg_confidence_score', stats)
    
    def test_user_preferences(self):
        """Test user preferences management"""
        user_id = "test_user"
        preferences = {
            'preferred_domains': ['technology', 'science'],
            'preferred_file_types': ['pdf', 'docx']
        }
        
        self.reranker.update_user_preferences(user_id, preferences)
        
        # Verify preferences were stored
        self.assertIn(user_id, self.reranker.user_preferences)
        self.assertEqual(
            self.reranker.user_preferences[user_id]['preferred_domains'],
            ['technology', 'science']
        )


class TestPerformanceAnalytics(unittest.TestCase):
    """Test performance analytics functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = {
            'max_metrics_per_type': 100,
            'monitoring_interval': 5,
            'auto_start_monitoring': False
        }
        self.analytics = PerformanceAnalytics(self.config)
    
    def test_analytics_initialization(self):
        """Test analytics initialization"""
        self.assertIsNotNone(self.analytics)
        self.assertFalse(self.analytics.monitoring_active)
        self.assertEqual(self.analytics.max_metrics_per_type, 100)
    
    def test_query_performance_tracking(self):
        """Test query performance tracking"""
        query_metric = QueryMetric(
            query_id="test_123",
            query_text="What is machine learning?",
            processing_time=1.5,
            response_time=2.0,
            chunk_count=5,
            reranking_time=0.3,
            llm_time=1.2,
            cache_hit=False,
            user_id="test_user"
        )
        
        self.analytics.track_query_performance(query_metric)
        
        # Verify metric was stored
        self.assertGreater(len(self.analytics.query_metrics), 0)
        self.assertEqual(self.analytics.query_metrics[-1].query_id, "test_123")
    
    def test_system_performance_tracking(self):
        """Test system performance tracking"""
        system_metric = SystemMetric(
            cpu_usage=45.2,
            memory_usage=67.8,
            disk_usage=23.1,
            active_connections=12,
            queue_size=5
        )
        
        self.analytics.track_system_performance(system_metric)
        
        # Verify metric was stored
        self.assertGreater(len(self.analytics.system_metrics), 0)
        self.assertEqual(self.analytics.system_metrics[-1].cpu_usage, 45.2)
    
    def test_user_activity_tracking(self):
        """Test user activity tracking"""
        activity_metric = UserActivityMetric(
            user_id="test_user",
            session_id="session_123",
            action_type="query",
            action_data={"query": "What is AI?"}
        )
        
        self.analytics.track_user_activity(activity_metric)
        
        # Verify metric was stored
        self.assertGreater(len(self.analytics.user_activity), 0)
        self.assertEqual(self.analytics.user_activity[-1].user_id, "test_user")
    
    def test_error_tracking(self):
        """Test error tracking"""
        self.analytics.track_error(
            error_type="query_error",
            error_message="Failed to process query",
            context={"query": "test query"}
        )
        
        # Verify error was stored
        self.assertGreater(len(self.analytics.error_logs), 0)
        self.assertEqual(self.analytics.error_logs[-1]['error_type'], "query_error")
    
    def test_query_analytics(self):
        """Test query analytics generation"""
        # Add some test data
        for i in range(5):
            query_metric = QueryMetric(
                query_id=f"test_{i}",
                query_text=f"Test query {i}",
                processing_time=1.0 + i * 0.1,
                response_time=2.0 + i * 0.1,
                chunk_count=3 + i,
                reranking_time=0.2,
                llm_time=1.0,
                cache_hit=i % 2 == 0
            )
            self.analytics.track_query_performance(query_metric)
        
        analytics = self.analytics.get_query_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertEqual(analytics['total_queries'], 5)
        self.assertIn('avg_response_time', analytics)
        self.assertIn('cache_hit_rate', analytics)
        self.assertIn('query_volume_by_hour', analytics)
    
    def test_system_analytics(self):
        """Test system analytics generation"""
        # Add some test data
        for i in range(5):
            system_metric = SystemMetric(
                cpu_usage=40.0 + i * 5,
                memory_usage=60.0 + i * 3,
                disk_usage=20.0 + i * 2,
                active_connections=10 + i,
                queue_size=i
            )
            self.analytics.track_system_performance(system_metric)
        
        analytics = self.analytics.get_system_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('avg_cpu_usage', analytics)
        self.assertIn('max_memory_usage', analytics)
        self.assertIn('system_health_score', analytics)
    
    def test_user_analytics(self):
        """Test user analytics generation"""
        # Add some test data
        for i in range(10):
            activity_metric = UserActivityMetric(
                user_id=f"user_{i % 3}",
                session_id=f"session_{i}",
                action_type="query" if i % 2 == 0 else "upload",
                action_data={"action": f"action_{i}"}
            )
            self.analytics.track_user_activity(activity_metric)
        
        analytics = self.analytics.get_user_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertEqual(analytics['unique_users'], 3)
        self.assertIn('action_distribution', analytics)
        self.assertIn('user_engagement_score', analytics)
    
    def test_error_analytics(self):
        """Test error analytics generation"""
        # Add some test errors
        for i in range(5):
            self.analytics.track_error(
                error_type=f"error_type_{i % 2}",
                error_message=f"Error message {i}",
                context={"index": i}
            )
        
        analytics = self.analytics.get_error_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertEqual(analytics['total_errors'], 5)
        self.assertIn('error_types', analytics)
        self.assertIn('most_common_errors', analytics)
    
    def test_performance_report_generation(self):
        """Test comprehensive performance report generation"""
        # Add test data
        query_metric = QueryMetric(
            query_id="test_123",
            query_text="Test query",
            processing_time=1.5,
            response_time=2.0,
            chunk_count=5,
            reranking_time=0.3,
            llm_time=1.2,
            cache_hit=False
        )
        self.analytics.track_query_performance(query_metric)
        
        system_metric = SystemMetric(
            cpu_usage=45.2,
            memory_usage=67.8,
            disk_usage=23.1,
            active_connections=12,
            queue_size=5
        )
        self.analytics.track_system_performance(system_metric)
        
        report = self.analytics.generate_performance_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('query_analytics', report)
        self.assertIn('system_analytics', report)
        self.assertIn('user_analytics', report)
        self.assertIn('error_analytics', report)
        self.assertIn('performance_recommendations', report)
    
    def test_metrics_export(self):
        """Test metrics export functionality"""
        # Add test data
        query_metric = QueryMetric(
            query_id="test_123",
            query_text="Test query",
            processing_time=1.5,
            response_time=2.0,
            chunk_count=5,
            reranking_time=0.3,
            llm_time=1.2,
            cache_hit=False
        )
        self.analytics.track_query_performance(query_metric)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            self.analytics.export_metrics(export_path)
            
            # Verify export file was created and contains data
            with open(export_path, 'r') as f:
                export_data = json.load(f)
            
            self.assertIn('export_timestamp', export_data)
            self.assertIn('metrics', export_data)
            self.assertIn('query_performance', export_data['metrics'])
            
        finally:
            import os
            os.unlink(export_path)


class TestRealTimeMonitoring(unittest.TestCase):
    """Test real-time monitoring functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = MonitoringConfig({
            'health_check_interval': 5,
            'system_metrics_interval': 2,
            'auto_start_monitoring': False
        })
        self.monitor = RealTimeMonitor(self.config)
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor)
        self.assertFalse(self.monitor.monitoring_active)
        self.assertEqual(self.monitor.config.health_check_interval, 5)
    
    def test_health_check_creation(self):
        """Test health check creation"""
        health_check = self.monitor._check_system_health()
        
        self.assertIsInstance(health_check, HealthCheck)
        self.assertEqual(health_check.component, 'system')
        self.assertIn(health_check.status, HealthStatus)
        self.assertIsInstance(health_check.message, str)
        self.assertIsInstance(health_check.timestamp, datetime)
    
    def test_alert_creation(self):
        """Test alert creation"""
        alert_id = self.monitor._create_alert(
            'test_alert',
            AlertSeverity.WARNING,
            'Test alert message',
            'test_component',
            {'test_key': 'test_value'}
        )
        
        # Verify alert was created
        self.assertIn(alert_id, self.monitor.active_alerts)
        alert = self.monitor.active_alerts[alert_id]
        self.assertEqual(alert.type, 'test_alert')
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertEqual(alert.message, 'Test alert message')
        self.assertEqual(alert.component, 'test_component')
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment"""
        alert_id = self.monitor._create_alert(
            'test_alert',
            AlertSeverity.WARNING,
            'Test alert message',
            'test_component'
        )
        
        self.monitor.acknowledge_alert(alert_id, "test_user")
        
        alert = self.monitor.active_alerts[alert_id]
        self.assertTrue(alert.acknowledged)
        self.assertEqual(alert.metadata['acknowledged_by'], "test_user")
    
    def test_alert_resolution(self):
        """Test alert resolution"""
        alert_id = self.monitor._create_alert(
            'test_alert',
            AlertSeverity.WARNING,
            'Test alert message',
            'test_component'
        )
        
        self.monitor.resolve_alert(alert_id, "test_user", "Issue resolved")
        
        # Verify alert was moved to history
        self.assertNotIn(alert_id, self.monitor.active_alerts)
        self.assertGreater(len(self.monitor.alert_history), 0)
        
        resolved_alert = self.monitor.alert_history[-1]
        self.assertTrue(resolved_alert.resolved)
        self.assertEqual(resolved_alert.metadata['resolved_by'], "test_user")
        self.assertEqual(resolved_alert.metadata['resolution_notes'], "Issue resolved")
    
    def test_system_health_retrieval(self):
        """Test system health status retrieval"""
        health_status = self.monitor.get_system_health()
        
        self.assertIsInstance(health_status, dict)
        # Should have default unknown status for components
        self.assertIn('system', health_status)
        self.assertEqual(health_status['system'], HealthStatus.UNKNOWN)
    
    def test_active_alerts_retrieval(self):
        """Test active alerts retrieval"""
        # Create some test alerts
        self.monitor._create_alert(
            'test_alert_1',
            AlertSeverity.WARNING,
            'Test alert 1',
            'test_component'
        )
        self.monitor._create_alert(
            'test_alert_2',
            AlertSeverity.ERROR,
            'Test alert 2',
            'test_component'
        )
        
        active_alerts = self.monitor.get_active_alerts()
        
        self.assertIsInstance(active_alerts, list)
        self.assertEqual(len(active_alerts), 2)
        self.assertTrue(all(isinstance(alert, Alert) for alert in active_alerts))
    
    def test_health_check_history(self):
        """Test health check history retrieval"""
        # Perform some health checks
        for i in range(3):
            health_check = self.monitor._check_system_health()
            self.monitor.health_checks.append(health_check)
        
        history = self.monitor.get_health_check_history(limit=5)
        
        self.assertIsInstance(history, list)
        self.assertLessEqual(len(history), 5)
        self.assertTrue(all(isinstance(check, HealthCheck) for check in history))
    
    def test_performance_metrics_retrieval(self):
        """Test performance metrics retrieval"""
        # Add some test metrics
        for i in range(3):
            metric = {
                'timestamp': datetime.now(),
                'cpu_usage': 40.0 + i * 5,
                'memory_usage': 60.0 + i * 3,
                'disk_usage': 20.0 + i * 2
            }
            self.monitor.performance_metrics['system'].append(metric)
        
        metrics = self.monitor.get_performance_metrics('system')
        
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics['component'], 'system')
        self.assertEqual(len(metrics['metrics']), 3)
    
    def test_monitoring_data_export(self):
        """Test monitoring data export"""
        # Add some test data
        self.monitor._create_alert(
            'test_alert',
            AlertSeverity.WARNING,
            'Test alert message',
            'test_component'
        )
        
        health_check = self.monitor._check_system_health()
        self.monitor.health_checks.append(health_check)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            self.monitor.export_monitoring_data(export_path)
            
            # Verify export file was created and contains data
            with open(export_path, 'r') as f:
                export_data = json.load(f)
            
            self.assertIn('export_timestamp', export_data)
            self.assertIn('health_checks', export_data)
            self.assertIn('active_alerts', export_data)
            self.assertIn('component_health', export_data)
            
        finally:
            import os
            os.unlink(export_path)
    
    def test_alert_handler_registration(self):
        """Test alert handler registration"""
        def test_handler(alert):
            pass
        
        self.monitor.add_alert_handler(test_handler)
        
        self.assertIn(test_handler, self.monitor.alert_handlers)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.monitor.monitoring_active:
            self.monitor.stop_monitoring()


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 2 features"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.reranker = get_advanced_reranker()
        self.analytics = get_analytics()
        self.monitor = get_monitor()
    
    def test_reranking_with_analytics_integration(self):
        """Test reranking with analytics integration"""
        # Create test chunks
        chunks = [
            {
                'page_content': 'Machine learning is a subset of AI.',
                'metadata': {'filename': 'ai_doc.pdf', 'chunk_index': 0}
            },
            {
                'page_content': 'Deep learning uses neural networks.',
                'metadata': {'filename': 'ai_doc.pdf', 'chunk_index': 1}
            }
        ]
        
        # Perform reranking
        query = "What is machine learning?"
        start_time = time.time()
        result = self.reranker.rerank(query, chunks, RerankingStrategy.HYBRID, top_k=2)
        processing_time = time.time() - start_time
        
        # Create query metric
        query_metric = QueryMetric(
            query_id="integration_test",
            query_text=query,
            processing_time=processing_time,
            response_time=processing_time,
            chunk_count=len(chunks),
            reranking_time=result.metrics.processing_time,
            llm_time=0.0,  # Not applicable for reranking test
            cache_hit=False
        )
        
        # Track in analytics
        self.analytics.track_query_performance(query_metric)
        
        # Verify integration
        self.assertIsInstance(result, RerankingResult)
        self.assertGreater(len(self.analytics.query_metrics), 0)
        self.assertEqual(self.analytics.query_metrics[-1].query_id, "integration_test")
    
    def test_monitoring_with_analytics_integration(self):
        """Test monitoring with analytics integration"""
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Wait for some metrics to be collected
        time.sleep(3)
        
        # Get system health
        health_status = self.monitor.get_system_health()
        
        # Get analytics
        system_analytics = self.analytics.get_system_analytics()
        
        # Verify integration
        self.assertIsInstance(health_status, dict)
        self.assertIsInstance(system_analytics, dict)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
    
    def test_end_to_end_workflow(self):
        """Test end-to-end workflow with all Phase 2 features"""
        # 1. Perform reranking
        chunks = [
            {
                'page_content': 'Test content 1',
                'metadata': {'filename': 'test.pdf', 'chunk_index': 0}
            },
            {
                'page_content': 'Test content 2',
                'metadata': {'filename': 'test.pdf', 'chunk_index': 1}
            }
        ]
        
        query = "Test query"
        result = self.reranker.rerank(query, chunks, RerankingStrategy.HYBRID, top_k=2)
        
        # 2. Track performance
        query_metric = QueryMetric(
            query_id="e2e_test",
            query_text=query,
            processing_time=result.metrics.processing_time,
            response_time=result.metrics.processing_time,
            chunk_count=len(chunks),
            reranking_time=result.metrics.processing_time,
            llm_time=0.0,
            cache_hit=False
        )
        self.analytics.track_query_performance(query_metric)
        
        # 3. Check monitoring
        health_check = self.monitor._check_system_health()
        self.monitor.health_checks.append(health_check)
        
        # 4. Generate reports
        performance_report = self.analytics.generate_performance_report()
        
        # Verify all components work together
        self.assertIsInstance(result, RerankingResult)
        self.assertIsInstance(performance_report, dict)
        self.assertIsInstance(health_check, HealthCheck)
        
        # Verify data consistency
        self.assertEqual(result.metrics.input_chunks, len(chunks))
        self.assertEqual(result.metrics.output_chunks, 2)
        self.assertGreater(result.metrics.processing_time, 0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

