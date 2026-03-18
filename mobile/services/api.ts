import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { APP_CONFIG } from '../config/env';

type User = {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  organization: {
    id: number;
    name: string;
    domain: string;
    status: string;
  };
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

type AuthResponse = {
  api_token: string;
  user: User;
  organization: Organization;
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

// Create axios instance
const api = axios.create({
  baseURL: APP_CONFIG.API_BASE_URL,
  timeout: APP_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    console.log('Request config:', {
      baseURL: config.baseURL,
      url: config.url,
      method: config.method,
      headers: config.headers,
      data: config.data
    });
    
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.error('⚠️ No auth token found');
    }
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    console.log('Response data:', response.data);
    return response;
  },
  async (error) => {
    console.error(`❌ API Error: ${error.response?.status || 'Network Error'} ${error.config?.url}`);
    console.error('Error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
      config: error.config
    });
    
    if (error.response?.status === 401) {
      await SecureStore.deleteItemAsync('auth_token');
    }
    return Promise.reject(error);
  }
);

// API Methods
export const apiInterface = {
  // Get available organizations
  getOrganizations: async (): Promise<Organization[]> => {
    const response = await api.get('/auth/organizations');
    return response.data;
  },

  // Sign up
  signup: async (data: SignupRequest): Promise<AuthResponse> => {
    console.log('📝 Starting signup process with data:', {
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      hasPassword: !!data.password
    });
    
    try {
      const response = await api.post('/auth/signup', data);
      console.log('✅ Signup successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Signup failed:', error);
      throw error;
    }
  },

  // Login
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch (error: any) {
      // Don't throw error for logout - it's okay if the API call fails
      // The token will be cleared locally regardless
      console.log('⚠️ Logout API call failed, continuing with local logout:', error);
    }
  },
  sendAgenticMessage: async (message: string): Promise<{ status: string }> => {
    const response = await api.post('/agentic-chat/messages', { message });
    return response.data;
  },
};

export default api;
