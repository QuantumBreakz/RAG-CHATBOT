import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, Paperclip, Mic, Square, Sparkles, ArrowUp } from 'lucide-react';
import { Message } from '../types';
import { ChatMessage } from './ChatMessage';
import { Button } from './ui/Button';
import { LoadingSpinner } from './ui/LoadingSpinner';

interface ChatInterfaceProps {
  messages: Message[];
  isStreaming: boolean;
  onSendMessage: (message: string) => void;
  conversationTitle?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isStreaming,
  onSendMessage,
  conversationTitle
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isStreaming) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  const suggestedQuestions = [
    "What are the main topics covered in the uploaded documents?",
    "Can you summarize the key findings?",
    "What are the recommendations mentioned?",
    "Are there any specific dates or deadlines mentioned?"
  ];

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-emerald-50 via-white to-green-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-6 py-4 shadow-sm animate-slide-up">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-600" />
              {conversationTitle || 'New Conversation'}
            </h2>
            <p className="text-sm text-muted-foreground">
              AI-powered document analysis and Q&A
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isStreaming && (
              <div className="flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm animate-fade-in">
                <LoadingSpinner size="sm" />
                Thinking...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full p-6 animate-fade-in">
            <div className="text-center max-w-2xl">
              <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-green-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg animate-scale-in">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to XOR Chatbot
              </h3>
              <p className="text-muted-foreground mb-8 leading-relaxed">
                Upload your documents and start asking questions. Our AI will analyze your documents 
                and provide accurate, context-aware answers with source references.
              </p>
              
              {/* Suggested Questions */}
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700 mb-3">Try asking:</p>
                <div className="grid gap-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => setInputValue(question)}
                      className="text-left p-3 bg-white border border-gray-200 rounded-xl hover:border-emerald-300 hover:bg-emerald-50 transition-all duration-200 text-sm text-gray-700 hover:text-emerald-700 hover:scale-105 animate-slide-up"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto px-6 py-8">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white/80 backdrop-blur-sm border-t border-gray-200 px-6 py-4 animate-slide-up">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-3 p-3 bg-white border border-gray-300 rounded-2xl shadow-sm focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                icon={Paperclip}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 transition-all duration-200 hover:scale-110"
              />
              
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your documents..."
                className="flex-1 resize-none border-0 outline-none bg-transparent placeholder-gray-500 text-gray-900 min-h-[20px] max-h-[120px] transition-all duration-200"
                rows={1}
                disabled={isStreaming}
              />
              
              <div className="flex items-center gap-2 flex-shrink-0">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  icon={isRecording ? Square : Mic}
                  onClick={() => setIsRecording(!isRecording)}
                  className={`transition-all duration-200 hover:scale-110 ${isRecording ? 'text-red-500 hover:text-red-600' : 'text-gray-400 hover:text-gray-600'}`}
                />
                
                <Button
                  type="submit"
                  variant={inputValue.trim() ? 'primary' : 'ghost'}
                  size="sm"
                  icon={isStreaming ? Loader : (inputValue.trim() ? ArrowUp : Send)}
                  disabled={!inputValue.trim() || isStreaming}
                  className={`transition-all duration-200 hover:scale-110 ${
                    inputValue.trim() 
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg' 
                      : 'text-gray-400'
                  }`}
                />
              </div>
            </div>
          </form>
          
          <div className="flex items-center justify-between mt-3 px-3">
            <p className="text-xs text-gray-500">
              Press Enter to send, Shift+Enter for new line
            </p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>XOR Chatbot</span>
              <span>•</span>
              <span>100% Local & Private</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};