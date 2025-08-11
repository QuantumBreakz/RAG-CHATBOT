import React, { useEffect, useState } from 'react';
import { Save, RotateCcw, Database, Brain, Settings as SettingsIcon, Palette, Shield, Zap, Download, Trash2, Globe, Server } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { useChat } from '../contexts/ChatContext';
import { useTheme } from '../contexts/ThemeContext';
import { logger } from '../lib/logger';

const Settings: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { clearHistory } = useChat();
  
  // Settings state
  const [modelName, setModelName] = useState('mistral:latest');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  
  // Online model state
  const [useOnlineModel, setUseOnlineModel] = useState(false);
  const [onlineProvider, setOnlineProvider] = useState('openai');
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [currentProvider, setCurrentProvider] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<{[key: string]: boolean}>({});
  
  // Logs state
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Load settings on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('xor-rag-settings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        setModelName(settings.modelName || 'mistral:latest');
        setTemperature(settings.temperature ?? 0.7);
        setMaxTokens(settings.maxTokens ?? 1000);
        setStreamingEnabled(settings.streamingEnabled !== false);
        setAutoSave(settings.autoSave !== false);
        setUseOnlineModel(settings.useOnlineModel || false);
        setOnlineProvider(settings.onlineProvider || 'openai');
      } catch (error) {
        logger.error('Failed to load settings:', error);
      }
    }
    
    // Load available online providers
    loadAvailableProviders();
  }, []);

  // Auto-save settings when they change
  useEffect(() => {
    if (autoSave) {
      saveSettings();
    }
  }, [modelName, temperature, maxTokens, streamingEnabled, useOnlineModel, onlineProvider, autoSave]);

  const saveSettings = () => {
    const settings = {
      modelName,
      temperature,
      maxTokens,
      streamingEnabled,
      autoSave,
      useOnlineModel,
      onlineProvider
    };
    localStorage.setItem('xor-rag-settings', JSON.stringify(settings));
    logger.info('Settings saved');
  };

  const loadAvailableProviders = async () => {
    try {
      const response = await fetch('/api/models/online/available');
      const data = await response.json();
      setAvailableProviders(data.providers || []);
      setCurrentProvider(data.current_provider);
      
      // Test provider status
      const status: {[key: string]: boolean} = {};
      for (const provider of data.providers || []) {
        const testResponse = await fetch('/api/models/online/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: `provider=${provider}`
        });
        const testData = await testResponse.json();
        status[provider] = testData.working || false;
      }
      setProviderStatus(status);
    } catch (error) {
      logger.error('Failed to load available providers:', error);
    }
  };

  const setOnlineModel = async (provider: string) => {
    try {
      const response = await fetch('/api/models/online/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `provider=${provider}`
      });
      const data = await response.json();
      if (data.status === 'success') {
        setOnlineProvider(provider);
        setCurrentProvider(provider);
        logger.info(`Switched to ${provider} provider`);
      } else {
        logger.error(`Failed to switch to ${provider}:`, data.message);
      }
    } catch (error) {
      logger.error('Failed to set online model:', error);
    }
  };

  const handleResetKB = async () => {
    if (window.confirm('Are you sure you want to reset the knowledge base? This will delete all uploaded documents.')) {
      try {
        const response = await fetch('/reset_kb', { method: 'POST' });
        if (response.ok) {
          logger.info('Knowledge base reset successfully');
        } else {
          logger.error('Failed to reset knowledge base');
        }
      } catch (error) {
        logger.error('Error resetting knowledge base:', error);
      }
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history?')) {
      clearHistory();
      logger.info('Chat history cleared');
    }
  };

  const handleDownloadLogs = () => {
    logger.downloadLogs();
  };

  const handleClearLogs = () => {
    logger.clearLogs();
    setLogs([]);
  };

  const handleViewLogs = () => {
    setLogs(logger.getLogs());
    setShowLogs(!showLogs);
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center gap-3 mb-8">
        <SettingsIcon className="w-8 h-8 text-blue-600" />
        <h1 className="text-3xl font-bold">Settings</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Configuration */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Model Configuration</h2>
          </div>
          
          {/* Model Type Toggle */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Model Type</label>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setUseOnlineModel(false)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  !useOnlineModel 
                    ? 'bg-blue-600 text-white border-blue-600' 
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                }`}
              >
                <Server className="w-4 h-4 inline mr-2" />
                Local (Offline)
              </button>
              <button
                onClick={() => setUseOnlineModel(true)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  useOnlineModel 
                    ? 'bg-green-600 text-white border-green-600' 
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                }`}
              >
                <Globe className="w-4 h-4 inline mr-2" />
                Online
              </button>
            </div>
          </div>

          {!useOnlineModel ? (
            /* Local Model Settings */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Local Model</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., mistral:latest"
                />
              </div>
            </div>
          ) : (
            /* Online Model Settings */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Online Provider</label>
                <select
                  value={onlineProvider}
                  onChange={(e) => setOnlineProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {availableProviders.map(provider => (
                    <option key={provider} value={provider}>
                      {provider.charAt(0).toUpperCase() + provider.slice(1)}
                      {providerStatus[provider] ? ' ✅' : ' ❌'}
                    </option>
                  ))}
                </select>
                {availableProviders.length === 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    No online providers available. Add API keys to your .env file.
                  </p>
                )}
              </div>
              
              {currentProvider && (
                <div className="text-sm text-gray-600">
                  Current provider: <span className="font-medium">{currentProvider}</span>
                </div>
              )}
            </div>
          )}

          {/* Common Model Settings */}
          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Temperature</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Focused (0)</span>
                <span>{temperature}</span>
                <span>Creative (2)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="streaming"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="streaming" className="text-sm font-medium">
                Enable Streaming Responses
              </label>
            </div>
          </div>
        </Card>

        {/* System Settings */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-green-600" />
            <h2 className="text-xl font-semibold">System Settings</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoSave"
                checked={autoSave}
                onChange={(e) => setAutoSave(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="autoSave" className="text-sm font-medium">
                Auto-save Settings
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="darkMode"
                checked={theme === 'dark'}
                onChange={toggleTheme}
                className="mr-2"
              />
              <label htmlFor="darkMode" className="text-sm font-medium">
                Dark Mode
              </label>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <Button
              onClick={handleClearHistory}
              variant="outline"
              className="w-full"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear Chat History
            </Button>

            <Button
              onClick={handleResetKB}
              variant="outline"
              className="w-full"
            >
              <Database className="w-4 h-4 mr-2" />
              Reset Knowledge Base
            </Button>
          </div>
        </Card>

        {/* System Logs */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-yellow-600" />
            <h2 className="text-xl font-semibold">System Logs</h2>
          </div>

          <div className="space-y-3">
            <Button
              onClick={handleViewLogs}
              variant="outline"
              className="w-full"
            >
              {showLogs ? 'Hide' : 'View'} System Logs
            </Button>

            {showLogs && (
              <div className="mt-4">
                <div className="bg-gray-100 rounded-lg p-4 max-h-64 overflow-y-auto">
                  {logs.length > 0 ? (
                    logs.map((log, index) => (
                      <div key={index} className="text-sm font-mono mb-1">
                        {log}
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500">No logs available</p>
                  )}
                </div>
                
                <div className="flex gap-2 mt-3">
                  <Button
                    onClick={handleDownloadLogs}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Download
                  </Button>
                  <Button
                    onClick={handleClearLogs}
                    variant="outline"
                    size="sm"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Clear
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Settings;