"""
Conversation Management Module for RAG Chatbot
Handles conversation organization, folders, export/import, and templates
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import zipfile
import tempfile
import shutil


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
    """Metadata for conversation management"""
    folder_id: Optional[str] = None
    tags: List[str] = None
    priority: int = 0  # 0-10, higher is more important
    status: ConversationStatus = ConversationStatus.ACTIVE
    last_accessed: datetime = None
    access_count: int = 0
    shared_with: List[str] = None  # User IDs or emails
    export_history: List[Dict] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = datetime.now()
        if self.shared_with is None:
            self.shared_with = []
        if self.export_history is None:
            self.export_history = []


class ConversationManager:
    """Manages conversation organization, folders, and templates"""
    
    def __init__(self, storage_path: str = "conversations"):
        self.storage_path = storage_path
        self.folders_path = os.path.join(storage_path, "folders")
        self.templates_path = os.path.join(storage_path, "templates")
        self.exports_path = os.path.join(storage_path, "exports")
        
        # Create directories if they don't exist
        for path in [self.storage_path, self.folders_path, self.templates_path, self.exports_path]:
            os.makedirs(path, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
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
    
    # Analytics
    def get_conversation_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """Get analytics for a conversation"""
        metadata = self._load_conversation_metadata(conversation_id)
        conversation_data = self._load_conversation_data(conversation_id)
        
        analytics = {
            "conversation_id": conversation_id,
            "access_count": metadata.access_count if metadata else 0,
            "last_accessed": metadata.last_accessed.isoformat() if metadata else None,
            "message_count": len(conversation_data.get('messages', [])) if conversation_data else 0,
            "shared_with_count": len(metadata.shared_with) if metadata else 0,
            "export_count": len(metadata.export_history) if metadata else 0,
            "status": metadata.status.value if metadata else ConversationStatus.ACTIVE.value
        }
        
        return analytics
    
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


# Global conversation manager instance
conversation_manager = ConversationManager() 