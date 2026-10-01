import re
with open('frontend/src/services/api.js', 'r', encoding='utf-8') as f:
    c = f.read()

patch = '''
const pendingRequests = new Map();

export const api = {
  get: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) => {
    const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const key = `GET::${url}`;
    
    if (pendingRequests.has(key)) {
      return pendingRequests.get(key);
    }
    
    const promise = request(endpoint, { ...options, method: 'GET' }, timeoutMs)
      .finally(() => {
        pendingRequests.delete(key);
      });
      
    pendingRequests.set(key, promise);
    return promise;
  },

  post: (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
'''

c = c.replace("""export const api = {
  get: (endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>
    request(endpoint, { ...options, method: 'GET' }, timeoutMs),

  post: (endpoint, body, options = {}, timeoutMs = DEFAULT_TIMEOUT) =>""", patch)

with open('frontend/src/services/api.js', 'w', encoding='utf-8') as f:
    f.write(c)