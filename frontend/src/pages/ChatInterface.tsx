import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, X, Settings, Trash2, Plus, Bot, User, Sparkles, Pencil } from 'lucide-react';
import { useChat } from '../contexts/ChatContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { useGlobalLoading } from '../App';

const ChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [documents, setDocuments] = useState<{filename: string, count: number, examples: any[]}[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [conversations, setConversations] = useState<{id: string, title: string, created_at: string}[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isDeletingDocument, setIsDeletingDocument] = useState<string | null>(null);
  const [isDeletingConversation, setIsDeletingConversation] = useState<string | null>(null);
  const [isResettingKB, setIsResettingKB] = useState(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [bannerType, setBannerType] = useState<'success' | 'error' | null>(null);
  const [vectorstoreHealthy, setVectorstoreHealthy] = useState<boolean | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState<string>("");
  // Add state for LLM streaming progress
  const [llmProgress, setLlmProgress] = useState<number | null>(null);
  const [llmStreaming, setLlmStreaming] = useState(false);
  const [embeddingStatus, setEmbeddingStatus] = useState<string | null>(null);
  // Add state for streaming assistant message
  const [streamingAssistantContent, setStreamingAssistantContent] = useState<string>("");
  
  const {
    sessions,
    currentSession,
    createSession,
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

  // Fetch documents from backend on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      setIsLoadingDocuments(true);
      setLoading(true);
      try {
        const response = await fetch('/api/documents');
        const data = await response.json();
        setDocuments(data.documents || []);
      } catch (err) {
        setDocuments([]);
        setBannerMessage('Failed to fetch documents.');
        setBannerType('error');
      }
      setIsLoadingDocuments(false);
      setLoading(false);
    };
    fetchDocuments();
  }, []);

  // Fetch conversations from backend on mount
  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoadingConversations(true);
      setLoading(true);
      try {
        const response = await fetch('/api/history/list');
        const data = await response.json();
        setConversations(data.conversations || []);
      } catch (err) {
        setConversations([]);
        setBannerMessage('Failed to fetch conversations.');
        setBannerType('error');
      }
      setIsLoadingConversations(false);
      setLoading(false);
    };
    fetchConversations();
  }, []);

  // Load a conversation from backend
  const handleLoadConversation = async (convId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/history/get/${convId}`);
      const data = await response.json();
      setCurrentSessionFromBackend(data.conversation);
    } catch (err) {
      setBannerMessage('Failed to load conversation.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Delete a conversation from backend
  const handleDeleteConversation = async (convId: string) => {
    if (!window.confirm('Are you sure you want to delete this conversation? This cannot be undone.')) return;
    setIsDeletingConversation(convId);
    setLoading(true);
    try {
      await fetch(`/api/history/delete/${convId}`, { method: 'DELETE' });
      setConversations((prev: {id: string, title: string, created_at: string}[]) => prev.filter((conv: {id: string}) => conv.id !== convId));
      setBannerMessage('Conversation deleted.');
      setBannerType('success');
    } catch (err) {
      setBannerMessage('Failed to delete conversation.');
      setBannerType('error');
    }
    setIsDeletingConversation(null);
    setLoading(false);
  };

  // Export a conversation as JSON
  const handleExportConversation = async (convId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/history/export/${convId}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${convId}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setBannerMessage('Failed to export conversation.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Helper to refresh document list from backend
  const refreshDocuments = async () => {
    setIsLoadingDocuments(true);
    setLoading(true);
    try {
      const response = await fetch('/api/documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      setDocuments([]);
      setBannerMessage('Failed to fetch documents.');
      setBannerType('error');
    }
    setIsLoadingDocuments(false);
    setLoading(false);
  };

  // Delete document from backend
  const handleDeleteDocument = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This cannot be undone.`)) return;
    setIsDeletingDocument(filename);
    setLoading(true);
    try {
      await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      setBannerMessage(`Document "${filename}" deleted.`);
      setBannerType('success');
      await refreshDocuments();
    } catch (err) {
      setBannerMessage(`Failed to delete document "${filename}".`);
      setBannerType('error');
    }
    setIsDeletingDocument(null);
    setLoading(false);
  };

  // Admin/Status actions
  const handleResetKB = async () => {
    if (!window.confirm('Are you sure you want to reset the knowledge base? This will remove all documents and cannot be undone.')) return;
    setIsResettingKB(true);
    setLoading(true);
    setStatusMessage('Resetting knowledge base...');
    try {
      const response = await fetch('/api/reset_kb', { method: 'POST' });
      if (!response.ok) throw new Error('Reset failed');
      const data = await response.json();
      setStatusMessage(data.status || 'Knowledge base reset.');
      setBannerMessage('Knowledge base reset.');
      setBannerType('success');
      await refreshDocuments();
    } catch (err) {
      setStatusMessage('Failed to reset knowledge base.');
      setBannerMessage('Failed to reset knowledge base.');
      setBannerType('error');
    }
    setIsResettingKB(false);
    setLoading(false);
  };

  const handleHealthCheck = async () => {
    setStatusMessage('Checking backend health...');
    setLoading(true);
    try {
      const response = await fetch('/api/health');
      if (!response.ok) throw new Error('Health check failed');
      const data = await response.json();
      setStatusMessage(data.status === 'ok' ? 'Backend healthy.' : 'Backend not healthy.');
    } catch (err) {
      setStatusMessage('Backend health check failed.');
      setBannerMessage('Backend health check failed.');
      setBannerType('error');
    }
    setLoading(false);
  };

  const handleTestVectorstore = async () => {
    setStatusMessage('Testing vector store...');
    setLoading(true);
    try {
      const response = await fetch('/api/test_vectorstore');
      if (!response.ok) throw new Error('Vectorstore test failed');
      const data = await response.json();
      setStatusMessage(data.message || data.status);
    } catch (err) {
      setStatusMessage('Vector store test failed.');
      setBannerMessage('Vector store test failed.');
      setBannerType('error');
    }
    setLoading(false);
  };

  // Check vectorstore health on mount and periodically
  useEffect(() => {
    const checkVectorstore = async () => {
      try {
        const response = await fetch('/api/test_vectorstore');
        const data = await response.json();
        setVectorstoreHealthy(data.status === 'ok');
      } catch (err) {
        setVectorstoreHealthy(false);
      }
    };
    checkVectorstore();
    const interval = setInterval(checkVectorstore, 30000); // every 30s
    return () => clearInterval(interval);
  }, []);

  // --- Streaming Assistant Message Bubble Helper ---
  // Returns a message bubble for the currently streaming assistant message
  const renderStreamingAssistantBubble = () => {
    if (!llmStreaming || !streamingAssistantContent) return null;
    return (
      <div className="flex justify-start">
        <div className="flex items-start space-x-3 max-w-2xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <Card variant="elevated" className="p-4">
            <p className="text-sm leading-relaxed whitespace-pre-line">
              {streamingAssistantContent}
              <span className="ml-1 animate-blink">|</span>
            </p>
            <div className="text-xs mt-2 text-muted-foreground">
              Streaming...
            </div>
          </Card>
        </div>
      </div>
    );
  };

  // --- Fix: Always scroll to latest message, including during streaming ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, streamingAssistantContent, llmStreaming]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isSending) return;

    if (!currentSession) {
      await createSession();
      await refreshConversations();
    }

    const userMessage = inputValue.trim();
    setIsSending(true);
    setLoading(true);
    setLlmStreaming(true);
    setLlmProgress(0);
    setStreamingAssistantContent(""); // Reset streaming content

    // Add user message
    addMessage(userMessage, 'user');
    // Add a placeholder for the assistant's streaming message
    addMessage('', 'assistant');
    setInputValue(""); // Clear input for better UX

    try {
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          question: userMessage,
          n_results: '3',
          expand: '2',
          filename: '',
          conversation_history: JSON.stringify(currentSession?.messages || [])
        })
      });

      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      let decoder = new TextDecoder();
      let done = false;
      let receivedLength = 0;
      let totalLength = 0;
      if (response.headers.has('content-length')) {
        totalLength = parseInt(response.headers.get('content-length') || '0', 10);
      }
      let streamedContent = "";
      let buffer = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          receivedLength += value.length;
          if (totalLength > 0) {
            setLlmProgress(Math.round((receivedLength / totalLength) * 100));
          } else {
            setLlmProgress(null); // Indeterminate
          }
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          let lines = buffer.split('\n');
          buffer = lines.pop() || ""; // Save incomplete line for next chunk

          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                if (data.answer !== undefined) {
                  streamedContent += data.answer;
                  setStreamingAssistantContent(streamedContent);
                  console.log("Streaming content:", streamedContent);
                }
              } catch (err) {
                console.error("JSON parse error:", err, "Line:", line);
              }
            }
          }
        }
      }
      // Handle any remaining buffered line
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          if (data.answer !== undefined) {
            streamedContent += data.answer;
            setStreamingAssistantContent(streamedContent);
            console.log("Streaming content (final buffer):", streamedContent);
          }
        } catch (err) {
          console.error("JSON parse error (final buffer):", err, "Buffer:", buffer);
        }
      }

      setLlmProgress(100);
      setTimeout(() => setLlmProgress(null), 500);
      updateStreamingMessage(streamedContent);
    } catch (err) {
      addMessage('Error contacting backend.', 'assistant');
      setBannerMessage('Error contacting backend.');
      setBannerType('error');
      console.error("Streaming error:", err);
    }
    setIsSending(false);
    setLoading(false);
    setLlmStreaming(false);
    setStreamingAssistantContent("");
    setTimeout(() => refreshConversations(), 500);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    setIsUploading(true);
    setLoading(true);
    setUploadProgress(0);
    setEmbeddingStatus('Creating embeddings and chunks...');

    for (const [idx, file] of Array.from(files).entries()) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        setUploadProgress(Math.round(((idx + 1) / files.length) * 100));
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();

        if (data.status?.includes('uploaded and embedded')) {
          setBannerMessage(`Embeddings created for "${file.name}" (${data.num_chunks} chunks).`);
          setBannerType('success');
          setEmbeddingStatus(`Embeddings created for "${file.name}" (${data.num_chunks} chunks).`);
        } else if (data.status?.includes('already exist')) {
          setBannerMessage(`Embeddings already exist for "${file.name}".`);
          setBannerType('success');
          setEmbeddingStatus(`Embeddings already exist for "${file.name}".`);
        } else {
          setBannerMessage(`Embedding failed for "${file.name}": ${data.status}`);
          setBannerType('error');
          setEmbeddingStatus(`Embedding failed for "${file.name}": ${data.status}`);
        }
        addDocument(file.name);
      } catch (err) {
        setBannerMessage(`Failed to upload document "${file.name}".`);
        setBannerType('error');
        setEmbeddingStatus(`Failed to upload document "${file.name}".`);
      }
    }
    setIsUploading(false);
    setLoading(false);
    setUploadProgress(null);
    setTimeout(() => setEmbeddingStatus(null), 2000);
    await refreshDocuments();
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Add this function to handle title save
  const handleSaveTitle = async () => {
    if (!currentSession) return;
    const updatedTitle = editedTitle.trim() || 'Untitled Conversation';
    // Update in frontend state using renameSession
    renameSession(currentSession.id, updatedTitle);
    setIsEditingTitle(false);
    // Persist to backend
    try {
      await fetch('/api/history/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentSession, title: updatedTitle })
      });
      setBannerMessage('Conversation renamed.');
      setBannerType('success');
      // Refresh conversations list and update sidebar
      setConversations((prev) => prev.map(conv => conv.id === currentSession.id ? { ...conv, title: updatedTitle } : conv));
      // After renaming, refresh conversations
      await refreshConversations();
    } catch (err) {
      setBannerMessage('Failed to rename conversation.');
      setBannerType('error');
    }
  };

  // Helper to refresh conversation list from backend
  const refreshConversations = async () => {
    setIsLoadingConversations(true);
    setLoading(true);
    try {
      const response = await fetch('/api/history/list');
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (err) {
      setConversations([]);
      setBannerMessage('Failed to fetch conversations.');
      setBannerType('error');
    }
    setIsLoadingConversations(false);
    setLoading(false);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Embedding Status Toast/Banner */}
      {embeddingStatus && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-primary text-white px-6 py-2 rounded shadow-lg text-sm animate-fade-in">
          {embeddingStatus}
        </div>
      )}
      {/* Sidebar */}
      <div className="w-80 bg-surface border-r border-border flex flex-col">
        {/* Banner for error/success */}
        {bannerMessage && (
          <div className={`p-2 text-xs text-center ${bannerType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{bannerMessage}</div>
        )}
        {/* New Chat Button */}
        <div className="p-4 border-b border-border">
          <Button 
            onClick={createSession}
            className="w-full group"
            variant="outline"
          >
            <Plus className="mr-2 h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
            New Conversation
          </Button>
        </div>

        {/* Chat Sessions (History) */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 flex items-center">
            <Sparkles className="mr-2 h-4 w-4" />
            Recent Conversations
          </h3>
          {isLoadingConversations ? (
            <div className="text-xs text-muted-foreground">Loading conversations...</div>
          ) : conversations.length > 0 ? (
            conversations.map((conv: {id: string, title: string, created_at: string}) => (
            <Card
                key={conv.id}
              hover
                className={`p-4 cursor-pointer transition-all duration-300 ${currentSession?.id === conv.id ? 'border-2 border-primary' : ''}`}
                onClick={() => handleLoadConversation(conv.id)}
            >
                <div className="flex items-center justify-between">
                  <div>
              <div className="text-sm font-medium text-foreground truncate mb-1">
                      {conv.title}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(conv.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <Button
                      onClick={e => { e.stopPropagation(); handleExportConversation(conv.id); }}
                      variant="ghost"
                      size="sm"
                      className="p-1"
                      disabled={isDeletingConversation === conv.id}
                    >
                      <FileText className="h-4 w-4 text-primary" />
                    </Button>
                    <Button
                      onClick={e => { e.stopPropagation(); handleDeleteConversation(conv.id); }}
                      variant="ghost"
                      size="sm"
                      className="p-1"
                      disabled={isDeletingConversation === conv.id}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
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
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="ghost"
              size="sm"
              className="p-2"
            >
              <Upload className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {isLoadingDocuments ? (
              <div className="text-xs text-muted-foreground">Loading documents...</div>
            ) : documents.length > 0 ? (
              documents.map((doc: {filename: string, count: number, examples: any[]}, index: number) => (
                <Card key={index} className="p-3 group flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="text-xs text-foreground truncate">{doc.filename}</span>
                  </div>
                  <Button
                    onClick={() => handleDeleteDocument(doc.filename)}
                    variant="ghost"
                    size="sm"
                    className="p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    disabled={isDeletingDocument === doc.filename}
                  >
                    <X className="h-3 w-3 text-muted-foreground hover:text-red-500" />
                  </Button>
              </Card>
              ))
            ) : (
            <Card className="p-6 text-center">
              <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">No documents uploaded</p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="ghost"
                size="sm"
                className="mt-2 text-xs"
              >
                Upload files
              </Button>
            </Card>
          )}
          </div>
        </div>

        {/* Settings & Admin */}
        <div className="p-4 border-t border-border">
          <div className="flex space-x-2 mb-2">
            <Button
              variant="outline"
              size="sm"
              onClick={clearHistory}
              className="flex-1 group"
              disabled={isResettingKB}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleHealthCheck}
              disabled={isResettingKB}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Health
            </Button>
          </div>
          <div className="flex space-x-2 mb-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleResetKB}
              disabled={isResettingKB}
            >
              <X className="mr-2 h-4 w-4" />
              Reset KB
            </Button>
          </div>
          {/* Vectorstore health status */}
          <div className="mt-2 text-xs flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${vectorstoreHealthy === null ? 'bg-gray-300' : vectorstoreHealthy ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span>
              Vectorstore: {vectorstoreHealthy === null ? 'Checking...' : vectorstoreHealthy ? 'Healthy' : 'Unavailable'}
            </span>
          </div>
          {statusMessage && (
            <div className="text-xs text-muted-foreground mt-2">{statusMessage}</div>
          )}
        </div>
        {/* Persistent error banner if vectorstore is down */}
        {vectorstoreHealthy === false && (
          <div className="p-2 text-xs text-center bg-red-100 text-red-800 font-semibold">
            Vectorstore is unavailable. Some features may not work.
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-surface border-b border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-foreground flex items-center">
                <Bot className="mr-3 h-6 w-6 text-primary" />
                {isEditingTitle ? (
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
                    {currentSession?.title || 'XOR RAG Assistant'}
                    <button
                      className="ml-2 text-primary hover:text-primary-dark"
                      onClick={() => {
                        setEditedTitle(currentSession?.title || '');
                        setIsEditingTitle(true);
                      }}
                      title="Rename Conversation"
                    >
                      <Pencil className="w-4 h-4 inline" />
                    </button>
                  </>
                )}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {uploadedDocuments.length > 0 
                  ? `${uploadedDocuments.length} document${uploadedDocuments.length > 1 ? 's' : ''} loaded • Ready to answer questions`
                  : 'No documents loaded • Upload files to get started'
                }
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {isUploading && (
                <div className="flex items-center space-x-2 text-sm text-primary">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                  <span>Processing...</span>
                </div>
              )}
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <span className="text-sm text-muted-foreground">Online</span>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!currentSession || currentSession.messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <Card variant="elevated" glow className="p-12 text-center max-w-lg">
                <div className="text-6xl mb-6">🤖</div>
                <h3 className="text-2xl font-bold mb-4 text-foreground">
                  Welcome to XOR RAG
                </h3>
                <p className="text-muted-foreground mb-6 leading-relaxed">
                  Start a conversation or upload documents to begin. Your AI assistant is ready to help 
                  with intelligent document-based questions and analysis.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button 
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline"
                    className="group"
                  >
                    <Upload className="mr-2 h-4 w-4 group-hover:-translate-y-1 transition-transform duration-300" />
                    Upload Documents
                  </Button>
                  <Button 
                    onClick={createSession}
                    variant="primary"
                  >
                    Start Chatting
                  </Button>
                </div>
              </Card>
            </div>
          ) : (
            <>
              {currentSession.messages.map((message, idx) => (
                <div
                  key={message.id || idx}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex items-start space-x-3 max-w-2xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
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
                    <Card
                      variant={message.role === 'user' ? 'default' : 'elevated'}
                      className={`p-4 ${
                        message.role === 'user'
                          ? 'bg-primary text-white border-primary/30'
                          : 'bg-surface-elevated'
                      }`}
                    >
                      <p className="text-sm leading-relaxed">
                        {message.content && message.content.trim() !== '' ? message.content : <span className="italic text-gray-400">[No content]</span>}
                      </p>
                      <div className={`text-xs mt-2 ${
                        message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </div>
                    </Card>
                  </div>
                </div>
              ))}
              {/* Streaming Assistant Bubble */}
              {renderStreamingAssistantBubble()}
            </>
          )}
          {isSending && !llmStreaming && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-2xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <Card variant="elevated" className="p-4">
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
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-surface border-t border-border p-6">
          <form onSubmit={handleSendMessage} className="flex items-end space-x-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc,.txt"
              multiple
              className="hidden"
            />
            
            <div className="flex-1 relative">
              <Card variant="elevated" className="overflow-hidden">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="w-full p-4 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none resize-none min-h-[60px] max-h-32"
                  disabled={isSending}
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
              disabled={!inputValue.trim() || isSending}
              className="p-4 group"
              size="lg"
            >
              <Send className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
          </form>
          
          <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <span>{inputValue.length}/2000</span>
          </div>
        </div>
      </div>
      {(isUploading || llmStreaming) && (
        <div className="fixed top-0 left-0 w-full z-50">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${isUploading ? uploadProgress || 0 : llmProgress || 0}%` }}
            ></div>
          </div>
          <div className="text-xs text-center mt-1 text-muted-foreground">
            {isUploading && embeddingStatus}
            {llmStreaming && 'Processing LLM response...'}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;