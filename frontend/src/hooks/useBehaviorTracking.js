import { useEffect, useRef, useState } from "react";
import api from "../services/api";

/**
 * Counts review indicators while a student works:
 * - tab switches (document hidden)
 * - pointer leaving the window
 * - blocked external pastes (incremented by the caller)
 *
 * When a coding session id is provided, increments are synced to it every
 * 5 seconds. Only counts are sent — never content.
 */
export function useBehaviorTracking({ sessionId }) {
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [mouseLeaveCount, setMouseLeaveCount] = useState(0);
  const [blockedPasteCount, setBlockedPasteCount] = useState(0);

  const latest = useRef({ tab: 0, paste: 0, mouse: 0 });
  const synced = useRef({ tab: 0, paste: 0, mouse: 0 });

  useEffect(() => {
    latest.current = { tab: tabSwitchCount, paste: blockedPasteCount, mouse: mouseLeaveCount };
  }, [tabSwitchCount, blockedPasteCount, mouseLeaveCount]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) setTabSwitchCount((c) => c + 1);
    };
    const handleMouseLeave = () => setMouseLeaveCount((c) => c + 1);

    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.documentElement.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return undefined;

    const interval = setInterval(async () => {
      const current = latest.current;
      const increments = {
        tab: Math.max(0, current.tab - synced.current.tab),
        paste: Math.max(0, current.paste - synced.current.paste),
        mouse: Math.max(0, current.mouse - synced.current.mouse),
      };
      if (!increments.tab && !increments.paste && !increments.mouse) return;

      try {
        await api.patch(`/activities/coding-sessions/${sessionId}/activity`, {
          tab_switch_increment: increments.tab,
          blocked_paste_increment: increments.paste,
          mouseleave_increment: increments.mouse,
          idle_duration_increment_seconds: 0,
        });
        synced.current = { ...current };
      } catch (err) {
        // Keep the unsent increments; they are retried on the next tick.
        console.warn("Activity indicator sync failed", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return {
    tabSwitchCount,
    mouseLeaveCount,
    blockedPasteCount,
    setBlockedPasteCount,
  };
}
