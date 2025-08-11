import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  Alert,
  Switch,
  TouchableOpacity,
} from 'react-native';
import { Card, Button, List, Divider, TextInput, Portal, Modal } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SettingsScreen: React.FC = () => {
  const { theme, isDarkMode, toggleTheme } = useTheme();
  const [showApiModal, setShowApiModal] = useState(false);
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [chunkSize, setChunkSize] = useState('600');
  const [chunkOverlap, setChunkOverlap] = useState('200');
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [enableAutoSave, setEnableAutoSave] = useState(true);

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
    content: {
      flex: 1,
      padding: 20,
    },
    section: {
      marginBottom: 20,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 10,
    },
    settingItem: {
      backgroundColor: theme.colors.surface,
      marginBottom: 10,
      borderRadius: 8,
    },
    settingRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: 15,
    },
    settingText: {
      fontSize: 16,
      color: theme.colors.text,
      flex: 1,
    },
    settingDescription: {
      fontSize: 14,
      color: theme.colors.textSecondary,
      marginTop: 5,
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
      marginBottom: 15,
    },
    modalButtons: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginTop: 20,
    },
    infoCard: {
      backgroundColor: theme.colors.surface,
      marginBottom: 20,
    },
    infoTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 5,
    },
    infoText: {
      fontSize: 14,
      color: theme.colors.textSecondary,
      lineHeight: 20,
    },
  });

  const handleSaveSettings = async () => {
    try {
      await AsyncStorage.setItem('api_url', apiUrl);
      await AsyncStorage.setItem('chunk_size', chunkSize);
      await AsyncStorage.setItem('chunk_overlap', chunkOverlap);
      await AsyncStorage.setItem('enable_notifications', enableNotifications.toString());
      await AsyncStorage.setItem('enable_auto_save', enableAutoSave.toString());
      
      Alert.alert('Success', 'Settings saved successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const handleResetSettings = () => {
    Alert.alert(
      'Reset Settings',
      'Are you sure you want to reset all settings to default?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.multiRemove([
                'api_url',
                'chunk_size',
                'chunk_overlap',
                'enable_notifications',
                'enable_auto_save',
              ]);
              setApiUrl('http://localhost:8000');
              setChunkSize('600');
              setChunkOverlap('200');
              setEnableNotifications(true);
              setEnableAutoSave(true);
              Alert.alert('Success', 'Settings reset to default');
            } catch (error) {
              Alert.alert('Error', 'Failed to reset settings');
            }
          },
        },
      ]
    );
  };

  const handleClearData = () => {
    Alert.alert(
      'Clear All Data',
      'This will delete all conversations and settings. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.clear();
              Alert.alert('Success', 'All data cleared');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear data');
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <ScrollView style={styles.content}>
        <Card style={styles.infoCard}>
          <Card.Content>
            <Text style={styles.infoTitle}>XOR RAG Chatbot Mobile</Text>
            <Text style={styles.infoText}>
              Version 1.0.0 • Powered by Mistral 7B • Advanced AI Features
            </Text>
          </Card.Content>
        </Card>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Appearance</Text>
          <Card style={styles.settingItem}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.settingText}>Dark Mode</Text>
                <Text style={styles.settingDescription}>
                  Switch between light and dark themes
                </Text>
              </View>
              <Switch
                value={isDarkMode}
                onValueChange={toggleTheme}
                trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                thumbColor={isDarkMode ? '#FFFFFF' : '#FFFFFF'}
              />
            </View>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>API Configuration</Text>
          <Card style={styles.settingItem}>
            <TouchableOpacity onPress={() => setShowApiModal(true)}>
              <View style={styles.settingRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.settingText}>Backend API URL</Text>
                  <Text style={styles.settingDescription}>
                    {apiUrl}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={theme.colors.textSecondary} />
              </View>
            </TouchableOpacity>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Document Processing</Text>
          <Card style={styles.settingItem}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.settingText}>Chunk Size</Text>
                <Text style={styles.settingDescription}>
                  Size of document chunks for processing
                </Text>
              </View>
              <TextInput
                value={chunkSize}
                onChangeText={setChunkSize}
                keyboardType="numeric"
                style={{ width: 80, textAlign: 'center' }}
                mode="outlined"
                dense
              />
            </View>
          </Card>
          <Card style={styles.settingItem}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.settingText}>Chunk Overlap</Text>
                <Text style={styles.settingDescription}>
                  Overlap between document chunks
                </Text>
              </View>
              <TextInput
                value={chunkOverlap}
                onChangeText={setChunkOverlap}
                keyboardType="numeric"
                style={{ width: 80, textAlign: 'center' }}
                mode="outlined"
                dense
              />
            </View>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          <Card style={styles.settingItem}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.settingText}>Enable Notifications</Text>
                <Text style={styles.settingDescription}>
                  Receive notifications for new messages
                </Text>
              </View>
              <Switch
                value={enableNotifications}
                onValueChange={setEnableNotifications}
                trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                thumbColor={enableNotifications ? '#FFFFFF' : '#FFFFFF'}
              />
            </View>
          </Card>
          <Card style={styles.settingItem}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.settingText}>Auto Save</Text>
                <Text style={styles.settingDescription}>
                  Automatically save conversations
                </Text>
              </View>
              <Switch
                value={enableAutoSave}
                onValueChange={setEnableAutoSave}
                trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                thumbColor={enableAutoSave ? '#FFFFFF' : '#FFFFFF'}
              />
            </View>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data Management</Text>
          <Button
            mode="outlined"
            onPress={handleSaveSettings}
            style={{ marginBottom: 10 }}
            icon="content-save"
          >
            Save Settings
          </Button>
          <Button
            mode="outlined"
            onPress={handleResetSettings}
            style={{ marginBottom: 10 }}
            icon="refresh"
          >
            Reset to Default
          </Button>
          <Button
            mode="outlined"
            onPress={handleClearData}
            style={{ marginBottom: 10 }}
            icon="delete"
            textColor={theme.colors.error}
          >
            Clear All Data
          </Button>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Advanced Features</Text>
              <Text style={styles.infoText}>
                • Agentic RAG with multi-agent architecture{'\n'}
                • Multi-OCR with layout analysis{'\n'}
                • Web search integration{'\n'}
                • Anti-hallucination system{'\n'}
                • Cross-language support{'\n'}
                • Template-based chunking
              </Text>
            </Card.Content>
          </Card>
        </View>
      </ScrollView>

      <Portal>
        <Modal
          visible={showApiModal}
          onDismiss={() => setShowApiModal(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Text style={styles.modalTitle}>Backend API URL</Text>
          <View style={styles.inputContainer}>
            <TextInput
              label="API URL"
              value={apiUrl}
              onChangeText={setApiUrl}
              mode="outlined"
              placeholder="http://localhost:8000"
              style={{ backgroundColor: theme.colors.background }}
            />
          </View>
          <View style={styles.modalButtons}>
            <Button
              mode="outlined"
              onPress={() => setShowApiModal(false)}
            >
              Cancel
            </Button>
            <Button
              mode="contained"
              onPress={() => setShowApiModal(false)}
              style={{ backgroundColor: theme.colors.primary }}
            >
              Save
            </Button>
          </View>
        </Modal>
      </Portal>
    </SafeAreaView>
  );
};

export default SettingsScreen;
