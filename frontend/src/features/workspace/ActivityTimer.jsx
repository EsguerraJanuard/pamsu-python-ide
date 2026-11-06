import { useEffect, useEffectEvent, useState } from "react";
import PropTypes from "prop-types";
import Icon from "../../components/ui/Icon";

// Checked 4× a second so a tick is never shown late; the time itself comes
// from the end timestamp, so a throttled background tab still ends on time.
const TICK_MS = 250;
// Seconds left at which the student is warned.
const WARNINGS = [5 * 60, 60];

const pad = (value) => String(value).padStart(2, "0");

/** 754 → "12:34"; 3_754 → "1:02:34". */
export function formatClock(totalSeconds) {
  const seconds = Math.max(0, totalSeconds);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(rest)}` : `${pad(minutes)}:${pad(rest)}`;
}

const secondsUntil = (endsAtMs) => Math.max(0, Math.ceil((endsAtMs - Date.now()) / 1000));

/**
 * Server timer → device-clock milliseconds. server_now corrects for a device
 * clock that is off, so every student's timer ends at the server's ends_at.
 */
export function toClientTimer(body) {
  const skew = new Date(body.server_now).getTime() - Date.now();
  const toDeviceMs = (value) => (value ? new Date(value).getTime() - skew : null);
  return { ...body, endsAtMs: toDeviceMs(body.ends_at), submitUntilMs: toDeviceMs(body.submit_until) };
}

/**
 * Seconds left until endsAtMs, updated by a setInterval. Calls onExpire once
 * at 00:00 (at once if the time is already up) and onWarning(seconds) when
 * 5 minutes and 1 minute are left.
 */
export function useCountdown(endsAtMs, { onExpire, onWarning } = {}) {
  const [secondsLeft, setSecondsLeft] = useState(null);
  const expire = useEffectEvent(() => onExpire?.());
  const warn = useEffectEvent((seconds) => onWarning?.(seconds));

  useEffect(() => {
    if (!endsAtMs) {
      setSecondsLeft(null);
      return undefined;
    }
    let last = secondsUntil(endsAtMs);
    setSecondsLeft(last);
    if (last === 0) {
      expire();
      return undefined;
    }
    const interval = window.setInterval(() => {
      const next = secondsUntil(endsAtMs);
      if (next === last) return;
      WARNINGS.forEach((mark) => {
        if (last > mark && next <= mark && next > 0) warn(mark);
      });
      last = next;
      setSecondsLeft(next);
      if (next === 0) {
        window.clearInterval(interval);
        expire();
      }
    }, TICK_MS);
    return () => window.clearInterval(interval);
  }, [endsAtMs]);

  return secondsLeft;
}

const TONES = {
  idle: "border-border-subtle bg-bg-alt text-text-muted",
  calm: "border-border-subtle bg-bg-panel text-text-main",
  warning: "border-psu-gold/50 bg-psu-gold/10 text-text-amber",
  urgent: "border-psu-red/30 bg-psu-red/[0.08] text-text-rose",
};

/**
 * Countdown for the workspace header. Before the student starts it shows the
 * limit; while running, the time left; afterwards 00:00.
 */
export default function ActivityTimer({ limitMinutes, endsAtMs, running, timeUp, onExpire, onWarning }) {
  const secondsLeft = useCountdown(running ? endsAtMs : null, { onExpire, onWarning });

  if (!running && !timeUp) {
    return (
      <div className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold ${TONES.idle}`}>
        <Icon name="clock" className="h-3.5 w-3.5" />
        Timed · {limitMinutes} min
      </div>
    );
  }

  const seconds = timeUp ? 0 : secondsLeft ?? limitMinutes * 60;
  const tone = timeUp || seconds <= 60 ? "urgent" : seconds <= 5 * 60 ? "warning" : "calm";
  const minutesLeft = Math.ceil(seconds / 60);

  return (
    <div
      role="timer"
      aria-label={timeUp ? "Time is up" : `Time left: about ${minutesLeft} ${minutesLeft === 1 ? "minute" : "minutes"}`}
      title={timeUp ? "Time is up" : "Time left. The timer cannot be paused."}
      className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs transition-colors ${TONES[tone]}`}
    >
      <Icon name="clock" className={`h-3.5 w-3.5 ${tone === "urgent" && !timeUp ? "animate-pulse" : ""}`} />
      <span className="font-mono text-sm font-semibold tabular-nums" aria-hidden="true">
        {formatClock(seconds)}
      </span>
      {timeUp && <span className="font-semibold">Time is up</span>}
    </div>
  );
}

ActivityTimer.propTypes = {
  limitMinutes: PropTypes.number.isRequired,
  endsAtMs: PropTypes.number,
  running: PropTypes.bool.isRequired,
  timeUp: PropTypes.bool.isRequired,
  onExpire: PropTypes.func,
  onWarning: PropTypes.func,
};
