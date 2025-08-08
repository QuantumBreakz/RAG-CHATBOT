"""
Enhanced Conversation Management Module for RAG Chatbot
Handles advanced conversation organization, intelligent analysis, context management, 
folders, export/import, templates, and conversation insights
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import zipfile
import tempfile
import shutil
from collections import defaultdict, Counter
import hashlib


class ConversationStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    TEMPLATE = "template"
    SHARED = "shared"


class ConversationType(Enum):
    REGULAR = "regular"
    TEMPLATE = "template"
    SHARED = "shared"
    IMPORTED = "imported"
    ANALYTICAL = "analytical"
    RESEARCH = "research"
    SUPPORT = "support"
    CREATIVE = "creative"


class ConversationPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class ConversationCategory(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    RESEARCH = "research"
    SUPPORT = "support"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    DOCUMENTATION = "documentation"


@dataclass
class ConversationFolder:
    """Represents a conversation folder/category"""
    id: str
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"  # Default blue
    created_at: datetime = None
    updated_at: datetime = None
    conversation_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class ConversationTemplate:
    """Represents a conversation template"""
    id: str
    name: str
    description: str
    category: str
    system_prompt: str
    initial_messages: List[Dict[str, Any]]
    tags: List[str] = None
    created_at: datetime = None
    usage_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []


@dataclass
class ConversationMetadata:
    """Enhanced metadata for conversation management"""
    folder_id: Optional[str] = None
    tags: List[str] = None
    priority: int = 5  # 0-10, higher is more important
    status: ConversationStatus = ConversationStatus.ACTIVE
    last_accessed: datetime = None
    access_count: int = 0
    shared_with: List[str] = None  # User IDs or emails
    export_history: List[Dict] = None
    category: ConversationCategory = ConversationCategory.GENERAL
    estimated_duration: Optional[int] = None  # in minutes
    complexity_score: float = 0.0  # 0-1 scale
    engagement_score: float = 0.0  # 0-1 scale
    context_retention: float = 0.0  # 0-1 scale
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.shared_with is None:
            self.shared_with = []
        if self.export_history is None:
            self.export_history = []


@dataclass
class ConversationInsights:
    """Intelligent insights about a conversation"""
    key_topics: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0  # -1 to 1
    user_intent: str = "general"
    conversation_flow: str = "linear"  # linear, branching, circular
    knowledge_gaps: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    context_switches: int = 0
    average_response_time: float = 0.0
    user_satisfaction_indicators: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Context management for conversations"""
    current_topic: str = ""
    context_stack: List[Dict[str, Any]] = field(default_factory=list)
    memory_bank: Dict[str, Any] = field(default_factory=dict)
    context_window: int = 10  # Number of messages to keep in context
    context_importance: Dict[str, float] = field(default_factory=dict)
    context_retention_policy: str = "adaptive"  # adaptive, fixed, sliding


@dataclass
class ConversationAnalytics:
    """Analytics data for conversation performance"""
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    average_message_length: float = 0.0
    response_time_stats: Dict[str, float] = field(default_factory=dict)
    topic_distribution: Dict[str, int] = field(default_factory=dict)
    user_engagement_metrics: Dict[str, float] = field(default_factory=dict)
    conversation_quality_score: float = 0.0
    completion_rate: float = 0.0
    user_satisfaction_score: float = 0.0


