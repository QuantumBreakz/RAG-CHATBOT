import React, { useState } from 'react';
import { Save, RotateCcw, Database, Brain, Settings as SettingsIcon, Palette, Shield, Zap } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { useChat } from '../contexts/ChatContext';
import { useTheme } from '../contexts/ThemeContext';

const Settings: React.FC = () => {
  const { clearHistory } = useChat();
  const { theme, toggleTheme } = useTheme();
  
  const [settings, setSettings] = useState({
    modelName: 'llama2',
    chunkSize: 1000,
    chunkOverlap: 200,
    maxTokens: 4000,
    temperature: 0.7,
    cacheEnabled: true,
    cacheTTL: 3600,
    maxDocuments: 50,
    vectorDimensions: 1536,
    streamingEnabled: true,
    autoSave: true
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveBanner, setSaveBanner] = useState<string | null>(null);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    localStorage.setItem('xor-rag-settings', JSON.stringify(settings));
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    setSaveBanner('Settings saved successfully!');
    setTimeout(() => setSaveBanner(null), 2000);
  };

  const handleReset = () => {
    setSettings({
      modelName: 'llama2',
      chunkSize: 1000,
      chunkOverlap: 200,
      maxTokens: 4000,
      temperature: 0.7,
      cacheEnabled: true,
      cacheTTL: 3600,
      maxDocuments: 50,
      vectorDimensions: 1536,
      streamingEnabled: true,
      autoSave: true
    });
  };

  const settingSections = [
    {
      icon: Brain,
      title: 'Model Configuration',
      description: 'Configure AI model parameters and behavior',
      color: 'from-primary to-primary-dark'
    },
    {
      icon: Database,
      title: 'Vector Database',
      description: 'Manage document processing and retrieval settings',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: Zap,
      title: 'Performance',
      description: 'Optimize system performance and caching',
      color: 'from-yellow-500 to-orange-500'
    },
    {
      icon: Palette,
      title: 'Appearance',
      description: 'Customize the interface theme and layout',
      color: 'from-purple-500 to-pink-500'
    }
  ];

  return (
    <div className="min-h-screen bg-background p-4">
      {saveBanner && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-primary text-white px-6 py-2 rounded shadow-lg text-sm animate-fade-in">
          {saveBanner}
        </div>
      )}
      <div className="max-w-6xl mx-auto">
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
            Settings
          </h1>
          <p className="text-xl text-muted-foreground">
            Configure your XOR RAG chatbot preferences and system parameters
          </p>
        </div>

        <div className="grid gap-8">
          {/* Model Configuration */}
          <Card variant="elevated" glow className="p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-r from-primary to-primary-dark rounded-xl">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-foreground">Model Configuration</h2>
                <p className="text-muted-foreground">Configure AI model parameters and behavior</p>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Model Name
                </label>
                <select
                  value={settings.modelName}
                  onChange={(e) => handleSettingChange('modelName', e.target.value)}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                >
                  <option value="llama2">Llama 2 (7B)</option>
                  <option value="llama2:13b">Llama 2 (13B)</option>
                  <option value="codellama">Code Llama</option>
                  <option value="mistral">Mistral (7B)</option>
                  <option value="neural-chat">Neural Chat</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={settings.maxTokens}
                  onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                  min="1000"
                  max="8000"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Temperature: {settings.temperature}
                </label>
                <input
                  type="range"
                  value={settings.temperature}
                  onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                  className="w-full h-2 bg-surface-elevated rounded-lg appearance-none cursor-pointer slider"
                  min="0"
                  max="1"
                  step="0.1"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                  <span>Focused</span>
                  <span>Balanced</span>
                  <span>Creative</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Vector Database Configuration */}
          <Card variant="elevated" glow className="p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-foreground">Vector Database</h2>
                <p className="text-muted-foreground">Manage document processing and retrieval settings</p>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Chunk Size
                </label>
                <input
                  type="number"
                  value={settings.chunkSize}
                  onChange={(e) => handleSettingChange('chunkSize', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                  min="500"
                  max="2000"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Chunk Overlap
                </label>
                <input
                  type="number"
                  value={settings.chunkOverlap}
                  onChange={(e) => handleSettingChange('chunkOverlap', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                  min="0"
                  max="500"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Vector Dimensions
                </label>
                <input
                  type="number"
                  value={settings.vectorDimensions}
                  onChange={(e) => handleSettingChange('vectorDimensions', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                  min="384"
                  max="2048"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Max Documents
                </label>
                <input
                  type="number"
                  value={settings.maxDocuments}
                  onChange={(e) => handleSettingChange('maxDocuments', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300"
                  min="10"
                  max="100"
                />
              </div>
            </div>
          </Card>

          {/* Performance Settings */}
          <Card variant="elevated" glow className="p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-foreground">Performance</h2>
                <p className="text-muted-foreground">Optimize system performance and caching</p>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 bg-surface-elevated rounded-xl border border-border hover:border-primary/30 transition-all duration-300 cursor-pointer">
                  <div>
                    <span className="text-sm font-semibold text-foreground">Enable Cache</span>
                    <p className="text-xs text-muted-foreground">Cache responses for faster retrieval</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.cacheEnabled}
                      onChange={(e) => handleSettingChange('cacheEnabled', e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-12 h-6 rounded-full transition-all duration-300 ${
                      settings.cacheEnabled ? 'bg-primary' : 'bg-border'
                    }`}>
                      <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
                        settings.cacheEnabled ? 'translate-x-6' : 'translate-x-0.5'
                      } translate-y-0.5`}></div>
                    </div>
                  </div>
                </label>

                <label className="flex items-center justify-between p-4 bg-surface-elevated rounded-xl border border-border hover:border-primary/30 transition-all duration-300 cursor-pointer">
                  <div>
                    <span className="text-sm font-semibold text-foreground">Streaming</span>
                    <p className="text-xs text-muted-foreground">Enable real-time response streaming</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.streamingEnabled}
                      onChange={(e) => handleSettingChange('streamingEnabled', e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-12 h-6 rounded-full transition-all duration-300 ${
                      settings.streamingEnabled ? 'bg-primary' : 'bg-border'
                    }`}>
                      <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
                        settings.streamingEnabled ? 'translate-x-6' : 'translate-x-0.5'
                      } translate-y-0.5`}></div>
                    </div>
                  </div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-semibold text-foreground mb-3">
                  Cache TTL (seconds)
                </label>
                <input
                  type="number"
                  value={settings.cacheTTL}
                  onChange={(e) => handleSettingChange('cacheTTL', parseInt(e.target.value))}
                  className="w-full p-4 bg-surface-elevated border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300 disabled:opacity-50"
                  min="300"
                  max="86400"
                  disabled={!settings.cacheEnabled}
                />
              </div>
            </div>
          </Card>

          {/* Appearance Settings */}
          <Card variant="elevated" glow className="p-8">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
                <Palette className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-foreground">Appearance</h2>
                <p className="text-muted-foreground">Customize the interface theme and layout</p>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="flex items-center justify-between p-6 bg-surface-elevated rounded-xl border border-border">
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">Theme Mode</h3>
                    <p className="text-sm text-muted-foreground">Switch between dark and light themes</p>
                  </div>
                  <button
                    onClick={toggleTheme}
                    className={`relative inline-flex h-8 w-16 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background ${
                      theme === 'dark' ? 'bg-primary' : 'bg-border'
                    }`}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform duration-300 ${
                        theme === 'dark' ? 'translate-x-9' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="p-6 bg-surface-elevated rounded-xl border border-border">
                  <h3 className="text-lg font-semibold text-foreground mb-4">Theme Preview</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-4 h-4 bg-primary rounded-full"></div>
                      <span className="text-sm text-foreground">Primary Color</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-4 h-4 bg-surface-elevated border border-border rounded-full"></div>
                      <span className="text-sm text-foreground">Surface Color</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-4 h-4 bg-foreground rounded-full"></div>
                      <span className="text-sm text-foreground">Text Color</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <label className="flex items-center justify-between p-4 bg-surface-elevated rounded-xl border border-border hover:border-primary/30 transition-all duration-300 cursor-pointer">
                  <div>
                    <span className="text-sm font-semibold text-foreground">Auto Save</span>
                    <p className="text-xs text-muted-foreground">Automatically save settings changes</p>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.autoSave}
                      onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-12 h-6 rounded-full transition-all duration-300 ${
                      settings.autoSave ? 'bg-primary' : 'bg-border'
                    }`}>
                      <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
                        settings.autoSave ? 'translate-x-6' : 'translate-x-0.5'
                      } translate-y-0.5`}></div>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-8">
            {/* <Button
              onClick={clearHistory}
              variant="outline"
              className="text-red-500 border-red-500/30 hover:bg-red-500/10 hover:border-red-500/50 group"
            >
              <RotateCcw className="mr-2 h-4 w-4 group-hover:rotate-180 transition-transform duration-500" />
              Clear All Data
            </Button> */}
            
            <div className="flex space-x-4">
              <Button
                onClick={handleReset}
                variant="outline"
                className="group"
              >
                <Shield className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform duration-300" />
                Reset to Defaults
              </Button>
              <Button
                onClick={handleSave}
                isLoading={isSaving}
                className="group"
              >
                <Save className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform duration-300" />
                Save Settings
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;