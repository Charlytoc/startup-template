import { StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Button, Card, Text, useTheme } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import React from 'react';

export default function HomeScreen() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const theme = useTheme();

  const styles = createStyles(theme);

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
        <Text style={[styles.loadingText, { color: theme.colors.onBackground }]}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Card style={[styles.ctaCard, { backgroundColor: theme.colors.surface }]} elevation={2}>
        <Card.Content style={styles.ctaContent}>
          <Text variant="headlineSmall" style={[styles.title, { color: theme.colors.onSurface }]}>
            {isAuthenticated ? `Welcome, ${user?.first_name || user?.email}` : 'Reusable App Template'}
          </Text>
          <Text variant="bodyMedium" style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
            Minimal shell ready for auth, websocket notifications, and async agentic tasks.
          </Text>
          {isAuthenticated ? (
            <>
              <Button mode="contained" onPress={() => router.push('/(tabs)/agentic-chat')} style={styles.button}>
                Open Agentic Chat
              </Button>
              <Button mode="outlined" onPress={logout} style={styles.button}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button mode="contained" onPress={() => router.push('/auth/login')} style={styles.button}>
                Login
              </Button>
              <Button mode="outlined" onPress={() => router.push('/auth/signup')} style={styles.button}>
                Sign Up
              </Button>
            </>
          )}
        </Card.Content>
      </Card>
    </View>
  );
}

const createStyles = (theme: any) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    padding: 20,
    justifyContent: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
  loadingText: {
    fontSize: 16,
  },
  ctaCard: {
    borderRadius: 20,
  },
  ctaContent: {
    padding: 20,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  subtitle: {
    marginBottom: 20,
    lineHeight: 22,
  },
  button: {
    marginBottom: 10,
  },
});

