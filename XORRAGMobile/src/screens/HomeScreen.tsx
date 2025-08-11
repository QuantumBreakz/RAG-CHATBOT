import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { Card, Button, Title, Paragraph } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useNavigation } from '@react-navigation/native';

const HomeScreen: React.FC = () => {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const features = [
    {
      title: 'Advanced AI Chat',
      description: 'Powered by Mistral 7B with Agentic RAG capabilities',
      icon: 'chatbubbles',
      color: '#007AFF',
    },
    {
      title: 'Multi-OCR Processing',
      description: 'Advanced document processing with layout analysis',
      icon: 'document-text',
      color: '#34C759',
    },
    {
      title: 'Web Search Integration',
      description: 'Real-time information from the web via Tavily API',
      icon: 'globe',
      color: '#FF9500',
    },
    {
      title: 'Anti-Hallucination',
      description: 'Comprehensive fact verification and validation',
      icon: 'shield-checkmark',
      color: '#FF3B30',
    },
    {
      title: 'Cross-Language Support',
      description: 'Multi-language processing for 11+ languages',
      icon: 'language',
      color: '#AF52DE',
    },
    {
      title: 'Template Chunking',
      description: 'Intelligent document processing strategies',
      icon: 'layers',
      color: '#5856D6',
    },
  ];

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
    featuresGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      marginBottom: 20,
    },
    featureCard: {
      width: '48%',
      marginBottom: 15,
      backgroundColor: theme.colors.surface,
    },
    featureIcon: {
      alignSelf: 'center',
      marginBottom: 10,
    },
    featureTitle: {
      fontSize: 14,
      fontWeight: 'bold',
      color: theme.colors.text,
      textAlign: 'center',
      marginBottom: 5,
    },
    featureDescription: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
    actionButtons: {
      marginTop: 20,
    },
    button: {
      marginBottom: 15,
    },
    statsContainer: {
      backgroundColor: theme.colors.surface,
      padding: 20,
      borderRadius: 10,
      marginBottom: 20,
    },
    statsTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: 15,
    },
    statsGrid: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
    statItem: {
      alignItems: 'center',
    },
    statNumber: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.primary,
    },
    statLabel: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginTop: 5,
    },
  });

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
          <Card style={styles.statsContainer}>
            <Title style={styles.statsTitle}>System Status</Title>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>✅</Text>
                <Text style={styles.statLabel}>Online</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>🔒</Text>
                <Text style={styles.statLabel}>Secure</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>📱</Text>
                <Text style={styles.statLabel}>Mobile</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>⚡</Text>
                <Text style={styles.statLabel}>Fast</Text>
              </View>
            </View>
          </Card>

          <Title style={{ color: theme.colors.text, marginBottom: 15 }}>
            Advanced Features
          </Title>

          <View style={styles.featuresGrid}>
            {features.map((feature, index) => (
              <Card key={index} style={styles.featureCard}>
                <Card.Content>
                  <Ionicons
                    name={feature.icon as any}
                    size={32}
                    color={feature.color}
                    style={styles.featureIcon}
                  />
                  <Text style={styles.featureTitle}>{feature.title}</Text>
                  <Text style={styles.featureDescription}>
                    {feature.description}
                  </Text>
                </Card.Content>
              </Card>
            ))}
          </View>

          <View style={styles.actionButtons}>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Chat' as never)}
              style={[styles.button, { backgroundColor: theme.colors.primary }]}
              icon="chat"
            >
              Start New Chat
            </Button>

            <Button
              mode="outlined"
              onPress={() => navigation.navigate('Conversations' as never)}
              style={styles.button}
              icon="list"
            >
              View Conversations
            </Button>

            <Button
              mode="outlined"
              onPress={() => navigation.navigate('Settings' as never)}
              style={styles.button}
              icon="settings"
            >
              Settings
            </Button>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default HomeScreen;
