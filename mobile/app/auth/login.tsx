import { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { TextInput, Button, Text, IconButton, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import { AppDialog } from '../../components/AppDialog';
import { useDialog } from '../../hooks/use-dialog';

export default function LoginScreen() {
  const router = useRouter();
  const { login } = useAuth();
  const theme = useTheme();
  const dialog = useDialog();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      dialog.show('Error', 'Email and password are required');
      return false;
    }
    return true;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await login({
        email: formData.email,
        password: formData.password,
      });

      // Login successful - the AuthContext will handle the user state
      // and the home screen will handle the redirection
      router.replace('/(tabs)');
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Login failed. Please try again.';
      dialog.show('Error', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const styles = createStyles(theme);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <IconButton
          icon="arrow-left"
          size={24}
          onPress={() => router.back()}
        />
        <Text variant="headlineMedium" style={styles.title}>Welcome Back</Text>
        <View style={styles.placeholder} />
      </View>

      <View style={styles.form}>
        <TextInput
          label="Email"
          value={formData.email}
          onChangeText={(value) => handleInputChange('email', value)}
          mode="outlined"
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          textContentType="emailAddress"
          autoComplete="email"
          style={styles.input}
        />

        <TextInput
          label="Password"
          value={formData.password}
          onChangeText={(value) => handleInputChange('password', value)}
          mode="outlined"
          secureTextEntry={!showPassword}
          autoCapitalize="none"
          textContentType="password"
          autoComplete="password"
          right={
            <TextInput.Icon
              icon={showPassword ? 'eye-off' : 'eye'}
              onPress={() => setShowPassword(!showPassword)}
            />
          }
          style={styles.input}
        />

        <Button
          mode="contained"
          onPress={handleLogin}
          loading={isLoading}
          disabled={isLoading}
          style={styles.loginButton}
        >
          Sign In
        </Button>

        <View style={styles.signupLink}>
          <Text variant="bodyLarge">Don&apos;t have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/auth/signup')}>
            <Text variant="bodyLarge" style={styles.signupLinkText}>Sign Up</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      <AppDialog
        visible={dialog.visible}
        title={dialog.title}
        message={dialog.message}
        actions={dialog.actions}
        onDismiss={dialog.hide}
      />
    </ScrollView>
  );
}

const createStyles = (theme: any) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flexGrow: 1,
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  title: {
    fontWeight: 'bold',
  },
  placeholder: {
    width: 40,
  },
  form: {
    flex: 1,
  },
  input: {
    marginBottom: 16,
  },
  loginButton: {
    marginTop: 20,
  },
  signupLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  signupLinkText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
});
