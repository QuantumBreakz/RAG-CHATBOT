import React, { useState, createContext, useContext } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider, DefaultTheme, DarkTheme } from 'react-native-paper';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import ChatScreen from './src/screens/ChatScreen';
import ConversationManagerScreen from './src/screens/ConversationManagerScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import AboutScreen from './src/screens/AboutScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import MonitoringScreen from './src/screens/MonitoringScreen';

// Import contexts
import { ThemeProvider } from './src/contexts/ThemeContext';
import { ChatProvider } from './src/contexts/ChatContext';

// Global Loading Context
const LoadingContext = createContext<{ loading: boolean; setLoading: (v: boolean) => void }>({ 
  loading: false, 
  setLoading: () => {} 
});
export const useGlobalLoading = () => useContext(LoadingContext);

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Bottom Tab Navigator
function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'Home') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Chat') {
            iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
          } else if (route.name === 'Conversations') {
            iconName = focused ? 'list' : 'list-outline';
          } else if (route.name === 'Settings') {
            iconName = focused ? 'settings' : 'settings-outline';
          } else {
            iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Chat" component={ChatScreen} />
      <Tab.Screen name="Conversations" component={ConversationManagerScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

// Main Stack Navigator
function StackNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#007AFF',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen 
        name="MainTabs" 
        component={TabNavigator} 
        options={{ headerShown: false }}
      />
      <Stack.Screen name="About" component={AboutScreen} />
      <Stack.Screen name="Analytics" component={AnalyticsScreen} />
      <Stack.Screen name="Monitoring" component={MonitoringScreen} />
    </Stack.Navigator>
  );
}

function App() {
  const [loading, setLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const theme = isDarkMode ? DarkTheme : DefaultTheme;

  return (
    <LoadingContext.Provider value={{ loading, setLoading }}>
      <PaperProvider theme={theme}>
        <ThemeProvider>
          <ChatProvider>
            <NavigationContainer>
              <StatusBar style={isDarkMode ? 'light' : 'dark'} />
              <StackNavigator />
            </NavigationContainer>
          </ChatProvider>
        </ThemeProvider>
      </PaperProvider>
    </LoadingContext.Provider>
  );
}

export default App;
