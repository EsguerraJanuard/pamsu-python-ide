/**
 * Reads the claims of the access token issued by POST /login and POST /guest.
 *
 * The token carries only `sub` (account id), `pamsu_user_role` and `pwd_ver`
 * plus the standard type/iat/exp/jti claims. The browser cannot verify the
 * signature (the key stays on the server), so the role read here is used for
 * routing and display only. The server authorizes every request from its own
 * database record, never from these claims.
 */

export const ROLE_CLAIM = "pamsu_user_role";

const VALID_ROLES = new Set(["student", "instructor", "admin"]);

/** The decoded payload, or null if the token is malformed. */
export function decodeTokenPayload(token) {
  if (typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length !== 3 || !parts[1]) return null;
  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const bytes = Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    return payload && typeof payload === "object" && !Array.isArray(payload) ? payload : null;
  } catch {
    return null;
  }
}

/**
 * The account role from the token, or null if it is missing or unknown.
 * Tokens from a server older than 2026-10-27 name it `role`.
 */
export function roleFromToken(token) {
  const payload = decodeTokenPayload(token);
  const role = payload?.[ROLE_CLAIM] ?? payload?.role;
  return VALID_ROLES.has(role) ? role : null;
}

/** The account id (`sub`) as a number, or null. */
export function userIdFromToken(token) {
  const id = Number(decodeTokenPayload(token)?.sub);
  return Number.isInteger(id) && id > 0 ? id : null;
}

/** True once the token's `exp` time has passed. Malformed tokens count as expired. */
export function isTokenExpired(token, now = Date.now()) {
  const payload = decodeTokenPayload(token);
  if (!payload) return true;
  return typeof payload.exp === "number" && payload.exp * 1000 <= now;
}
