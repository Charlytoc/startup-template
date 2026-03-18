import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from 'react-native-paper';

interface HeaderProps {
  title: string;
  showBackButton?: boolean;
  showMenuButton?: boolean;
  onBackPress?: () => void;
  onMenuPress?: () => void;
  rightComponent?: React.ReactNode;
}

export default function Header({
  title,
  showBackButton = false,
  showMenuButton = false,
  onBackPress,
  onMenuPress,
  rightComponent,
}: HeaderProps) {
  const theme = useTheme();
  const styles = createStyles(theme);

  return (
    <View style={styles.container}>
      <StatusBar 
        barStyle={theme.dark ? "light-content" : "dark-content"}
        backgroundColor={theme.colors.surface}
        translucent={false}
      />
      <View style={styles.content}>
        <View style={styles.leftSection}>
          {showBackButton && (
            <TouchableOpacity onPress={onBackPress} style={styles.iconButton}>
              <Ionicons name="arrow-back" size={24} color={theme.colors.primary} />
            </TouchableOpacity>
          )}
          {showMenuButton && (
            <TouchableOpacity onPress={onMenuPress} style={styles.iconButton}>
              <Ionicons name="menu" size={24} color={theme.colors.primary} />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.centerSection}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
        </View>

        <View style={styles.rightSection}>
          {rightComponent}
        </View>
      </View>
    </View>
  );
}

const createStyles = (theme: any) => StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.outline,
    paddingTop: 0, // Let StatusBar handle the spacing
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 56,
    paddingTop: Platform.OS === 'ios' ? 12 : 16,
  },
  leftSection: {
    flexDirection: 'row',
    alignItems: 'center',
    minWidth: 80,
  },
  centerSection: {
    flex: 1,
    alignItems: 'center',
  },
  rightSection: {
    flexDirection: 'row',
    alignItems: 'center',
    minWidth: 80,
    justifyContent: 'flex-end',
  },
  iconButton: {
    padding: 8,
    marginRight: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
    textAlign: 'center',
  },
});
