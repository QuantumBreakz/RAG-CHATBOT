import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { Card } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useChat } from '../contexts/ChatContext';

const AnalyticsScreen: React.FC = () => {
  const { theme } = useTheme();
  const { sessions } = useChat();

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
      marginBottom: 15,
    },
    statsCard: {
      backgroundColor: theme.colors.surface,
      marginBottom: 15,
    },
    statsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
    },
    statItem: {
      width: '48%',
      alignItems: 'center',
      padding: 15,
      backgroundColor: theme.colors.background,
      borderRadius: 8,
      marginBottom: 10,
    },
    statNumber: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.primary,
      marginBottom: 5,
    },
    statLabel: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      textAlign: 'center',
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
  });

  // Calculate analytics
  const totalConversations = sessions.length;
  const totalMessages = sessions.reduce((acc, session) => acc + session.messages.length, 0);
  const averageMessagesPerConversation = totalConversations > 0 ? (totalMessages / totalConversations).toFixed(1) : '0';
  const recentConversations = sessions.filter(session => {
    const sessionDate = new Date(session.updatedAt);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return sessionDate > weekAgo;
  }).length;

  const features = [
    { icon: 'chatbubbles', text: 'Agentic RAG processing', status: 'Active' },
    { icon: 'document-text', text: 'Multi-OCR analysis', status: 'Active' },
    { icon: 'globe', text: 'Web search integration', status: 'Available' },
    { icon: 'shield-checkmark', text: 'Anti-hallucination', status: 'Active' },
    { icon: 'language', text: 'Cross-language support', status: 'Available' },
    { icon: 'layers', text: 'Template chunking', status: 'Active' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Analytics</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Usage Statistics</Text>
          <Card style={styles.statsCard}>
            <Card.Content>
              <View style={styles.statsGrid}>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{totalConversations}</Text>
                  <Text style={styles.statLabel}>Total Conversations</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{totalMessages}</Text>
                  <Text style={styles.statLabel}>Total Messages</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{averageMessagesPerConversation}</Text>
                  <Text style={styles.statLabel}>Avg Messages/Conv</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{recentConversations}</Text>
                  <Text style={styles.statLabel}>This Week</Text>
                </View>
              </View>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Feature Status</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Advanced AI Features</Text>
              <Text style={styles.infoText}>
                Current status of advanced features in your mobile app:
              </Text>
              <View style={styles.featureList}>
                {features.map((feature, index) => (
                  <View key={index} style={styles.featureItem}>
                    <Ionicons
                      name={feature.icon as any}
                      size={20}
                      color={feature.status === 'Active' ? theme.colors.success : theme.colors.warning}
                      style={styles.featureIcon}
                    />
                    <Text style={styles.featureText}>{feature.text}</Text>
                    <Text style={[styles.featureText, { color: feature.status === 'Active' ? theme.colors.success : theme.colors.warning }]}>
                      {feature.status}
                    </Text>
                  </View>
                ))}
              </View>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Insights</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Mobile App Performance</Text>
              <Text style={styles.infoText}>
                • Optimized for mobile devices{'\n'}
                • Offline-first architecture{'\n'}
                • Local data storage{'\n'}
                • Fast response times{'\n'}
                • Battery-efficient operations
              </Text>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data Privacy</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Your Data is Secure</Text>
              <Text style={styles.infoText}>
                • All conversations stored locally{'\n'}
                • No data sent to external servers{'\n'}
                • End-to-end encryption{'\n'}
                • Complete privacy control{'\n'}
                • GDPR compliant
              </Text>
            </Card.Content>
          </Card>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default AnalyticsScreen;
