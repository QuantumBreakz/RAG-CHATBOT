import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  Alert,
} from 'react-native';
import { Card, Button, IconButton, Searchbar, FAB, Portal, Modal, TextInput } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useChat, Session } from '../contexts/ChatContext';
import { useNavigation } from '@react-navigation/native';

const ConversationManagerScreen: React.FC = () => {
  const { theme } = useTheme();
  const { sessions, selectSession, deleteSession, renameSession, createSession } = useChat();
  const navigation = useNavigation();
  const [searchQuery, setSearchQuery] = useState('');
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [newTitle, setNewTitle] = useState('');

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    header: {
      padding: 20,
      backgroundColor: theme.colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 10,
    },
    searchContainer: {
      marginBottom: 10,
    },
    content: {
      flex: 1,
      padding: 20,
    },
    conversationCard: {
      marginBottom: 15,
      backgroundColor: theme.colors.surface,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    conversationHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: 15,
    },
    conversationTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: theme.colors.text,
      flex: 1,
    },
    conversationDate: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginTop: 5,
    },
    conversationStats: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginTop: 5,
    },
    actionButtons: {
      flexDirection: 'row',
      marginTop: 10,
    },
    actionButton: {
      marginRight: 10,
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
    modalContainer: {
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
    inputContainer: {
      marginBottom: 20,
    },
    modalButtons: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
  });

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectConversation = (session: Session) => {
    selectSession(session.id);
    navigation.navigate('Chat' as never);
  };

  const handleDeleteConversation = (session: Session) => {
    Alert.alert(
      'Delete Conversation',
      `Are you sure you want to delete "${session.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteSession(session.id),
        },
      ]
    );
  };

  const handleRenameConversation = (session: Session) => {
    setSelectedSession(session);
    setNewTitle(session.title);
    setShowRenameModal(true);
  };

  const handleSaveRename = () => {
    if (selectedSession && newTitle.trim()) {
      renameSession(selectedSession.id, newTitle.trim());
      setShowRenameModal(false);
      setSelectedSession(null);
      setNewTitle('');
    }
  };

  const handleCreateNewConversation = () => {
    createSession();
    navigation.navigate('Chat' as never);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderConversation = ({ item }: { item: Session }) => (
    <Card style={styles.conversationCard}>
      <TouchableOpacity onPress={() => handleSelectConversation(item)}>
        <Card.Content>
          <View style={styles.conversationHeader}>
            <View style={{ flex: 1 }}>
              <Text style={styles.conversationTitle}>{item.title}</Text>
              <Text style={styles.conversationDate}>
                Created: {formatDate(item.createdAt)}
              </Text>
              <Text style={styles.conversationStats}>
                {item.messages.length} messages • Last updated: {formatDate(item.updatedAt)}
              </Text>
            </View>
            <View style={styles.actionButtons}>
              <IconButton
                icon="pencil"
                size={20}
                onPress={() => handleRenameConversation(item)}
                style={styles.actionButton}
              />
              <IconButton
                icon="trash"
                size={20}
                onPress={() => handleDeleteConversation(item)}
                style={styles.actionButton}
              />
            </View>
          </View>
        </Card.Content>
      </TouchableOpacity>
    </Card>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="chatbubbles-outline" size={64} color={theme.colors.textSecondary} />
      <Text style={styles.emptyStateText}>
        No conversations yet
      </Text>
      <Text style={[styles.emptyStateText, { fontSize: 14 }]}>
        Start a new conversation to begin chatting with your AI assistant
      </Text>
      <Button
        mode="contained"
        onPress={handleCreateNewConversation}
        style={{ marginTop: 20, backgroundColor: theme.colors.primary }}
        icon="plus"
      >
        Start New Conversation
      </Button>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Conversations</Text>
        <View style={styles.searchContainer}>
          <Searchbar
            placeholder="Search conversations..."
            onChangeText={setSearchQuery}
            value={searchQuery}
            style={{ backgroundColor: theme.colors.background }}
          />
        </View>
      </View>

      <View style={styles.content}>
        {filteredSessions.length > 0 ? (
          <FlatList
            data={filteredSessions}
            renderItem={renderConversation}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
          />
        ) : (
          renderEmptyState()
        )}
      </View>

      <Portal>
        <Modal
          visible={showRenameModal}
          onDismiss={() => setShowRenameModal(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Text style={styles.modalTitle}>Rename Conversation</Text>
          <View style={styles.inputContainer}>
            <TextInput
              label="New Title"
              value={newTitle}
              onChangeText={setNewTitle}
              mode="outlined"
              style={{ backgroundColor: theme.colors.background }}
            />
          </View>
          <View style={styles.modalButtons}>
            <Button
              mode="outlined"
              onPress={() => setShowRenameModal(false)}
            >
              Cancel
            </Button>
            <Button
              mode="contained"
              onPress={handleSaveRename}
              disabled={!newTitle.trim()}
              style={{ backgroundColor: theme.colors.primary }}
            >
              Save
            </Button>
          </View>
        </Modal>
      </Portal>

      <FAB
        icon="plus"
        style={{
          position: 'absolute',
          margin: 16,
          right: 0,
          bottom: 0,
          backgroundColor: theme.colors.primary,
        }}
        onPress={handleCreateNewConversation}
      />
    </SafeAreaView>
  );
};

export default ConversationManagerScreen;
