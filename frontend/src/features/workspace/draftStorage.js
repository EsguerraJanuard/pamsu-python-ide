/**
 * Local autosave for the activity workspace.
 *
 * Lab computers are shared, so a draft belongs to one account: the key
 * carries the user id, and signing out removes every saved draft.
 * Drafts saved by older builds (keyed by activity only) are discarded,
 * because the account that wrote them is unknown.
 */

const DRAFT_PREFIX = "pamsu-workspace-draft-";
const LEGACY_DRAFT_KEY = /^pamsu-workspace-draft-\d+$/;

export function draftKeyFor(userId, activityId) {
  return `${DRAFT_PREFIX}u${userId}-${activityId}`;
}

export function readDraft(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function saveDraft(key, code) {
  try {
    localStorage.setItem(key, code);
  } catch {
    // The editor remains usable without storage.
  }
}

function removeDrafts(matches) {
  try {
    const keys = [];
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      if (key && matches(key)) keys.push(key);
    }
    keys.forEach((key) => localStorage.removeItem(key));
  } catch {
    // Storage unavailable.
  }
}

/** Removes every workspace draft on this browser (used on sign-out). */
export function clearAllDrafts() {
  removeDrafts((key) => key.startsWith(DRAFT_PREFIX));
}

/** Removes drafts saved before drafts were scoped to an account. */
export function clearLegacyDrafts() {
  removeDrafts((key) => LEGACY_DRAFT_KEY.test(key));
}
