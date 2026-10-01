/**
 * Centralized API Client for PAMSU Web-Based Python IDE
 * Handles JWT Bearer authentication, request timeouts, network error normalization,
 * and strict FastAPI / Pydantic error response parsing.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = Number(import.meta.env.VITE_DEFAULT_REQUEST_TIMEOUT_MS) || 15000;

export class ApiError extends Error {
  constructor(message, status = 0, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

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
    if (token) {
      // Notify backend to blacklist the token
      await fetch(`${BASE_URL}/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => {});
    }
    localStorage.removeItem('pamsu_access_token');
    localStorage.removeItem('pamsu_user_role');
  } catch {
    // Ignore storage access errors in restricted browser environments
  }
};

const parseErrorMessage = (errorData, status) => {
  if (!errorData) {
    return `HTTP Error ${status}: Request failed without details.`;
  }

  if (status === 422 && Array.isArray(errorData.detail)) {
    const validationErrors = errorData.detail
      .map((err) => `${err.loc?.slice(-1)[0] || 'Field'} is invalid or exceeds maximum length.`)
      .join('; ');
    return `Validation Error: ${validationErrors}`;
  }

  if (typeof errorData.detail === 'string') {
    return errorData.detail;
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

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return null;
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json().catch(() => null) : await response.text();

    if (!response.ok) {
      if (response.status === 401) {
        clearSessionTokens();
        window.dispatchEvent(new CustomEvent('pamsu:unauthorized'));
      }

      const errorMessage = parseErrorMessage(data, response.status);
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out. Please check your connection or try again.', 408);
    }

    if (!navigator.onLine || error.message.includes('Failed to fetch')) {
      throw new ApiError('Cannot connect to the server. Please verify the backend is running.', 0);
    }

    throw new ApiError(error.message || 'An unexpected network error occurred.', 500);
  }
};

export const api = {
  get: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(endpoint, { ...options, method: 'GET' }, timeoutMs),

  post: (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(
      endpoint,
      {
        ...options,
        method: 'POST',
        body: body instanceof FormData ? body : JSON.stringify(body),
      },
      timeoutMs
    ),

  put: (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(
      endpoint,
      {
        ...options,
        method: 'PUT',
        body: body instanceof FormData ? body : JSON.stringify(body),
      },
      timeoutMs
    ),

  patch: (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(
      endpoint,
      {
        ...options,
        method: 'PATCH',
        body: body instanceof FormData ? body : JSON.stringify(body),
      },
      timeoutMs
    ),

  delete: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(endpoint, { ...options, method: 'DELETE' }, timeoutMs),
};

export default api;