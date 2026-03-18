import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';
import { apiInterface } from '../services/api';

type User = {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  organization: Organization;
  profile_picture?: string | null;
  is_active: boolean;
  is_staff: boolean;
  created: string;
};

type Organization = {
  id: number;
  name: string;
  domain: string;
  status: string;
};

type SignupRequest = {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  organization_id?: number;
};

type LoginRequest = {
  email: string;
  password: string;
};
interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signup: (data: SignupRequest) => Promise<void>;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setUser: (user: User | null) => void;
  setOrganization: (organization: Organization | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Load user from stored token on app start
  useEffect(() => {
    loadStoredUser();
  }, []);

  const loadStoredUser = async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        console.log('🔍 Loading stored user...');
        const userData = await apiInterface.getCurrentUser();
        console.log('✅ User data loaded:', userData);
        setUser(userData);

      }
    } catch (error) {
      console.log('❌ No stored user found or token expired:', error);
      await SecureStore.deleteItemAsync('auth_token');
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (data: SignupRequest) => {
    try {
      const response = await apiInterface.signup(data);
      
      // Store token
      await SecureStore.setItemAsync('auth_token', response.api_token);
      
      // Update state
      setUser(response.user as User);
      setOrganization(response.organization as Organization);
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  };

  const login = async (data: LoginRequest) => {
    try {
      const response = await apiInterface.login(data);
      
      // Store token
      await SecureStore.setItemAsync('auth_token', response.api_token);
      
      // Update state
      setUser(response.user as User);
      setOrganization(response.organization as Organization);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      console.log('🚪 Starting logout process...');
      
      // Try to call logout API, but don't fail if it doesn't work
      try {
        await apiInterface.logout();
        console.log('✅ Logout API call successful');
      } catch (apiError) {
        console.log('⚠️ Logout API call failed, continuing with local logout:', apiError);
      }
    } catch (error) {
      console.error('❌ Logout error:', error);
    } finally {
      // Always clear stored data regardless of API call success
      console.log('🧹 Clearing local auth data...');
      await SecureStore.deleteItemAsync('auth_token');
      setUser(null);
      setOrganization(null);
      console.log('✅ Logout completed - user logged out locally');
      
      // Redirect to landing page
      router.replace('/(tabs)');
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await apiInterface.getCurrentUser();
      setUser(userData);
      setOrganization(userData.organization as Organization);
    } catch (error) {
      console.error('Refresh user error:', error);
      await logout();
    }
  };

  const value: AuthContextType = {
    user,
    organization,
    isLoading,
    isAuthenticated,
    signup,
    login,
    logout,
    refreshUser,
    setUser,
    setOrganization,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};