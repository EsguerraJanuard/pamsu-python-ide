import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import Icon from "./Icon";

const MENU_GAP = 6;
const MENU_MARGIN = 8;
const MENU_ITEM_TONES = {
  default: "text-text-main hover:bg-bg-alt focus-visible:bg-bg-alt",
  danger: "text-text-rose hover:bg-psu-red/[0.06] focus-visible:bg-psu-red/[0.06]",
  success: "text-text-emerald hover:bg-emerald-600/[0.07] focus-visible:bg-emerald-600/[0.07]",
};

/**
 * The "⋮" button for one table row and its menu. The menu is rendered in a
 * portal with fixed positioning, so the table's scroll wrapper and the card's
 * rounded clipping never cut it off. It opens below the button (above when
 * there is no room) and closes on a choice, Escape, Tab, an outside click,
 * scrolling or resizing. Arrow keys, Home and End move between items.
 *
 * items: [{ id, label, hint?, icon, onSelect, disabled?, tone?, separatorBefore? }]
 */
export default function RowActionsMenu({ label, items, busy = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const menuId = useId();

  const close = useCallback((returnFocus) => {
    setIsOpen(false);
    setPosition(null);
    if (returnFocus) triggerRef.current?.focus();
  }, []);

  // Measure and place the menu before it is painted.
  useLayoutEffect(() => {
    if (!isOpen || !triggerRef.current || !menuRef.current) return;
    const anchor = triggerRef.current.getBoundingClientRect();
    const { offsetWidth: width, offsetHeight: height } = menuRef.current;
    const roomBelow = window.innerHeight - anchor.bottom - MENU_GAP - MENU_MARGIN;
    const above = height > roomBelow && anchor.top - MENU_GAP - MENU_MARGIN >= height;
    setPosition({
      top: above ? anchor.top - MENU_GAP - height : anchor.bottom + MENU_GAP,
      left: Math.max(MENU_MARGIN, Math.min(anchor.right - width, window.innerWidth - width - MENU_MARGIN)),
      above,
    });
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !position) return;
    menuRef.current?.querySelector('[role="menuitem"]:not(:disabled)')?.focus({ preventScroll: true });
  }, [isOpen, position]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onPointerDown = (event) => {
      if (menuRef.current?.contains(event.target) || triggerRef.current?.contains(event.target)) return;
      close(false);
    };
    // A fixed menu would drift away from its row, so moving the page closes it.
    const onViewportChange = () => close(false);
    document.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
    };
  }, [isOpen, close]);

  const onMenuKeyDown = (event) => {
    const options = [...menuRef.current.querySelectorAll('[role="menuitem"]:not(:disabled)')];
    const index = options.indexOf(document.activeElement);
    const focusAt = (i) => options[(i + options.length) % options.length]?.focus();
    if (event.key === "ArrowDown") focusAt(index + 1);
    else if (event.key === "ArrowUp") focusAt(index - 1);
    else if (event.key === "Home") focusAt(0);
    else if (event.key === "End") focusAt(options.length - 1);
    else if (event.key === "Escape" || event.key === "Tab") close(true);
    else return;
    event.preventDefault();
  };

  const choose = (item) => {
    // Focus goes back to the ⋮ button first, so a dialog the action opens
    // returns focus there when it closes.
    close(true);
    item.onSelect();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
        aria-busy={busy || undefined}
        title="More actions"
        onClick={() => (isOpen ? close(false) : setIsOpen(true))}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" && !isOpen) {
            event.preventDefault();
            setIsOpen(true);
          }
        }}
        className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border transition-colors ${
          isOpen
            ? "border-psu-maroon/40 bg-selected text-text-brand"
            : "border-border-subtle bg-bg-panel text-text-muted hover:border-border-strong hover:bg-bg-alt hover:text-text-main"
        }`}
      >
        {busy ? <Icon name="refresh" className="h-4 w-4 animate-spin" /> : <Icon name="dotsVertical" className="h-4 w-4" strokeWidth={3} />}
      </button>
      {isOpen &&
        createPortal(
          <div
            ref={menuRef}
            id={menuId}
            role="menu"
            aria-label={label}
            onKeyDown={onMenuKeyDown}
            style={{ top: position?.top ?? 0, left: position?.left ?? 0, visibility: position ? "visible" : "hidden" }}
            className={`fixed z-50 w-64 rounded-xl border border-border-subtle bg-bg-panel p-1.5 shadow-[0_16px_40px_-12px_var(--shadow-popover)] animate-scale-in ${
              position?.above ? "origin-bottom-right" : "origin-top-right"
            }`}
          >
            {items.map((item) => (
              <div key={item.id}>
                {item.separatorBefore && <div role="separator" className="mx-1 my-1.5 h-px bg-border-subtle" />}
                <button
                  type="button"
                  role="menuitem"
                  disabled={item.disabled}
                  onClick={() => choose(item)}
                  className={`flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent ${
                    MENU_ITEM_TONES[item.tone || "default"]
                  }`}
                >
                  <Icon name={item.icon} className="mt-0.5 h-4 w-4 shrink-0" />
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    {item.hint && <span className="mt-0.5 block text-xs font-normal leading-snug text-text-muted">{item.hint}</span>}
                  </span>
                </button>
              </div>
            ))}
          </div>,
          document.body,
        )}
    </>
  );
}