class ConversationManager:
    """Enhanced conversation manager with intelligent analysis and context management"""
    
    def __init__(self, storage_path: str = "conversations"):
        self.storage_path = storage_path
        self.folders_path = os.path.join(storage_path, "folders")
        self.templates_path = os.path.join(storage_path, "templates")
        self.analytics_path = os.path.join(storage_path, "analytics")
        self.insights_path = os.path.join(storage_path, "insights")
        self.context_path = os.path.join(storage_path, "context")
        
        # Initialize storage directories
        for path in [self.folders_path, self.templates_path, self.analytics_path, 
                    self.insights_path, self.context_path]:
            os.makedirs(path, exist_ok=True)
        
        # Initialize analysis components
        self.logger = logging.getLogger(__name__)
        self._initialize_analysis_tools()
    
    def _initialize_analysis_tools(self):
        """Initialize tools for conversation analysis"""
        # Topic detection patterns
        self.topic_patterns = {
            'technical': [r'\b(api|code|programming|development|software|algorithm|database|server|client)\b'],
            'research': [r'\b(research|study|analysis|investigation|survey|data|findings)\b'],
            'support': [r'\b(help|support|issue|problem|error|bug|fix|troubleshoot)\b'],
            'creative': [r'\b(design|creative|art|story|writing|content|brand|visual)\b'],
            'planning': [r'\b(plan|strategy|roadmap|timeline|schedule|project|goal)\b']
        }
        
        # Sentiment indicators
        self.sentiment_indicators = {
            'positive': ['great', 'excellent', 'amazing', 'perfect', 'love', 'awesome', 'fantastic'],
            'negative': ['bad', 'terrible', 'awful', 'hate', 'disappointed', 'frustrated', 'angry'],
            'neutral': ['okay', 'fine', 'alright', 'normal', 'standard', 'usual']
        }
        
        # Intent detection patterns
        self.intent_patterns = {
            'question': [r'\b(what|how|why|when|where|who|which)\b'],
            'request': [r'\b(can you|please|help me|show me|explain|demonstrate)\b'],
            'statement': [r'\b(this is|I have|there is|it is|we are)\b'],
            'command': [r'\b(do this|create|make|build|generate|write)\b']
        }
    
    # Folder Management
    def create_folder(self, name: str, description: str = None, color: str = "#3B82F6") -> ConversationFolder:
        """Create a new conversation folder"""
        folder_id = str(uuid.uuid4())
        folder = ConversationFolder(
            id=folder_id,
            name=name,
            description=description,
            color=color
        )
        
        self._save_folder(folder)
        return folder
    
    def get_folders(self) -> List[ConversationFolder]:
        """Get all conversation folders"""
        folders = []
        if os.path.exists(self.folders_path):
            for filename in os.listdir(self.folders_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.folders_path, filename), 'r') as f:
                            data = json.load(f)
                            folder = ConversationFolder(**data)
                            folders.append(folder)
                    except Exception as e:
                        self.logger.error(f"Error loading folder {filename}: {str(e)}")
        
        return sorted(folders, key=lambda x: x.name)
    
    def update_folder(self, folder_id: str, **kwargs) -> Optional[ConversationFolder]:
        """Update a conversation folder"""
        folder = self._load_folder(folder_id)
        if folder:
            for key, value in kwargs.items():
                if hasattr(folder, key):
                    setattr(folder, key, value)
            folder.updated_at = datetime.now()
            self._save_folder(folder)
            return folder
        return None
    
    def delete_folder(self, folder_id: str) -> bool:
        """Delete a conversation folder"""
        folder_path = os.path.join(self.folders_path, f"{folder_id}.json")
        if os.path.exists(folder_path):
            os.remove(folder_path)
            return True
        return False
    
    def move_conversation_to_folder(self, conversation_id: str, folder_id: str) -> bool:
        """Move a conversation to a specific folder"""
        # This would integrate with the existing conversation storage
        # For now, we'll update the metadata
        try:
            # Load existing conversation metadata
            metadata = self._load_conversation_metadata(conversation_id)
            if metadata:
                metadata.folder_id = folder_id
                metadata.last_accessed = datetime.now()
                self._save_conversation_metadata(conversation_id, metadata)
                return True
        except Exception as e:
            self.logger.error(f"Error moving conversation {conversation_id}: {str(e)}")
        return False
    
    # Template Management
    def create_template(self, name: str, description: str, category: str, 
                       system_prompt: str, initial_messages: List[Dict]) -> ConversationTemplate:
        """Create a new conversation template"""
        template_id = str(uuid.uuid4())
        template = ConversationTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            system_prompt=system_prompt,
            initial_messages=initial_messages
        )
        
        self._save_template(template)
        return template
    
    def get_templates(self, category: str = None) -> List[ConversationTemplate]:
        """Get conversation templates, optionally filtered by category"""
        templates = []
        if os.path.exists(self.templates_path):
            for filename in os.listdir(self.templates_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.templates_path, filename), 'r') as f:
                            data = json.load(f)
                            template = ConversationTemplate(**data)
                            if category is None or template.category == category:
                                templates.append(template)
                    except Exception as e:
                        self.logger.error(f"Error loading template {filename}: {str(e)}")
        
        return sorted(templates, key=lambda x: x.name)
    
    def use_template(self, template_id: str) -> Optional[Dict]:
        """Use a template to create a new conversation"""
        template = self._load_template(template_id)
        if template:
            # Increment usage count
            template.usage_count += 1
            self._save_template(template)
            
            # Return template data for new conversation
            return {
                "template_id": template.id,
                "template_name": template.name,
                "system_prompt": template.system_prompt,
                "initial_messages": template.initial_messages,
                "category": template.category
            }
        return None
    
    # Export/Import
    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """Export a conversation to a file"""
        try:
            # Load conversation data (this would integrate with existing storage)
            conversation_data = self._load_conversation_data(conversation_id)
            if not conversation_data:
                return None
            
            # Add metadata
            metadata = self._load_conversation_metadata(conversation_id)
            export_data = {
                "conversation": conversation_data,
                "metadata": asdict(metadata) if metadata else {},
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "format": format,
                    "version": "1.0"
                }
            }
            
            # Create export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{conversation_id}_{timestamp}.{format}"
            export_path = os.path.join(self.exports_path, filename)
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            # Update export history
            if metadata:
                metadata.export_history.append({
                    "exported_at": datetime.now().isoformat(),
                    "filename": filename,
                    "format": format
                })
                self._save_conversation_metadata(conversation_id, metadata)
            
            return export_path
            
        except Exception as e:
            self.logger.error(f"Error exporting conversation {conversation_id}: {str(e)}")
            return None
    
    def export_conversations_batch(self, conversation_ids: List[str], format: str = "zip") -> Optional[str]:
        """Export multiple conversations as a batch"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"conversations_batch_{timestamp}.zip"
            zip_path = os.path.join(self.exports_path, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for conv_id in conversation_ids:
                    export_path = self.export_conversation(conv_id, "json")
                    if export_path:
                        zipf.write(export_path, os.path.basename(export_path))
            
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error exporting conversations batch: {str(e)}")
            return None
    
    def import_conversation(self, file_path: str) -> Optional[str]:
        """Import a conversation from a file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate import data
            if 'conversation' not in import_data:
                raise ValueError("Invalid conversation export file")
            
            # Generate new conversation ID
            new_conversation_id = str(uuid.uuid4())
            
            # Save imported conversation
            self._save_conversation_data(new_conversation_id, import_data['conversation'])
            
            # Save metadata if available
            if 'metadata' in import_data:
                metadata = ConversationMetadata(**import_data['metadata'])
                metadata.last_accessed = datetime.now()
                self._save_conversation_metadata(new_conversation_id, metadata)
            
            return new_conversation_id
            
        except Exception as e:
            self.logger.error(f"Error importing conversation: {str(e)}")
            return None
    
    # Sharing
    def share_conversation(self, conversation_id: str, user_ids: List[str]) -> bool:
        """Share a conversation with other users"""
        try:
            metadata = self._load_conversation_metadata(conversation_id)
            if metadata:
                metadata.shared_with.extend(user_ids)
                metadata.shared_with = list(set(metadata.shared_with))  # Remove duplicates
                metadata.status = ConversationStatus.SHARED
                self._save_conversation_metadata(conversation_id, metadata)
                return True
        except Exception as e:
            self.logger.error(f"Error sharing conversation {conversation_id}: {str(e)}")
        return False
    
    def get_shared_conversations(self, user_id: str) -> List[str]:
        """Get conversations shared with a specific user"""
        shared_conversations = []
        # This would scan all conversation metadata
        # For now, return empty list
        return shared_conversations
    
    # Enhanced Analytics
    def get_conversation_analytics(self, conversation_id: str) -> ConversationAnalytics:
        """Get comprehensive analytics for a conversation"""
        try:
            data = self._load_conversation_data(conversation_id)
            if not data:
                return ConversationAnalytics()
            
            messages = data.get('messages', [])
            if not messages:
                return ConversationAnalytics()
            
            # Basic analytics
            total_messages = len(messages)
            user_messages = len([m for m in messages if m.get('role') == 'user'])
            assistant_messages = len([m for m in messages if m.get('role') == 'assistant'])
            
            # Calculate average message length
            total_length = sum(len(m.get('content', '')) for m in messages)
            avg_length = total_length / total_messages if total_messages > 0 else 0
            
            # Advanced analytics
            topic_distribution = self._analyze_topic_distribution(messages)
            response_time_stats = self._calculate_response_times(messages)
            user_engagement = self._calculate_user_engagement(messages)
            quality_score = self._calculate_conversation_quality(messages)
            
            return ConversationAnalytics(
                total_messages=total_messages,
                user_messages=user_messages,
                assistant_messages=assistant_messages,
                average_message_length=avg_length,
                topic_distribution=topic_distribution,
                response_time_stats=response_time_stats,
                user_engagement_metrics=user_engagement,
                conversation_quality_score=quality_score,
                completion_rate=self._calculate_completion_rate(messages),
                user_satisfaction_score=self._calculate_satisfaction_score(messages)
            )
        except Exception as e:
            self.logger.error(f"Error getting analytics for {conversation_id}: {e}")
            return ConversationAnalytics()
    
    def analyze_conversation_insights(self, conversation_id: str) -> ConversationInsights:
        """Analyze conversation for intelligent insights"""
        try:
            data = self._load_conversation_data(conversation_id)
            if not data:
                return ConversationInsights()
            
            messages = data.get('messages', [])
            if not messages:
                return ConversationInsights()
            
            # Extract insights
            key_topics = self._extract_key_topics(messages)
            sentiment_score = self._calculate_sentiment(messages)
            user_intent = self._detect_user_intent(messages)
            conversation_flow = self._analyze_conversation_flow(messages)
            knowledge_gaps = self._identify_knowledge_gaps(messages)
            action_items = self._extract_action_items(messages)
            follow_up_questions = self._generate_follow_up_questions(messages)
            context_switches = self._count_context_switches(messages)
            avg_response_time = self._calculate_average_response_time(messages)
            satisfaction_indicators = self._detect_satisfaction_indicators(messages)
            
            return ConversationInsights(
                key_topics=key_topics,
                sentiment_score=sentiment_score,
                user_intent=user_intent,
                conversation_flow=conversation_flow,
                knowledge_gaps=knowledge_gaps,
                action_items=action_items,
                follow_up_questions=follow_up_questions,
                context_switches=context_switches,
                average_response_time=avg_response_time,
                user_satisfaction_indicators=satisfaction_indicators
            )
        except Exception as e:
            self.logger.error(f"Error analyzing insights for {conversation_id}: {e}")
            return ConversationInsights()
    
    def manage_conversation_context(self, conversation_id: str) -> ConversationContext:
        """Manage context for a conversation"""
        try:
            context_file = os.path.join(self.context_path, f"{conversation_id}.json")
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    context_data = json.load(f)
                return ConversationContext(**context_data)
            
            # Create new context
            context = ConversationContext()
            self._save_conversation_context(conversation_id, context)
            return context
        except Exception as e:
            self.logger.error(f"Error managing context for {conversation_id}: {e}")
            return ConversationContext()
    
    def update_conversation_context(self, conversation_id: str, new_topic: str = None, 
                                  context_data: Dict[str, Any] = None):
        """Update conversation context"""
        try:
            context = self.manage_conversation_context(conversation_id)
            
            if new_topic:
                context.current_topic = new_topic
            
            if context_data:
                context.memory_bank.update(context_data)
            
            # Update context importance
            if new_topic:
                context.context_importance[new_topic] = 1.0
            
            self._save_conversation_context(conversation_id, context)
        except Exception as e:
            self.logger.error(f"Error updating context for {conversation_id}: {e}")
    
    def get_conversation_recommendations(self, conversation_id: str) -> Dict[str, Any]:
        """Get intelligent recommendations for a conversation"""
        try:
            insights = self.analyze_conversation_insights(conversation_id)
            analytics = self.get_conversation_analytics(conversation_id)
            
            recommendations = {
                'suggested_topics': self._suggest_related_topics(insights.key_topics),
                'improvement_areas': self._identify_improvement_areas(insights, analytics),
                'next_steps': self._suggest_next_steps(insights.action_items),
                'template_suggestions': self._suggest_templates(insights.user_intent),
                'follow_up_questions': insights.follow_up_questions,
                'priority_level': self._calculate_priority_level(insights, analytics)
            }
            
            return recommendations
        except Exception as e:
            self.logger.error(f"Error getting recommendations for {conversation_id}: {e}")
            return {}
    
    # Helper methods
    def _save_folder(self, folder: ConversationFolder):
        """Save a folder to disk"""
        folder_path = os.path.join(self.folders_path, f"{folder.id}.json")
        with open(folder_path, 'w') as f:
            json.dump(asdict(folder), f, indent=2, default=str)
    
    def _load_folder(self, folder_id: str) -> Optional[ConversationFolder]:
        """Load a folder from disk"""
        folder_path = os.path.join(self.folders_path, f"{folder_id}.json")
        if os.path.exists(folder_path):
            with open(folder_path, 'r') as f:
                data = json.load(f)
                return ConversationFolder(**data)
        return None
    
    def _save_template(self, template: ConversationTemplate):
        """Save a template to disk"""
        template_path = os.path.join(self.templates_path, f"{template.id}.json")
        with open(template_path, 'w') as f:
            json.dump(asdict(template), f, indent=2, default=str)
    
    def _load_template(self, template_id: str) -> Optional[ConversationTemplate]:
        """Load a template from disk"""
        template_path = os.path.join(self.templates_path, f"{template_id}.json")
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                data = json.load(f)
                return ConversationTemplate(**data)
        return None
    
    def _save_conversation_metadata(self, conversation_id: str, metadata: ConversationMetadata):
        """Save conversation metadata"""
        # This would integrate with existing conversation storage
        # For now, we'll create a separate metadata file
        metadata_path = os.path.join(self.storage_path, f"{conversation_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
    
    def _load_conversation_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """Load conversation metadata"""
        metadata_path = os.path.join(self.storage_path, f"{conversation_id}_metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                return ConversationMetadata(**data)
        return None
    
    def _save_conversation_data(self, conversation_id: str, data: Dict):
        """Save conversation data"""
        # This would integrate with existing conversation storage
        data_path = os.path.join(self.storage_path, f"{conversation_id}.json")
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_conversation_data(self, conversation_id: str) -> Optional[Dict]:
        """Load conversation data"""
        data_path = os.path.join(self.storage_path, f"{conversation_id}.json")
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return json.load(f)
        return None
    
    # Advanced Analytics Helper Methods
    def _analyze_topic_distribution(self, messages: List[Dict]) -> Dict[str, int]:
        """Analyze topic distribution in messages"""
        topic_counts = defaultdict(int)
        
        for message in messages:
            content = message.get('content', '').lower()
            for topic, patterns in self.topic_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        topic_counts[topic] += 1
                        break
        
        return dict(topic_counts)
    
    def _calculate_response_times(self, messages: List[Dict]) -> Dict[str, float]:
        """Calculate response time statistics"""
        response_times = []
        
        for i in range(1, len(messages)):
            if messages[i].get('role') == 'assistant' and messages[i-1].get('role') == 'user':
                # Calculate time difference (simplified)
                response_times.append(1.0)  # Placeholder
        
        if response_times:
            return {
                'average': sum(response_times) / len(response_times),
                'min': min(response_times),
                'max': max(response_times)
            }
        return {'average': 0.0, 'min': 0.0, 'max': 0.0}
    
    def _calculate_user_engagement(self, messages: List[Dict]) -> Dict[str, float]:
        """Calculate user engagement metrics"""
        user_messages = [m for m in messages if m.get('role') == 'user']
        
        if not user_messages:
            return {'message_length': 0.0, 'interaction_frequency': 0.0}
        
        avg_length = sum(len(m.get('content', '')) for m in user_messages) / len(user_messages)
        interaction_frequency = len(user_messages) / len(messages) if messages else 0
        
        return {
            'message_length': avg_length,
            'interaction_frequency': interaction_frequency
        }
    
    def _calculate_conversation_quality(self, messages: List[Dict]) -> float:
        """Calculate overall conversation quality score"""
        if not messages:
            return 0.0
        
        # Simple quality metrics
        message_count = len(messages)
        avg_length = sum(len(m.get('content', '')) for m in messages) / message_count
        user_assistant_ratio = len([m for m in messages if m.get('role') == 'user']) / message_count
        
        # Quality score based on message count, length, and balance
        quality_score = min(1.0, (message_count / 10) * 0.4 + (avg_length / 100) * 0.3 + user_assistant_ratio * 0.3)
        
        return quality_score
    
    def _calculate_completion_rate(self, messages: List[Dict]) -> float:
        """Calculate conversation completion rate"""
        if not messages:
            return 0.0
        
        # Simple completion logic
        last_message = messages[-1]
        if last_message.get('role') == 'assistant':
            return 1.0
        return 0.5
    
    def _calculate_satisfaction_score(self, messages: List[Dict]) -> float:
        """Calculate user satisfaction score"""
        if not messages:
            return 0.0
        
        satisfaction_indicators = self._detect_satisfaction_indicators(messages)
        positive_count = len([i for i in satisfaction_indicators if 'positive' in i])
        total_indicators = len(satisfaction_indicators)
        
        if total_indicators == 0:
            return 0.5  # Neutral default
        
        return positive_count / total_indicators
    
    def _extract_key_topics(self, messages: List[Dict]) -> List[str]:
        """Extract key topics from conversation"""
        all_content = ' '.join([m.get('content', '') for m in messages])
        
        # Simple keyword extraction
        keywords = ['api', 'code', 'help', 'problem', 'design', 'research', 'plan', 'analysis']
        found_topics = [topic for topic in keywords if topic in all_content.lower()]
        
        return found_topics[:5]  # Return top 5 topics
    
    def _calculate_sentiment(self, messages: List[Dict]) -> float:
        """Calculate overall sentiment score"""
        if not messages:
            return 0.0
        
        positive_count = 0
        negative_count = 0
        
        for message in messages:
            content = message.get('content', '').lower()
            
            for word in self.sentiment_indicators['positive']:
                if word in content:
                    positive_count += 1
            
            for word in self.sentiment_indicators['negative']:
                if word in content:
                    negative_count += 1
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words
    
    def _detect_user_intent(self, messages: List[Dict]) -> str:
        """Detect primary user intent"""
        user_messages = [m for m in messages if m.get('role') == 'user']
        
        if not user_messages:
            return "general"
        
        intent_counts = defaultdict(int)
        
        for message in user_messages:
            content = message.get('content', '').lower()
            
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        intent_counts[intent] += 1
                        break
        
        if intent_counts:
            return max(intent_counts, key=intent_counts.get)
        
        return "general"
    
    def _analyze_conversation_flow(self, messages: List[Dict]) -> str:
        """Analyze conversation flow pattern"""
        if len(messages) < 3:
            return "linear"
        
        # Simple flow analysis
        user_messages = [i for i, m in enumerate(messages) if m.get('role') == 'user']
        
        if len(user_messages) <= 1:
            return "linear"
        
        # Check for branching (multiple user messages in sequence)
        for i in range(len(user_messages) - 1):
            if user_messages[i+1] - user_messages[i] == 1:
                return "branching"
        
        return "linear"
    
    def _identify_knowledge_gaps(self, messages: List[Dict]) -> List[str]:
        """Identify potential knowledge gaps"""
        gaps = []
        
        for message in messages:
            content = message.get('content', '').lower()
            if any(word in content for word in ['don\'t know', 'not sure', 'unclear', 'confused']):
                gaps.append("User uncertainty detected")
        
        return gaps
    
    def _extract_action_items(self, messages: List[Dict]) -> List[str]:
        """Extract action items from conversation"""
        action_items = []
        
        for message in messages:
            content = message.get('content', '').lower()
            if any(word in content for word in ['need to', 'should', 'must', 'will do', 'plan to']):
                action_items.append(content[:100] + "...")
        
        return action_items[:5]  # Return top 5 action items
    
    def _generate_follow_up_questions(self, messages: List[Dict]) -> List[str]:
        """Generate follow-up questions based on conversation"""
        questions = [
            "Would you like me to elaborate on any specific topic?",
            "Is there anything else you'd like to explore?",
            "Do you have any questions about what we discussed?"
        ]
        
        return questions[:3]
    
    def _count_context_switches(self, messages: List[Dict]) -> int:
        """Count context switches in conversation"""
        switches = 0
        topics = []
        
        for message in messages:
            content = message.get('content', '').lower()
            current_topics = []
            
            for topic, patterns in self.topic_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        current_topics.append(topic)
                        break
            
            if topics and set(current_topics) != set(topics):
                switches += 1
            
            topics = current_topics
        
        return switches
    
    def _calculate_average_response_time(self, messages: List[Dict]) -> float:
        """Calculate average response time"""
        # Simplified calculation
        return 2.5  # Placeholder value
    
    def _detect_satisfaction_indicators(self, messages: List[Dict]) -> List[str]:
        """Detect user satisfaction indicators"""
        indicators = []
        
        for message in messages:
            content = message.get('content', '').lower()
            
            if any(word in content for word in self.sentiment_indicators['positive']):
                indicators.append('positive')
            elif any(word in content for word in self.sentiment_indicators['negative']):
                indicators.append('negative')
        
        return indicators
    
    def _suggest_related_topics(self, key_topics: List[str]) -> List[str]:
        """Suggest related topics based on key topics"""
        topic_suggestions = {
            'technical': ['API documentation', 'Code examples', 'Best practices'],
            'research': ['Data analysis', 'Literature review', 'Methodology'],
            'support': ['Troubleshooting', 'FAQ', 'Contact support'],
            'creative': ['Design inspiration', 'Brand guidelines', 'Visual examples']
        }
        
        suggestions = []
        for topic in key_topics:
            if topic in topic_suggestions:
                suggestions.extend(topic_suggestions[topic])
        
        return suggestions[:5]
    
    def _identify_improvement_areas(self, insights: ConversationInsights, 
                                  analytics: ConversationAnalytics) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        if analytics.conversation_quality_score < 0.5:
            improvements.append("Conversation quality could be improved")
        
        if insights.sentiment_score < 0:
            improvements.append("User satisfaction needs attention")
        
        if analytics.completion_rate < 0.8:
            improvements.append("Conversation completion rate is low")
        
        return improvements
    
    def _suggest_next_steps(self, action_items: List[str]) -> List[str]:
        """Suggest next steps based on action items"""
        return [f"Follow up on: {item}" for item in action_items[:3]]
    
    def _suggest_templates(self, user_intent: str) -> List[str]:
        """Suggest relevant templates based on user intent"""
        template_suggestions = {
            'question': ['FAQ Template', 'Research Template'],
            'request': ['Support Template', 'Technical Template'],
            'statement': ['Analysis Template', 'Documentation Template'],
            'command': ['Creative Template', 'Planning Template']
        }
        
        return template_suggestions.get(user_intent, ['General Template'])
    
    def _calculate_priority_level(self, insights: ConversationInsights, 
                                analytics: ConversationAnalytics) -> str:
        """Calculate priority level for conversation"""
        score = 0
        
        # Factors that increase priority
        if analytics.conversation_quality_score > 0.8:
            score += 2
        if insights.sentiment_score > 0.5:
            score += 1
        if analytics.user_satisfaction_score > 0.8:
            score += 2
        
        # Factors that decrease priority
        if analytics.completion_rate < 0.5:
            score -= 1
        
        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"
    
    def _save_conversation_context(self, conversation_id: str, context: ConversationContext):
        """Save conversation context"""
        context_file = os.path.join(self.context_path, f"{conversation_id}.json")
        with open(context_file, 'w') as f:
            json.dump(asdict(context), f, indent=2, default=str)


# Global conversation manager instance
conversation_manager = ConversationManager() 