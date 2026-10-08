import { useEffect, useRef, useState } from "react";
import api from "../services/api";

/**
 * Custom hook that encapsulates all behavior-tracking logic:
 * - Tab switch detection (visibilitychange + blur)
 * - Mouse leave detection
 * - Blocked paste counting
 * - Telemetry heartbeat to backend
 *
 * Returns state variables and helpers for the Workspace component.
 */
export function useBehaviorTracking({ sessionId }) {
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [mouseLeaveCount, setMouseLeaveCount] = useState(0);
  const [blockedPasteCount, setBlockedPasteCount] = useState(0);
  const [showBehaviorNotice, setShowBehaviorNotice] = useState(false);

  // Keep a ref mirror so the heartbeat interval always reads fresh values
  const stateRefs = useRef({ tabSwitchCount: 0, blockedPasteCount: 0, mouseLeaveCount: 0 });
  useEffect(() => {
    stateRefs.current = { tabSwitchCount, blockedPasteCount, mouseLeaveCount };
  }, [tabSwitchCount, blockedPasteCount, mouseLeaveCount]);

  // Visibility change + blur listeners
  useEffect(() => {
    const handleLossOfFocus = () => {
      setTabSwitchCount((c) => c + 1);
      setShowBehaviorNotice(true);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) handleLossOfFocus();
    };

    const handleMouseLeave = () => {
      setMouseLeaveCount((c) => c + 1);
      setShowBehaviorNotice(true);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleLossOfFocus);
    document.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleLossOfFocus);
      document.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  // Telemetry heartbeat - sends increments every 5 seconds
  const lastCounts = useRef({ tab: 0, paste: 0, mouse: 0 });
  useEffect(() => {
    const interval = setInterval(async () => {
      const currentTab = stateRefs.current.tabSwitchCount;
      const currentPaste = stateRefs.current.blockedPasteCount;
      const currentMouse = stateRefs.current.mouseLeaveCount;

      const tabInc = Math.max(0, currentTab - lastCounts.current.tab);
      const pasteInc = Math.max(0, currentPaste - lastCounts.current.paste);
      const mouseInc = Math.max(0, currentMouse - lastCounts.current.mouse);

      if (tabInc === 0 && pasteInc === 0 && mouseInc === 0) return;

      try {
        if (sessionId) {
          await api.patch(`/activities/coding-sessions/${sessionId}/activity`, {
            tab_switch_increment: tabInc,
            blocked_paste_increment: pasteInc,
            mouseleave_increment: mouseInc,
            idle_duration_increment_seconds: 0,
          }).catch(() => {});
        }
        
        // Also deduct integrity points globally!
        await api.patch('/users/me/integrity', {
            is_graded: !!sessionId,
            tab_switch_increment: tabInc,
            blocked_paste_increment: pasteInc,
            mouseleave_increment: mouseInc,
        }).catch(() => {});

        lastCounts.current.tab = currentTab;
        lastCounts.current.paste = currentPaste;
        lastCounts.current.mouse = currentMouse;
      } catch (err) {
        console.error("Failed to send heartbeat", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return {
    tabSwitchCount,
    mouseLeaveCount,
    blockedPasteCount,
    setBlockedPasteCount,
    showBehaviorNotice,
    setShowBehaviorNotice,
  };
}
