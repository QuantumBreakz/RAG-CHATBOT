import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  Linking,
} from 'react-native';
import { Card, Button } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

const AboutScreen: React.FC = () => {
  const { theme } = useTheme();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    header: {
      padding: 20,
      alignItems: 'center',
      backgroundColor: theme.colors.surface,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: theme.colors.text,
      textAlign: 'center',
      marginBottom: 10,
    },
    subtitle: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      marginBottom: 20,
    },
    content: {
      flex: 1,
      padding: 20,
    },
    section: {
      marginBottom: 20,
    },
    sectionTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 15,
    },
    infoCard: {
      backgroundColor: theme.colors.surface,
      marginBottom: 15,
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
    featureList: {
      marginTop: 10,
    },
    featureItem: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    featureIcon: {
      marginRight: 10,
    },
    featureText: {
      fontSize: 14,
      color: theme.colors.textSecondary,
      flex: 1,
    },
    versionInfo: {
      alignItems: 'center',
      marginTop: 20,
    },
    versionText: {
      fontSize: 14,
      color: theme.colors.textSecondary,
      marginBottom: 5,
    },
  });

  const features = [
    { icon: 'brain', text: 'Agentic RAG with multi-agent architecture' },
    { icon: 'document-text', text: 'Multi-OCR with layout analysis' },
    { icon: 'globe', text: 'Web search integration via Tavily API' },
    { icon: 'shield-checkmark', text: 'Anti-hallucination system' },
    { icon: 'language', text: 'Cross-language support for 11+ languages' },
    { icon: 'layers', text: 'Template-based chunking strategies' },
    { icon: 'chatbubbles', text: 'Advanced conversation management' },
    { icon: 'settings', text: 'Comprehensive settings and configuration' },
  ];

  const handleOpenLink = (url: string) => {
    Linking.openURL(url);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>XOR RAG Chatbot</Text>
          <Text style={styles.subtitle}>
            Secure, Fully Offline, Multi-Document Q&A with Advanced AI Features
          </Text>
        </View>

        <View style={styles.content}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About</Text>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>What is XOR RAG Chatbot?</Text>
                <Text style={styles.infoText}>
                  XOR RAG Chatbot is a production-ready, completely offline RAG (Retrieval-Augmented Generation) 
                  chatbot designed for document Q&A. Built with advanced AI capabilities, it provides secure, 
                  private, and intelligent document processing and conversation.
                </Text>
              </Card.Content>
            </Card>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Advanced Features</Text>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>Powered by Mistral 7B</Text>
                <Text style={styles.infoText}>
                  Our mobile app leverages the same advanced AI capabilities as the web version, 
                  featuring cutting-edge language models and intelligent processing.
                </Text>
                <View style={styles.featureList}>
                  {features.map((feature, index) => (
                    <View key={index} style={styles.featureItem}>
                      <Ionicons
                        name={feature.icon as any}
                        size={20}
                        color={theme.colors.primary}
                        style={styles.featureIcon}
                      />
                      <Text style={styles.featureText}>{feature.text}</Text>
                    </View>
                  ))}
                </View>
              </Card.Content>
            </Card>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Technology Stack</Text>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>Frontend</Text>
                <Text style={styles.infoText}>
                  • React Native with TypeScript{'\n'}
                  • React Navigation for routing{'\n'}
                  • React Native Paper for UI components{'\n'}
                  • Expo for development and deployment
                </Text>
              </Card.Content>
            </Card>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>Backend</Text>
                <Text style={styles.infoText}>
                  • FastAPI with Python{'\n'}
                  • ChromaDB for vector storage{'\n'}
                  • Redis for caching{'\n'}
                  • Ollama for local LLM inference{'\n'}
                  • Mistral 7B as the primary language model
                </Text>
              </Card.Content>
            </Card>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Security & Privacy</Text>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>Completely Offline</Text>
                <Text style={styles.infoText}>
                  • All AI models run locally{'\n'}
                  • No data sent to external services{'\n'}
                  • Local storage for conversations{'\n'}
                  • Zero internet required after setup
                </Text>
              </Card.Content>
            </Card>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Support</Text>
            <Card style={styles.infoCard}>
              <Card.Content>
                <Text style={styles.infoTitle}>Getting Help</Text>
                <Text style={styles.infoText}>
                  For support, documentation, and updates, visit our project repository.
                </Text>
                <Button
                  mode="contained"
                  onPress={() => handleOpenLink('https://github.com/QuantumBreakz/PITB-RAG')}
                  style={{ marginTop: 10, backgroundColor: theme.colors.primary }}
                  icon="github"
                >
                  View on GitHub
                </Button>
              </Card.Content>
            </Card>
          </View>

          <View style={styles.versionInfo}>
            <Text style={styles.versionText}>Version 1.0.0</Text>
            <Text style={styles.versionText}>Built with React Native & Expo</Text>
            <Text style={styles.versionText}>Powered by Mistral 7B</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default AboutScreen;
