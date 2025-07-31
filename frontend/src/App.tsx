import React, { useState, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { ChatProvider } from './contexts/ChatContext';
import Header from './components/layout/Header';
import Homepage from './pages/Homepage';
import ChatInterface from './pages/ChatInterface';
import ConversationManager from './pages/ConversationManager';
import Settings from './pages/Settings';
import About from './pages/About';

// Global Loading Context
const LoadingContext = createContext<{ loading: boolean; setLoading: (v: boolean) => void }>({ loading: false, setLoading: () => {} });
export const useGlobalLoading = () => useContext(LoadingContext);

// Global Error Boundary
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: any }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }
  componentDidCatch(error: any, errorInfo: any) {
    // Log error if needed
    console.error(error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-red-50 text-red-800">
          <h1 className="text-3xl font-bold mb-4">Something went wrong.</h1>
          <pre className="bg-red-100 p-4 rounded-lg max-w-xl overflow-x-auto">{String(this.state.error)}</pre>
          <button className="mt-6 px-4 py-2 bg-primary text-white rounded" onClick={() => window.location.reload()}>Reload</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [loading, setLoading] = useState(false);
  return (
    <LoadingContext.Provider value={{ loading, setLoading }}>
      <ErrorBoundary>
    <ThemeProvider>
      <ChatProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <div className="min-h-screen bg-background text-foreground transition-all duration-500">
                {loading && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
                    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
            <Header />
            <main>
              <Routes>
                <Route path="/" element={<Homepage />} />
                <Route path="/chat" element={<ChatInterface />} />
                <Route path="/conversation-manager" element={<ConversationManager />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/about" element={<About />} />
              </Routes>
            </main>
          </div>
        </Router>
      </ChatProvider>
    </ThemeProvider>
      </ErrorBoundary>
    </LoadingContext.Provider>
  );
}

export default App;