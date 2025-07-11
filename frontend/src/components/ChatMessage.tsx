import React, { useState, useEffect } from 'react';
import { Message } from '../types';
import { formatTimestamp } from '../utils/helpers';
import { Copy, Check, ThumbsUp, ThumbsDown, MoreHorizontal, FileText, ExternalLink } from 'lucide-react';
import { Avatar } from './ui/Avatar';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Tooltip } from './ui/Tooltip';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const [displayedContent, setDisplayedContent] = useState('');
  const isUser = message.role === 'user';
  
  // Streaming effect for AI messages
  useEffect(() => {
    if (!isUser && message.isStreaming) {
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex < message.content.length) {
          setDisplayedContent(message.content.slice(0, currentIndex + 1));
          currentIndex++;
        } else {
          clearInterval(interval);
        }
      }, 20);
      return () => clearInterval(interval);
    } else {
      setDisplayedContent(message.content);
    }
  }, [message.content, message.isStreaming, isUser]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`group relative mb-8 animate-slide-up ${isUser ? 'ml-12' : 'mr-12'}`}>
      <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <Avatar type={message.role} size="md" className="flex-shrink-0 mt-1" />
        
        <div className="flex-1 min-w-0">
          <div className={`relative rounded-2xl px-6 py-4 shadow-sm border transition-all duration-200 hover:shadow-md ${
            isUser 
              ? 'bg-gradient-to-br from-emerald-600 to-emerald-700 text-white border-emerald-600' 
              : 'bg-white border-gray-200 text-gray-900'
          }`}>
            {/* Message content */}
            <div className="prose prose-sm max-w-none">
              <p className={`mb-0 leading-relaxed ${isUser ? 'text-white' : 'text-gray-800'}`}>
                {displayedContent}
                {message.isStreaming && (
                  <span className="inline-block w-2 h-5 bg-current ml-1 animate-pulse rounded-sm" />
                )}
              </p>
            </div>

            {/* Message actions */}
            {!isUser && !message.isStreaming && (
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-all duration-200">
                <Tooltip content={copied ? 'Copied!' : 'Copy message'}>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={copied ? Check : Copy}
                    onClick={handleCopy}
                    className="text-gray-500 hover:text-gray-700 transition-all duration-200 hover:scale-110"
                  />
                </Tooltip>
                <Tooltip content="Good response">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={ThumbsUp}
                    className="text-gray-500 hover:text-emerald-600 transition-all duration-200 hover:scale-110"
                  />
                </Tooltip>
                <Tooltip content="Poor response">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={ThumbsDown}
                    className="text-gray-500 hover:text-red-600 transition-all duration-200 hover:scale-110"
                  />
                </Tooltip>
                <Tooltip content="More options">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={MoreHorizontal}
                    className="text-gray-500 hover:text-gray-700 transition-all duration-200 hover:scale-110"
                  />
                </Tooltip>
              </div>
            )}
          </div>
          
          {/* Timestamp */}
          <div className={`flex items-center gap-2 mt-2 text-xs text-gray-500 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}>
            <span>{formatTimestamp(message.timestamp)}</span>
          </div>
          
          {/* Context sources */}
          {message.context && message.context.length > 0 && (
            <div className="mt-4 p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-100 animate-fade-in">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-emerald-600" />
                <h4 className="text-sm font-semibold text-emerald-900">Sources</h4>
                <Badge variant="info" size="sm">{message.context.length}</Badge>
              </div>
              <div className="space-y-3">
                {message.context.map((chunk, index) => (
                  <div key={chunk.id} className="bg-white rounded-lg p-3 border border-emerald-200 hover:border-emerald-300 transition-all duration-200 hover:shadow-sm animate-slide-up" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {chunk.source}
                        </span>
                        {chunk.page && (
                          <Badge variant="default" size="sm">Page {chunk.page}</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {chunk.similarity && (
                          <Badge variant="success" size="sm">
                            {Math.round(chunk.similarity * 100)}% match
                          </Badge>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={ExternalLink}
                          className="text-gray-400 hover:text-emerald-600 transition-all duration-200 hover:scale-110"
                        />
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};