# React Native Paper Setup

React Native Paper is now installed and configured in the app.

## Available Components

### Buttons
```tsx
import { Button } from 'react-native-paper';

<Button mode="contained" onPress={handlePress}>
  Press me
</Button>

<Button mode="outlined" onPress={handlePress}>
  Outlined
</Button>

<Button mode="text" onPress={handlePress}>
  Text Button
</Button>
```

### Text Inputs
```tsx
import { TextInput } from 'react-native-paper';

<TextInput
  label="Email"
  value={email}
  onChangeText={setEmail}
  mode="outlined"
  keyboardType="email-address"
/>
```

### Cards
```tsx
import { Card, Text } from 'react-native-paper';

<Card>
  <Card.Content>
    <Text variant="titleLarge">Card Title</Text>
    <Text variant="bodyMedium">Card content</Text>
  </Card.Content>
</Card>
```

### Other Components
- `Surface` - Elevated surfaces
- `Divider` - Separator lines
- `Chip` - Compact elements
- `IconButton` - Icon buttons
- `FAB` - Floating action button
- `Snackbar` - Toast messages
- `Dialog` - Modal dialogs
- `List` - List items with icons
- `Avatar` - User avatars
- `Badge` - Notification badges

## Theme Access

```tsx
import { useTheme } from 'react-native-paper';

function MyComponent() {
  const theme = useTheme();
  
  return (
    <View style={{ backgroundColor: theme.colors.primary }}>
      {/* content */}
    </View>
  );
}
```

## Dynamic Styling with Theme

For components that need theme-aware styling, use this pattern:

```tsx
const createStyles = (theme: any) => StyleSheet.create({
  container: {
    backgroundColor: theme.colors.background,
  },
  text: {
    color: theme.colors.onBackground,
  },
});

function MyComponent() {
  const theme = useTheme();
  const styles = createStyles(theme);
  
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Content</Text>
    </View>
  );
}
```

## Dark Mode Support

The app automatically switches between light and dark themes based on the device's color scheme. All Paper components will automatically adapt their colors and styling.

Available theme colors:
- `theme.colors.background` - Main background color
- `theme.colors.surface` - Card/surface background
- `theme.colors.onBackground` - Text on background
- `theme.colors.onSurface` - Text on surface
- `theme.colors.primary` - Primary brand color
- `theme.colors.outline` - Border colors
- `theme.colors.outlineVariant` - Lighter borders

## Documentation

Full documentation: https://callstack.github.io/react-native-paper/

