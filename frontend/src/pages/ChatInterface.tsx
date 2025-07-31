import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useChat } from '../contexts/ChatContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import DomainFilter from '../components/DomainFilter';
import SourceDisplay from '../components/SourceDisplay';
import ContextPreview from '../components/ContextPreview';
import MessageActions from '../components/MessageActions';
import AdvancedSearch from '../components/AdvancedSearch';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Upload, 
  Trash2, 
  Settings, 
  Plus, 
  MessageSquare, 
  FileText, 
  Sparkles,
  Mic,
  MicOff,
  Volume2,
  Search,
  Filter,
  X,
  ChevronDown,
  Edit,
  RotateCcw,
  Copy,
  Eye,
  EyeOff,
  Bot,
  User
} from 'lucide-react';
import { useGlobalLoading } from '../App';
import debounce from 'lodash.debounce';
import { v4 as uuidv4 } from 'uuid';

const CHAT_STATE_KEY = 'xor_rag_chat_state';
const CONVERSATIONS_KEY = 'xor_rag_conversations';

const API_URL = 'http://localhost:8000';

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
  const [lastSessionId, setLastSessionId] = useState<string | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [fileProcessing, setFileProcessing] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [currentSources, setCurrentSources] = useState<any[]>([]);
  const [supportedFileTypes, setSupportedFileTypes] = useState<{[key: string]: string}>({});
  const [showFileTypeInfo, setShowFileTypeInfo] = useState(false);
  const [showContextPreview, setShowContextPreview] = useState(false);
  const [contextMetadata, setContextMetadata] = useState<any>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
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

  // Streaming state for assistant
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingStatus, setStreamingStatus] = useState<'idle' | 'streaming'>('idle');

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
      console.warn('Failed to fetch supported file types:', err);
    }
  };

  const fetchConversations = async () => {
    setOperationState(s => ({ ...s, loadingConversations: true }));
    setLoading(true);
    try {
      const data = await apiCall('/api/history/list');
      setConversations(data.conversations || []);
      // Update chat context sessions as well
      if (data.conversations && Array.isArray(data.conversations)) {
        setSessions(data.conversations.map(conv => ({
          id: conv.id,
          title: conv.title,
          messages: [], // Optionally fetch messages for each conversation if needed
          createdAt: conv.created_at ? new Date(conv.created_at) : new Date(),
          documents: []
        })));
      }
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

  const resetStreaming = () => {
    setStreamingContent('');
    setStreamingStatus('idle');
  };

  // Event handlers
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || operationState.sending || streamingStatus === 'streaming') return;

    // Ensure a conversation is selected or created
    let sessionToUse = currentSession;
    if (!sessionToUse) {
      if (sessions && sessions.length > 0) {
        selectSession(sessions[0].id);
        sessionToUse = sessions[0];
      } else {
        // Create a new conversation and use it
        createSession();
        // Wait for state to update (force sync)
        // This is a hack, ideally use a callback or state update
        sessionToUse = {
          id: uuidv4(),
          title: 'New Conversation',
          messages: [],
          createdAt: new Date(),
          documents: []
        };
      }
    }

    const userMessage = inputValue.trim();
    setOperationState(s => ({ ...s, sending: true }));
    setInputValue("");
    setFileError(null);

    // Reset streaming state
    resetStreaming();

    // If this is a new conversation, ensure context is empty
    const isNewConversation = !sessionToUse || (sessionToUse.messages && sessionToUse.messages.length === 0);

    // Add user message immediately
    addMessage(userMessage, 'user');

    // Add a placeholder assistant message for streaming (remove any existing empty assistant message first)
    if (sessionToUse && sessionToUse.messages.length > 0) {
      const lastMsg = sessionToUse.messages[sessionToUse.messages.length - 1];
      if (lastMsg.role === 'assistant' && !lastMsg.content) {
        setCurrentSessionFromBackend({
          ...sessionToUse,
          messages: sessionToUse.messages.slice(0, -1)
        });
      }
    }
    addMessage('', 'assistant');

    try {
      setStreamingStatus('streaming');
      setStreamingContent('');
      let streamed = '';
      let contextMetadata = null;
      let sources = [];
      // Use only the current session's messages for context, and for new conversations, context is empty
      const conversationHistory = isNewConversation ? [] : (sessionToUse?.messages.filter(m => m.role !== 'assistant' || m.content) || []);
      let response;
      if (attachedFile) {
        setFileProcessing(true);
        // Use multipart/form-data if file is attached
        const formData = new FormData();
        formData.append('question', userMessage);
        formData.append('n_results', '3');
        formData.append('expand', '2');
        formData.append('filename', '');
        formData.append('domain_filter', selectedDomain || '');
        formData.append('conversation_history', JSON.stringify(conversationHistory));
        formData.append('file', attachedFile);
        response = await fetch('/api/query/stream', {
          method: 'POST',
          body: formData
        });
        setFileProcessing(false);
        if (!response.ok) {
          const err = await response.json();
          setFileError(err.error || 'File processing failed.');
          setOperationState(s => ({ ...s, sending: false }));
          setStreamingStatus('idle');
          setAttachedFile(null);
          return;
        }
      } else {
        // Use existing x-www-form-urlencoded flow
        response = await fetch('/api/query/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            question: userMessage,
            n_results: '3',
            expand: '2',
            filename: '',
            domain_filter: selectedDomain || '',
            conversation_history: JSON.stringify(conversationHistory)
          })
        });
      }
      setAttachedFile(null); // Reset after sending
      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = '';
      let finished = false;
      while (!done && !finished) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                if (data.status === 'streaming' && data.answer !== undefined) {
                  streamed += data.answer;
                  setStreamingContent(streamed);
                  updateStreamingMessage(streamed); // Real-time update
                }
                if (data.status === 'success') {
                  if (data.answer !== undefined) {
                    streamed += data.answer;
                    setStreamingContent(streamed);
                    updateStreamingMessage(streamed); // Final update
                  }
                  // Capture context metadata and sources
                  if (data.context_metadata) {
                    contextMetadata = data.context_metadata;
                  }
                  if (data.sources) {
                    sources = data.sources;
                  }
                  finished = true;
                  break;
                }
                if (data.status === 'error' && data.answer) {
                  setFileError(data.answer);
                  finished = true;
                  break;
                }
              } catch (err) {
                // Ignore parse errors for incomplete lines
              }
            }
          }
        }
      }
      // Handle any remaining buffered line
      if (buffer.trim() && !finished) {
        try {
          const data = JSON.parse(buffer);
          if (data.status === 'streaming' && data.answer !== undefined) {
            streamed += data.answer;
            setStreamingContent(streamed);
            updateStreamingMessage(streamed);
          }
          if (data.status === 'success') {
            if (data.answer !== undefined) {
              streamed += data.answer;
              setStreamingContent(streamed);
              updateStreamingMessage(streamed);
            }
            // Capture context metadata and sources
            if (data.context_metadata) {
              contextMetadata = data.context_metadata;
            }
            if (data.sources) {
              sources = data.sources;
            }
          }
          if (data.status === 'error' && data.answer) {
            setFileError(data.answer);
          }
        } catch (err) {
          // Ignore parse errors for incomplete lines
        }
      }
      setStreamingStatus('idle');
      // After streaming, update the session's messages by removing the placeholder and appending the real assistant message
      if (sessionToUse) {
        // Remove the last (empty) assistant message and append the real one
        const filteredMessages = sessionToUse.messages.filter((m, idx, arr) => {
          // Remove the last assistant message if it's empty
          if (idx === arr.length - 1 && m.role === 'assistant' && !m.content) return false;
          return true;
        });
        // Ensure the user's message is present before the assistant's response
        let updatedMessages = [...filteredMessages];
        // If the last message is not the user's message, add it
        if (
          updatedMessages.length === 0 ||
          updatedMessages[updatedMessages.length - 1].role !== 'user' ||
          updatedMessages[updatedMessages.length - 1].content !== userMessage
        ) {
          updatedMessages.push({ id: uuidv4(), role: 'user', content: userMessage, timestamp: new Date(), isStreaming: false });
        }
        // Only append the assistant message if it's not already present as the last message
        const lastMsg = updatedMessages[updatedMessages.length - 1];
        if (!(lastMsg && lastMsg.role === 'assistant' && lastMsg.content === streamed)) {
          updatedMessages.push({ 
            id: uuidv4(), 
            role: 'assistant', 
            content: streamed, 
            timestamp: new Date(), 
            isStreaming: false,
            sources: sources,
            contextMetadata: contextMetadata
          });
        }
        setCurrentSessionFromBackend({
          ...sessionToUse,
          messages: updatedMessages
        });
        await apiCall('/api/history/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...sessionToUse,
            created_at: sessionToUse.createdAt instanceof Date ? sessionToUse.createdAt.toISOString() : sessionToUse.createdAt,
            uploads: (sessionToUse.documents || []).map(filename => ({ filename })),
            messages: updatedMessages
          })
        });
      }
    } catch (error) {
      showBanner('Failed to send message.', 'error');
      setFileError('Failed to send message.');
      // Remove the empty assistant message on error
      if (sessionToUse && sessionToUse.messages.length > 0) {
        const messagesWithoutEmpty = sessionToUse.messages.filter((m, idx, arr) => !(idx === arr.length - 1 && m.role === 'assistant' && !m.content));
        setCurrentSessionFromBackend({
          ...sessionToUse,
          messages: messagesWithoutEmpty
        });
      }
    } finally {
      setOperationState(s => ({ ...s, sending: false }));
      setStreamingStatus('idle');
      setFileProcessing(false);
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
          created_at: convToRename.createdAt instanceof Date ? convToRename.createdAt.toISOString() : convToRename.createdAt,
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
          setLastSessionId(parsed.currentSession.id);
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
      let backendCurrentSession = null;
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
        setSessions(backendConvs.map((conv: any) => ({
          id: conv.id,
          title: conv.title,
          messages: [],
          createdAt: conv.created_at ? new Date(conv.created_at) : new Date(),
          documents: []
        })));
        // Try to fetch the current session from backend
        if (localCurrentSessionId) {
          try {
            const data = await apiCall(`/api/history/get/${localCurrentSessionId}`);
            if (data.conversation) {
              backendCurrentSession = data.conversation;
              setCurrentSessionFromBackend(data.conversation);
              setLastSessionId(data.conversation.id);
            } else if (localCurrentSession) {
              setCurrentSessionFromBackend(localCurrentSession);
              setLastSessionId(localCurrentSession.id);
            }
          } catch {
            if (localCurrentSession) {
              setCurrentSessionFromBackend(localCurrentSession);
              setLastSessionId(localCurrentSession.id);
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
                setLastSessionId(data.conversation.id);
              } else {
                setCurrentSessionFromBackend(firstConv);
                setLastSessionId(firstConv.id);
              }
            } catch {
              setCurrentSessionFromBackend(firstConv);
              setLastSessionId(firstConv.id);
            }
          }
        }
      } catch {
        // If backend fetch fails, always use the local copy
        if (localCurrentSession) {
          setCurrentSessionFromBackend(localCurrentSession);
          setLastSessionId(localCurrentSession.id);
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
    if (safeCurrentSession) setLastSessionId(safeCurrentSession.id);
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

  // Render streaming assistant bubble - only show when actively streaming
  const renderStreamingAssistantBubble = () => {
    if (streamingStatus !== 'streaming' || !streamingContent) return null;
    return (
      <div className="flex justify-start">
        <div className="flex items-start space-x-3 max-w-2xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-elevated border border-border flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <Card variant="elevated" className="p-4">
            <ReactMarkdown components={{p: ({node, ...props}) => <p className="text-sm leading-relaxed whitespace-pre-line" {...props} />}}>
              {streamingContent}
            </ReactMarkdown>
            <span className="ml-1 animate-pulse">|</span>
            <div className="text-xs mt-2 text-muted-foreground">
              Streaming...
            </div>
          </Card>
        </div>
      </div>
    );
  };

  // Message action handlers - moved before memoizedMessages
  const handleEditMessage = (messageId: string, newContent: string) => {
    if (currentSession) {
      const updatedMessages = currentSession.messages.map(msg => 
        msg.id === messageId ? { ...msg, content: newContent } : msg
      );
      
      // Update the session with edited message
      const updatedSession = { ...currentSession, messages: updatedMessages };
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
    )) || [], [currentSession?.messages, showContextPreview, editingMessageId]);

  // Restore handleSelectSession and handleCreateNewConversation with correct logic
  const handleSelectSession = async (convId: string) => {
    selectSession(convId);
    try {
      const data = await apiCall(`/api/history/get/${convId}`);
      if (data.conversation) {
        setCurrentSessionFromBackend(data.conversation);
      }
    } catch {}
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
        created_at: newConv.created_at || newConv.createdAt,
        uploads: (newConv.uploads || []).map(filename => ({ filename })),
      })
    });
    // Add to conversations and set as current
    setConversations((prev: any[]) => [
      { id: newConv.id, title: newConv.title, created_at: newConv.created_at },
      ...prev
    ]);
    await handleSelectSession(newConv.id);
  };

  // New handler for inline file attach
  const handleInlineFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setAttachedFile(e.target.files[0]);
    }
  };

  // Voice recording logic
  const handleStartRecording = async () => {
    setIsRecording(true);
    setAudioDuration(null);
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      let startTime = Date.now();
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioDuration((Date.now() - startTime) / 1000);
        if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = URL.createObjectURL(audioBlob);
        setIsTranscribing(true);
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice.wav');
        showBanner('Transcribing voice input...', 'success');
        try {
          const response = await fetch(`${API_URL}/transcribe`, {
            method: 'POST',
            body: formData
          });
          const data = await response.json();
          setIsTranscribing(false);
          if (data.text) {
            setInputValue(data.text);
            showBanner('Voice transcription complete.', 'success');
          } else {
            showBanner(data.error || 'Transcription failed.', 'error');
          }
        } catch (err) {
          setIsTranscribing(false);
          showBanner('Transcription failed.', 'error');
        }
      };
      mediaRecorder.start();
    } catch (err) {
      setIsRecording(false);
      showBanner('Microphone access denied or not available.', 'error');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <div className="flex h-screen w-screen bg-background">
      {/* Sidebar */}
      <div className="bg-surface border-r border-border flex flex-col w-80 flex-none h-screen z-40 fixed left-0 top-0 overflow-y-auto max-h-screen shadow-lg">
        {bannerMessage && (
          <div className={`p-2 text-xs text-center rounded-b ${bannerType === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} shadow`}>
            {bannerMessage}
          </div>
        )}
        
        {/* New Chat & Rename Buttons */}
        <div className="p-4 border-b border-border flex flex-col gap-2 mt-16">
          <Button onClick={handleCreateNewConversation} className="w-full group rounded-lg shadow-sm" variant="outline">
            <Plus className="mr-2 h-4 w-4 group-hover:rotate-90 transition-transform duration-300" />
            New Conversation
          </Button>
        </div>

        {/* Chat Sessions */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar max-h-[calc(100vh-300px)]">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 flex items-center">
            <Sparkles className="mr-2 h-4 w-4" />
            Recent Conversations
          </h3>
          {conversations.length > 0 ? (
            conversations.map((conv) => (
              <Card key={conv.id} hover className={`p-4 cursor-pointer transition-all duration-300 rounded-lg shadow-sm flex items-center justify-between ${currentSession?.id === conv.id ? 'border-2 border-primary' : ''}`}
                onClick={() => handleSelectSession(conv.id)}>
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
                      {doc.file_type && (
                        <span className="text-xs text-muted-foreground capitalize">{doc.file_type}</span>
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
      <div className="flex-1 flex flex-col ml-80 min-w-0">
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
              {renderStreamingAssistantBubble()}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <Card variant="elevated" glow className="p-12 text-center max-w-lg rounded-lg shadow-lg">
                <div className="text-6xl mb-6">🤖</div>
                <h3 className="text-2xl font-bold mb-4 text-foreground">Hi! How can I help you today?</h3>
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
                  disabled={operationState.sending || streamingStatus === 'streaming' || isRecording || isTranscribing}
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
              disabled={operationState.sending || streamingStatus === 'streaming' || isRecording || isTranscribing}
            >
              <span role="img" aria-label="Attach">📎</span>
            </Button>
            <Button
              type="submit"
              disabled={!inputValue.trim() || operationState.sending || streamingStatus === 'streaming' || isRecording || isTranscribing}
              className="p-4 group rounded-full shadow-md hover:bg-primary-dark transition-colors duration-200"
              size="lg"
            >
              <Send className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
            <Button
              type="button"
              className="p-4 group rounded-full shadow-md hover:bg-primary-dark transition-colors duration-200 relative"
              size="lg"
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              disabled={operationState.sending || streamingStatus === 'streaming' || isTranscribing}
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
    </div>
  );
};

export default ChatInterface;