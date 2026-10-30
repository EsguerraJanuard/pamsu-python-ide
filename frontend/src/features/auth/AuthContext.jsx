import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { clearSessionTokens } from '../../services/api';
import { clearApiCache } from '../../services/queryClient';
import { clearAllDrafts, clearLegacyDrafts } from '../workspace/draftStorage';
import { isTokenExpired, roleFromToken, userIdFromToken } from './token';

const AuthContext = createContext(null);

const SESSION_EXPIRED_FLAG = 'pamsu_session_expired';

// The access token is the session: the role is read from it (token.js).
// The profile (name, email, school ID…) comes from the sign-in response and
// is kept here, in app state, with a copy in storage so a reload or a new
// tab still shows it. Neither the token nor storage holds a separate role.
const TOKEN_KEY = 'pamsu_access_token';
const PROFILE_KEY = 'pamsu_user_data';
const LEGACY_ROLE_KEY = 'pamsu_user_role';

const EMPTY_STATE = { token: null, role: null, user: null, isLoading: false };

export const homePathForRole = (role) => {
  if (role === 'admin') return '/admin/dashboard';
  if (role === 'instructor') return '/instructor/dashboard';
  return '/student/dashboard';
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

/** Profile fields only: the role always comes from the token. */
const profileWithoutRole = (userData) => {
  if (!userData || typeof userData !== 'object') return null;
  const { role: _role, ...profile } = userData;
  return profile;
};

/**
 * The user object pages read: the stored profile plus the role from the
 * token. Without a stored profile (cleared storage), the account id from the
 * token still scopes drafts and theme preferences.
 */
const buildUser = (token, role, profile) => {
  const userId = userIdFromToken(token);
  return {
    ...(profile || {}),
    user_id: profile?.user_id ?? userId,
    role,
  };
};

const removeStoredSession = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(PROFILE_KEY);
    localStorage.removeItem(LEGACY_ROLE_KEY);
  } catch {
    // Storage unavailable.
  }
};

const readStoredProfile = () => {
  try {
    const stored = localStorage.getItem(PROFILE_KEY);
    return stored ? profileWithoutRole(JSON.parse(stored)) : null;
  } catch {
    return null;
  }
};

/**
 * Lazy initializer reads persistent storage instantly upon app launch
 * without triggering secondary cascading re-renders.
 */
const getInitialAuthState = () => {
  let storedToken;
  try {
    storedToken = localStorage.getItem(TOKEN_KEY);
    // Written by versions before 2026-10-27; the token is the only source now.
    localStorage.removeItem(LEGACY_ROLE_KEY);
  } catch {
    return EMPTY_STATE;
  }

  if (!storedToken) return EMPTY_STATE;

  if (isTokenExpired(storedToken)) {
    markSessionExpired();
    removeStoredSession();
    return EMPTY_STATE;
  }

  const role = roleFromToken(storedToken);
  if (!role) {
    removeStoredSession();
    return EMPTY_STATE;
  }

  return {
    token: storedToken,
    role,
    user: buildUser(storedToken, role, readStoredProfile()),
    isLoading: false,
  };
};

export const AuthProvider = ({ children }) => {
  const [authState, setAuthState] = useState(getInitialAuthState);

  const endSession = useCallback(() => {
    clearSessionTokens();
    removeStoredSession();
    clearApiCache();
    setAuthState(EMPTY_STATE);
  }, []);

  // Signing out on a shared lab computer must not leave code behind.
  const logout = useCallback(() => {
    clearAllDrafts();
    endSession();
  }, [endSession]);

  // The API client reports 401 responses; the session is no longer valid.
  // Drafts are kept: they are scoped to this account, which can sign back in.
  useEffect(() => {
    const handleUnauthorized = () => {
      markSessionExpired();
      endSession();
    };
    window.addEventListener('pamsu:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('pamsu:unauthorized', handleUnauthorized);
  }, [endSession]);

  // Tabs share the stored token, and every request reads it from storage.
  // Follow a sign-out or sign-in made in another tab: otherwise this tab kept
  // sending requests without a token (a 401 every 5 s from the workspace
  // heartbeat), or with another account's token (alpha tester, 2026-10-28).
  // The "storage" event fires only in the other tabs.
  const currentToken = authState.token;
  useEffect(() => {
    const handleStorage = (event) => {
      // key is null when another tab cleared all of storage.
      if (event.key !== null && event.key !== TOKEN_KEY && event.key !== PROFILE_KEY) return;
      const next = getInitialAuthState();
      if (next.token === currentToken) {
        // Same session: keep the profile in step (sign-in writes it just
        // after the token; a name change in Settings rewrites it).
        if (next.token && event.key === PROFILE_KEY) setAuthState(next);
        return;
      }
      if (!next.token) {
        // Signed out (or the session ended) in another tab. That tab already
        // told the server, so this one only forgets the session.
        clearApiCache();
        setAuthState(EMPTY_STATE);
      } else if (!currentToken || userIdFromToken(next.token) === userIdFromToken(currentToken)) {
        // Signed in in another tab, or the same account signed in again.
        setAuthState(next);
      } else {
        // Another account signed in: start again from its home page, so
        // nothing loaded for the previous account stays on screen.
        window.location.replace(homePathForRole(next.role));
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [currentToken]);

  /**
   * Starts a session from a sign-in response. Returns the role read from
   * the token; throws if the token has no valid role.
   */
  const login = useCallback((newToken, userData) => {
    const role = roleFromToken(newToken);
    if (!role) {
      throw new Error('The sign-in response did not include a valid account role.');
    }
    const profile = profileWithoutRole(userData);

    clearLegacyDrafts();
    clearApiCache();
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    localStorage.removeItem(LEGACY_ROLE_KEY);

    setAuthState({
      token: newToken,
      role,
      user: buildUser(newToken, role, profile),
      isLoading: false,
    });
    return role;
  }, []);

  const updateUser = useCallback((newUserData) => {
    const profile = profileWithoutRole(newUserData);
    try {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    } catch {
      // The in-memory profile still updates.
    }
    setAuthState((prev) => ({
      ...prev,
      user: buildUser(prev.token, prev.role, profile),
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
