import { Component } from "react";

/**
 * Last-resort boundary so a rendering bug shows a branded recovery screen
 * instead of a blank page. Technical details go to the console only.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Unhandled UI error:", error, info?.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <main className="flex min-h-screen items-center justify-center bg-bg-base p-6 text-text-main">
        <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-panel p-8 text-center shadow-sm">
          <img src="/school_logo.png" alt="Pampanga State University logo" className="mx-auto mb-5 h-14 w-14 object-contain" />
          <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">PAMSU Python IDE</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">Something went wrong</h1>
          <p className="mt-2 text-sm leading-relaxed text-text-muted">
            This page ran into an unexpected problem and could not be displayed. Your saved work is not affected.
            Reloading usually fixes it.
          </p>
          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">
            <button type="button" className="btn-primary" onClick={() => window.location.reload()}>
              Reload page
            </button>
            <button type="button" className="btn-secondary" onClick={() => window.location.assign("/")}>
              Go to my dashboard
            </button>
          </div>
        </div>
      </main>
    );
  }
}
