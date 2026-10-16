import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { clearSessionTokens } from '../../services/api';

const AuthContext = createContext(null);

const SESSION_EXPIRED_FLAG = 'pamsu_session_expired';

const EMPTY_STATE = { token: null, role: null, user: null, isLoading: false };

export const homePathForRole = (role) => {
  if (role === 'admin') return '/admin/dashboard';
  if (role === 'instructor') return '/instructor/dashboard';
  return '/student/dashboard';
};

const isTokenExpired = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now();
  } catch {
    return false;
  }
};

const markSessionExpired = () => {
  try {
    sessionStorage.setItem(SESSION_EXPIRED_FLAG, '1');
  } catch {
    // Notice is optional.
  }
};

/** Returns true once if the previous session ended because it expired. */
export const consumeSessionExpiredNotice = () => {
  try {
    const flagged = sessionStorage.getItem(SESSION_EXPIRED_FLAG) === '1';
    sessionStorage.removeItem(SESSION_EXPIRED_FLAG);
    return flagged;
  } catch {
    return false;
  }
};

/**
 * Lazy initializer reads persistent storage instantly upon app launch
 * without triggering secondary cascading re-renders.
 */
const getInitialAuthState = () => {
  try {
    const storedToken = localStorage.getItem('pamsu_access_token');
    const storedRole = localStorage.getItem('pamsu_user_role');
    const storedUser = localStorage.getItem('pamsu_user_data');

    if (storedToken && storedRole && storedUser) {
      if (isTokenExpired(storedToken)) {
        markSessionExpired();
        localStorage.removeItem('pamsu_access_token');
        localStorage.removeItem('pamsu_user_role');
        localStorage.removeItem('pamsu_user_data');
        return EMPTY_STATE;
      }
      return {
        token: storedToken,
        role: storedRole,
        user: JSON.parse(storedUser),
        isLoading: false,
      };
    }
  } catch {
    clearSessionTokens();
    try {
      localStorage.removeItem('pamsu_user_data');
    } catch {
      // Storage unavailable.
    }
  }

  return EMPTY_STATE;
};

export const AuthProvider = ({ children }) => {
  const [authState, setAuthState] = useState(getInitialAuthState);

  const logout = useCallback(() => {
    clearSessionTokens();
    try {
      localStorage.removeItem('pamsu_user_data');
    } catch {
      // Storage unavailable.
    }
    setAuthState(EMPTY_STATE);
  }, []);

  // The API client reports 401 responses; the session is no longer valid.
  useEffect(() => {
    const handleUnauthorized = () => {
      markSessionExpired();
      logout();
    };
    window.addEventListener('pamsu:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('pamsu:unauthorized', handleUnauthorized);
  }, [logout]);

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

  const updateUser = useCallback((newUserData) => {
    localStorage.setItem('pamsu_user_data', JSON.stringify(newUserData));
    setAuthState((prev) => ({
      ...prev,
      user: newUserData,
    }));
  }, []);

  const value = {
    user: authState.user,
    role: authState.role,
    token: authState.token,
    isAuthenticated: Boolean(authState.token),
    isLoading: authState.isLoading,
    login,
    logout,
    updateUser,
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
