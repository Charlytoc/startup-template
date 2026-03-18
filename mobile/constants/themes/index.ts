import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';

import defaultNeutral from './default-neutral.json';
import tealModern from './teal-modern.json';
import salmonCoral from './salmon-coral.json';
import blueProfessional from './blue-professional.json';
import purpleCreative from './purple-creative.json';
import greenNature from './green-nature.json';

export interface ThemeColors {
  primary: string;
  primaryContainer: string;
  secondary: string;
  secondaryContainer: string;
  tertiary: string;
  tertiaryContainer: string;
  surface: string;
  surfaceVariant: string;
  background: string;
  error: string;
  errorContainer: string;
  onPrimary: string;
  onSecondary: string;
  onTertiary: string;
  onSurface: string;
  onSurfaceVariant: string;
  onBackground: string;
  onError: string;
  outline: string;
  outlineVariant: string;
  shadow: string;
  shadowDark: string;
}

export interface ThemeDefinition {
  id: string;
  name: string;
  description: string;
  light: ThemeColors;
  dark: ThemeColors;
}

export const AVAILABLE_THEMES: ThemeDefinition[] = [
  defaultNeutral,
  tealModern,
  salmonCoral,
  blueProfessional,
  purpleCreative,
  greenNature,
];

export const getThemeById = (themeId: string): ThemeDefinition | null => {
  return AVAILABLE_THEMES.find(theme => theme.id === themeId) || null;
};

export const createPaperTheme = (themeDef: ThemeDefinition, isDark: boolean = false) => {
  const colors = isDark ? themeDef.dark : themeDef.light;
  const baseTheme = isDark ? MD3DarkTheme : MD3LightTheme;

  return {
    ...baseTheme,
    colors: {
      ...baseTheme.colors,
      ...colors,
    },
  };
};
