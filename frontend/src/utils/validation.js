/**
 * Class (enrollment) codes: 6 to 20 letters A-Z and digits 0-9, with no
 * spaces or special characters. Same rule as CLASS_CODE_PATTERN in
 * backend/app/schemas/enrollment_schema.py.
 */
export const CLASS_CODE_PATTERN = /^[A-Z0-9]{6,20}$/;

/** An error message for a typed class code, or "" when it is valid. */
export function classCodeError(value) {
  const code = String(value ?? "");
  if (!code) return "Enter the class code from your instructor.";
  if (/\s/.test(code)) return "Class codes have no spaces. Remove the spaces and try again.";
  if (/[^A-Za-z0-9]/.test(code)) return "Class codes use only letters (A–Z) and numbers (0–9), with no symbols.";
  if (code.length < 6 || code.length > 20) return "Class codes are 6 to 20 letters and numbers long.";
  return CLASS_CODE_PATTERN.test(code.toUpperCase()) ? "" : "Enter a valid class code.";
}
