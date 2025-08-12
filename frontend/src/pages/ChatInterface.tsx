import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useChat } from '../contexts/ChatContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import DomainFilter from '../components/DomainFilter';
import SourceDisplay from '../components/SourceDisplay';
import ContextPreview from '../components/ContextPreview';
import MessageActions from '../components/MessageActions';
import AdvancedSearch from '../components/AdvancedSearch';
import ModelSelectionModal from '../components/ModelSelectionModal';
import ModelToast from '../components/ModelToast';
import ReactMarkdown from 'react-markdown';
import { 
  Send,
  Upload,
  Trash2,
  Plus,
  MessageSquare,
  FileText,
  Sparkles,
  X,
  ChevronDown,
  ChevronRight,
  Bot,
  User,
  Pencil,
  ArrowRight
} from 'lucide-react';
import { useGlobalLoading } from '../App';
import debounce from 'lodash.debounce';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../lib/logger';
import { detectContentType, shouldShowModelSelection, type DetectedContentType } from '../lib/contentDetection';

const CHAT_STATE_KEY = 'xor_rag_chat_state';
const CONVERSATIONS_KEY = 'xor_rag_conversations';

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
  const [renamingConvId, setRenamingConvId] = useState<string | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [fileProcessing] = useState(false);
  const [fileError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [/* currentSources */, setCurrentSources] = useState<any[]>([]);
  const [supportedFileTypes, setSupportedFileTypes] = useState<{[key: string]: string}>({});
  const [showFileTypeInfo, setShowFileTypeInfo] = useState(false);
  const [showContextPreview, setShowContextPreview] = useState(false);
  const [contextMetadata, setContextMetadata] = useState<any>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('xor-rag-sidebar-width');
    return saved ? parseInt(saved) : 320;
  });
  const [isResizing, setIsResizing] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [streamingState, setStreamingState] = useState({ status: 'idle', content: '' });
  
  // Model selection modal state
  const [showModelSelection, setShowModelSelection] = useState(false);
  const [detectedContentType, setDetectedContentType] = useState<DetectedContentType>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [modelSelectionLoading, setModelSelectionLoading] = useState(false);
  
  // Session-level model tracking
  const [sessionModel, setSessionModel] = useState<'local' | 'openai'>('local');
  const [showModelToast, setShowModelToast] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioUrlRef = useRef<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    sessions,
    setSessions,
    currentSession,
    createSession,
    // createSessionFromPrevious,
    selectSession,
    addMessage,
    clearHistory,
    // uploadedDocuments,
    addDocument,
    // removeDocument,
    setCurrentSessionFromBackend,
    beginStreamingMessage,
    appendStreamingContent,
    finalizeStreamingMessage,
    renameSession
  } = useChat();

  const { /* loading, */ setLoading } = useGlobalLoading();
  // Provide a stable setter for lastSessionId even if we don't read the value
  const setLastSessionId = useRef<(id: string | null) => void>();
  setLastSessionId.current = (_id: string | null) => {};

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

  const fetchSupportedFileTypes = async () => {
    try {
      const data = await apiCall('/api/supported-file-types');
      setSupportedFileTypes(data.supported_types || {});
    } catch (err) {
      console.error('Failed to fetch supported file types:', err);
    }
  };

  const fetchConversations = async () => {
    setOperationState(s => ({ ...s, loadingConversations: true }));
    try {
      const data = await apiCall('/api/history/list');
      setConversations(data.conversations || []);
    } catch (err) {
      showBanner('Failed to fetch conversations.', 'error');
    }
    setOperationState(s => ({ ...s, loadingConversations: false }));
  };

  const checkVectorstore = async () => {
    try {
      const data = await apiCall('/api/test_vectorstore');
      setVectorstoreHealthy(data.status === 'ok');
    } catch (err) {
      setVectorstoreHealthy(false);
    }
  };

  // const resetStreaming = () => {
  //   setStreamingState({ status: 'idle', content: '' });
  // };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || operationState.sending || streamingState.status === 'streaming') return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setOperationState(s => ({ ...s, sending: true }));

    // Ensure we have a current session - create one if needed
    if (!currentSession) {
      logger.info('No current session, creating new session');
      createSession();
      // Wait a bit for the session to be created and state to update
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Double-check if session was created
      if (!currentSession) {
        logger.error('Failed to create session after timeout');
        setOperationState(s => ({ ...s, sending: false }));
        return;
      }
    }

    // Now we should have a valid session, add the user message
    logger.info('Adding user message', { message: userMessage, sessionId: currentSession?.id });
    addMessage(userMessage, 'user');
    
    // Wait a moment for the message to be added
    await new Promise(resolve => setTimeout(resolve, 50));
    
    logger.info('User message added', { sessionId: currentSession?.id, messageCount: currentSession?.messages?.length });

    // Check settings for streaming toggle and online model
    let streamingEnabled = true;
    let useOnlineModel = false;
    let onlineProvider = 'openai';
    try {
      const settings = JSON.parse(localStorage.getItem('xor-rag-settings') || '{}');
      if (typeof settings.streamingEnabled === 'boolean') streamingEnabled = settings.streamingEnabled;
      if (typeof settings.useOnlineModel === 'boolean') useOnlineModel = settings.useOnlineModel;
      if (typeof settings.onlineProvider === 'string') onlineProvider = settings.onlineProvider;
    } catch {}
    
    if (streamingEnabled) {
      setStreamingState({ status: 'streaming', content: '' });
      // Create placeholder assistant message that will be filled during streaming
      logger.info('Starting streaming response', { sessionId: currentSession?.id });
      beginStreamingMessage();
      
      // Remove the fallback that creates empty messages
      // setTimeout(() => {
      //   if (!currentSession?.messages?.some(m => m.role === 'assistant' && m.isStreaming)) {
      //     logger.warn('Fallback: creating streaming message manually', { sessionId: currentSession?.id });
      //     addMessage('', 'assistant');
      //   }
      // }, 100);

      try {
        const formData = new FormData();
        formData.append('question', userMessage);
        formData.append('n_results', '3');
        formData.append('expand', '2');
        formData.append('conversation_history', JSON.stringify(currentSession?.messages?.slice(-10) || []));
        formData.append('session_id', currentSession?.id || '');
        
        // Add session model and attached file
        if (sessionModel === 'openai') {
          formData.append('online_model', 'openai');
        }
        
        if (attachedFile) {
          formData.append('file', attachedFile);
        }
        
        // Add LLM settings
        try {
          const settings = JSON.parse(localStorage.getItem('xor-rag-settings') || '{}');
          if (settings.modelName) formData.append('model', settings.modelName);
          if (settings.temperature !== undefined) formData.append('temperature', settings.temperature.toString());
          if (settings.maxTokens) formData.append('max_tokens', settings.maxTokens.toString());
          if (useOnlineModel && onlineProvider) formData.append('online_model', onlineProvider);
        } catch (e) {
          logger.error('Failed to parse settings for API call:', e);
        }

        const response = await fetch('/api/query/stream', {
          method: 'POST',
          body: formData,
          headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body reader available');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                if (data.status === 'streaming' && data.answer) {
                  appendStreamingContent(data.answer);
                } else if (data.status === 'success') {
                  // Finalize the streaming message with the complete response
                  // The content is already accumulated in the streaming message during streaming
                  // data.answer is empty in the final response, so we don't use it
                  finalizeStreamingMessage('', {
                    sources: data.sources || [],
                    contextMetadata: data.context_metadata || {}
                  });
                  
                  // Wait a moment for the state to update before saving
                  await new Promise(resolve => setTimeout(resolve, 100));
                  
                  // Save conversation state
                  if (currentSession) {
                    // ChatContext already handles localStorage saving, so we only need backend save
                    // Also save to backend
                    try {
                      await apiCall('/api/history/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          id: currentSession.id,
                          title: currentSession.title,
                          messages: currentSession.messages,
                          created_at: currentSession.createdAt.toISOString(),
                          uploads: currentSession.documents.map(filename => ({ filename }))
                        })
                      });
                    } catch (err) {
                      console.warn('Failed to save conversation to backend:', err);
                    }
                    
                    logger.info('Streaming response finalized', { sessionId: currentSession.id });
                  }
                }
              } catch (e) {
                logger.error('Failed to parse streaming response:', e);
              }
            }
          }
        }
      } catch (error) {
        logger.error('Streaming request failed:', error);
        finalizeStreamingMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, {
          sources: [],
          contextMetadata: {}
        });
      } finally {
        setStreamingState({ status: 'idle', content: '' });
        setOperationState(s => ({ ...s, sending: false }));
      }
    } else {
      // Non-streaming request
      try {
        const formData = new FormData();
        formData.append('question', userMessage);
        formData.append('n_results', '3');
        formData.append('expand', '2');
        formData.append('conversation_history', JSON.stringify(currentSession?.messages?.slice(-10) || []));
        formData.append('session_id', currentSession?.id || '');
        
        // Add session model and attached file
        if (sessionModel === 'openai') {
          formData.append('online_model', 'openai');
        }
        
        if (attachedFile) {
          formData.append('file', attachedFile);
        }
        
        // Add LLM settings
        try {
          const settings = JSON.parse(localStorage.getItem('xor-rag-settings') || '{}');
          if (settings.modelName) formData.append('model', settings.modelName);
          if (settings.temperature !== undefined) formData.append('temperature', settings.temperature.toString());
          if (settings.maxTokens) formData.append('max_tokens', settings.maxTokens.toString());
          if (useOnlineModel && onlineProvider) formData.append('online_model', onlineProvider);
        } catch (e) {
          logger.error('Failed to parse settings for API call:', e);
        }

        const response = await fetch('/api/query', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.status === 'success' || data.answer) {
          addMessage(data.answer, 'assistant', {
            sources: data.sources || [],
            contextMetadata: data.context_metadata || {}
          });
          
          // Wait a moment for the state to update before saving
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // Save conversation state
          if (currentSession) {
            // ChatContext already handles localStorage saving, so we only need backend save
            // Also save to backend
            try {
              await apiCall('/api/history/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  id: currentSession.id,
                  title: currentSession.title,
                  messages: currentSession.messages,
                  created_at: currentSession.createdAt.toISOString(),
                  uploads: currentSession.documents.map(filename => ({ filename }))
                })
              });
            } catch (err) {
              console.warn('Failed to save conversation to backend:', err);
            }
            
            logger.info('Non-streaming response received', { sessionId: currentSession.id });
          }
        } else {
          throw new Error(data.error || 'Unknown error');
        }
      } catch (error) {
        logger.error('Non-streaming request failed:', error);
        addMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'assistant', {
          sources: [],
          contextMetadata: {}
        });
      } finally {
        setOperationState(s => ({ ...s, sending: false }));
      }
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, _documentType: string = 'default') => {
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
      
      // Get the selected document type from localStorage
      const selectedDocType = localStorage.getItem('xor-rag-document-type') || 'default';
      formData.append('document_type', selectedDocType);

      try {
        const data = await apiCall('/api/upload', {
          method: 'POST',
          body: formData
        });

        if (data.status?.includes('uploaded and embedded')) {
          const docType = data.document_type === 'master_document' ? 'Master Document' : 'Regular Document';
          showBanner(`${docType} embeddings created for "${file.name}" (${data.num_chunks} chunks).`, 'success');
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



  const handleModelSelection = async (selectedModel: 'local' | 'openai') => {
    if (!pendingFile) return;
    
    setModelSelectionLoading(true);
    setShowModelSelection(false);
    
    try {
      // Set the session model for this chat
      setSessionModel(selectedModel);
      
      // Set the attached file
      setAttachedFile(pendingFile);
      
      // Show toast notification
      setShowModelToast(true);
      setTimeout(() => setShowModelToast(false), 5000); // Hide after 5 seconds
      
      // Show banner with model selection
      const modelName = selectedModel === 'openai' ? 'OpenAI' : 'Local';
      showBanner(`Using ${modelName} model for this chat session.`, 'success');
      
    } finally {
      setModelSelectionLoading(false);
      setPendingFile(null);
      setDetectedContentType(null);
    }
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

  const handleSaveTitle = async (convId?: string) => {
    const convToRename = convId ? sessions.find(s => s.id === convId) : currentSession;
    if (!convToRename) return;
    const updatedTitle = editedTitle.trim() || 'Untitled Conversation';
    renameSession(convToRename.id, updatedTitle);
    setIsEditingTitle(false);
    setRenamingConvId(null);
    try {
      await apiCall('/api/history/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...convToRename,
          title: updatedTitle,
          created_at: convToRename.createdAt instanceof Date ? convToRename.createdAt.toISOString() : (convToRename as any).created_at || convToRename.createdAt,
          uploads: (convToRename.documents || []).map(filename => ({ filename })),
        })
      });
      showBanner('Conversation renamed.', 'success');
      // Update local conversations list after successful API call
      setConversations(prev => prev.map(conv => conv.id === convToRename.id ? { ...conv, title: updatedTitle } : conv));
      // Also update localStorage
      const updatedConvs = conversations.map(conv => conv.id === convToRename.id ? { ...conv, title: updatedTitle } : conv);
      localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updatedConvs));
      await fetchConversations(); // Sync with backend if online
    } catch (err) {
      showBanner('Failed to rename conversation.', 'error');
    }
  };

  const handleResetKB = async () => {
    if (!window.confirm('Are you sure you want to reset the knowledge base? This will delete all uploaded documents.')) return;
    setLoading(true);
    setStatusMessage('Resetting knowledge base...');
    try {
      const data = await apiCall('/api/reset_kb', { method: 'POST' });
      
      if (data.status && data.status.includes('successfully')) {
        setStatusMessage('Knowledge base reset successfully.');
        showBanner('Knowledge base reset successfully.', 'success');
        // Clear local document state
        setDocuments([]);
        // Refresh documents list
        await fetchDocuments();
      } else {
        setStatusMessage('Failed to reset knowledge base.');
        showBanner('Failed to reset knowledge base.', 'error');
      }
    } catch (err) {
      console.error('Reset KB error:', err);
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

  // Add delete handler
  const handleDeleteConversation = async (convId: string) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    // Remove from local state and localStorage first
    setConversations(prev => prev.filter(conv => conv.id !== convId));
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations.filter(conv => conv.id !== convId)));
    // Remove from sessions and currentSession
    if (currentSession && currentSession.id === convId) {
      // If deleting the current session, select another or clear
      const remaining = sessions.filter(s => s.id !== convId);
      if (remaining.length > 0) {
        selectSession(remaining[0].id);
      } else {
        clearHistory();
      }
    }
    // Remove from backend if needed (optional, depending on your API)
    try {
      await apiCall('/api/history/delete/' + convId, { method: 'DELETE' });
      showBanner('Conversation deleted.', 'success');
      await fetchConversations(); // Sync with backend if online
    } catch (err) {
      showBanner('Failed to delete conversation.', 'error');
    }
  };

  // Scroll functionality
  const scrollToBottom = useMemo(() => debounce(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, 100), []);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, streamingState.content, streamingState.status, scrollToBottom]);

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
  }, [currentSession?.messages, streamingState.content]);

  // Initialize data
  useEffect(() => {
    // On page load, always restore from localStorage first
    const savedState = localStorage.getItem(CHAT_STATE_KEY);
    let localCurrentSessionId = null;
    let localCurrentSession = null;
    let localConversations = [];
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        if (parsed.sessions) setSessions(parsed.sessions);
        if (parsed.currentSession) {
          setCurrentSessionFromBackend(parsed.currentSession);
          localCurrentSessionId = parsed.currentSession.id;
          localCurrentSession = parsed.currentSession;
          setLastSessionId.current && setLastSessionId.current(parsed.currentSession.id);
        }
        if (parsed.conversations) {
          setConversations(parsed.conversations);
          localConversations = parsed.conversations;
        }
      } catch {}
    }
    // Fetch conversations from backend, but always fallback to local if missing
    (async () => {
      let backendConvs = [];
      // let backendCurrentSession = null;
      try {
        const data = await apiCall('/api/history/list');
        backendConvs = data.conversations || [];
        // If current session is not in backend conversations, add it
        if (localCurrentSession && !backendConvs.some((c: any) => c.id === localCurrentSession.id)) {
          backendConvs = [
            { id: localCurrentSession.id, title: localCurrentSession.title, created_at: String(localCurrentSession.created_at) },
            ...backendConvs
          ];
        }
        setConversations(backendConvs);
        // Try to fetch the current session from backend
        if (localCurrentSessionId) {
          try {
            const data = await apiCall(`/api/history/get/${localCurrentSessionId}`);
            if (data.conversation) {
              // backendCurrentSession = data.conversation;
              setCurrentSessionFromBackend(data.conversation);
              // track last session id if needed
              setLastSessionId.current && setLastSessionId.current(data.conversation.id);
            } else if (localCurrentSession) {
              setCurrentSessionFromBackend(localCurrentSession);
              setLastSessionId.current && setLastSessionId.current(localCurrentSession.id);
            }
          } catch {
            if (localCurrentSession) {
              setCurrentSessionFromBackend(localCurrentSession);
              setLastSessionId.current && setLastSessionId.current(localCurrentSession.id);
            }
          }
        } else if (backendConvs.length > 0) {
          // If no current session, set the first conversation as current
          const firstConv = backendConvs[0];
          if (firstConv) {
            try {
              const data = await apiCall(`/api/history/get/${firstConv.id}`);
              if (data.conversation) {
                setCurrentSessionFromBackend(data.conversation);
                setLastSessionId.current && setLastSessionId.current(data.conversation.id);
              } else {
                setCurrentSessionFromBackend(firstConv);
                setLastSessionId.current && setLastSessionId.current(firstConv.id);
              }
            } catch {
              setCurrentSessionFromBackend(firstConv);
              setLastSessionId.current && setLastSessionId.current(firstConv.id);
            }
          }
        }
      } catch {
        // If backend fetch fails, always use the local copy
        if (localCurrentSession) {
          setCurrentSessionFromBackend(localCurrentSession);
          setLastSessionId.current && setLastSessionId.current(localCurrentSession.id);
        }
        if (localConversations.length > 0) {
          setConversations(localConversations);
        }
      }
    })();
    fetchDocuments();
    checkVectorstore();
    const interval = setInterval(checkVectorstore, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchDocuments();
    fetchConversations();
    checkVectorstore();
    fetchSupportedFileTypes();
  }, []);

  useEffect(() => {
    if (currentSession) {
      setCurrentSources(currentSession.sources || []);
    }
  }, [currentSession]);

  // Always persist conversations and current session to localStorage after any change
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
    // Ensure current session is in conversations
    let safeConversations = [...conversations];
    if (safeCurrentSession && !safeConversations.some((c: any) => c.id === safeCurrentSession.id)) {
      safeConversations = [
        { id: safeCurrentSession.id, title: safeCurrentSession.title, created_at: (safeCurrentSession.createdAt instanceof Date ? safeCurrentSession.createdAt.toISOString() : String(safeCurrentSession.createdAt)) },
        ...safeConversations
      ];
    }
    localStorage.setItem(CHAT_STATE_KEY, JSON.stringify({ 
      sessions: safeSessions, 
      currentSession: safeCurrentSession, 
      conversations: safeConversations
    }));
    // if (safeCurrentSession) track last session id if needed
    // setLastSessionId.current && setLastSessionId.current(safeCurrentSession.id);
  }, [sessions, currentSession, conversations]);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(CONVERSATIONS_KEY);
    if (saved) {
      try {
        setConversations(JSON.parse(saved));
      } catch {}
    }
  }, []);
  // On every change, persist the full conversations list to localStorage for offline mode
  useEffect(() => {
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
  }, [conversations]);

  // After creating, renaming, or deleting a conversation, always call fetchConversations() to refresh the sidebar
  // This useEffect is now redundant as persistence handles it.
  // useEffect(() => {
  //   fetchConversations();
  // }, [currentSession]);

  // Streaming bubble is no longer needed; content streams directly into the assistant message.

  // Message action handlers - moved before memoizedMessages
  const handleEditMessage = (messageId: string, newContent: string) => {
    if (currentSession) {
      // const updatedMessages = currentSession.messages.map(msg => 
      //   msg.id === messageId ? { ...msg, content: newContent } : msg
      // );
      
      // Update the session with edited message
      // const updatedSession = { ...currentSession, messages: updatedMessages };
      // This would typically update the backend and local storage
      console.log('Message edited:', messageId, newContent);
    }
    setEditingMessageId(null);
  };

  const handleResendMessage = (messageId: string) => {
    if (currentSession) {
      const message = currentSession.messages.find(msg => msg.id === messageId);
      if (message && message.role === 'user') {
        setInputValue(message.content);
        // Trigger send with the message content
        handleSendMessage(new Event('submit') as any);
      }
    }
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content).then(() => {
      showBanner('Message copied to clipboard', 'success');
    }).catch(() => {
      showBanner('Failed to copy message', 'error');
    });
  };

  const handleContextPreviewToggle = () => {
    setShowContextPreview(!showContextPreview);
  };

  // Memoized messages
  const memoizedMessages = useMemo(() => {
    if (currentSession?.messages) {
      currentSession.messages.forEach((msg, idx) => {
      });
    }
    
    return currentSession?.messages?.map((message, idx) => (
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
          <Card variant={message.role === 'user' ? 'default' : 'elevated'} className={`p-4 rounded-lg shadow-sm w-full group ${
            message.role === 'user' ? 'bg-primary text-white border-primary/30' : 'bg-surface-elevated'
          }`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <ReactMarkdown components={{p: ({node, ...props}) => <p className="text-sm leading-relaxed whitespace-pre-line" {...props} />}}>
                  {message.content || ''}
                </ReactMarkdown>
                <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
                  {message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                </div>
                {message.role === 'assistant' && message.sources && (
                  <SourceDisplay sources={message.sources} className="mt-3" />
                )}
              </div>
              <MessageActions
                messageId={message.id || `msg-${idx}`}
                content={message.content || ''}
                role={message.role}
                onEdit={handleEditMessage}
                onResend={handleResendMessage}
                onCopy={handleCopyMessage}
                isEditing={editingMessageId === (message.id || `msg-${idx}`)}
                onCancelEdit={() => setEditingMessageId(null)}
              />
            </div>
            
            {/* Context Preview for Assistant Messages */}
            {message.role === 'assistant' && message.contextMetadata && (
              <ContextPreview
                contextMetadata={message.contextMetadata}
                sources={message.sources || []}
                isVisible={showContextPreview}
                onToggleVisibility={handleContextPreviewToggle}
              />
            )}
          </Card>
        </div>
      </div>
    )) || [];
  }, [currentSession?.messages, showContextPreview, editingMessageId]);

  // Restore handleSelectSession and handleCreateNewConversation with correct logic
  const handleSelectSession = async (convId: string) => {
    selectSession(convId);
    try {
      const data = await apiCall(`/api/history/get/${convId}`);
      if (data.conversation) {
        setCurrentSessionFromBackend(data.conversation);
      }
    } catch {}
    
    // Reset session model for different conversation
    setSessionModel('local');
    setShowModelToast(false);
  };

  const handleCreateNewConversation = async () => {
    // Create a new conversation and persist to backend
    const now = new Date().toISOString();
    const newConv = {
      id: uuidv4(),
      title: 'New Conversation',
      created_at: now,
      messages: [],
      uploads: []
    };
    await apiCall('/api/history/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...newConv,
        created_at: newConv.created_at || (newConv as any).createdAt,
        uploads: (newConv.uploads || []).map(filename => ({ filename })),
      })
    });
    // Add to conversations and set as current
    setConversations((prev: any[]) => [
      { id: newConv.id, title: newConv.title, created_at: newConv.created_at },
      ...prev
    ]);
    await handleSelectSession(newConv.id);
    
    // Reset session model for new conversation
    setSessionModel('local');
    setShowModelToast(false);
  };

  // New handler for inline file attach
  const handleInlineFileAttach = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      
      // Detect content type for chat attachments
      const detectionResult = await detectContentType(file);
      
      // Check if we should show model selection modal
      if (shouldShowModelSelection(detectionResult)) {
        setPendingFile(file);
        setDetectedContentType(detectionResult.type);
        setShowModelSelection(true);
        return; // Wait for user selection
      } else {
        // Process normally with local model
        setAttachedFile(file);
      }
    }
  };

  // Voice recording logic
  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setIsTranscribing(true);
        
        try {
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.wav');
          
          const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
          });
          
          if (response.ok) {
            const data = await response.json();
            setInputValue(data.text || '');
          } else {
            showBanner('Transcription failed.', 'error');
          }
        } catch (error) {
          showBanner('Transcription failed.', 'error');
        } finally {
          setIsTranscribing(false);
        }
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        if (audioUrlRef.current) {
          URL.revokeObjectURL(audioUrlRef.current);
          audioUrlRef.current = null;
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      showBanner('Failed to start recording.', 'error');
    }
  };

  // Sidebar resize handlers
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handleResizeMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    const newWidth = e.clientX;
    const minWidth = 240; // Minimum sidebar width
    const maxWidth = window.innerWidth * 0.6; // Maximum 60% of screen width
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
      localStorage.setItem('xor-rag-sidebar-width', newWidth.toString());
    }
  };

  const toggleSidebar = () => {
    if (isSidebarCollapsed) {
      setIsSidebarCollapsed(false);
      setSidebarWidth(320); // Restore to default width
      localStorage.setItem('xor-rag-sidebar-width', '320');
    } else {
      setIsSidebarCollapsed(true);
      setSidebarWidth(60); // Collapsed width
      localStorage.setItem('xor-rag-sidebar-width', '60');
    }
  };

  const handleResizeEnd = () => {
    setIsResizing(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  };

  // Add and remove event listeners
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  }, [isResizing]);

  return (
    <div className="flex h-screen w-screen bg-background">
      {/* Sidebar */}
      <div 
        className="bg-surface border-r border-border flex flex-col h-screen z-40 fixed left-0 top-0 overflow-y-auto max-h-screen shadow-lg transition-all duration-200"
        style={{ width: `${sidebarWidth}px` }}
      >
        {/* Sidebar Toggle Button */}
        <div className="absolute top-4 right-4 z-50">
          <Button
            onClick={toggleSidebar}
            variant="ghost"
            size="sm"
            className="p-2 rounded-full bg-surface/80 backdrop-blur-sm border border-border hover:bg-surface-elevated"
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>

        {bannerMessage && (
          <div className={`p-2 text-xs text-center rounded-b ${bannerType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} shadow`}>
            {bannerMessage}
          </div>
        )}
        
        {/* New Chat & Rename Buttons */}
        <div className="p-4 border-b border-border flex flex-col gap-2 mt-16">
          {isSidebarCollapsed ? (
            <Button 
              onClick={handleCreateNewConversation} 
              className="w-full group rounded-lg shadow-sm p-2" 
              variant="outline"
              title="New Conversation"
            >
              <Plus className="h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
            </Button>
          ) : (
            <Button onClick={handleCreateNewConversation} className="w-full group rounded-lg shadow-sm" variant="outline">
              <Plus className="mr-2 h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
              New Conversation
            </Button>
          )}
        </div>

        {/* Chat Sessions */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar max-h-[calc(100vh-300px)]">
          {!isSidebarCollapsed && (
            <h3 className="text-sm font-semibold text-muted-foreground mb-4 flex items-center">
              <Sparkles className="mr-2 h-4 w-4" />
              Recent Conversations
            </h3>
          )}
          {conversations.length > 0 ? (
            conversations.map((conv) => (
              <Card key={conv.id} hover className={`p-4 cursor-pointer transition-all duration-300 rounded-lg shadow-sm flex items-center justify-between ${currentSession?.id === conv.id ? 'border-2 border-primary' : ''}`}
                onClick={() => handleSelectSession(conv.id)}>
                {isSidebarCollapsed ? (
                  <div className="flex flex-col items-center space-y-1">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <MessageSquare className="w-4 h-4 text-primary" />
                    </div>
                    <div className="text-xs text-center text-muted-foreground truncate w-full" title={conv.title}>
                      {conv.title?.charAt(0) || 'C'}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 w-full">
                    <div className="flex-1 min-w-0">
                      {renamingConvId === conv.id ? (
                        <input
                          className="text-sm font-medium text-foreground truncate mb-1 bg-surface border-b border-primary focus:outline-none px-2 py-1 rounded"
                          value={editedTitle}
                          autoFocus
                          onChange={e => setEditedTitle(e.target.value)}
                          onBlur={() => handleSaveTitle(conv.id)}
                          onKeyDown={e => {
                            if (e.key === 'Enter') handleSaveTitle(conv.id);
                            if (e.key === 'Escape') { setIsEditingTitle(false); setRenamingConvId(null); }
                          }}
                          style={{ width: '10rem' }}
                        />
                      ) : (
                        <span className="text-sm font-medium text-foreground truncate mb-1">{conv.title}</span>
                      )}
                      <div className="text-xs text-muted-foreground">
                        {conv.created_at ? new Date(conv.created_at).toLocaleString() : ''}
                      </div>
                    </div>
                    <button
                      className="ml-1 text-primary hover:text-primary-dark focus:outline-none rounded p-1"
                      onClick={e => {
                        e.stopPropagation();
                        setEditedTitle(conv.title || '');
                        setIsEditingTitle(true);
                        setRenamingConvId(conv.id);
                      }}
                      title="Rename Conversation"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      className="ml-1 text-red-500 hover:text-red-700 focus:outline-none rounded p-1"
                      onClick={async e => {
                        e.stopPropagation();
                        await handleDeleteConversation(conv.id);
                      }}
                      title="Delete Conversation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </Card>
            ))
          ) : (
            <div className="text-xs text-muted-foreground">No conversations found.</div>
          )}
        </div>

        {/* Document Context */}
        <div className="p-4 border-t border-border">
          {!isSidebarCollapsed && (
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-muted-foreground flex items-center">
                <FileText className="mr-2 h-4 w-4" />
                Knowledge Base
              </h3>
              <div className="flex items-center space-x-2">
                <Button 
                  onClick={() => setShowFileTypeInfo(!showFileTypeInfo)} 
                  variant="ghost" 
                  size="sm" 
                  className="p-1"
                  title="Supported file types"
                >
                  <Sparkles className="h-4 w-4" />
                </Button>
                <Button onClick={() => fileInputRef.current?.click()} variant="ghost" size="sm" className="p-2">
                  <Upload className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
          
          {/* Document Type Selection */}
          {!isSidebarCollapsed && (
            <div className="mb-4">
              <label className="text-xs text-muted-foreground mb-2 block">Document Type:</label>
              <select 
                className="w-full text-xs p-2 border border-border rounded bg-surface text-foreground"
                onChange={(e) => {
                  const selectedType = e.target.value;
                  // Store the selected document type for uploads
                  localStorage.setItem('xor-rag-document-type', selectedType);
                }}
                defaultValue={localStorage.getItem('xor-rag-document-type') || 'default'}
              >
                <option value="default">Default - Regular chunks</option>
                <option value="master_document">Master Document - Complete analysis</option>
              </select>
            </div>
          )}
          
          {/* Supported File Types Info */}
          {showFileTypeInfo && (
            <Card className="p-3 mb-3 rounded-lg shadow-sm bg-blue-50 dark:bg-blue-900/20">
              <div className="text-xs text-muted-foreground mb-2">
                <strong>Supported file types:</strong>
              </div>
              <div className="grid grid-cols-2 gap-1 text-xs">
                {Object.entries(supportedFileTypes).map(([ext, desc]) => (
                  <div key={ext} className="flex items-center space-x-1">
                    <span className="text-primary font-mono">{ext}</span>
                    <span className="text-muted-foreground">-</span>
                    <span className="truncate">{desc}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
          
          {/* Advanced Search */}
          <div className="mb-4">
            <AdvancedSearch
              onSearch={(query, filters) => {
                console.log('Search performed:', query, filters);
                // Could integrate with chat or show results in a modal
              }}
              onResultSelect={(result) => {
                console.log('Search result selected:', result);
                // Could add the content to chat or show details
              }}
              placeholder="Search documents..."
            />
          </div>
          
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {operationState.loadingDocuments ? (
              <div className="text-xs text-muted-foreground">Loading documents...</div>
            ) : documents.length > 0 ? (
              documents.map((doc, index) => (
                <Card key={index} className="p-3 group flex items-center justify-between rounded-lg shadow-sm">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                    <div className="flex flex-col">
                      <span className="text-xs text-foreground truncate">{doc.filename}</span>
                                      {(doc as any).file_type && (
                  <span className="text-xs text-muted-foreground capitalize">{(doc as any).file_type}</span>
                )}
                    </div>
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
      </div>

      {/* Resize Handle */}
      <div
        className="fixed top-0 left-0 w-1 h-full z-50 cursor-col-resize hover:bg-primary/20 transition-colors duration-200"
        style={{ left: `${sidebarWidth - 2}px` }}
        onMouseDown={handleResizeStart}
        title="Drag to resize sidebar"
      >
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-0.5 h-8 bg-border hover:bg-primary transition-colors duration-200 rounded-full"></div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div 
        className="flex-1 flex flex-col min-w-0 transition-all duration-200"
        style={{ marginLeft: `${sidebarWidth}px` }}
      >
        {/* Chat Header - stretch across full width, add padding and shadow */}
        <div className="bg-surface border-b border-border px-8 py-5 flex items-center justify-between sticky top-0 z-30 shadow-md w-full">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-primary" />
            {currentSession ? (
              isEditingTitle ? (
                <input
                  className="text-xl font-bold bg-surface border-b border-primary focus:outline-none px-2 py-1 rounded"
                  value={editedTitle}
                  autoFocus
                  onChange={e => setEditedTitle(e.target.value)}
                  onBlur={() => handleSaveTitle()}
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
                    className="ml-2 text-primary hover:text-primary-dark focus:outline-none rounded transition-colors duration-200"
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
          <div className="flex items-center space-x-4">
            <DomainFilter 
              selectedDomain={selectedDomain}
              onDomainChange={setSelectedDomain}
            />
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
              <span className="text-sm text-muted-foreground">Online</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-background custom-scrollbar min-h-0">
          {memoizedMessages.length > 0 ? (
            <>
              {memoizedMessages}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <Card variant="elevated" glow className="p-12 text-center max-w-lg rounded-lg shadow-lg">
                <div className="text-6xl mb-6">🤖</div>
                <h3 className="text-2xl font-bold mb-4 text-foreground">Hi! How can I help you today?</h3>
              </Card>
            </div>
          )}
          {operationState.sending && streamingState.status !== 'streaming' && (
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
        <div className="bg-surface border-t border-border px-8 py-5 flex items-end gap-4 sticky bottom-0 z-20 shadow-md">
          <form onSubmit={handleSendMessage} className="flex items-end w-full gap-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc,.txt"
              multiple
              className="hidden"
            />
            {/* Inline attach for chat prompt */}
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              ref={el => {
                // Use a separate ref for inline attach
                (window as any).inlineFileInputRef = el;
              }}
              onChange={handleInlineFileAttach}
            />
            <div className="flex-1 relative">
              <Card variant="elevated" className="overflow-hidden rounded-lg shadow-sm">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="w-full p-4 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none resize-none min-h-[60px] max-h-32 rounded-lg"
                  disabled={operationState.sending || streamingState.status === 'streaming' || isRecording || isTranscribing}
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
              </Card>
              {/* Show attached file name if present */}
              {attachedFile && (
                <div className="text-xs text-primary mt-1 flex items-center gap-2">
                  <span>📎 {attachedFile.name}</span>
                  <button type="button" className="ml-1 text-red-500 hover:text-red-700" onClick={() => setAttachedFile(null)}>Remove</button>
                </div>
              )}
              {/* Show file processing spinner/status */}
              {fileProcessing && (
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                  <span className="animate-spin">⏳</span> Processing file (OCR)...
                </div>
              )}
              {/* Show file error if any */}
              {fileError && (
                <div className="text-xs text-red-500 mt-1 flex items-center gap-2">
                  <span>⚠️ {fileError}</span>
                </div>
              )}
            </div>
            {/* Inline attach button */}
            <Button
              type="button"
              className="p-4 group rounded-full shadow-md hover:bg-primary-dark transition-colors duration-200"
              size="lg"
              onClick={() => (window as any).inlineFileInputRef && (window as any).inlineFileInputRef.click()}
              disabled={operationState.sending || streamingState.status === 'streaming' || isRecording || isTranscribing}
            >
              <span role="img" aria-label="Attach">📎</span>
            </Button>
            <Button
              type="submit"
              disabled={!inputValue.trim() || operationState.sending || streamingState.status === 'streaming' || isRecording || isTranscribing}
              className={`p-4 group rounded-full shadow-md transition-colors duration-200`}
              size="lg"
            >
              <Send className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
            <Button
              type="button"
              className="p-4 group rounded-full shadow-md hover:bg-primary-dark transition-colors duration-200 relative"
              size="lg"
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              disabled={operationState.sending || streamingState.status === 'streaming' || isTranscribing}
              aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
              title={isRecording ? 'Stop recording' : 'Record voice input'}
            >
              {isRecording ? (
                <span className="flex items-center">
                  <span role="img" aria-label="Stop">🛑</span>
                  <span className="ml-2 animate-pulse text-xs">Recording...</span>
                  <span className="ml-2 w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                </span>
              ) : isTranscribing ? (
                <span className="flex items-center">
                  <span className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  <span className="ml-2 text-xs">Transcribing...</span>
                </span>
              ) : (
                <span role="img" aria-label="Mic">🎤</span>
              )}
            </Button>
          </form>
        </div>
      </div>
      
      {/* Model Selection Modal */}
      <ModelSelectionModal
        isOpen={showModelSelection}
        onClose={() => {
          setShowModelSelection(false);
          setPendingFile(null);
          setDetectedContentType(null);
        }}
        onModelSelect={handleModelSelection}
        detectedType={detectedContentType || 'image'}
        fileName={pendingFile?.name || ''}
        isLoading={modelSelectionLoading}
      />
      
      {/* Model Toast Notification */}
      <ModelToast
        isVisible={showModelToast}
        model={sessionModel}
        onClose={() => setShowModelToast(false)}
      />
    </div>
  );
};

export default ChatInterface;