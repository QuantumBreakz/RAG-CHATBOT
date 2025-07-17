import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Send, Upload, FileText, X, Settings, Trash2, Plus, Bot, User, Sparkles, Pencil, ArrowRight } from 'lucide-react';
import { useChat } from '../contexts/ChatContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { useGlobalLoading } from '../App';
import { useStreamingAssistant } from './useStreamingAssistant';
import debounce from 'lodash.debounce';

const CHAT_STATE_KEY = 'xor_rag_chat_state';

const ChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [operationState, setOperationState] = useState({
    sending: false,
    uploading: false,
    loadingDocuments: false,
    loadingConversations: false,
  });
  const [documents, setDocuments] = useState<{filename: string, count: number, examples: any[]}[]>([]);
  const [conversations, setConversations] = useState<{id: string, title: string, created_at: string}[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerType, setBannerType] = useState<'success' | 'error' | null>(null);
  const [vectorstoreHealthy, setVectorstoreHealthy] = useState<boolean | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState<string>("");
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    sessions,
    setSessions,
    currentSession,
    createSession,
    createSessionFromPrevious,
    selectSession,
    addMessage,
    clearHistory,
    uploadedDocuments,
    addDocument,
    removeDocument,
    setCurrentSessionFromBackend,
    updateStreamingMessage,
    renameSession
  } = useChat();

  const { loading, setLoading } = useGlobalLoading();

  const {
    streamingContent,
    progress: streamingProgress,
    status: streamingStatus,
    error: streamingError,
    startStreaming,
    resetStreaming
  } = useStreamingAssistant();

  // Utility functions
  const showBanner = (message: string, type: 'success' | 'error') => {
    setBannerMessage(message);
    setBannerType(type);
    setTimeout(() => setBannerMessage(null), 3000);
  };

  const apiCall = async (url: string, options: RequestInit = {}) => {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Request failed');
    return data;
  };

  // Data fetching
  const fetchDocuments = async () => {
    setOperationState(s => ({ ...s, loadingDocuments: true }));
    setLoading(true);
    try {
      const data = await apiCall('/api/documents');
      setDocuments(data.documents || []);
    } catch (err) {
      showBanner('Failed to fetch documents.', 'error');
    }
    setOperationState(s => ({ ...s, loadingDocuments: false }));
    setLoading(false);
  };

  const fetchConversations = async () => {
    setOperationState(s => ({ ...s, loadingConversations: true }));
    setLoading(true);
    try {
      const data = await apiCall('/api/history/list');
      setConversations(data.conversations || []);
    } catch (err) {
      showBanner('Failed to fetch conversations.', 'error');
    }
    setOperationState(s => ({ ...s, loadingConversations: false }));
    setLoading(false);
  };

  const checkVectorstore = async () => {
    try {
      const data = await apiCall('/api/test_vectorstore');
      setVectorstoreHealthy(data.status === 'ok');
    } catch (err) {
      setVectorstoreHealthy(false);
    }
  };

  // Event handlers
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || operationState.sending || streamingStatus === 'streaming') return;

    const userMessage = inputValue.trim();
    setOperationState(s => ({ ...s, sending: true }));
    setInputValue("");

    // Add user message immediately
    addMessage(userMessage, 'user');

    try {
      // Start streaming and get the final content
      const streamedContent = await startStreaming(userMessage, currentSession?.messages || []);
      
      // Add assistant response after streaming completes
      addMessage(streamedContent, 'assistant');
      
      // Save to backend
      if (currentSession) {
        const updatedMessages = [
          ...currentSession.messages,
          { role: 'user', content: userMessage, timestamp: new Date() },
          { role: 'assistant', content: streamedContent, timestamp: new Date() }
        ];
        await apiCall('/api/history/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...currentSession,
            messages: updatedMessages
          })
        });
      }
    } catch (error) {
      showBanner('Failed to send message.', 'error');
    } finally {
      setOperationState(s => ({ ...s, sending: false }));
      resetStreaming();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    setOperationState(s => ({ ...s, uploading: true }));
    setLoading(true);

    // Get chunk size from settings
    let chunkSize = 1000;
    try {
      const settings = JSON.parse(localStorage.getItem('xor-rag-settings') || '{}');
      if (settings.chunkSize) chunkSize = settings.chunkSize;
    } catch {}

    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('chunk_size', chunkSize.toString());

      try {
        const data = await apiCall('/api/upload', {
          method: 'POST',
          body: formData
        });

        if (data.status?.includes('uploaded and embedded')) {
          showBanner(`Embeddings created for "${file.name}" (${data.num_chunks} chunks).`, 'success');
        } else if (data.status?.includes('already exist')) {
          showBanner(`Embeddings already exist for "${file.name}".`, 'success');
        } else {
          showBanner(`Embedding failed for "${file.name}": ${data.status}`, 'error');
        }
        addDocument(file.name);
      } catch (err) {
        showBanner(`Failed to upload document "${file.name}".`, 'error');
      }
    }

    setOperationState(s => ({ ...s, uploading: false }));
    setLoading(false);
    fetchDocuments();
  };

  const handleDeleteDocument = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    setLoading(true);
    try {
      await apiCall(`/api/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      showBanner(`Document "${filename}" deleted.`, 'success');
      fetchDocuments();
    } catch (err) {
      showBanner(`Failed to delete document "${filename}".`, 'error');
    }
    setLoading(false);
  };

  const handleSaveTitle = async () => {
    if (!currentSession) return;
    const updatedTitle = editedTitle.trim() || 'Untitled Conversation';
    renameSession(currentSession.id, updatedTitle);
    setIsEditingTitle(false);
    
    try {
      await apiCall('/api/history/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentSession, title: updatedTitle })
      });
      showBanner('Conversation renamed.', 'success');
      setConversations(prev => prev.map(conv => 
        conv.id === currentSession.id ? { ...conv, title: updatedTitle } : conv
      ));
    } catch (err) {
      showBanner('Failed to rename conversation.', 'error');
    }
  };

  const handleResetKB = async () => {
    if (!window.confirm('Are you sure you want to reset the knowledge base?')) return;
    setLoading(true);
    setStatusMessage('Resetting knowledge base...');
    try {
      const data = await apiCall('/api/reset_kb', { method: 'POST' });
      setStatusMessage(data.status || 'Knowledge base reset.');
      showBanner('Knowledge base reset.', 'success');
      fetchDocuments();
    } catch (err) {
      setStatusMessage('Failed to reset knowledge base.');
      showBanner('Failed to reset knowledge base.', 'error');
    }
    setLoading(false);
  };

  const handleHealthCheck = async () => {
    setStatusMessage('Checking backend health...');
    setLoading(true);
    try {
      const data = await apiCall('/api/health');
      setStatusMessage(data.status === 'ok' ? 'Backend healthy.' : 'Backend not healthy.');
    } catch (err) {
      setStatusMessage('Backend health check failed.');
      showBanner('Backend health check failed.', 'error');
    }
    setLoading(false);
  };

  // Scroll functionality
  const scrollToBottom = useMemo(() => debounce(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, 100), []);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, streamingContent, streamingStatus, scrollToBottom]);

  useEffect(() => {
    const handleScroll = () => {
      if (!messagesEndRef.current) return;
      const container = messagesEndRef.current.parentElement;
      if (!container) return;
      const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 40;
      setShowScrollButton(!atBottom);
    };
    const container = messagesEndRef.current?.parentElement;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [currentSession?.messages, streamingContent]);

  // Initialize data
  useEffect(() => {
    fetchDocuments();
    fetchConversations();
    checkVectorstore();
    const interval = setInterval(checkVectorstore, 30000);
    return () => clearInterval(interval);
  }, []);

  // Persistence
  useEffect(() => {
    const saved = localStorage.getItem(CHAT_STATE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.sessions && sessions.length === 0) setSessions(parsed.sessions);
        if (parsed.currentSession && !currentSession) setCurrentSessionFromBackend(parsed.currentSession);
        if (parsed.conversations && conversations.length === 0) setConversations(parsed.conversations);
      } catch {}
    }
  }, []);

  useEffect(() => {
    const safeSessions = sessions.map(s => ({
      ...s,
      createdAt: s.createdAt instanceof Date ? s.createdAt : new Date(s.createdAt),
      messages: (s.messages || []).map(m => ({
        ...m,
        timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp)
      }))
    }));
    const safeCurrentSession = currentSession ? {
      ...currentSession,
      createdAt: currentSession.createdAt instanceof Date ? currentSession.createdAt : new Date(currentSession.createdAt),
      messages: (currentSession.messages || []).map(m => ({
        ...m,
        timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp)
      }))
    } : null;
    localStorage.setItem(CHAT_STATE_KEY, JSON.stringify({ 
      sessions: safeSessions, 
      currentSession: safeCurrentSession, 
      conversations 
    }));
  }, [sessions, currentSession, conversations]);

  // Render streaming assistant bubble
  const renderStreamingAssistantBubble = () => {
    if (streamingStatus !== 'streaming' || !streamingContent) return null;
    return (
      <div className="flex justify-start">
        <div className="flex items-start space-x-3 max-w-2xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <Card variant="elevated" className="p-4">
            <p className="text-sm leading-relaxed whitespace-pre-line">
              {streamingContent}
              <span className="ml-1 animate-pulse">|</span>
            </p>
            <div className="text-xs mt-2 text-muted-foreground">
              Streaming...
            </div>
          </Card>
        </div>
      </div>
    );
  };

  // Memoized messages
  const memoizedMessages = useMemo(() =>
    currentSession?.messages?.map((message, idx) => (
      <div key={message.id || idx} className={`flex w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
        <div className={`flex items-start space-x-3 max-w-2xl w-full ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            message.role === 'user' 
              ? 'bg-gradient-to-r from-primary to-primary-dark' 
              : 'bg-surface-elevated border border-border'
          }`}>
            {message.role === 'user' ? (
              <User className="h-4 w-4 text-white" />
            ) : (
              <Bot className="h-4 w-4 text-primary" />
            )}
          </div>
          <Card variant={message.role === 'user' ? 'default' : 'elevated'} className={`p-4 rounded-lg shadow-sm w-full ${
            message.role === 'user' ? 'bg-primary text-white border-primary/30' : 'bg-surface-elevated'
          }`}>
            <p className="text-sm leading-relaxed whitespace-pre-line">
              {message.content || ''}
            </p>
            <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
              {message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
            </div>
          </Card>
        </div>
      </div>
    )) || [], [currentSession?.messages]);

  return (
    <div className="flex h-screen w-screen bg-background">
      {/* Sidebar */}
      <div className="bg-surface border-r border-border flex flex-col w-80 flex-none h-screen z-40 fixed left-0 top-0">
        {bannerMessage && (
          <div className={`p-2 text-xs text-center rounded-b ${bannerType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} shadow`}>
            {bannerMessage}
          </div>
        )}
        
        {/* New Chat Buttons */}
        <div className="p-4 border-b border-border flex flex-col gap-2">
          <Button onClick={createSession} className="w-full group rounded-lg shadow-sm" variant="outline">
            <Plus className="mr-2 h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
            New Conversation
          </Button>
          <Button onClick={createSessionFromPrevious} className="w-full group rounded-lg shadow-sm" variant="outline">
            <Sparkles className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform duration-300" />
            Duplicate Conversation
          </Button>
        </div>

        {/* Chat Sessions */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 flex items-center">
            <Sparkles className="mr-2 h-4 w-4" />
            Recent Conversations
          </h3>
          {sessions.length > 0 ? (
            sessions.map((conv) => (
              <Card key={conv.id} hover className={`p-4 cursor-pointer transition-all duration-300 rounded-lg shadow-sm ${
                currentSession?.id === conv.id ? 'border-2 border-primary' : ''
              }`} onClick={() => selectSession(conv.id)}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-foreground truncate mb-1">{conv.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {conv.createdAt ? new Date(conv.createdAt).toLocaleString() : ''}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          ) : (
            <div className="text-xs text-muted-foreground">No conversations found.</div>
          )}
        </div>

        {/* Document Context */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-muted-foreground flex items-center">
              <FileText className="mr-2 h-4 w-4" />
              Knowledge Base
            </h3>
            <Button onClick={() => fileInputRef.current?.click()} variant="ghost" size="sm" className="p-2">
              <Upload className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {operationState.loadingDocuments ? (
              <div className="text-xs text-muted-foreground">Loading documents...</div>
            ) : documents.length > 0 ? (
              documents.map((doc, index) => (
                <Card key={index} className="p-3 group flex items-center justify-between rounded-lg shadow-sm">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-xs text-foreground truncate">{doc.filename}</span>
                  </div>
                  <Button onClick={() => handleDeleteDocument(doc.filename)} variant="ghost" size="sm" 
                    className="p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <X className="h-3 w-3 text-muted-foreground hover:text-red-500" />
                  </Button>
                </Card>
              ))
            ) : (
              <Card className="p-6 text-center rounded-lg shadow-sm">
                <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">No documents uploaded</p>
                <Button onClick={() => fileInputRef.current?.click()} variant="ghost" size="sm" className="mt-2 text-xs">
                  Upload files
                </Button>
              </Card>
            )}
          </div>
        </div>

        {/* Settings & Admin */}
        <div className="p-4 border-t border-border">
          <div className="flex space-x-2 mb-2">
            <Button variant="outline" size="sm" className="flex-1" onClick={handleHealthCheck}>
              <Sparkles className="mr-2 h-4 w-4" />
              Health
            </Button>
            <Button variant="outline" size="sm" className="flex-1" onClick={handleResetKB}>
              <X className="mr-2 h-4 w-4" />
              Reset KB
            </Button>
          </div>
          <div className="mt-2 text-xs flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${
              vectorstoreHealthy === null ? 'bg-gray-300' : vectorstoreHealthy ? 'bg-green-500' : 'bg-red-500'
            }`}></span>
            <span>
              Vectorstore: {vectorstoreHealthy === null ? 'Checking...' : vectorstoreHealthy ? 'Healthy' : 'Unavailable'}
            </span>
          </div>
          {statusMessage && (
            <div className="text-xs text-muted-foreground mt-2">{statusMessage}</div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col ml-80">
        {/* Chat Header */}
        <div className="bg-surface border-b border-border p-4 md:p-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-primary" />
            {currentSession ? (
              isEditingTitle ? (
                <input
                  className="text-xl font-bold bg-surface border-b border-primary focus:outline-none px-2 py-1 rounded"
                  value={editedTitle}
                  autoFocus
                  onChange={e => setEditedTitle(e.target.value)}
                  onBlur={handleSaveTitle}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleSaveTitle();
                    if (e.key === 'Escape') setIsEditingTitle(false);
                  }}
                  style={{ width: '16rem' }}
                />
              ) : (
                <>
                  <span className="text-xl font-bold truncate max-w-xs md:max-w-md">
                    {currentSession.title || 'XOR RAG Assistant'}
                  </span>
                  <button
                    className="ml-2 text-primary hover:text-primary-dark focus:outline-none rounded"
                    onClick={() => {
                      setEditedTitle(currentSession.title || '');
                      setIsEditingTitle(true);
                    }}
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                </>
              )
            ) : (
              <span className="text-xl font-bold text-muted-foreground">No conversation loaded</span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            <span className="text-sm text-muted-foreground">Online</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 md:space-y-6 bg-background custom-scrollbar">
          {memoizedMessages.length > 0 ? (
            <>
              {memoizedMessages}
              {renderStreamingAssistantBubble()}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <Card variant="elevated" glow className="p-12 text-center max-w-lg rounded-lg shadow-lg">
                <div className="text-6xl mb-6">🤖</div>
                <h3 className="text-2xl font-bold mb-4 text-foreground">Welcome to XOR RAG</h3>
                <p className="text-muted-foreground mb-6 leading-relaxed">
                  Start a conversation or upload documents to begin. Your AI assistant is ready to help 
                  with intelligent document-based questions and analysis.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button onClick={() => fileInputRef.current?.click()} variant="outline" className="group rounded-lg shadow-sm">
                    <Upload className="mr-2 h-4 w-4 group-hover:-translate-y-1 transition-transform duration-300" />
                    Upload Documents
                  </Button>
                  <Button onClick={createSession} variant="primary" className="group rounded-lg shadow-sm">
                    Start Chatting
                  </Button>
                </div>
              </Card>
            </div>
          )}
          
          {operationState.sending && streamingStatus !== 'streaming' && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-2xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <Card variant="elevated" className="p-4 rounded-lg shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-sm text-muted-foreground">Thinking...</span>
                  </div>
                </Card>
              </div>
            </div>
          )}
          
          {showScrollButton && (
            <button
              className="fixed bottom-24 right-6 z-40 bg-primary text-white rounded-full p-3 shadow-lg hover:bg-primary-dark transition"
              onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })}
            >
              <ArrowRight className="rotate-90 h-5 w-5" />
            </button>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-surface border-t border-border p-4 md:p-6 flex items-end gap-4 sticky bottom-0 z-20">
          <form onSubmit={handleSendMessage} className="flex items-end w-full gap-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc,.txt"
              multiple
              className="hidden"
            />
            <div className="flex-1 relative">
              <Card variant="elevated" className="overflow-hidden rounded-lg shadow-sm">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="w-full p-4 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none resize-none min-h-[60px] max-h-32 rounded-lg"
                  disabled={operationState.sending || streamingStatus === 'streaming'}
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
              </Card>
            </div>
            <Button
              type="submit"
              disabled={!inputValue.trim() || operationState.sending || streamingStatus === 'streaming'}
              className="p-4 group rounded-full shadow-md"
              size="lg"
            >
              <Send className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;