import { useEffect, useState } from "react";

import { copyText } from "../../utils/clipboard";
import Icon from "./Icon";

/**
 * Labelled, read-only code block with a copy button (test-case input and
 * expected output). Empty `code` shows `emptyText` and disables copying.
 */
export default function CodePanel({ label, code, emptyText = "(none)", maxHeight = "max-h-40" }) {
  const [copyState, setCopyState] = useState("idle"); // idle | copied | failed
  const hasCode = Boolean(code);

  useEffect(() => {
    if (copyState === "idle") return undefined;
    const timer = setTimeout(() => setCopyState("idle"), 2000);
    return () => clearTimeout(timer);
  }, [copyState]);

  const handleCopy = async () => {
    setCopyState((await copyText(code)) ? "copied" : "failed");
  };

  return (
    <div className="overflow-hidden rounded-lg border border-border-subtle bg-bg-panel">
      <div className="flex items-center justify-between gap-2 border-b border-border-subtle bg-bg-alt/70 py-1 pl-3 pr-1">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{label}</span>
        <button
          type="button"
          onClick={handleCopy}
          disabled={!hasCode}
          aria-label={`Copy ${label.toLowerCase()}`}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-semibold text-text-muted transition-colors hover:bg-bg-panel hover:text-text-main disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
        >
          <Icon name={copyState === "copied" ? "tick" : "copy"} className={`h-3.5 w-3.5 ${copyState === "copied" ? "text-text-emerald" : ""}`} />
          <span aria-live="polite">{copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}</span>
        </button>
      </div>
      <pre className={`${maxHeight} overflow-auto p-3 font-mono text-xs leading-relaxed ${hasCode ? "text-text-main" : "italic text-text-muted"}`}>
        {hasCode ? code : emptyText}
      </pre>
    </div>
  );
}
