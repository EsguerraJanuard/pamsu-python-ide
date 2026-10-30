import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * List filters and search text kept in the page URL (?view=archived&q=cc102),
 * so they survive a reload and can be shared as a link.
 *
 * `defaults`: { name: defaultValue } for every filter the page owns. Define
 *   it once outside the component. A value equal to its default is left out
 *   of the URL, so an unfiltered page keeps a clean address.
 * `allowed`: optional { name: [valid values] }. A value from the URL that is
 *   not in the list (an old or edited link) reads as the default.
 *
 * Returns [values, setFilters]. setFilters({ name: value, ... }) changes one
 * or several filters at once and replaces the history entry, so typing in a
 * search box doesn't fill the Back button. Other query parameters are kept.
 */
export default function useUrlFilters(defaults, allowed = null) {
  const [searchParams, setSearchParams] = useSearchParams();

  const values = useMemo(() => {
    const result = {};
    for (const [name, fallback] of Object.entries(defaults)) {
      const raw = searchParams.get(name);
      const valid = raw !== null && (!allowed?.[name] || allowed[name].includes(raw));
      result[name] = valid ? raw : fallback;
    }
    return result;
  }, [searchParams, defaults, allowed]);

  const setFilters = useCallback(
    (updates) => {
      setSearchParams(
        () => {
          // Built on the current address, not the one from the last render:
          // React Router hands its updater the render-time params, so two
          // changes in one event would otherwise overwrite each other.
          const params = new URLSearchParams(window.location.search);
          for (const [name, value] of Object.entries(updates)) {
            if (value === null || value === undefined || value === "" || value === defaults[name]) {
              params.delete(name);
            } else {
              params.set(name, String(value));
            }
          }
          return params;
        },
        { replace: true, preventScrollReset: true },
      );
    },
    [setSearchParams, defaults],
  );

  return [values, setFilters];
}
