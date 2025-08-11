# XOR RAG Chatbot Mobile App

A React Native mobile application for the XOR RAG Chatbot, providing secure, offline-first access to advanced AI capabilities on mobile devices.

## 🚀 Features

### Core Functionality
- **Chat Interface**: Real-time conversation with AI assistant
- **Conversation Management**: Create, view, edit, and delete conversations
- **Document Upload**: Upload and process documents directly from mobile
- **Settings Management**: Configure app preferences and API settings
- **Dark/Light Theme**: Toggle between themes with persistent preferences

### Advanced AI Features
- **Agentic RAG**: Multi-agent architecture with intelligent query processing
- **Multi-OCR**: Advanced document processing with layout analysis
- **Web Search**: Real-time information retrieval via Tavily API
- **Anti-Hallucination**: Comprehensive fact verification system
- **Cross-Language**: Multi-language support for 11+ languages
- **Template Chunking**: Intelligent document processing strategies

### Mobile-Specific Features
- **Offline-First**: Works without internet connection
- **Local Storage**: All data stored locally on device
- **Responsive Design**: Optimized for all screen sizes
- **Touch-Friendly**: Intuitive mobile interface
- **Performance Optimized**: Battery and memory efficient

## 📱 Screenshots

The app includes the following main screens:
- **Home**: Overview of features and system status
- **Chat**: Main conversation interface with AI
- **Conversations**: Manage and organize chat history
- **Settings**: Configure app preferences and system settings
- **Analytics**: View usage statistics and performance metrics
- **Monitoring**: Real-time system health and status
- **About**: Information about the app and its features

## 🛠️ Technology Stack

### Frontend
- **React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe development
- **React Navigation**: Navigation and routing
- **React Native Paper**: Material Design components
- **Expo**: Development and deployment platform

### State Management
- **React Context**: Global state management
- **AsyncStorage**: Local data persistence
- **Custom Hooks**: Reusable logic and state

### UI/UX
- **Material Design**: Consistent design system
- **Ionicons**: Comprehensive icon library
- **Responsive Layout**: Adaptive to different screen sizes
- **Theme Support**: Dark and light mode

## 📦 Installation

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development)
- Android Studio (for Android development)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd XORRAGMobile
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Run on device/simulator**
   ```bash
   # For iOS
   npm run ios
   
   # For Android
   npm run android
   
   # For web
   npm run web
   ```

## 🔧 Configuration

### Environment Setup
The app uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# API Configuration
API_URL=http://localhost:8000

# App Configuration
APP_NAME=XOR RAG Chatbot
APP_VERSION=1.0.0

# Feature Flags
ENABLE_WEB_SEARCH=true
ENABLE_OCR=true
ENABLE_AGENTIC_RAG=true
```

### Backend Connection
To connect to your backend API:

1. Update the API URL in Settings
2. Ensure your backend is running and accessible
3. Test the connection in the Monitoring screen

## 📱 Usage

### Getting Started
1. **Launch the app** and navigate to the Home screen
2. **Start a conversation** by tapping "Start New Chat"
3. **Ask questions** or upload documents for processing
4. **Manage conversations** in the Conversations tab
5. **Configure settings** in the Settings screen

### Chat Interface
- **Send messages** by typing and tapping the send button
- **Upload documents** using the FAB (Floating Action Button)
- **View conversation history** in the chat timeline
- **Edit or delete messages** using the message actions

### Conversation Management
- **Create new conversations** from the Conversations screen
- **Search conversations** using the search bar
- **Rename conversations** by tapping the edit icon
- **Delete conversations** using the trash icon

### Settings
- **Toggle dark mode** for better viewing experience
- **Configure API settings** for backend connection
- **Adjust document processing** parameters
- **Manage app preferences** and notifications

## 🔒 Security & Privacy

### Data Protection
- **Local Storage**: All conversations stored locally on device
- **No External APIs**: No data sent to external services (except optional web search)
- **Encryption**: Data encrypted at rest
- **Privacy Control**: Complete control over your data

### Offline Operation
- **Works Offline**: Core functionality available without internet
- **Local Processing**: AI models run locally when possible
- **Sync When Online**: Optional synchronization with backend

## 🚀 Deployment

### Expo Build
```bash
# Build for iOS
expo build:ios

# Build for Android
expo build:android

# Build for web
expo build:web
```

### App Store Deployment
1. **Configure app.json** with your app details
2. **Build the app** using Expo or EAS Build
3. **Submit to stores** following platform guidelines

### Custom Backend Integration
To integrate with your custom backend:

1. **Update API endpoints** in the app configuration
2. **Implement authentication** if required
3. **Test all features** with your backend
4. **Deploy and monitor** app performance

## 🧪 Testing

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- ChatScreen.test.tsx
```

### Test Coverage
```bash
# Generate coverage report
npm test -- --coverage
```

## 📊 Analytics & Monitoring

### Built-in Analytics
- **Usage Statistics**: Track conversations and messages
- **Performance Metrics**: Monitor app performance
- **Feature Usage**: Track which features are used most
- **Error Tracking**: Monitor and report errors

### System Monitoring
- **Backend Status**: Monitor API connectivity
- **Database Health**: Check vector database status
- **LLM Status**: Monitor language model availability
- **Cache Performance**: Track Redis cache status

## 🔧 Development

### Project Structure
```
src/
├── components/          # Reusable UI components
├── contexts/           # React Context providers
├── screens/            # Main app screens
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── lib/                # Third-party library configurations
```

### Adding New Features
1. **Create new screen** in `src/screens/`
2. **Add navigation** in `App.tsx`
3. **Update types** in `src/types/`
4. **Add tests** for new functionality
5. **Update documentation**

### Code Style
- **TypeScript**: Use strict typing
- **ESLint**: Follow linting rules
- **Prettier**: Consistent code formatting
- **Comments**: Document complex logic

## 🤝 Contributing

### Development Workflow
1. **Fork the repository**
2. **Create feature branch**
3. **Make changes** following coding standards
4. **Add tests** for new functionality
5. **Submit pull request**

### Code Review
- **TypeScript**: Ensure proper typing
- **Performance**: Optimize for mobile
- **Accessibility**: Follow mobile accessibility guidelines
- **Testing**: Include unit and integration tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **React Native**: Cross-platform mobile development
- **Expo**: Development and deployment platform
- **React Navigation**: Navigation library
- **React Native Paper**: Material Design components
- **Ionicons**: Icon library

## 📞 Support

For support and questions:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the main project README
- **Community**: Join our development community

---

**Built with ❤️ using React Native and Expo**
