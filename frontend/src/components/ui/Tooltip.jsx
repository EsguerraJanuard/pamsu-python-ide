import { cloneElement, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

const GAP = 8;
const VIEWPORT_MARGIN = 8;

function placeTooltip(anchor, tip, side) {
  const width = tip.offsetWidth;
  const height = tip.offsetHeight;
  let left;
  let top;

  if (side === "right") {
    left = anchor.right + GAP;
    top = anchor.top + (anchor.height - height) / 2;
  } else {
    left = anchor.left + (anchor.width - width) / 2;
    top = side === "bottom" ? anchor.bottom + GAP : anchor.top - height - GAP;
    // Not enough room on the requested side: flip vertically.
    if (side === "top" && top < VIEWPORT_MARGIN) top = anchor.bottom + GAP;
    if (side === "bottom" && top + height > window.innerHeight - VIEWPORT_MARGIN) top = anchor.top - height - GAP;
  }

  const maxLeft = window.innerWidth - width - VIEWPORT_MARGIN;
  const maxTop = window.innerHeight - height - VIEWPORT_MARGIN;
  return {
    left: Math.max(VIEWPORT_MARGIN, Math.min(left, maxLeft)),
    top: Math.max(VIEWPORT_MARGIN, Math.min(top, maxTop)),
  };
}

const isKeyboardFocus = (element) => {
  try {
    return element.matches(":focus-visible");
  } catch {
    return true;
  }
};

/**
 * Small visual tooltip for icon-only controls. It shows on hover and on
 * keyboard focus, hides on Escape, blur, scroll or resize, and is rendered in
 * a portal with fixed positioning so `overflow-hidden` containers (such as
 * the sidebar rail) never clip it. It is clamped to the viewport.
 *
 * The tooltip is a sighted-user mirror only (`aria-hidden`): the trigger must
 * carry its own accessible name (`aria-label`) and, when needed, an
 * `aria-describedby` that points at text which is always in the DOM.
 *
 * `children` must be a single element that accepts mouse/focus handlers.
 */
export default function Tooltip({ content, side = "top", children }) {
  const [anchor, setAnchor] = useState(null);
  const [position, setPosition] = useState(null);
  const tipRef = useRef(null);

  const show = (element) => {
    setPosition(null);
    setAnchor(element.getBoundingClientRect());
  };
  const hide = () => setAnchor(null);

  useLayoutEffect(() => {
    if (anchor && tipRef.current) setPosition(placeTooltip(anchor, tipRef.current, side));
  }, [anchor, side, content]);

  useEffect(() => {
    if (!anchor) return undefined;
    const handleKey = (event) => {
      if (event.key === "Escape") hide();
    };
    window.addEventListener("keydown", handleKey);
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide);
    return () => {
      window.removeEventListener("keydown", handleKey);
      window.removeEventListener("scroll", hide, true);
      window.removeEventListener("resize", hide);
    };
  }, [anchor]);

  const chain = (handler, own) => (event) => {
    handler?.(event);
    own(event);
  };

  const trigger = cloneElement(children, {
    onMouseEnter: chain(children.props.onMouseEnter, (event) => show(event.currentTarget)),
    onMouseLeave: chain(children.props.onMouseLeave, hide),
    onFocus: chain(children.props.onFocus, (event) => {
      if (isKeyboardFocus(event.currentTarget)) show(event.currentTarget);
    }),
    onBlur: chain(children.props.onBlur, hide),
  });

  return (
    <>
      {trigger}
      {anchor &&
        content &&
        createPortal(
          <div
            ref={tipRef}
            aria-hidden="true"
            style={position ?? { left: 0, top: 0, visibility: "hidden" }}
            className="pointer-events-none fixed z-[110] max-w-[220px] rounded-md bg-text-main px-2 py-1 text-[11px] font-medium leading-snug text-bg-panel shadow-[0_4px_12px_var(--shadow-popover)]"
          >
            {content}
          </div>,
          document.body,
        )}
    </>
  );
}
