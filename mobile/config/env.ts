import Constants from 'expo-constants';

const DEV_API_URL = 'https://bksbznb5-8000.use.devtunnels.ms/api';
const DEV_REALTIME_URL = 'https://bksbznb5-3001.use.devtunnels.ms';

export const API_BASE_URL = Constants.expoConfig?.extra?.apiUrl || DEV_API_URL;
export const REALTIME_URL = Constants.expoConfig?.extra?.realtimeUrl || DEV_REALTIME_URL;

export const APP_CONFIG = {
  API_BASE_URL,
  REALTIME_URL,
  TIMEOUT: 10000,
} as const;
