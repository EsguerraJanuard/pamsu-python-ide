/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { clearSessionTokens } from '../services/api';

const AuthContext = createContext(null);

/**
 * Lazy initializer reads persistent storage instantly upon app launch
 * without triggering secondary cascading re-renders.
 */
const getInitialAuthState = () => {
  const storedToken = localStorage.getItem('pamsu_access_token');
  const storedRole = localStorage.getItem('pamsu_user_role');
  const storedUser = localStorage.getItem('pamsu_user_data');

  if (storedToken && storedRole && storedUser) {
    try {
      return {
        token: storedToken,
        role: storedRole,
        user: JSON.parse(storedUser),
        isLoading: false,
      };
    } catch {
      clearSessionTokens();
      localStorage.removeItem('pamsu_user_data');
    }
  }

  return {
    token: null,
    role: null,
    user: null,
    isLoading: false,
  };
};

export const AuthProvider = ({ children }) => {
  // Initialize state lazily to eliminate synchronous useEffect re-renders
  const [authState, setAuthState] = useState(getInitialAuthState);

  // Logout handler cleans memory and persistent storage
  const logout = useCallback(() => {
    clearSessionTokens();
    localStorage.removeItem('pamsu_user_data');
    setAuthState({
      token: null,
      role: null,
      user: null,
      isLoading: false,
    });
  }, []);

  // Listen for automatic logout if the backend reports a 401 Unauthorized error
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('pamsu:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('pamsu:unauthorized', handleUnauthorized);
  }, [logout]);

  // Login handler saves credentials and updates state immediately
  const login = useCallback((newToken, userData, userRole) => {
    localStorage.setItem('pamsu_access_token', newToken);
    localStorage.setItem('pamsu_user_role', userRole);
    localStorage.setItem('pamsu_user_data', JSON.stringify(userData));
    
    setAuthState({
      token: newToken,
      user: userData,
      role: userRole,
      isLoading: false,
    });
  }, []);

  const value = {
    user: authState.user,
    role: authState.role,
    token: authState.token,
    isAuthenticated: Boolean(authState.token),
    isLoading: authState.isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;