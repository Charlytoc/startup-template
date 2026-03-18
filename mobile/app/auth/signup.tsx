import React, { useState } from 'react';
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

export default function SignupScreen() {
  const router = useRouter();
  const { signup } = useAuth();
  const theme = useTheme();
  const dialog = useDialog();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      dialog.show('Error', 'Email and password are required');
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      dialog.show('Error', 'Passwords do not match');
      return false;
    }

    if (formData.password.length < 6) {
      dialog.show('Error', 'Password must be at least 6 characters');
      return false;
    }

    return true;
  };

  const handleSignup = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await signup({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name || undefined,
        last_name: formData.last_name || undefined,
      });

      // Signup successful - the AuthContext will handle the user state
      // and the home screen will handle the redirection
      router.replace('/(tabs)');
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Signup failed. Please try again.';
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
        <Text variant="headlineMedium" style={styles.title}>Create Account</Text>
        <View style={styles.placeholder} />
      </View>

      <View style={styles.form}>
        <TextInput
          label="Email *"
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
          label="Password *"
          value={formData.password}
          onChangeText={(value) => handleInputChange('password', value)}
          mode="outlined"
          secureTextEntry
          autoCapitalize="none"
          textContentType="newPassword"
          autoComplete="password-new"
          style={styles.input}
        />

        <TextInput
          label="Confirm Password *"
          value={formData.confirmPassword}
          onChangeText={(value) => handleInputChange('confirmPassword', value)}
          mode="outlined"
          secureTextEntry
          autoCapitalize="none"
          textContentType="newPassword"
          autoComplete="password-new"
          style={styles.input}
        />

        <TextInput
          label="First Name"
          value={formData.first_name}
          onChangeText={(value) => handleInputChange('first_name', value)}
          mode="outlined"
          autoCapitalize="words"
          textContentType="givenName"
          autoComplete="name-given"
          style={styles.input}
        />

        <TextInput
          label="Last Name"
          value={formData.last_name}
          onChangeText={(value) => handleInputChange('last_name', value)}
          mode="outlined"
          autoCapitalize="words"
          textContentType="familyName"
          autoComplete="name-family"
          style={styles.input}
        />

        <Button
          mode="contained"
          onPress={handleSignup}
          loading={isLoading}
          disabled={isLoading}
          style={styles.signupButton}
        >
          Create Account
        </Button>

        <View style={styles.loginLink}>
          <Text variant="bodyLarge">Already have an account? </Text>
          <TouchableOpacity onPress={() => router.push('/auth/login')}>
            <Text variant="bodyLarge" style={styles.loginLinkText}>Sign In</Text>
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
  signupButton: {
    marginTop: 20,
  },
  loginLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  loginLinkText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
});
