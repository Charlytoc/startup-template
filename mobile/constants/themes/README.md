# Dynamic Theme System

Simple theme management using React Native Paper and AsyncStorage.

## Architecture

```
ThemeProvider (App Root)
  └─ Loads theme from storage/backend
  └─ Provides theme to PaperProvider
  └─ All components use useTheme() from Paper
```

## Usage

### In Components

```tsx
import { useTheme } from 'react-native-paper';

const MyComponent = () => {
  const theme = useTheme();
  
  return (
    <View style={{ backgroundColor: theme.colors.background }}>
      <Text style={{ color: theme.colors.onBackground }}>Hello</Text>
    </View>
  );
};
```

### Changing Themes

```tsx
import { useAppTheme } from '@/hooks/use-app-theme';

const MyComponent = () => {
  const { themeId, availableThemes, changeTheme } = useAppTheme();
  
  return (
    <Button onPress={() => changeTheme('salmon-coral')}>
      Change Theme
    </Button>
  );
};
```

## Adding New Themes

1. Create a new JSON file in `constants/themes/` (e.g., `green-nature.json`)
2. Define light and dark colors following the structure:

```json
{
  "id": "green-nature",
  "name": "Green Nature",
  "description": "Fresh and natural",
  "light": {
    "primary": "#4CAF50",
    "secondary": "#8BC34A",
    ...
  },
  "dark": {
    "primary": "#66BB6A",
    "secondary": "#9CCC65",
    ...
  }
}
```

3. Import and add to `AVAILABLE_THEMES` in `constants/themes/index.ts`

## Backend Integration

The system automatically fetches the default theme from:
- **Endpoint**: `GET /api/config/theme/`
- **Response**: `{ default_theme_key: "salmon-coral" }`

If the backend is unavailable, it uses the locally saved theme or falls back to `teal-modern`.

## How It Works

1. **On App Start**: `ThemeProvider` loads theme from AsyncStorage
2. **Backend Check**: Tries to fetch default theme from API
3. **State Management**: Uses React's `useState` to trigger re-renders
4. **Persistence**: Saves theme selection to AsyncStorage
5. **Theme Application**: `useMemo` ensures Paper theme only recreates when needed

## Files

- `use-app-theme.ts` - Hook for theme selection
- `ThemeProvider.tsx` - Root provider component
- `index.ts` - Theme definitions and utilities
- `*.json` - Individual theme files
