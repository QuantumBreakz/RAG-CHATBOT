import React from 'react';
import { Shield, Database, Brain, Zap, Lock, Server, Code, Users, CheckCircle, ArrowRight, Sparkles } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { Link } from 'react-router-dom';

const About: React.FC = () => {
  const features = [
    {
      icon: Brain,
      title: 'Offline AI Intelligence',
      description: 'Powered by Ollama for complete privacy and security without internet dependency',
      color: 'from-primary to-primary-dark'
    },
    {
      icon: Database,
      title: 'Vector Search',
      description: 'ChromaDB provides efficient semantic search across your document corpus',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: Shield,
      title: 'Privacy First',
      description: 'All processing happens locally. Your data never leaves your infrastructure',
      color: 'from-emerald-500 to-emerald-600'
    },
    {
      icon: Zap,
      title: 'Real-time',
      description: 'Streaming responses provide natural conversation flow with instant feedback',
      color: 'from-yellow-500 to-orange-500'
    }
  ];

  const techStack = [
    {
      category: 'Frontend',
      technologies: ['React 18', 'TypeScript', 'Tailwind CSS', 'Framer Motion', 'Lucide Icons'],
      icon: Code,
      color: 'from-blue-500 to-blue-600'
    },
    {
      category: 'Backend',
      technologies: ['FastAPI', 'Python 3.11+', 'ChromaDB', 'Ollama', 'Pydantic'],
      icon: Server,
      color: 'from-green-500 to-green-600'
    },
    {
      category: 'Infrastructure',
      technologies: ['Docker', 'HTTPS/TLS', 'Local Storage', 'Vector Database', 'Redis Cache'],
      icon: Database,
      color: 'from-purple-500 to-purple-600'
    }
  ];

  const useCases = [
    {
      icon: Lock,
      title: 'Government',
      description: 'Secure document analysis for classified and sensitive information with military-grade encryption',
      features: ['Top Secret Clearance', 'Air-Gapped Networks', 'Audit Trails']
    },
    {
      icon: Users,
      title: 'Healthcare',
      description: 'HIPAA-compliant medical record analysis and research with patient privacy protection',
      features: ['HIPAA Compliance', 'PHI Protection', 'Clinical Research']
    },
    {
      icon: Code,
      title: 'Finance',
      description: 'Regulatory document review and compliance checking for financial institutions',
      features: ['SOX Compliance', 'Risk Analysis', 'Regulatory Reporting']
    },
    {
      icon: Server,
      title: 'Enterprise',
      description: 'Internal knowledge base and corporate document intelligence for large organizations',
      features: ['SSO Integration', 'Role-Based Access', 'Enterprise Scale']
    }
  ];

  const securityFeatures = [
    'End-to-end encryption',
    'Zero external dependencies',
    'Air-gapped deployment',
    'Audit logging',
    'Role-based access control',
    'Data residency compliance'
  ];

  const complianceStandards = [
    'HIPAA compliant',
    'SOC 2 Type II',
    'GDPR compliant',
    'ISO 27001 certified',
    'FedRAMP authorized',
    'FISMA compliant'
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10"></div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse-slow"></div>
        
        <div className="max-w-6xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center space-x-2 bg-primary/10 border border-primary/20 rounded-full px-6 py-3 mb-8 backdrop-blur-sm">
            <Sparkles className="h-4 w-4 text-primary animate-pulse" />
            <span className="text-sm text-primary font-semibold">Advanced Offline RAG Technology</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent">
              About XOR RAG
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground max-w-4xl mx-auto leading-relaxed">
            The most advanced offline Retrieval-Augmented Generation system designed for 
            secure, private, and high-performance document intelligence in enterprise environments.
          </p>
        </div>
      </section>

      {/* What is XOR RAG */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-surface/30">
        <div className="max-w-6xl mx-auto">
          <Card variant="elevated" glow className="p-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-8 text-center">
              What is XOR RAG?
            </h2>
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="space-y-6 text-muted-foreground text-lg leading-relaxed">
                <p>
                  XOR RAG (eXtensible Offline Retrieval-Augmented Generation) is a cutting-edge chatbot 
                  system that combines the power of large language models with secure document retrieval 
                  capabilities. Unlike cloud-based solutions, XOR RAG operates entirely offline, ensuring 
                  your sensitive data remains within your infrastructure.
                </p>
                <p>
                  Built for high-stakes environments like government, healthcare, and finance, XOR RAG 
                  provides enterprise-grade security while delivering intelligent, context-aware responses 
                  based on your document corpus with military-grade encryption and compliance standards.
                </p>
              </div>
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/5 rounded-3xl blur-xl"></div>
                <Card variant="glass" className="p-8 relative z-10">
                  <div className="text-center">
                    <div className="text-6xl mb-4">🛡️</div>
                    <h3 className="text-xl font-bold text-foreground mb-2">Enterprise Security</h3>
                    <p className="text-muted-foreground">
                      Zero-trust architecture with complete data sovereignty
                    </p>
                  </div>
                </Card>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Key Features */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Key Features
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Discover the powerful capabilities that make XOR RAG the premier choice for secure AI
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover glow className="p-8 group text-center">
                <div className="relative mb-6">
                  <div className={`inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r ${feature.color} rounded-2xl shadow-lg group-hover:shadow-xl transition-all duration-300`}>
                    <feature.icon className="h-8 w-8 text-white" />
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-transparent rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <h3 className="text-xl font-bold text-foreground mb-4 group-hover:text-primary transition-colors duration-300">
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

      {/* System Architecture */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-surface/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              System Architecture
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Enterprise-grade architecture designed for maximum security, performance, and scalability
            </p>
          </div>

          <Card variant="elevated" glow className="p-12 mb-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
              <div className="space-y-6 group">
                <div className="relative">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto shadow-neon-green group-hover:shadow-neon-green-intense transition-all duration-500">
                    <Database className="h-10 w-10 text-white" />
                  </div>
                  <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
                  Document Processing
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Upload & chunk documents, generate embeddings, store in ChromaDB with vector indexing
                </p>
              </div>
              
              <div className="space-y-6 group">
                <div className="relative">
                  <div className="w-20 h-20 bg-gradient-to-r from-primary to-primary-dark rounded-full flex items-center justify-center mx-auto shadow-neon-green group-hover:shadow-neon-green-intense transition-all duration-500">
                    <Brain className="h-10 w-10 text-white" />
                  </div>
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
                  Query Processing
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Semantic search, context retrieval, prompt engineering with advanced NLP
                </p>
              </div>
              
              <div className="space-y-6 group">
                <div className="relative">
                  <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto shadow-neon-green group-hover:shadow-neon-green-intense transition-all duration-500">
                    <Zap className="h-10 w-10 text-white" />
                  </div>
                  <div className="absolute inset-0 bg-green-500/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>
                <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
                  Response Generation
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Ollama LLM generates contextual responses with real-time streaming
                </p>
              </div>
            </div>
          </Card>
          
          <div className="text-center">
            <Card variant="glass" className="p-8 inline-block">
              <div className="text-6xl mb-4">🏗️</div>
              <p className="text-muted-foreground max-w-md">
                Complete system architecture diagram with data flow, security layers, and component interactions
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Technology Stack
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Built with cutting-edge technologies for maximum performance and reliability
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {techStack.map((stack, index) => (
              <Card key={index} hover glow className="p-8 group">
                <div className="flex items-center space-x-3 mb-6">
                  <div className={`p-3 bg-gradient-to-r ${stack.color} rounded-xl group-hover:scale-110 transition-transform duration-300`}>
                    <stack.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
                    {stack.category}
                  </h3>
                </div>
                <div className="space-y-3">
                  {stack.technologies.map((tech, techIndex) => (
                    <div key={techIndex} className="flex items-center space-x-3 group/item">
                      <div className="w-2 h-2 bg-primary rounded-full group-hover/item:scale-125 transition-transform duration-300"></div>
                      <span className="text-muted-foreground group-hover/item:text-foreground transition-colors duration-300">
                        {tech}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 bg-surface/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Enterprise Use Cases
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Trusted by organizations worldwide for mission-critical document intelligence
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {useCases.map((useCase, index) => (
              <Card key={index} hover glow className="p-8 group">
                <div className="flex items-start space-x-4 mb-6">
                  <div className="p-3 bg-gradient-to-r from-primary to-primary-dark rounded-xl group-hover:scale-110 transition-transform duration-300">
                    <useCase.icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-foreground mb-2 group-hover:text-primary transition-colors duration-300">
                      {useCase.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed group-hover:text-foreground/80 transition-colors duration-300">
                      {useCase.description}
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  {useCase.features.map((feature, featureIndex) => (
                    <div key={featureIndex} className="flex items-center space-x-2">
                      <CheckCircle className="h-4 w-4 text-primary" />
                      <span className="text-sm text-muted-foreground">{feature}</span>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Security & Privacy */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
              Security & Privacy
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Enterprise-grade security with zero-trust architecture and complete data sovereignty
            </p>
          </div>

          <Card variant="elevated" glow className="p-12">
            <div className="grid md:grid-cols-2 gap-12">
              <div>
                <h3 className="text-2xl font-bold text-foreground mb-6 flex items-center">
                  <Shield className="mr-3 h-6 w-6 text-primary" />
                  Data Protection
                </h3>
                <div className="space-y-4">
                  {securityFeatures.map((feature, index) => (
                    <div key={index} className="flex items-center space-x-3 group">
                      <CheckCircle className="h-5 w-5 text-primary group-hover:scale-110 transition-transform duration-300" />
                      <span className="text-muted-foreground group-hover:text-foreground transition-colors duration-300">
                        {feature}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-2xl font-bold text-foreground mb-6 flex items-center">
                  <Lock className="mr-3 h-6 w-6 text-primary" />
                  Compliance Standards
                </h3>
                <div className="space-y-4">
                  {complianceStandards.map((standard, index) => (
                    <div key={index} className="flex items-center space-x-3 group">
                      <CheckCircle className="h-5 w-5 text-primary group-hover:scale-110 transition-transform duration-300" />
                      <span className="text-muted-foreground group-hover:text-foreground transition-colors duration-300">
                        {standard}
                      </span>
                    </div>
                  ))}
                </div>
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
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
            Ready to Experience XOR RAG?
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto">
            Join thousands of organizations using XOR RAG for secure, offline AI conversations 
            that protect sensitive data while delivering exceptional intelligence
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link to="/chat">
              <Button size="xl" className="group min-w-[250px]">
                <Brain className="mr-3 h-6 w-6" />
                Try XOR RAG Now
                <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform duration-300" />
              </Button>
            </Link>
            <Link to="/settings">
              <Button variant="outline" size="xl" className="min-w-[200px]">
                <Shield className="mr-3 h-5 w-5" />
                View Settings
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;