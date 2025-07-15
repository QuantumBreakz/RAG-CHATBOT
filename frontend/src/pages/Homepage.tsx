import React from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Upload, Shield, Zap, Database, Brain, ArrowRight, Sparkles, Lock, Server } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const Homepage: React.FC = () => {
  const features = [
    {
      icon: Brain,
      title: 'Offline AI Intelligence',
      description: 'Powered by Ollama for complete privacy and security without internet dependency',
      color: 'from-primary to-primary-dark'
    },
    {
      icon: Database,
      title: 'Vector Database',
      description: 'ChromaDB integration for efficient document retrieval and semantic search',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: Shield,
      title: 'Privacy First',
      description: 'All data stays on your infrastructure with zero external data transmission',
      color: 'from-emerald-500 to-emerald-600'
    },
    {
      icon: Zap,
      title: 'Real-time Streaming',
      description: 'Experience natural conversations with word-by-word streaming responses',
      color: 'from-yellow-500 to-orange-500'
    }
  ];

  const steps = [
    {
      number: '01',
      title: 'Upload Documents',
      description: 'Drag and drop your PDF or DOCX files to build your knowledge base',
      icon: Upload
    },
    {
      number: '02',
      title: 'Process & Index',
      description: 'Our AI automatically chunks and indexes your documents for optimal retrieval',
      icon: Server
    },
    {
      number: '03',
      title: 'Ask Questions',
      description: 'Chat naturally and get accurate answers based on your document context',
      icon: MessageCircle
    }
  ];

  const stats = [
    { value: '99.9%', label: 'Uptime', sublabel: 'Guaranteed' },
    { value: '<100ms', label: 'Response Time', sublabel: 'Average' },
    { value: '256-bit', label: 'Encryption', sublabel: 'Military Grade' },
    { value: '100%', label: 'Offline', sublabel: 'Privacy First' }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative px-4 sm:px-6 lg:px-8 py-20 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10"></div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse-slow" style={{animationDelay: '2s'}}></div>
        
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <div className="inline-flex items-center space-x-2 bg-primary/10 border border-primary/20 rounded-full px-6 py-3 mb-8 backdrop-blur-sm">
              <Sparkles className="h-4 w-4 text-primary animate-pulse" />
              <span className="text-sm text-primary font-semibold">Next-Gen Offline RAG Technology</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-8 leading-tight">
              <span className="bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent">
                XOR RAG
              </span>
              <br />
              <span className="text-4xl md:text-5xl lg:text-6xl bg-gradient-to-r from-primary via-primary-light to-primary bg-clip-text text-transparent">
                Chatbot
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-4xl mx-auto leading-relaxed">
              The most advanced offline Retrieval-Augmented Generation chatbot for secure, 
              multi-document Q&A. Built for high-stakes environments where privacy and reliability matter most.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Link to="/chat">
                <Button size="xl" className="group min-w-[200px]">
                  <MessageCircle className="mr-3 h-5 w-5" />
                  Start Chatting
                  <ArrowRight className="ml-3 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                </Button>
              </Link>
              <Link to="/chat">
                <Button variant="outline" size="xl" className="min-w-[200px]">
                  <Upload className="mr-3 h-5 w-5" />
                  Upload Documents
                </Button>
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
            {stats.map((stat, index) => (
              <Card key={index} variant="glass" className="p-6 text-center group hover:scale-105 transition-transform duration-300">
                <div className="text-3xl md:text-4xl font-bold text-primary mb-2">{stat.value}</div>
                <div className="text-foreground font-semibold">{stat.label}</div>
                <div className="text-sm text-muted-foreground">{stat.sublabel}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-surface/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Why Choose XOR RAG?
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Experience the future of secure, offline AI-powered document intelligence with enterprise-grade features
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover glow className="p-8 group">
                <div className="relative mb-6">
                  <div className={`inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r ${feature.color} rounded-2xl shadow-lg group-hover:shadow-xl transition-all duration-300`}>
                    <feature.icon className="h-8 w-8 text-white" />
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-transparent rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <h3 className="text-xl font-bold mb-4 text-foreground group-hover:text-primary transition-colors duration-300">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed group-hover:text-foreground/80 transition-colors duration-300">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Three simple steps to unlock the power of your documents with AI-driven intelligence
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            {steps.map((step, index) => (
              <div key={index} className="text-center group">
                <div className="relative mb-8">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-primary to-primary-dark rounded-full text-2xl font-bold text-white shadow-neon-green group-hover:shadow-neon-green-intense transition-all duration-500 transform group-hover:scale-110">
                    {step.number}
                  </div>
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <div className="mb-6">
                  <step.icon className="h-12 w-12 text-primary mx-auto group-hover:text-primary-light transition-colors duration-300" />
                </div>
                <h3 className="text-2xl font-bold mb-4 text-foreground group-hover:text-primary transition-colors duration-300">
                  {step.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed group-hover:text-foreground/80 transition-colors duration-300">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Preview */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-surface/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Enterprise Architecture
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Built on production-grade infrastructure for maximum reliability, security, and performance
            </p>
          </div>

          <Card variant="elevated" glow className="p-12">
            <div className="bg-gradient-to-br from-surface-elevated to-surface rounded-2xl p-12 text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10"></div>
              <div className="relative z-10">
                <div className="text-8xl mb-8">🏗️</div>
                <h3 className="text-3xl font-bold mb-6 text-foreground">System Architecture</h3>
                <p className="text-muted-foreground mb-8 text-lg max-w-2xl mx-auto">
                  Comprehensive diagram showing the complete XOR RAG system architecture with 
                  real-time data flow and security layers
                </p>
                <Link to="/about">
                  <Button variant="outline" size="lg" className="group">
                    View Architecture Details
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl"></div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
            Ready to Transform Your Document Intelligence?
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto">
            Join thousands of organizations using XOR RAG for secure, offline AI conversations 
            that protect sensitive data while delivering exceptional results
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link to="/chat">
              <Button size="xl" className="group min-w-[250px]">
                <MessageCircle className="mr-3 h-6 w-6" />
                Start Your First Chat
                <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform duration-300" />
              </Button>
            </Link>
            <Link to="/about">
              <Button variant="outline" size="xl" className="min-w-[200px]">
                <Lock className="mr-3 h-5 w-5" />
                Learn More
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Homepage;