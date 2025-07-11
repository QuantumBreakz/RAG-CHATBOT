import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message } from '../types';
import * as chatApi from '../api/chat';
import * as convApi from '../api/conversation';
import * as uploadApi from '../api/upload';

// Helper function to add missing IDs to messages
const addMessageIds = (messages: Message[]): Message[] => {
  return messages.map((msg, index) => ({
    ...msg,
    id: msg.id || `${msg.role}_${Date.now()}_${index}`
  }));
};

export const useChat = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch conversations on mount
  useEffect(() => {
    setLoading(true);
    convApi.listConversations()
      .then(setConversations)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Fetch a conversation when activeConversationId changes
  useEffect(() => {
    if (activeConversationId) {
      convApi.getConversation(activeConversationId)
        .then((conv: Conversation) => {
          // Add missing IDs to messages
          const convWithIds = {
            ...conv,
            messages: addMessageIds(conv.messages)
          };
          setConversations((prev: Conversation[]) => {
            const others = prev.filter((c: Conversation) => c.id !== conv.id);
            return [convWithIds, ...others];
          });
        })
        .catch((e: Error) => setError(e.message));
    }
  }, [activeConversationId]);

  const createConversation = useCallback(async (title?: string) => {
    setLoading(true);
    try {
      const conv = await convApi.createConversation(title);
      const convWithIds = {
        ...conv,
        messages: addMessageIds(conv.messages)
      };
      setConversations((prev: Conversation[]) => [convWithIds, ...prev]);
      setActiveConversationId(conv.id);
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error('Unknown error occurred');
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    if (!activeConversationId) return;
    setIsStreaming(true);
    try {
      await chatApi.sendChatMessage(activeConversationId, message);
      // Fetch updated conversation
      const conv = await convApi.getConversation(activeConversationId);
      const convWithIds = {
        ...conv,
        messages: addMessageIds(conv.messages)
      };
      setConversations((prev: Conversation[]) => {
        const others = prev.filter((c: Conversation) => c.id !== conv.id);
        return [convWithIds, ...others];
      });
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error('Unknown error occurred');
      setError(error.message);
    } finally {
        setIsStreaming(false);
    }
  }, [activeConversationId]);

  const uploadFiles = useCallback(async (files: FileList) => {
    if (!activeConversationId) return;
    setLoading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadApi.uploadFile(file);
      }
      // Optionally refresh conversation/files state
      const conv = await convApi.getConversation(activeConversationId);
      const convWithIds = {
        ...conv,
        messages: addMessageIds(conv.messages)
      };
      setConversations((prev: Conversation[]) => {
        const others = prev.filter((c: Conversation) => c.id !== conv.id);
        return [convWithIds, ...others];
      });
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error('Unknown error occurred');
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [activeConversationId]);

  const deleteConversation = useCallback(async (conversationId: string) => {
    setLoading(true);
    try {
      await convApi.deleteConversation(conversationId);
      setConversations((prev: Conversation[]) => prev.filter((c: Conversation) => c.id !== conversationId));
    if (activeConversationId === conversationId) {
      setActiveConversationId(null);
      }
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error('Unknown error occurred');
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [activeConversationId]);

  const renameConversation = useCallback(async (conversationId: string, newTitle: string) => {
    setLoading(true);
    try {
      await convApi.renameConversation(conversationId, newTitle);
      const conv = await convApi.getConversation(conversationId);
      const convWithIds = {
        ...conv,
        messages: addMessageIds(conv.messages)
      };
      setConversations((prev: Conversation[]) => {
        const others = prev.filter((c: Conversation) => c.id !== conv.id);
        return [convWithIds, ...others];
      });
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error('Unknown error occurred');
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    conversations,
    activeConversation: conversations.find((c: Conversation) => c.id === activeConversationId) || null,
    isStreaming,
    createConversation,
    setActiveConversationId,
    sendMessage,
    uploadFiles,
    deleteConversation,
    renameConversation,
    loading,
    error,
  };
};