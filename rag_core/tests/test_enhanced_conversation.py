"""
Test suite for Enhanced Conversation Management System
Tests advanced conversation analytics, insights, context management, and recommendations
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any

from rag_core.conversation_manager import (
    ConversationManager, ConversationAnalytics, ConversationInsights,
    ConversationContext, ConversationMetadata, ConversationStatus,
    ConversationCategory, ConversationPriority, ConversationType
)


class TestEnhancedConversationManager:
    """Test the enhanced conversation management system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ConversationManager(storage_path=self.temp_dir)
        
        # Create test conversation data
        self.test_conversation_id = "test-conv-123"
        self.test_messages = [
            {
                "role": "user",
                "content": "I need help with API development. Can you show me how to create a REST API?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant", 
                "content": "I'd be happy to help you with API development! REST APIs are great for building scalable web services. Here are some key concepts: 1) Use HTTP methods (GET, POST, PUT, DELETE) 2) Design clear endpoints 3) Use proper status codes. Would you like me to show you a specific example?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Yes, please show me a Python Flask example. This is exactly what I need!",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Great! Here's a simple Flask REST API example: ```python\nfrom flask import Flask, request, jsonify\napp = Flask(__name__)\n@app.route('/api/users', methods=['GET'])\ndef get_users():\n    return jsonify({'users': []})\n``` This creates a basic endpoint. The code is clean and follows REST principles.",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Save test conversation
        self._save_test_conversation()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _save_test_conversation(self):
        """Save test conversation data"""
        conversation_data = {
            "id": self.test_conversation_id,
            "messages": self.test_messages,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        data_path = os.path.join(self.temp_dir, f"{self.test_conversation_id}.json")
        with open(data_path, 'w') as f:
            json.dump(conversation_data, f, indent=2)
    
    def test_initialization(self):
        """Test ConversationManager initialization"""
        assert self.manager is not None
        assert hasattr(self.manager, 'topic_patterns')
        assert hasattr(self.manager, 'sentiment_indicators')
        assert hasattr(self.manager, 'intent_patterns')
    
    def test_get_conversation_analytics(self):
        """Test comprehensive conversation analytics"""
        analytics = self.manager.get_conversation_analytics(self.test_conversation_id)
        
        assert isinstance(analytics, ConversationAnalytics)
        assert analytics.total_messages == 4
        assert analytics.user_messages == 2
        assert analytics.assistant_messages == 2
        assert analytics.average_message_length > 0
        assert isinstance(analytics.topic_distribution, dict)
        assert isinstance(analytics.response_time_stats, dict)
        assert isinstance(analytics.user_engagement_metrics, dict)
        assert 0 <= analytics.conversation_quality_score <= 1
        assert 0 <= analytics.completion_rate <= 1
        assert 0 <= analytics.user_satisfaction_score <= 1
    
    def test_analyze_conversation_insights(self):
        """Test conversation insights analysis"""
        insights = self.manager.analyze_conversation_insights(self.test_conversation_id)
        
        assert isinstance(insights, ConversationInsights)
        assert isinstance(insights.key_topics, list)
        assert -1 <= insights.sentiment_score <= 1
        assert insights.user_intent in ["question", "request", "statement", "command", "general"]
        assert insights.conversation_flow in ["linear", "branching", "circular"]
        assert isinstance(insights.knowledge_gaps, list)
        assert isinstance(insights.action_items, list)
        assert isinstance(insights.follow_up_questions, list)
        assert isinstance(insights.context_switches, int)
        assert insights.average_response_time >= 0
        assert isinstance(insights.user_satisfaction_indicators, list)
    
    def test_manage_conversation_context(self):
        """Test conversation context management"""
        context = self.manager.manage_conversation_context(self.test_conversation_id)
        
        assert isinstance(context, ConversationContext)
        assert isinstance(context.current_topic, str)
        assert isinstance(context.context_stack, list)
        assert isinstance(context.memory_bank, dict)
        assert isinstance(context.context_window, int)
        assert isinstance(context.context_importance, dict)
        assert context.context_retention_policy in ["adaptive", "fixed", "sliding"]
    
    def test_update_conversation_context(self):
        """Test updating conversation context"""
        new_topic = "API Development"
        context_data = {"framework": "Flask", "language": "Python"}
        
        self.manager.update_conversation_context(
            self.test_conversation_id,
            new_topic=new_topic,
            context_data=context_data
        )
        
        # Verify context was updated
        context = self.manager.manage_conversation_context(self.test_conversation_id)
        assert context.current_topic == new_topic
        assert context.memory_bank["framework"] == "Flask"
        assert context.memory_bank["language"] == "Python"
        assert context.context_importance[new_topic] == 1.0
    
    def test_get_conversation_recommendations(self):
        """Test conversation recommendations"""
        recommendations = self.manager.get_conversation_recommendations(self.test_conversation_id)
        
        assert isinstance(recommendations, dict)
        assert "suggested_topics" in recommendations
        assert "improvement_areas" in recommendations
        assert "next_steps" in recommendations
        assert "template_suggestions" in recommendations
        assert "follow_up_questions" in recommendations
        assert "priority_level" in recommendations
        assert recommendations["priority_level"] in ["low", "medium", "high"]
    
    def test_analyze_topic_distribution(self):
        """Test topic distribution analysis"""
        messages = [
            {"content": "I need help with API development and code examples"},
            {"content": "This is a technical question about programming"}
        ]
        
        topic_distribution = self.manager._analyze_topic_distribution(messages)
        
        assert isinstance(topic_distribution, dict)
        assert "technical" in topic_distribution
        assert topic_distribution["technical"] > 0
    
    def test_calculate_sentiment(self):
        """Test sentiment calculation"""
        messages = [
            {"content": "This is great! I love this solution."},
            {"content": "This is terrible and I hate it."},
            {"content": "This is okay, nothing special."}
        ]
        
        sentiment_score = self.manager._calculate_sentiment(messages)
        
        assert -1 <= sentiment_score <= 1
        # With 2 positive and 2 negative words, score should be 0
        assert sentiment_score == 0.0
        
        # Test with more positive messages
        positive_messages = [
            {"content": "This is amazing! I love it!"},
            {"content": "This is fantastic and wonderful."}
        ]
        
        positive_sentiment = self.manager._calculate_sentiment(positive_messages)
        assert positive_sentiment > 0
    
    def test_detect_user_intent(self):
        """Test user intent detection"""
        messages = [
            {"role": "user", "content": "What is the best way to create an API?"},
            {"role": "user", "content": "Can you help me with this problem?"},
            {"role": "user", "content": "I need to build a REST API"}
        ]
        
        intent = self.manager._detect_user_intent(messages)
        
        assert intent in ["question", "request", "statement", "command", "general"]
    
    def test_analyze_conversation_flow(self):
        """Test conversation flow analysis"""
        # Linear flow
        linear_messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"}
        ]
        
        flow = self.manager._analyze_conversation_flow(linear_messages)
        assert flow == "linear"
    
    def test_extract_key_topics(self):
        """Test key topic extraction"""
        messages = [
            {"content": "I need help with API development and code examples"},
            {"content": "This involves programming and technical work"}
        ]
        
        topics = self.manager._extract_key_topics(messages)
        
        assert isinstance(topics, list)
        assert len(topics) <= 5
        assert "api" in topics or "code" in topics
    
    def test_calculate_conversation_quality(self):
        """Test conversation quality calculation"""
        messages = [
            {"content": "This is a detailed question with lots of context and information."},
            {"content": "This is a comprehensive answer with examples and explanations."}
        ]
        
        quality_score = self.manager._calculate_conversation_quality(messages)
        
        assert 0 <= quality_score <= 1
    
    def test_calculate_user_engagement(self):
        """Test user engagement calculation"""
        messages = [
            {"role": "user", "content": "This is a user message"},
            {"role": "assistant", "content": "This is an assistant response"},
            {"role": "user", "content": "Another user message"}
        ]
        
        engagement = self.manager._calculate_user_engagement(messages)
        
        assert isinstance(engagement, dict)
        assert "message_length" in engagement
        assert "interaction_frequency" in engagement
        assert engagement["interaction_frequency"] > 0
    
    def test_identify_knowledge_gaps(self):
        """Test knowledge gap identification"""
        messages = [
            {"content": "I don't know how to do this"},
            {"content": "I'm not sure about the best approach"},
            {"content": "This is unclear to me"}
        ]
        
        gaps = self.manager._identify_knowledge_gaps(messages)
        
        assert isinstance(gaps, list)
        assert len(gaps) > 0
        assert "User uncertainty detected" in gaps
    
    def test_extract_action_items(self):
        """Test action item extraction"""
        messages = [
            {"content": "I need to implement this feature"},
            {"content": "I should create a new API endpoint"},
            {"content": "I must update the documentation"}
        ]
        
        action_items = self.manager._extract_action_items(messages)
        
        assert isinstance(action_items, list)
        assert len(action_items) > 0
    
    def test_count_context_switches(self):
        """Test context switch counting"""
        messages = [
            {"content": "Let's talk about API development"},
            {"content": "Now let's discuss database design"},
            {"content": "Back to API development"}
        ]
        
        switches = self.manager._count_context_switches(messages)
        
        assert isinstance(switches, int)
        assert switches >= 0
    
    def test_suggest_related_topics(self):
        """Test related topic suggestions"""
        key_topics = ["technical", "api"]
        
        suggestions = self.manager._suggest_related_topics(key_topics)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert "API documentation" in suggestions or "Code examples" in suggestions
    
    def test_calculate_priority_level(self):
        """Test priority level calculation"""
        from rag_core.conversation_manager import ConversationInsights, ConversationAnalytics
        
        insights = ConversationInsights(
            sentiment_score=0.8,
            key_topics=["technical"]
        )
        
        analytics = ConversationAnalytics(
            conversation_quality_score=0.9,
            user_satisfaction_score=0.8,
            completion_rate=0.9
        )
        
        priority = self.manager._calculate_priority_level(insights, analytics)
        
        assert priority in ["low", "medium", "high"]
    
    def test_analyze_conversations_batch(self):
        """Test batch conversation analysis"""
        # Create another test conversation
        conv_id_2 = "test-conv-456"
        messages_2 = [
            {"role": "user", "content": "Help with database design"},
            {"role": "assistant", "content": "Database design involves..."}
        ]
        
        conv_data_2 = {
            "id": conv_id_2,
            "messages": messages_2,
            "created_at": datetime.now().isoformat()
        }
        
        data_path_2 = os.path.join(self.temp_dir, f"{conv_id_2}.json")
        with open(data_path_2, 'w') as f:
            json.dump(conv_data_2, f, indent=2)
        
        # Test batch analysis
        conv_ids = [self.test_conversation_id, conv_id_2]
        
        # This would test the batch analysis functionality
        # For now, we'll test individual analytics
        analytics_1 = self.manager.get_conversation_analytics(conv_ids[0])
        analytics_2 = self.manager.get_conversation_analytics(conv_ids[1])
        
        assert isinstance(analytics_1, ConversationAnalytics)
        assert isinstance(analytics_2, ConversationAnalytics)
    
    def test_conversation_metadata_enhancement(self):
        """Test enhanced conversation metadata"""
        metadata = ConversationMetadata(
            folder_id="test-folder",
            tags=["api", "development"],
            priority=8,
            status=ConversationStatus.ACTIVE,
            category=ConversationCategory.TECHNICAL,
            complexity_score=0.7,
            engagement_score=0.8,
            context_retention=0.9
        )
        
        assert metadata.priority == 8
        assert metadata.category == ConversationCategory.TECHNICAL
        assert metadata.complexity_score == 0.7
        assert metadata.engagement_score == 0.8
        assert metadata.context_retention == 0.9
    
    def test_conversation_insights_structure(self):
        """Test conversation insights data structure"""
        insights = ConversationInsights(
            key_topics=["api", "development"],
            sentiment_score=0.6,
            user_intent="question",
            conversation_flow="linear",
            knowledge_gaps=["User uncertainty detected"],
            action_items=["Implement API endpoint"],
            follow_up_questions=["Would you like me to elaborate?"],
            context_switches=1,
            average_response_time=2.5,
            user_satisfaction_indicators=["positive"]
        )
        
        assert insights.key_topics == ["api", "development"]
        assert insights.sentiment_score == 0.6
        assert insights.user_intent == "question"
        assert insights.conversation_flow == "linear"
        assert len(insights.knowledge_gaps) > 0
        assert len(insights.action_items) > 0
        assert len(insights.follow_up_questions) > 0
        assert insights.context_switches == 1
        assert insights.average_response_time == 2.5
        assert "positive" in insights.user_satisfaction_indicators
    
    def test_conversation_context_management(self):
        """Test conversation context management features"""
        context = ConversationContext(
            current_topic="API Development",
            context_stack=[{"topic": "REST APIs", "importance": 0.8}],
            memory_bank={"framework": "Flask", "language": "Python"},
            context_window=10,
            context_importance={"API Development": 1.0},
            context_retention_policy="adaptive"
        )
        
        assert context.current_topic == "API Development"
        assert len(context.context_stack) > 0
        assert context.memory_bank["framework"] == "Flask"
        assert context.context_window == 10
        assert context.context_importance["API Development"] == 1.0
        assert context.context_retention_policy == "adaptive"
    
    def test_conversation_analytics_structure(self):
        """Test conversation analytics data structure"""
        analytics = ConversationAnalytics(
            total_messages=10,
            user_messages=5,
            assistant_messages=5,
            average_message_length=150.5,
            response_time_stats={"average": 2.5, "min": 1.0, "max": 5.0},
            topic_distribution={"technical": 3, "api": 2},
            user_engagement_metrics={"message_length": 120.0, "interaction_frequency": 0.5},
            conversation_quality_score=0.8,
            completion_rate=0.9,
            user_satisfaction_score=0.85
        )
        
        assert analytics.total_messages == 10
        assert analytics.user_messages == 5
        assert analytics.assistant_messages == 5
        assert analytics.average_message_length == 150.5
        assert analytics.response_time_stats["average"] == 2.5
        assert analytics.topic_distribution["technical"] == 3
        assert analytics.user_engagement_metrics["message_length"] == 120.0
        assert analytics.conversation_quality_score == 0.8
        assert analytics.completion_rate == 0.9
        assert analytics.user_satisfaction_score == 0.85


class TestConversationEnums:
    """Test conversation management enums"""
    
    def test_conversation_status_enum(self):
        """Test ConversationStatus enum"""
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.ARCHIVED.value == "archived"
        assert ConversationStatus.TEMPLATE.value == "template"
        assert ConversationStatus.SHARED.value == "shared"
    
    def test_conversation_type_enum(self):
        """Test ConversationType enum"""
        assert ConversationType.REGULAR.value == "regular"
        assert ConversationType.TEMPLATE.value == "template"
        assert ConversationType.SHARED.value == "shared"
        assert ConversationType.IMPORTED.value == "imported"
        assert ConversationType.ANALYTICAL.value == "analytical"
        assert ConversationType.RESEARCH.value == "research"
        assert ConversationType.SUPPORT.value == "support"
        assert ConversationType.CREATIVE.value == "creative"
    
    def test_conversation_priority_enum(self):
        """Test ConversationPriority enum"""
        assert ConversationPriority.LOW.value == 1
        assert ConversationPriority.NORMAL.value == 5
        assert ConversationPriority.HIGH.value == 8
        assert ConversationPriority.URGENT.value == 10
    
    def test_conversation_category_enum(self):
        """Test ConversationCategory enum"""
        assert ConversationCategory.GENERAL.value == "general"
        assert ConversationCategory.TECHNICAL.value == "technical"
        assert ConversationCategory.RESEARCH.value == "research"
        assert ConversationCategory.SUPPORT.value == "support"
        assert ConversationCategory.CREATIVE.value == "creative"
        assert ConversationCategory.ANALYSIS.value == "analysis"
        assert ConversationCategory.PLANNING.value == "planning"
        assert ConversationCategory.DOCUMENTATION.value == "documentation"


def test_enhanced_conversation_imports():
    """Test that all enhanced conversation management components can be imported"""
    from rag_core.conversation_manager import (
        ConversationManager, ConversationAnalytics, ConversationInsights,
        ConversationContext, ConversationMetadata, ConversationStatus,
        ConversationCategory, ConversationPriority, ConversationType
    )
    
    assert ConversationManager is not None
    assert ConversationAnalytics is not None
    assert ConversationInsights is not None
    assert ConversationContext is not None
    assert ConversationMetadata is not None
    assert ConversationStatus is not None
    assert ConversationCategory is not None
    assert ConversationPriority is not None
    assert ConversationType is not None


def test_conversation_analysis_tools():
    """Test conversation analysis tools initialization"""
    manager = ConversationManager()
    
    # Test topic patterns
    assert "technical" in manager.topic_patterns
    assert "research" in manager.topic_patterns
    assert "support" in manager.topic_patterns
    assert "creative" in manager.topic_patterns
    assert "planning" in manager.topic_patterns
    
    # Test sentiment indicators
    assert "positive" in manager.sentiment_indicators
    assert "negative" in manager.sentiment_indicators
    assert "neutral" in manager.sentiment_indicators
    
    # Test intent patterns
    assert "question" in manager.intent_patterns
    assert "request" in manager.intent_patterns
    assert "statement" in manager.intent_patterns
    assert "command" in manager.intent_patterns
