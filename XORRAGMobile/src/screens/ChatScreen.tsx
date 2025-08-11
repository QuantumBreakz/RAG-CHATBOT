import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { Card, Button, IconButton, FAB, Portal, Modal } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useChat, Message } from '../contexts/ChatContext';
import * as DocumentPicker from 'expo-document-picker';
import * as Sharing from 'expo-sharing';

const ChatScreen: React.FC = () => {
  const { theme } = useTheme();
  const { currentSession, addMessage, createSession } = useChat();
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showFilePicker, setShowFilePicker] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    chatContainer: {
      flex: 1,
    },
    messageContainer: {
      marginVertical: 5,
      marginHorizontal: 10,
    },
    userMessage: {
      alignSelf: 'flex-end',
      backgroundColor: theme.colors.primary,
      borderRadius: 15,
      padding: 12,
      maxWidth: '80%',
    },
    assistantMessage: {
      alignSelf: 'flex-start',
      backgroundColor: theme.colors.surface,
      borderRadius: 15,
      padding: 12,
      maxWidth: '80%',
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    messageText: {
      color: theme.colors.text,
      fontSize: 16,
    },
    userMessageText: {
      color: '#FFFFFF',
      fontSize: 16,
    },
    timestamp: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginTop: 5,
    },
    inputContainer: {
      flexDirection: 'row',
      padding: 10,
      backgroundColor: theme.colors.surface,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    textInput: {
      flex: 1,
      backgroundColor: theme.colors.background,
      borderRadius: 20,
      paddingHorizontal: 15,
      paddingVertical: 10,
      marginRight: 10,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    sendButton: {
      backgroundColor: theme.colors.primary,
      borderRadius: 20,
      width: 40,
      height: 40,
      justifyContent: 'center',
      alignItems: 'center',
    },
    emptyState: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },
    emptyStateText: {
      fontSize: 18,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      marginBottom: 20,
    },
    loadingContainer: {
      padding: 20,
      alignItems: 'center',
    },
    loadingText: {
      color: theme.colors.textSecondary,
      marginTop: 10,
    },
    filePickerModal: {
      backgroundColor: theme.colors.background,
      margin: 20,
      borderRadius: 10,
      padding: 20,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 20,
      textAlign: 'center',
    },
    fileOption: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 15,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    fileOptionText: {
      marginLeft: 15,
      fontSize: 16,
      color: theme.colors.text,
    },
  });

  useEffect(() => {
    if (!currentSession) {
      createSession();
    }
  }, []);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !currentSession) return;

    const userMessage = {
      content: inputText.trim(),
      role: 'user' as const,
    };

    addMessage(currentSession.id, userMessage);
    setInputText('');
    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      const assistantMessage = {
        content: `This is a simulated response to: "${userMessage.content}". In a real implementation, this would connect to your backend API.`,
        role: 'assistant' as const,
      };
      addMessage(currentSession.id, assistantMessage);
      setIsLoading(false);
    }, 2000);
  };

  const handleFileUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        copyToCacheDirectory: true,
      });

      if (result.canceled) return;

      const file = result.assets[0];
      Alert.alert('File Selected', `Selected: ${file.name}`);
      
      // Here you would upload the file to your backend
      // For now, we'll just show a success message
      if (currentSession) {
        addMessage(currentSession.id, {
          content: `📎 File uploaded: ${file.name}`,
          role: 'assistant',
        });
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick document');
    }
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    const messageTime = new Date(item.timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });

    return (
      <View style={styles.messageContainer}>
        <View style={isUser ? styles.userMessage : styles.assistantMessage}>
          <Text style={isUser ? styles.userMessageText : styles.messageText}>
            {item.content}
          </Text>
          <Text style={[styles.timestamp, { color: isUser ? 'rgba(255,255,255,0.7)' : theme.colors.textSecondary }]}>
            {messageTime}
          </Text>
        </View>
      </View>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="chatbubbles-outline" size={64} color={theme.colors.textSecondary} />
      <Text style={styles.emptyStateText}>
        Start a conversation with your AI assistant
      </Text>
      <Text style={[styles.emptyStateText, { fontSize: 14 }]}>
        Ask questions, upload documents, or explore advanced features
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.chatContainer}>
          <FlatList
            ref={flatListRef}
            data={currentSession?.messages || []}
            renderItem={renderMessage}
            keyExtractor={(item) => item.id}
            ListEmptyComponent={renderEmptyState}
            onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
            onLayout={() => flatListRef.current?.scrollToEnd()}
          />

          {isLoading && (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>AI is thinking...</Text>
            </View>
          )}
        </View>

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type your message..."
            placeholderTextColor={theme.colors.textSecondary}
            multiline
            maxLength={1000}
          />
          <TouchableOpacity
            style={styles.sendButton}
            onPress={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons name="send" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        <Portal>
          <Modal
            visible={showFilePicker}
            onDismiss={() => setShowFilePicker(false)}
            contentContainerStyle={styles.filePickerModal}
          >
            <Text style={styles.modalTitle}>Upload Document</Text>
            <TouchableOpacity
              style={styles.fileOption}
              onPress={() => {
                setShowFilePicker(false);
                handleFileUpload();
              }}
            >
              <Ionicons name="document" size={24} color={theme.colors.primary} />
              <Text style={styles.fileOptionText}>Select Document</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.fileOption}
              onPress={() => setShowFilePicker(false)}
            >
              <Ionicons name="close" size={24} color={theme.colors.textSecondary} />
              <Text style={styles.fileOptionText}>Cancel</Text>
            </TouchableOpacity>
          </Modal>
        </Portal>

        <FAB
          icon="plus"
          style={{
            position: 'absolute',
            margin: 16,
            right: 0,
            bottom: 80,
            backgroundColor: theme.colors.primary,
          }}
          onPress={() => setShowFilePicker(true)}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default ChatScreen;
