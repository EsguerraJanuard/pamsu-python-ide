/**
 * Pill on/off switch (a button with role="switch"). Name it with a
 * <label htmlFor={id}> or `aria-labelledby`; other props go to the button.
 */
export default function Switch({ id, checked, onChange, disabled = false, className = "", ...buttonProps }) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-out focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-focus disabled:cursor-not-allowed disabled:opacity-50 ${
        checked ? "bg-psu-maroon" : "bg-border-strong hover:bg-text-muted/40"
      } ${className}`}
      {...buttonProps}
    >
      <span
        aria-hidden="true"
        className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm ring-1 ring-black/5 transition-transform duration-200 ease-out ${
          checked ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}
