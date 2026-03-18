/**
 * Theme Configuration
 * 
 * Configure how often themes should be refreshed from the backend
 */

export const THEME_CONFIG = {
  // Refresh interval in seconds
  // Default: 24 hours (86400 seconds)
  // Options:
  // - 3600 (1 hour)
  // - 21600 (6 hours) 
  // - 86400 (24 hours) - Default
  // - 604800 (1 week)
  REFRESH_INTERVAL_SECONDS: 86400,
  
  // Force refresh on app start (ignores interval)
  // Useful for development or when you want fresh themes on each app launch
  FORCE_REFRESH_ON_START: false,
  
  // Enable debug logging for theme operations
  DEBUG_LOGGING: __DEV__,
};
