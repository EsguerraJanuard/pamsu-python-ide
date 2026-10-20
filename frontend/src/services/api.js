/**
 * Centralized API Client for the PSU Web-Based Python IDE
 * Handles JWT Bearer authentication, request timeouts, network error normalization,
 * and strict FastAPI / Pydantic error response parsing.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL;
const DEFAULT_TIMEOUT = Number(import.meta.env.VITE_DEFAULT_REQUEST_TIMEOUT_MS) || 15000;

export const API_BASE_URL = BASE_URL;

// Status 0 = the request never reached the server (offline, CORS, server down).
// Status 408 = the client-side timeout fired.
export const NETWORK_ERROR_STATUS = 0;
export const TIMEOUT_ERROR_STATUS = 408;

export class ApiError extends Error {
  constructor(message, status = 0, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Connectivity is broadcast so passive UI (the status bar) can reflect whether
 * the backend is reachable without issuing requests of its own.
 */
const emitConnectivity = (online) => {
  try {
    window.dispatchEvent(new CustomEvent('pamsu:connectivity', { detail: { online } }));
  } catch {
    // Event dispatch is best-effort only.
  }
};

const getAccessToken = () => {
  try {
    return localStorage.getItem('pamsu_access_token');
  } catch {
    return null;
  }
};

export const clearSessionTokens = async () => {
  try {
    const token = localStorage.getItem('pamsu_access_token');
    localStorage.removeItem('pamsu_access_token');
    localStorage.removeItem('pamsu_user_role');
    if (token) {
      // Notify backend to blacklist the token
      await fetch(`${BASE_URL}/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => {});
    }
  } catch {
    // Ignore storage access errors in restricted browser environments
  }
};

const parseErrorMessage = (errorData, status) => {
  if (!errorData || typeof errorData === 'string') {
    return `Request failed with status ${status}.`;
  }

  if (status === 422 && Array.isArray(errorData.detail)) {
    const validationErrors = errorData.detail
      .map((err) => {
        const field = err.loc?.slice(-1)[0];
        const label = typeof field === 'string' ? field.replace(/_/g, ' ') : 'A field';
        return err.msg ? `${label}: ${err.msg}` : `${label} is invalid.`;
      })
      .join('; ');
    return validationErrors || 'Some fields are invalid.';
  }

  if (typeof errorData.detail === 'string') {
    return errorData.detail;
  }

  if (errorData.detail && typeof errorData.detail.message === 'string') {
    return errorData.detail.message;
  }

  if (typeof errorData.message === 'string') {
    return errorData.message;
  }

  return `Request failed with status ${status}.`;
};

export const request = async (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const token = getAccessToken();

  const headers = new Headers(options.headers || {});

  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const config = {
    ...options,
    headers,
    signal: controller.signal,
  };

  let response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    clearTimeout(timeoutId);
    if (error?.name === 'AbortError') {
      throw new ApiError('The server took too long to respond. Please try again.', TIMEOUT_ERROR_STATUS);
    }
    emitConnectivity(false);
    throw new ApiError('Cannot reach the server. Check your connection or try again shortly.', NETWORK_ERROR_STATUS);
  }

  clearTimeout(timeoutId);
  emitConnectivity(true);

  if (response.status === 204 || response.headers.get('content-length') === '0') {
    if (!response.ok) {
      throw new ApiError(parseErrorMessage(null, response.status), response.status, null);
    }
    return null;
  }

  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');
  const data = isJson ? await response.json().catch(() => null) : await response.text().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && token) {
      clearSessionTokens();
      window.dispatchEvent(new CustomEvent('pamsu:unauthorized'));
    }

    throw new ApiError(parseErrorMessage(data, response.status), response.status, data);
  }

  return data;
};

/**
 * Classifies any thrown error into a user-facing category so pages can render
 * an honest state instead of a generic "failed" message. Raw backend internals
 * (stack traces, SQL errors) are never surfaced; 5xx responses get a generic text.
 */
export const describeApiError = (error, { resource = 'this information' } = {}) => {
  const status = error instanceof ApiError ? error.status : -1;

  if (status === NETWORK_ERROR_STATUS) {
    return {
      kind: 'unavailable',
      title: 'Server unavailable',
      message: `We couldn't reach the server to load ${resource}. The service may be offline or your connection was interrupted.`,
    };
  }
  if (status === TIMEOUT_ERROR_STATUS) {
    return {
      kind: 'timeout',
      title: 'Request timed out',
      message: `The server took too long to return ${resource}. Please try again.`,
    };
  }
  if (status === 401) {
    return {
      kind: 'unauthorized',
      title: 'Session expired',
      message: 'Your session has ended. Please sign in again to continue.',
    };
  }
  if (status === 403) {
    return {
      kind: 'forbidden',
      title: 'Access restricted',
      message: error.message && error.message !== 'Request failed with status 403.'
        ? error.message
        : `Your account does not have permission to view ${resource}.`,
    };
  }
  if (status === 404) {
    return {
      kind: 'not_found',
      title: 'Not found',
      message: `${resource.charAt(0).toUpperCase()}${resource.slice(1)} could not be found. It may have been removed or you may not have access.`,
    };
  }
  if (status === 409 || status === 400 || status === 422) {
    return {
      kind: 'invalid',
      title: 'Request not accepted',
      message: error.message,
    };
  }
  if (status === 429) {
    return {
      kind: 'rate_limited',
      title: 'Too many requests',
      message: 'Please wait a moment before trying again.',
    };
  }
  if (status >= 500) {
    return {
      kind: 'server',
      title: 'Server error',
      message: `The server ran into a problem while loading ${resource}. Please try again later.`,
    };
  }
  return {
    kind: 'unknown',
    title: 'Something went wrong',
    message: `We couldn't load ${resource}. Please try again.`,
  };
};

/** Short, single-line message for inline action failures (save, delete, etc.). */
export const getErrorMessage = (error, fallback = 'Something went wrong. Please try again.') => {
  if (!(error instanceof ApiError)) return fallback;
  if (error.status >= 500) return 'The server ran into a problem. Please try again later.';
  return error.message || fallback;
};

const withBody = (method) => (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
  request(
    endpoint,
    {
      ...options,
      method,
      ...(body === undefined ? {} : { body: body instanceof FormData ? body : JSON.stringify(body) }),
    },
    timeoutMs
  );

export const api = {
  get: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(endpoint, { ...options, method: 'GET' }, timeoutMs),
  post: withBody('POST'),
  put: withBody('PUT'),
  patch: withBody('PATCH'),
  delete: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(endpoint, { ...options, method: 'DELETE' }, timeoutMs),
};

export default api;
