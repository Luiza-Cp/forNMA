import React from "react";
import { createPortal } from "react-dom";

let tipCounter = 0;

// Help badge: opens on hover, keyboard focus or click (click keeps it open); Esc closes.
export function Tip({ text }) {
  const [open, setOpen] = React.useState(false);
  const [pinned, setPinned] = React.useState(false);
  const [position, setPosition] = React.useState({ left: 0, top: 0, below: false });
  const buttonRef = React.useRef(null);
  const closeTimerRef = React.useRef(null);
  const idRef = React.useRef(null);
  if (idRef.current === null) {
    tipCounter += 1;
    idRef.current = `tip-${tipCounter}`;
  }

  const clearCloseTimer = () => {
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  React.useEffect(() => clearCloseTimer, []);

  React.useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        setPinned(false);
      }
    };
    const onScroll = () => {
      setOpen(false);
      setPinned(false);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open]);

  const show = () => {
    clearCloseTimer();
    const rect = buttonRef.current?.getBoundingClientRect();
    if (rect) {
      const below = rect.top < 120;
      setPosition({
        left: Math.min(window.innerWidth - 150, Math.max(150, rect.left + rect.width / 2)),
        top: below ? rect.bottom + 8 : Math.max(12, rect.top - 8),
        below,
      });
    }
    setOpen(true);
  };

  const hideSoon = () => {
    if (pinned) return;
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => setOpen(false), 140);
  };

  if (!text) return null;

  return (
    <span className="tip-wrap">
      <button
        ref={buttonRef}
        type="button"
        className="tip-badge"
        aria-label="More information"
        aria-describedby={open ? idRef.current : undefined}
        aria-expanded={open}
        onMouseEnter={show}
        onMouseLeave={hideSoon}
        onFocus={show}
        onBlur={() => {
          setPinned(false);
          hideSoon();
        }}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          if (pinned) {
            setPinned(false);
            setOpen(false);
          } else {
            setPinned(true);
            show();
          }
        }}
      >
        i
      </button>
      {open && typeof document !== "undefined" && createPortal(
        <span
          id={idRef.current}
          className={`tip-popover ${position.below ? "below" : ""}`}
          role="tooltip"
          style={{ left: position.left, top: position.top }}
          onMouseEnter={clearCloseTimer}
          onMouseLeave={hideSoon}
          onMouseDown={(event) => event.preventDefault()}
        >
          {text}
        </span>,
        document.body
      )}
    </span>
  );
}
