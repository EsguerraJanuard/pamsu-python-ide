import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

const LIST_GAP = 6;
const LIST_MARGIN = 8;

/**
 * Styled single-select with listbox semantics and full keyboard support
 * (Enter/Space/ArrowDown open; arrows move; Enter selects; Escape closes).
 *
 * The option list is rendered in a portal with fixed positioning, so a card
 * with overflow-hidden (or a modal body) never clips it. It opens below the
 * button, above when there is no room, and follows the button on scroll.
 */
export default function CustomSelect({
  options,
  value,
  onChange,
  placeholder = "Select an option",
  className = "",
  ariaLabel,
  id,
  disabled = false,
}) {
  const generatedId = useId();
  const buttonId = id || `${generatedId}-button`;
  const listboxId = `${generatedId}-listbox`;
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [position, setPosition] = useState(null);
  const containerRef = useRef(null);
  const buttonRef = useRef(null);
  const listRef = useRef(null);

  const selectedIndex = options.findIndex((opt) => String(opt.value) === String(value));
  const selectedOption = selectedIndex >= 0 ? options[selectedIndex] : null;

  const place = useCallback(() => {
    if (!buttonRef.current || !listRef.current) return;
    const anchor = buttonRef.current.getBoundingClientRect();
    const height = listRef.current.offsetHeight;
    const roomBelow = window.innerHeight - anchor.bottom - LIST_GAP - LIST_MARGIN;
    const above = height > roomBelow && anchor.top - LIST_GAP - LIST_MARGIN >= height;
    setPosition({
      top: above ? anchor.top - LIST_GAP - height : anchor.bottom + LIST_GAP,
      left: anchor.left,
      width: anchor.width,
    });
  }, []);

  // Measure and place the list before it is painted.
  useLayoutEffect(() => {
    if (isOpen) place();
    else setPosition(null);
  }, [isOpen, place]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const handleClickOutside = (event) => {
      if (containerRef.current?.contains(event.target) || listRef.current?.contains(event.target)) return;
      setIsOpen(false);
    };
    // Scrolling the page moves the button, so the fixed list follows it;
    // scrolling inside the list itself needs nothing.
    const handleScroll = (event) => {
      if (listRef.current?.contains(event.target)) return;
      place();
    };
    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("scroll", handleScroll, true);
    window.addEventListener("resize", place);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", handleScroll, true);
      window.removeEventListener("resize", place);
    };
  }, [isOpen, place]);

  // Keep the highlighted option visible while moving through a long list.
  useEffect(() => {
    if (!isOpen || activeIndex < 0) return;
    document.getElementById(`${listboxId}-${activeIndex}`)?.scrollIntoView({ block: "nearest" });
  }, [isOpen, activeIndex, listboxId, position]);

  const open = () => {
    if (disabled) return;
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setIsOpen(true);
  };

  const choose = (index) => {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setIsOpen(false);
    buttonRef.current?.focus();
  };

  const handleKeyDown = (event) => {
    if (!isOpen) {
      if (["Enter", " ", "ArrowDown", "ArrowUp"].includes(event.key)) {
        event.preventDefault();
        open();
      }
      return;
    }
    if (event.key === "Escape" || event.key === "Tab") {
      if (event.key === "Escape") event.preventDefault();
      setIsOpen(false);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(options.length - 1, i + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(0, i - 1));
    } else if (event.key === "Home") {
      event.preventDefault();
      setActiveIndex(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActiveIndex(options.length - 1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      choose(activeIndex);
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        ref={buttonRef}
        id={buttonId}
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        aria-label={ariaLabel}
        aria-activedescendant={isOpen && activeIndex >= 0 ? `${listboxId}-${activeIndex}` : undefined}
        onClick={() => (isOpen ? setIsOpen(false) : open())}
        onKeyDown={handleKeyDown}
        // Same border, hover and focus ring as .input-field, from the theme tokens
        // (maroon in light mode, gold in dark mode); the ring also shows while open.
        className={`group flex w-full items-center justify-between gap-2 rounded-lg border border-border-strong bg-bg-panel text-left text-text-main shadow-sm transition-[border-color,box-shadow] hover:border-text-muted/60 focus:border-border-focus focus:outline-none focus:ring-2 focus:ring-border-focus/20 disabled:cursor-not-allowed disabled:bg-bg-alt disabled:text-text-muted disabled:shadow-none ${
          isOpen ? "border-border-focus ring-2 ring-border-focus/20" : ""
        } ${className || "px-3 py-2 text-sm"}`}
      >
        <span className={`truncate ${selectedOption ? "text-text-main" : "text-text-muted"}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg
          className={`h-4 w-4 shrink-0 transition-[transform,color] duration-150 ${
            isOpen ? "rotate-180 text-text-brand" : "text-text-muted group-hover:text-text-main"
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen &&
        createPortal(
          <ul
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-labelledby={buttonId}
            style={{
              top: position?.top ?? 0,
              left: position?.left ?? 0,
              width: position?.width,
              visibility: position ? "visible" : "hidden",
            }}
            // Above modals (z-[100]), so a select inside a dialog still shows its list.
            className="fixed z-[110] max-h-60 overflow-y-auto rounded-lg border border-border-subtle bg-bg-panel py-1 shadow-[0_16px_40px_-12px_var(--shadow-popover)] animate-scale-in"
          >
            {options.length === 0 && <li className="px-3 py-2.5 text-center text-sm italic text-text-muted">No options available</li>}
            {options.map((opt, index) => {
              const isSelected = index === selectedIndex;
              const isActive = index === activeIndex;
              return (
                <li
                  key={opt.value}
                  id={`${listboxId}-${index}`}
                  role="option"
                  aria-selected={isSelected}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(index)}
                  className={`flex cursor-pointer items-center justify-between gap-3 px-3 py-2.5 text-sm ${
                    isActive ? "bg-bg-alt" : ""
                  } ${isSelected ? "font-semibold text-text-brand" : "text-text-main"}`}
                >
                  <span>{opt.label}</span>
                  {isSelected && (
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </li>
              );
            })}
          </ul>,
          document.body,
        )}
    </div>
  );
}
