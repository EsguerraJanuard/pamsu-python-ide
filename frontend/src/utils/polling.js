/**
 * Pause before the next status check of code running in the background
 * (IDE Run, practice submit). `waitedMs` is the total of the pauses so far.
 *
 * Judge0 usually answers within 1–3 s, so the first seconds are checked
 * often, then less often. The old schedule checked every 1500 ms from the
 * start; every one of those times is still a check here (1500, 3000, 4500,
 * 6000, then every 1500), so a result is never shown later than before, and
 * one that is ready early is shown up to 1 s sooner.
 */
export function pollDelay(waitedMs) {
  if (waitedMs < 3000) return 500;
  if (waitedMs < 6000) return 750;
  return 1500;
}
