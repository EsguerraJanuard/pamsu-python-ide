import { useCallback, useEffect, useRef, useState } from "react";
import api, { NETWORK_ERROR_STATUS, TIMEOUT_ERROR_STATUS } from "../services/api";

const SYNC_INTERVAL_MS = 5000;
// A zero-count update is a heartbeat. It keeps the session on the instructor's
// Live Monitoring page, which drops sessions quiet for longer than
// LIVE_SESSION_WINDOW (3 minutes) in backend/app/services/coding_session_service.py.
const HEARTBEAT_INTERVAL_MS = 30000;
const START_RETRY_MS = 15000;
// Per-request caps from CodingSessionActivityUpdate; anything above waits for the next tick.
const MAX_INCREMENT = { tab: 100, paste: 100, mouse: 500 };
const NO_COUNTS = { tab: 0, paste: 0, mouse: 0 };

// React StrictMode runs effects twice in development. Sharing the in-flight
// start request per activity keeps that from opening two sessions.
const startRequests = new Map();

function startOrResumeSession(taskId) {
  const key = String(taskId);
  let pending = startRequests.get(key);
  if (!pending) {
    pending = api
      .post("/activities/coding-sessions/", { task_id: Number(taskId) })
      .finally(() => startRequests.delete(key));
    startRequests.set(key, pending);
  }
  return pending;
}

// Server unreachable, slow, busy, or a write conflict: worth trying again later.
function isTemporaryFailure(err) {
  const status = err?.status;
  return (
    status === NETWORK_ERROR_STATUS ||
    status === TIMEOUT_ERROR_STATUS ||
    status === 409 ||
    status === 429 ||
    status >= 500
  );
}

/**
 * Counts review indicators while a student works:
 * - tab switches (document hidden)
 * - pointer leaving the window
 * - blocked external pastes (reported by the caller with recordBlockedPaste)
 *
 * With a taskId, the hook starts (or resumes) the student's coding session for
 * that activity, sends new counts every 5 seconds and a heartbeat every 30, so
 * the instructor sees the session on Live Monitoring and the grading bench.
 * Without a taskId (practice), counts stay in this browser.
 *
 * Only counts are sent, never content. Shown counts are the session totals on
 * the server plus anything not sent yet, so they match what the instructor sees.
 */
export function useBehaviorTracking({ taskId = null } = {}) {
  const [session, setSession] = useState(null);
  const [unsent, setUnsent] = useState(NO_COUNTS);
  const [restartKey, setRestartKey] = useState(0);

  // Refs mirror the state for timers and async callbacks.
  const sessionRef = useRef(null);
  const unsentRef = useRef(NO_COUNTS);
  const syncQueue = useRef(Promise.resolve(null));
  const isSyncing = useRef(false);
  const lastSentAt = useRef(0);

  const addCount = useCallback((key) => {
    unsentRef.current = { ...unsentRef.current, [key]: unsentRef.current[key] + 1 };
    setUnsent(unsentRef.current);
  }, []);

  const recordBlockedPaste = useCallback(() => addCount("paste"), [addCount]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) addCount("tab");
    };
    const handleMouseLeave = () => addCount("mouse");

    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.documentElement.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [addCount]);

  // Start or resume the session. Runs again when a sync finds it gone or ended.
  useEffect(() => {
    if (!taskId) return undefined;
    let cancelled = false;
    let retryTimer = null;

    const begin = () => {
      startOrResumeSession(taskId)
        .then((started) => {
          if (cancelled) return;
          sessionRef.current = started;
          lastSentAt.current = Date.now();
          setSession(started);
        })
        .catch((err) => {
          if (cancelled) return;
          if (isTemporaryFailure(err)) {
            retryTimer = window.setTimeout(begin, START_RETRY_MS);
          } else {
            console.warn("No coding session for this activity; indicators stay in this browser.", err);
          }
        });
    };

    begin();
    return () => {
      cancelled = true;
      window.clearTimeout(retryTimer);
      sessionRef.current = null;
    };
  }, [taskId, restartKey]);

  /**
   * Sends the unsent counts now (all zero acts as a heartbeat) and resolves to
   * the updated session, or null when there is no session or the send failed.
   * Calls run one at a time, so the same counts are never sent twice.
   */
  const flush = useCallback(() => {
    const run = syncQueue.current.then(async () => {
      const current = sessionRef.current;
      if (!current) return null;

      const pending = unsentRef.current;
      const sent = {
        tab: Math.min(pending.tab, MAX_INCREMENT.tab),
        paste: Math.min(pending.paste, MAX_INCREMENT.paste),
        mouse: Math.min(pending.mouse, MAX_INCREMENT.mouse),
      };

      isSyncing.current = true;
      try {
        const updated = await api.patch(`/activities/coding-sessions/${current.session_id}/activity`, {
          tab_switch_increment: sent.tab,
          blocked_paste_increment: sent.paste,
          mouseleave_increment: sent.mouse,
          idle_duration_increment_seconds: 0,
        });

        const left = unsentRef.current;
        unsentRef.current = { tab: left.tab - sent.tab, paste: left.paste - sent.paste, mouse: left.mouse - sent.mouse };
        setUnsent(unsentRef.current);
        lastSentAt.current = Date.now();
        // Skip the copy if the session was replaced while this request was out.
        if (sessionRef.current?.session_id === current.session_id) {
          sessionRef.current = updated;
          setSession(updated);
        }
        return updated;
      } catch (err) {
        if ((err?.status === 404 || err?.status === 409) && sessionRef.current?.session_id === current.session_id) {
          // The session is gone or has ended: start or resume one. The counts
          // stay unsent until that works.
          sessionRef.current = null;
          setRestartKey((key) => key + 1);
        } else {
          console.warn("Activity indicator sync failed; retrying on the next tick.", err);
        }
        return null;
      } finally {
        isSyncing.current = false;
      }
    });
    syncQueue.current = run;
    return run;
  }, []);

  useEffect(() => {
    if (!taskId) return undefined;
    const timer = window.setInterval(() => {
      if (!sessionRef.current || isSyncing.current) return;
      const pending = unsentRef.current;
      const hasCounts = pending.tab > 0 || pending.paste > 0 || pending.mouse > 0;
      if (hasCounts || Date.now() - lastSentAt.current >= HEARTBEAT_INTERVAL_MS) flush();
    }, SYNC_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [taskId, flush]);

  return {
    sessionId: session?.session_id ?? null,
    session,
    tabSwitchCount: (session?.tab_switch_count ?? 0) + unsent.tab,
    blockedPasteCount: (session?.blocked_paste_count ?? 0) + unsent.paste,
    mouseLeaveCount: (session?.mouseleave_count ?? 0) + unsent.mouse,
    recordBlockedPaste,
    flush,
  };
}
