/**
 * True for a self-service guest ("Continue as Guest Student"). The sign-in
 * response says so in `is_guest`; servers older than 2026-10-27 don't send
 * it, so the guest email and school ID pattern is checked instead (the same
 * rule as is_guest_identity in backend/app/services/guest_service.py).
 */
export function isGuestUser(user) {
  if (!user) return false;
  if (typeof user.is_guest === "boolean") return user.is_guest;
  return user.role === "student" && /^guest_/i.test(user.email || "") && /^GST/.test(user.school_id || "");
}
