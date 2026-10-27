import { QueryClient } from "@tanstack/react-query";

import api from "./api";

/**
 * In-browser cache for API reads (zero-budget alternative to a Redis query
 * cache). Lists are kept for a short time, so moving between pages shows the
 * last result at once while a fresh copy loads in the background.
 *
 * Rules that keep it safe:
 * - Any successful write (POST, PUT, PATCH, DELETE) marks every cached read as
 *   out of date, so a page never keeps showing a list from before a change
 *   (the API client sends "pamsu:mutated").
 * - Signing in, signing out and an expired session empty the cache, so a
 *   shared lab computer never shows the previous account's data
 *   (AuthContext calls clearApiCache).
 */
export const LIST_STALE_MS = 30 * 1000;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: LIST_STALE_MS,
      gcTime: 5 * 60 * 1000,
      // Pages show their own error state with a "Try again" button.
      retry: false,
    },
  },
});

export const apiQueryKey = (endpoint) => ["api", endpoint];

/** A cached GET for loaders outside React components. */
export const cachedGet = (endpoint, { staleTime = LIST_STALE_MS } = {}) =>
  queryClient.fetchQuery({
    queryKey: apiQueryKey(endpoint),
    queryFn: () => api.get(endpoint),
    staleTime,
  });

/** Updates a cached response in place (e.g. after an archive), if one exists. */
export const updateCachedApi = (endpoint, updater) => queryClient.setQueryData(apiQueryKey(endpoint), updater);

export const invalidateApiCache = () => queryClient.invalidateQueries({ queryKey: ["api"] });

export const clearApiCache = () => queryClient.clear();

if (typeof window !== "undefined") {
  window.addEventListener("pamsu:mutated", () => {
    invalidateApiCache();
  });
}
