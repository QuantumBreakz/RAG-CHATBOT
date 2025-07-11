export interface Message {
  id?: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  context?: ContextChunk[];
  isStreaming?: boolean;
  context_preview?: string;
}

export interface ContextChunk {
  id: string;
  content: string;
  source: string;
  page?: number;
  similarity?: number;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  uploadedAt: string;
  chunks?: number;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  messages: Message[];
  uploads: UploadedFile[];
}

export interface AppSettings {
  theme: 'light' | 'dark';
  chunkSize: number;
  chunkOverlap: number;
  maxResults: number;
  temperature: number;
  model: string;
}