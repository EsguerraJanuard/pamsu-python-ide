import { useQuery } from "@tanstack/react-query";

import api from "../services/api";
import { apiQueryKey } from "../services/queryClient";

/**
 * Cached GET request. Pages that read the same endpoint share one cached
 * result (see services/queryClient.js). Pass a falsy endpoint to skip.
 *
 * Returns react-query's result: `data`, `error`, `isPending` (no data yet),
 * `isFetching` (a request is running) and `refetch`.
 */
export default function useApiQuery(endpoint, options = {}) {
  return useQuery({
    queryKey: apiQueryKey(endpoint),
    queryFn: () => api.get(endpoint),
    enabled: Boolean(endpoint),
    ...options,
  });
}
