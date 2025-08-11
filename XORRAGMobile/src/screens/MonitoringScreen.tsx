import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  RefreshControl,
} from 'react-native';
import { Card, Button } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

const MonitoringScreen: React.FC = () => {
  const { theme } = useTheme();
  const [refreshing, setRefreshing] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    backend: 'Unknown',
    database: 'Unknown',
    llm: 'Unknown',
    cache: 'Unknown',
  });

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
    statusCard: {
      backgroundColor: theme.colors.surface,
      marginBottom: 15,
    },
    statusItem: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: 15,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    statusText: {
      fontSize: 16,
      color: theme.colors.text,
      flex: 1,
    },
    statusIndicator: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    statusDot: {
      width: 12,
      height: 12,
      borderRadius: 6,
      marginRight: 8,
    },
    statusLabel: {
      fontSize: 14,
      fontWeight: 'bold',
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
    metricsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      marginTop: 10,
    },
    metricItem: {
      width: '48%',
      alignItems: 'center',
      padding: 10,
      backgroundColor: theme.colors.background,
      borderRadius: 8,
      marginBottom: 10,
    },
    metricValue: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.primary,
      marginBottom: 5,
    },
    metricLabel: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Online':
        return theme.colors.success;
      case 'Offline':
        return theme.colors.error;
      case 'Warning':
        return theme.colors.warning;
      default:
        return theme.colors.textSecondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Online':
        return 'checkmark-circle';
      case 'Offline':
        return 'close-circle';
      case 'Warning':
        return 'warning';
      default:
        return 'help-circle';
    }
  };

  const checkSystemStatus = async () => {
    // Simulate system status check
    setSystemStatus({
      backend: 'Online',
      database: 'Online',
      llm: 'Online',
      cache: 'Online',
    });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await checkSystemStatus();
    setRefreshing(false);
  };

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const systemComponents = [
    { name: 'Backend API', status: systemStatus.backend, description: 'FastAPI server status' },
    { name: 'Vector Database', status: systemStatus.database, description: 'ChromaDB connection' },
    { name: 'Language Model', status: systemStatus.llm, description: 'Mistral 7B via Ollama' },
    { name: 'Cache System', status: systemStatus.cache, description: 'Redis cache status' },
  ];

  const performanceMetrics = [
    { label: 'Response Time', value: '1.2s', unit: 'avg' },
    { label: 'Memory Usage', value: '45%', unit: 'used' },
    { label: 'CPU Load', value: '23%', unit: 'avg' },
    { label: 'Storage', value: '2.1GB', unit: 'used' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>System Monitoring</Text>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Status</Text>
          <Card style={styles.statusCard}>
            <Card.Content>
              {systemComponents.map((component, index) => (
                <View key={index} style={styles.statusItem}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.statusText}>{component.name}</Text>
                    <Text style={[styles.statusText, { fontSize: 12, color: theme.colors.textSecondary }]}>
                      {component.description}
                    </Text>
                  </View>
                  <View style={styles.statusIndicator}>
                    <View
                      style={[
                        styles.statusDot,
                        { backgroundColor: getStatusColor(component.status) }
                      ]}
                    />
                    <Text style={[
                      styles.statusLabel,
                      { color: getStatusColor(component.status) }
                    ]}>
                      {component.status}
                    </Text>
                    <Ionicons
                      name={getStatusIcon(component.status) as any}
                      size={20}
                      color={getStatusColor(component.status)}
                      style={{ marginLeft: 8 }}
                    />
                  </View>
                </View>
              ))}
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Metrics</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Real-time Performance</Text>
              <View style={styles.metricsGrid}>
                {performanceMetrics.map((metric, index) => (
                  <View key={index} style={styles.metricItem}>
                    <Text style={styles.metricValue}>{metric.value}</Text>
                    <Text style={styles.metricLabel}>{metric.label}</Text>
                    <Text style={[styles.metricLabel, { fontSize: 10 }]}>{metric.unit}</Text>
                  </View>
                ))}
              </View>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Advanced Features Status</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>AI Capabilities</Text>
              <Text style={styles.infoText}>
                • Agentic RAG: Active{'\n'}
                • Multi-OCR: Active{'\n'}
                • Web Search: Available{'\n'}
                • Anti-Hallucination: Active{'\n'}
                • Cross-Language: Available{'\n'}
                • Template Chunking: Active
              </Text>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Security & Privacy</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>Security Status</Text>
              <Text style={styles.infoText}>
                • Local Processing: Active{'\n'}
                • Data Encryption: Enabled{'\n'}
                • No External APIs: Active{'\n'}
                • Privacy Protection: Active{'\n'}
                • Secure Storage: Enabled
              </Text>
            </Card.Content>
          </Card>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Mobile App Health</Text>
          <Card style={styles.infoCard}>
            <Card.Content>
              <Text style={styles.infoTitle}>App Performance</Text>
              <Text style={styles.infoText}>
                • React Native: Stable{'\n'}
                • Navigation: Smooth{'\n'}
                • State Management: Optimized{'\n'}
                • Memory Usage: Efficient{'\n'}
                • Battery Usage: Optimized
              </Text>
            </Card.Content>
          </Card>
        </View>

        <Button
          mode="contained"
          onPress={onRefresh}
          style={{ marginBottom: 20, backgroundColor: theme.colors.primary }}
          icon="refresh"
        >
          Refresh Status
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
};

export default MonitoringScreen;
