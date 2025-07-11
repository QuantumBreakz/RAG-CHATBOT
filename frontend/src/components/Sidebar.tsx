import React, { useState } from 'react';
import { 
  Plus, 
  MessageSquare, 
  Settings, 
  Upload, 
  Database, 
  MoreHorizontal,
  Edit2,
  Trash2,
  Check,
  X,
  Search,
  Archive,
  Download,
  Moon,
  Sun,
  Zap
} from 'lucide-react';
import { Conversation, AppSettings } from '../types';
import { FileUpload } from './FileUpload';
import { formatTimestamp, truncateText } from '../utils/helpers';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onUploadFiles: (files: FileList) => void;
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
  onUploadFiles,
  settings,
  onSettingsChange
}) => {
  const [activeTab, setActiveTab] = useState<'chats' | 'upload' | 'settings'>('chats');
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState<string | null>(null);

  const activeConversation = conversations.find(c => c.id === activeConversationId);
  const filteredConversations = conversations.filter(conv => 
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.messages.some(msg => msg.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const startEditing = (conversation: Conversation) => {
    setEditingConversationId(conversation.id);
    setEditingTitle(conversation.title);
    setShowDropdown(null);
  };

  const cancelEditing = () => {
    setEditingConversationId(null);
    setEditingTitle('');
  };

  const saveEditing = () => {
    if (editingConversationId && editingTitle.trim()) {
      onRenameConversation(editingConversationId, editingTitle.trim());
    }
    cancelEditing();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveEditing();
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const toggleDropdown = (conversationId: string) => {
    setShowDropdown(showDropdown === conversationId ? null : conversationId);
  };

  const tabs = [
    { id: 'chats', label: 'Chats', icon: MessageSquare, count: conversations.length },
    { id: 'upload', label: 'Upload', icon: Upload, count: activeConversation?.uploadedFiles?.length || 0 },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full shadow-lg">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-emerald-50 to-green-50">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-green-700 rounded-xl flex items-center justify-center shadow-lg">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">XOR RAG</h1>
            <p className="text-sm text-muted-foreground">AI Document Assistant</p>
          </div>
        </div>
        
        <Button
          onClick={onNewConversation}
          variant="primary"
          size="md"
          icon={Plus}
          className="w-full"
        >
          New Conversation
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'chats' | 'upload' | 'settings')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? 'text-emerald-600 bg-white border-b-2 border-emerald-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <Badge variant="info" size="sm">{tab.count}</Badge>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden animate-fade-in">
        {activeTab === 'chats' && (
          <div className="h-full flex flex-col">
            {/* Search */}
            <div className="p-4 border-b border-gray-200">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Conversations */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-4 space-y-2">
                {filteredConversations.length === 0 ? (
                  <div className="text-center py-8 animate-fade-in">
                    <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">
                      {searchQuery ? 'No conversations found' : 'No conversations yet'}
                    </p>
                  </div>
                ) : (
                  filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`group relative rounded-xl p-4 cursor-pointer transition-all duration-200 animate-slide-up hover:scale-[1.02] ${
                        activeConversationId === conversation.id
                          ? 'bg-emerald-50 border-2 border-emerald-200 shadow-sm'
                          : 'hover:bg-gray-50 border-2 border-transparent'
                      }`}
                      onClick={() => onSelectConversation(conversation.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          {editingConversationId === conversation.id ? (
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={editingTitle}
                                onChange={(e) => setEditingTitle(e.target.value)}
                                onKeyDown={handleKeyPress}
                                className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                autoFocus
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                icon={Check}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  saveEditing();
                                }}
                                className="text-green-600 hover:text-green-700"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                icon={X}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  cancelEditing();
                                }}
                                className="text-gray-400 hover:text-gray-600"
                              />
                            </div>
                          ) : (
                            <>
                              <div className="flex items-center gap-2 mb-2">
                                <h3 className="text-sm font-semibold text-gray-900 truncate">
                                  {truncateText(conversation.title, 25)}
                                </h3>
                                {conversation.uploadedFiles.length > 0 && (
                                  <Badge variant="info" size="sm">
                                    {conversation.uploadedFiles.length}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-gray-500 mb-1">
                                {formatTimestamp(conversation.updatedAt)}
                              </p>
                              {conversation.messages.length > 0 && (
                                <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                                  {conversation.messages[conversation.messages.length - 1]?.content}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                        
                        {editingConversationId !== conversation.id && (
                          <div className="relative">
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={MoreHorizontal}
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleDropdown(conversation.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-all"
                            />
                            
                            {showDropdown === conversation.id && (
                              <div className="absolute right-0 top-8 w-40 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-1 animate-scale-in">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    startEditing(conversation);
                                  }}
                                  className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                >
                                  <Edit2 className="w-3 h-3" />
                                  Rename
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteConversation(conversation.id);
                                    setShowDropdown(null);
                                  }}
                                  className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                >
                                  <Trash2 className="w-3 h-3" />
                                  Delete
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'upload' && (
          <div className="p-6 animate-fade-in">
            <FileUpload
              onUpload={onUploadFiles}
              uploadedFiles={activeConversation?.uploadedFiles || []}
            />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="p-6 space-y-6 animate-fade-in">
            {/* Theme */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Appearance
              </label>
              <div className="flex gap-2">
                <Button
                  variant={settings.theme === 'light' ? 'primary' : 'secondary'}
                  size="sm"
                  icon={Sun}
                  onClick={() => onSettingsChange({...settings, theme: 'light'})}
                  className="flex-1 transition-all duration-200 hover:scale-105"
                >
                  Light
                </Button>
                <Button
                  variant={settings.theme === 'dark' ? 'primary' : 'secondary'}
                  size="sm"
                  icon={Moon}
                  onClick={() => onSettingsChange({...settings, theme: 'dark'})}
                  className="flex-1 transition-all duration-200 hover:scale-105"
                >
                  Dark
                </Button>
              </div>
            </div>

            {/* Model Settings */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Model: {settings.model}
              </label>
              <select
                value={settings.model}
                onChange={(e) => onSettingsChange({...settings, model: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all duration-200"
              >
                <option value="llama3.2:3b">Llama 3.2 3B</option>
                <option value="llama3.2:1b">Llama 3.2 1B</option>
                <option value="mistral:7b">Mistral 7B</option>
                <option value="codellama:7b">CodeLlama 7B</option>
              </select>
            </div>

            {/* Chunk Size */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Chunk Size: {settings.chunkSize} characters
              </label>
              <input
                type="range"
                min="200"
                max="1000"
                step="50"
                value={settings.chunkSize}
                onChange={(e) => onSettingsChange({...settings, chunkSize: parseInt(e.target.value)})}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider transition-all duration-200"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>200</span>
                <span>1000</span>
              </div>
            </div>

            {/* Max Results */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Max Results: {settings.maxResults}
              </label>
              <input
                type="range"
                min="5"
                max="20"
                value={settings.maxResults}
                onChange={(e) => onSettingsChange({...settings, maxResults: parseInt(e.target.value)})}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider transition-all duration-200"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>5</span>
                <span>20</span>
              </div>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Temperature: {settings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => onSettingsChange({...settings, temperature: parseFloat(e.target.value)})}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider transition-all duration-200"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.0 (Focused)</span>
                <span>1.0 (Creative)</span>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3 pt-4 border-t border-gray-200">
              <Button
                variant="secondary"
                size="md"
                icon={Download}
                className="w-full transition-all duration-200 hover:scale-105"
              >
                Export Conversations
              </Button>
              <Button
                variant="secondary"
                size="md"
                icon={Archive}
                className="w-full transition-all duration-200 hover:scale-105"
              >
                Archive Old Chats
              </Button>
              <Button
                variant="danger"
                size="md"
                icon={Database}
                className="w-full transition-all duration-200 hover:scale-105"
              >
                Reset Knowledge Base
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};