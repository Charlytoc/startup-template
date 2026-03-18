import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
import colors from './colors';

export const paperLightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: colors.primary,
    primaryContainer: colors.primary700,
    secondary: colors.secondary,
    secondaryContainer: colors.secondary700,
    tertiary: colors.accent,
    tertiaryContainer: colors.accent700,
    surface: colors.surface,
    surfaceVariant: colors.surfaceVariant,
    background: colors.background,
    error: colors.error,
    errorContainer: '#FFEBE9',
    onPrimary: '#FFFFFF',
    onSecondary: '#FFFFFF',
    onTertiary: '#2D3436',
    onSurface: colors.text,
    onSurfaceVariant: colors.textSecondary,
    onBackground: colors.text,
    onError: '#FFFFFF',
    outline: colors.border,
    outlineVariant: colors.borderLight,
    shadow: colors.shadow,
  },
};

export const paperDarkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: colors.primary,
    primaryContainer: colors.primary900,
    secondary: colors.secondary,
    secondaryContainer: colors.secondary700,
    tertiary: colors.accent,
    tertiaryContainer: colors.accent700,
    surface: '#1E1E1E',
    surfaceVariant: '#2D2D2D',
    background: '#121212',
    error: colors.error,
    errorContainer: '#93000A',
    onPrimary: '#FFFFFF',
    onSecondary: '#FFFFFF',
    onTertiary: '#2D3436',
    onSurface: '#E5E5E5',
    onSurfaceVariant: '#B2BEC3',
    onBackground: '#E5E5E5',
    onError: '#FFFFFF',
    outline: '#4A4A4A',
    outlineVariant: '#3A3A3A',
    shadow: colors.shadowDark,
  },
};

