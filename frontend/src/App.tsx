import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { useChat } from './hooks/useChat';
import { AppSettings } from './types';

const defaultSettings: AppSettings = {
  theme: 'light',
  chunkSize: 600,
  chunkOverlap: 200,
  maxResults: 10,
  temperature: 0.7,
  model: 'llama3.2:3b'
};

function App() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const {
    conversations,
    activeConversation,
    isStreaming,
    createConversation,
    setActiveConversationId,
    sendMessage,
    uploadFiles,
    deleteConversation,
    renameConversation
  } = useChat();

  // Create initial conversation on first load
  useEffect(() => {
    if (conversations.length === 0) {
      createConversation('Welcome to XOR Chat');
    }
  }, [conversations.length, createConversation]);

  const handleNewConversation = () => {
    createConversation();
  };

  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
  };

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  const handleUploadFiles = (files: FileList) => {
    uploadFiles(files);
  };

  const handleDeleteConversation = (conversationId: string) => {
    deleteConversation(conversationId);
  };

  const handleRenameConversation = (conversationId: string, newTitle: string) => {
    renameConversation(conversationId, newTitle);
  };

  const handleSettingsChange = (newSettings: AppSettings) => {
    setSettings(newSettings);
  };

  return (
    <div className={`h-screen flex ${settings.theme === 'dark' ? 'dark' : ''} bg-background`}>
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversation?.id || null}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        onUploadFiles={handleUploadFiles}
        settings={settings}
        onSettingsChange={handleSettingsChange}
      />
      
      <div className="flex-1 flex flex-col min-w-0">
        {activeConversation ? (
          <ChatInterface
            messages={activeConversation.messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            conversationTitle={activeConversation.title}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-green-50">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-green-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.436L3 21l1.436-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Ready to Start
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                Select a conversation from the sidebar or create a new one to begin your AI-powered document analysis.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;