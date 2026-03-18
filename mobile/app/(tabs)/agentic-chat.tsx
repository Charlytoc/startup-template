import React, { useEffect, useMemo, useState } from 'react';
import { FlatList, StyleSheet, View } from 'react-native';
import { Button, Card, Text, TextInput, useTheme } from 'react-native-paper';

import { useAuth } from '../../contexts/AuthContext';
import { apiInterface } from '../../services/api';
import { realtimeService } from '../../services/realtime';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created: string;
};

type RealtimeTransport = {
  message: {
    role: 'assistant';
    type: 'text';
    content: string;
    created: string;
  };
  timestamp: string;
};

export default function AgenticChatScreen() {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!user?.id) return;

    const setupRealtime = async () => {
      await realtimeService.connect();
      await realtimeService.joinUser(user.id);
    };

    const handleRealtime = (data: RealtimeTransport) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant`,
          role: 'assistant',
          content: data.message.content,
          created: data.timestamp,
        },
      ]);
    };

    setupRealtime().catch((error) => console.error('Realtime setup failed:', error));
    realtimeService.on('agentic-chat-message', handleRealtime);

    return () => {
      realtimeService.off('agentic-chat-message', handleRealtime);
      realtimeService.disconnect();
    };
  }, [user?.id]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-user`, role: 'user', content: trimmed, created: new Date().toISOString() },
    ]);
    setInput('');
    setSending(true);
    try {
      await apiInterface.sendAgenticMessage(trimmed);
    } catch (error) {
      console.error('Failed to send agentic chat message:', error);
    } finally {
      setSending(false);
    }
  };

  return (
    <View style={styles.container}>
      <Card style={styles.headerCard}>
        <Card.Content>
          <Text variant="titleMedium">Agentic Chat</Text>
          <Text variant="bodySmall" style={styles.subtitle}>
            {"Stateless async chat via Django -> Celery -> Redis -> Socket."}
          </Text>
        </Card.Content>
      </Card>

      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messages}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
            <Text style={item.role === 'user' ? styles.userText : styles.assistantText}>{item.content}</Text>
          </View>
        )}
      />

      <View style={styles.inputRow}>
        <TextInput
          mode="outlined"
          value={input}
          onChangeText={setInput}
          placeholder="Write a message"
          style={styles.input}
          multiline
        />
        <Button mode="contained" onPress={sendMessage} disabled={sending || !input.trim()}>
          Send
        </Button>
      </View>
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
      padding: 12,
    },
    headerCard: {
      marginBottom: 12,
    },
    subtitle: {
      marginTop: 6,
      color: theme.colors.onSurfaceVariant,
    },
    messages: {
      gap: 8,
      paddingBottom: 12,
    },
    bubble: {
      borderRadius: 12,
      padding: 10,
      maxWidth: '85%',
    },
    userBubble: {
      alignSelf: 'flex-end',
      backgroundColor: theme.colors.primary,
    },
    assistantBubble: {
      alignSelf: 'flex-start',
      backgroundColor: theme.colors.surfaceVariant,
    },
    userText: {
      color: '#fff',
    },
    assistantText: {
      color: theme.colors.onSurface,
    },
    inputRow: {
      gap: 8,
    },
    input: {
      maxHeight: 140,
    },
  });
