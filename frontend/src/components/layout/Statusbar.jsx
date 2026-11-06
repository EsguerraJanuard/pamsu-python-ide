import { useEffect, useState } from "react";
import { useAuth } from "../../features/auth/AuthContext";

const STATUS_CONFIG = {
  active: { label: "Signed in", dotClass: "bg-emerald-600" },
  expiring: { label: "Session expires soon", dotClass: "bg-psu-gold" },
  expired: { label: "Session expired — sign in again", dotClass: "bg-psu-red" },
  disconnected: { label: "Server unreachable", dotClass: "bg-psu-red" },
  unknown: { label: "Session status unknown", dotClass: "bg-text-muted/40" },
};

function readTokenExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

function deriveStatus(token, isReachable, now) {
  if (!isReachable) return "disconnected";
  if (!token) return "unknown";
  const expiresAt = readTokenExpiry(token);
  if (!expiresAt) return "unknown";
  if (expiresAt <= now) return "expired";
  if (expiresAt - now < 5 * 60 * 1000) return "expiring";
  return "active";
}

/**
 * Footer status line. Session state is derived from the access token's expiry,
 * reachability from the outcome of the most recent API request.
 */
export default function Statusbar({ contextLabel = "", pythonVersion = "Python 3" }) {
  const { token, user } = useAuth();
  const [isReachable, setIsReachable] = useState(true);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const handleConnectivity = (event) => setIsReachable(Boolean(event.detail?.online));
    window.addEventListener("pamsu:connectivity", handleConnectivity);
    const timer = window.setInterval(() => setNow(Date.now()), 30000);
    return () => {
      window.removeEventListener("pamsu:connectivity", handleConnectivity);
      window.clearInterval(timer);
    };
  }, []);

  const status = STATUS_CONFIG[deriveStatus(token, isReachable, now)];

  return (
    <footer
      className="flex h-8 shrink-0 items-center justify-between gap-4 border-t border-border-subtle bg-bg-panel px-4"
      aria-label="Session status"
    >
      <div className="flex min-w-0 items-center gap-2" role="status" aria-live="polite">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${status.dotClass}`} aria-hidden="true" />
        <span className="truncate font-mono text-[11px] text-text-muted">
          {status.label}
          {contextLabel ? ` · ${contextLabel}` : ""}
        </span>
      </div>
      <span className="hidden shrink-0 select-none font-mono text-[11px] text-text-muted sm:inline">
        {pythonVersion}
        {user?.name ? ` · ${user.name}` : ""}
      </span>
    </footer>
  );
}
