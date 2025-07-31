import React, { useState, useEffect } from 'react';
import { 
  Folder, 
  FolderPlus, 
  FileText, 
  Download, 
  Upload, 
  Share2, 
  Settings, 
  Trash2, 
  Edit, 
  Plus,
  Search,
  Filter,
  BarChart3,
  Users,
  Calendar,
  Tag,
  Star,
  Archive,
  Copy,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  MoreHorizontal,
  Sparkles,
  MessageSquare,
  BookOpen,
  Share,
  Lock,
  Unlock
} from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

interface ConversationFolder {
  id: string;
  name: string;
  description?: string;
  color: string;
  created_at: string;
  updated_at: string;
  conversation_count: number;
}

interface ConversationTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  system_prompt: string;
  initial_messages: any[];
  tags: string[];
  created_at: string;
  usage_count: number;
}

interface ConversationAnalytics {
  conversation_id: string;
  access_count: number;
  last_accessed: string;
  message_count: number;
  shared_with_count: number;
  export_count: number;
  status: string;
}

const ConversationManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'folders' | 'templates' | 'export' | 'sharing' | 'analytics'>('folders');
  const [folders, setFolders] = useState<ConversationFolder[]>([]);
  const [templates, setTemplates] = useState<ConversationTemplate[]>([]);
  const [analytics, setAnalytics] = useState<ConversationAnalytics[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<ConversationFolder | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<ConversationTemplate | null>(null);

  // Form states
  const [folderForm, setFolderForm] = useState({
    name: '',
    description: '',
    color: '#3B82F6'
  });

  const [templateForm, setTemplateForm] = useState({
    name: '',
    description: '',
    category: '',
    system_prompt: '',
    initial_messages: []
  });

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'folders':
          await loadFolders();
          break;
        case 'templates':
          await loadTemplates();
          break;
        case 'analytics':
          await loadAnalytics();
          break;
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFolders = async () => {
    try {
      const response = await fetch('/conversations/folders');
      const data = await response.json();
      if (data.folders) {
        setFolders(data.folders);
      }
    } catch (error) {
      console.error('Error loading folders:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/conversations/templates');
      const data = await response.json();
      if (data.templates) {
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const loadAnalytics = async () => {
    // Mock analytics data for demonstration
    setAnalytics([
      {
        conversation_id: 'conv-1',
        access_count: 15,
        last_accessed: '2024-01-15T10:30:00Z',
        message_count: 25,
        shared_with_count: 2,
        export_count: 1,
        status: 'active'
      },
      {
        conversation_id: 'conv-2',
        access_count: 8,
        last_accessed: '2024-01-14T15:45:00Z',
        message_count: 12,
        shared_with_count: 0,
        export_count: 0,
        status: 'archived'
      }
    ]);
  };

  const createFolder = async () => {
    try {
      const response = await fetch('/conversations/folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(folderForm)
      });

      if (response.ok) {
        setShowCreateFolder(false);
        setFolderForm({ name: '', description: '', color: '#3B82F6' });
        await loadFolders();
      }
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  const createTemplate = async () => {
    try {
      const response = await fetch('/conversations/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          ...templateForm,
          initial_messages: JSON.stringify(templateForm.initial_messages)
        })
      });

      if (response.ok) {
        setShowCreateTemplate(false);
        setTemplateForm({ name: '', description: '', category: '', system_prompt: '', initial_messages: [] });
        await loadTemplates();
      }
    } catch (error) {
      console.error('Error creating template:', error);
    }
  };

  const exportConversation = async (conversationId: string) => {
    try {
      const response = await fetch('/conversations/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          conversation_id: conversationId,
          format: 'json'
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Export successful:', data);
      }
    } catch (error) {
      console.error('Error exporting conversation:', error);
    }
  };

  const shareConversation = async (conversationId: string, userEmails: string[]) => {
    try {
      const response = await fetch('/conversations/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          conversation_id: conversationId,
          user_ids: JSON.stringify(userEmails)
        })
      });

      if (response.ok) {
        console.log('Conversation shared successfully');
      }
    } catch (error) {
      console.error('Error sharing conversation:', error);
    }
  };

  const renderFoldersTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Conversation Folders</h2>
        <Button onClick={() => setShowCreateFolder(true)} className="flex items-center space-x-2">
          <FolderPlus className="h-4 w-4" />
          <span>Create Folder</span>
        </Button>
      </div>

      {showCreateFolder && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Folder</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Name</label>
              <input
                type="text"
                value={folderForm.name}
                onChange={(e) => setFolderForm({ ...folderForm, name: e.target.value })}
                className="w-full p-2 border border-border rounded-lg bg-surface"
                placeholder="Enter folder name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={folderForm.description}
                onChange={(e) => setFolderForm({ ...folderForm, description: e.target.value })}
                className="w-full p-2 border border-border rounded-lg bg-surface"
                placeholder="Enter folder description"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Color</label>
              <input
                type="color"
                value={folderForm.color}
                onChange={(e) => setFolderForm({ ...folderForm, color: e.target.value })}
                className="w-full h-10 border border-border rounded-lg"
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={createFolder} disabled={!folderForm.name}>
                Create Folder
              </Button>
              <Button variant="outline" onClick={() => setShowCreateFolder(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {folders.map((folder) => (
          <Card key={folder.id} className="p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded-full" 
                  style={{ backgroundColor: folder.color }}
                />
                <div>
                  <h3 className="font-semibold">{folder.name}</h3>
                  <p className="text-sm text-muted-foreground">{folder.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <Button variant="ghost" size="sm">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-muted-foreground">
              <span>{folder.conversation_count} conversations</span>
              <span>{new Date(folder.created_at).toLocaleDateString()}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderTemplatesTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Conversation Templates</h2>
        <Button onClick={() => setShowCreateTemplate(true)} className="flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Create Template</span>
        </Button>
      </div>

      {showCreateTemplate && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Template</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Name</label>
                <input
                  type="text"
                  value={templateForm.name}
                  onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                  className="w-full p-2 border border-border rounded-lg bg-surface"
                  placeholder="Template name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <input
                  type="text"
                  value={templateForm.category}
                  onChange={(e) => setTemplateForm({ ...templateForm, category: e.target.value })}
                  className="w-full p-2 border border-border rounded-lg bg-surface"
                  placeholder="e.g., support, sales, general"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={templateForm.description}
                onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })}
                className="w-full p-2 border border-border rounded-lg bg-surface"
                placeholder="Template description"
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">System Prompt</label>
              <textarea
                value={templateForm.system_prompt}
                onChange={(e) => setTemplateForm({ ...templateForm, system_prompt: e.target.value })}
                className="w-full p-2 border border-border rounded-lg bg-surface"
                placeholder="Enter the system prompt for this template"
                rows={4}
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={createTemplate} disabled={!templateForm.name || !templateForm.system_prompt}>
                Create Template
              </Button>
              <Button variant="outline" onClick={() => setShowCreateTemplate(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <Card key={template.id} className="p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold">{template.name}</h3>
                <p className="text-sm text-muted-foreground">{template.description}</p>
              </div>
              <div className="flex items-center space-x-1">
                <Button variant="ghost" size="sm">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm">
                <Tag className="h-3 w-3" />
                <span className="bg-primary/10 text-primary px-2 py-1 rounded-full text-xs">
                  {template.category}
                </span>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {template.system_prompt}
              </p>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>{template.usage_count} uses</span>
                <span>{new Date(template.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="mt-3">
              <Button size="sm" className="w-full">
                Use Template
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderExportTab = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Export & Import</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Export Section */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <Download className="h-5 w-5" />
            <span>Export Conversations</span>
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Select Conversations</label>
              <div className="space-y-2">
                {['Conversation 1', 'Conversation 2', 'Conversation 3'].map((conv, index) => (
                  <label key={index} className="flex items-center space-x-2">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">{conv}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Export Format</label>
              <select className="w-full p-2 border border-border rounded-lg bg-surface">
                <option value="json">JSON</option>
                <option value="zip">ZIP (Batch)</option>
                <option value="txt">Plain Text</option>
              </select>
            </div>
            <Button className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export Selected
            </Button>
          </div>
        </Card>

        {/* Import Section */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <Upload className="h-5 w-5" />
            <span>Import Conversations</span>
          </h3>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground mb-2">
                Drag and drop conversation files here
              </p>
              <p className="text-xs text-muted-foreground">
                Supports JSON, ZIP, and TXT formats
              </p>
              <Button variant="outline" className="mt-3">
                Choose Files
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              <p>• Import individual conversation files</p>
              <p>• Import batch exports (ZIP files)</p>
              <p>• Maintains conversation metadata</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );

  const renderSharingTab = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Conversation Sharing</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Shared Conversations */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <Share2 className="h-5 w-5" />
            <span>Shared with Me</span>
          </h3>
          <div className="space-y-3">
            {[
              { id: '1', title: 'Project Discussion', shared_by: 'alice@example.com', date: '2024-01-15' },
              { id: '2', title: 'Technical Review', shared_by: 'bob@example.com', date: '2024-01-14' }
            ].map((conv) => (
              <div key={conv.id} className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div>
                  <p className="font-medium">{conv.title}</p>
                  <p className="text-sm text-muted-foreground">Shared by {conv.shared_by}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Share Conversations */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Share Conversations</span>
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Select Conversation</label>
              <select className="w-full p-2 border border-border rounded-lg bg-surface">
                <option value="">Choose a conversation...</option>
                <option value="conv-1">Project Discussion</option>
                <option value="conv-2">Technical Review</option>
                <option value="conv-3">Meeting Notes</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Share with Users</label>
              <input
                type="text"
                className="w-full p-2 border border-border rounded-lg bg-surface"
                placeholder="Enter email addresses (comma-separated)"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm">Allow editing</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm">Allow sharing</span>
              </label>
            </div>
            <Button className="w-full">
              <Share2 className="h-4 w-4 mr-2" />
              Share Conversation
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Conversation Analytics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MessageSquare className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">24</p>
              <p className="text-sm text-muted-foreground">Total Conversations</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <BarChart3 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">156</p>
              <p className="text-sm text-muted-foreground">Total Messages</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Share className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">8</p>
              <p className="text-sm text-muted-foreground">Shared Conversations</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Download className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">12</p>
              <p className="text-sm text-muted-foreground">Exports</p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Conversations</h3>
        <div className="space-y-3">
          {analytics.map((conv) => (
            <div key={conv.conversation_id} className="flex items-center justify-between p-3 border border-border rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <div>
                  <p className="font-medium">Conversation {conv.conversation_id}</p>
                  <p className="text-sm text-muted-foreground">
                    {conv.message_count} messages • {conv.access_count} accesses
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>{conv.shared_with_count} shared</span>
                <span>{conv.export_count} exports</span>
                <span>{new Date(conv.last_accessed).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

  const tabs = [
    { id: 'folders', label: 'Folders', icon: Folder },
    { id: 'templates', label: 'Templates', icon: FileText },
    { id: 'export', label: 'Export/Import', icon: Download },
    { id: 'sharing', label: 'Sharing', icon: Share2 },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 }
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Conversation Manager</h1>
          <p className="text-muted-foreground">
            Manage your conversations, templates, and sharing settings
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-border mb-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="min-h-[600px]">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {activeTab === 'folders' && renderFoldersTab()}
              {activeTab === 'templates' && renderTemplatesTab()}
              {activeTab === 'export' && renderExportTab()}
              {activeTab === 'sharing' && renderSharingTab()}
              {activeTab === 'analytics' && renderAnalyticsTab()}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversationManager; 