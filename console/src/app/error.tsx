'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console for diagnostic tracing
    console.error('Docket application error:', error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4 font-sans">
      <article
        className="w-full max-w-xl bg-sheet border-t-2 border-rule-strong border-x border-b border-rule p-6 sm:p-8 space-y-5"
        role="alert"
        aria-live="assertive"
      >
        <div className="border-b border-rule pb-3">
          <div className="text-xs font-mono text-secondary-ink mb-1">
            System notice · Docket exception
          </div>
          <h1 className="text-xl font-medium text-ink tracking-tight">
            An error interrupted the docket.
          </h1>
        </div>

        <div className="space-y-2 text-xs font-mono text-secondary-ink bg-desk/40 p-3 border border-rule">
          <p className="text-ink font-semibold">
            {error.name || 'Application Error'}: {error.message || 'An unexpected runtime error occurred.'}
          </p>
          {error.digest && (
            <p className="text-[11px] tabular-nums">
              Digest reference: {error.digest}
            </p>
          )}
        </div>

        <p className="text-xs text-secondary-ink leading-relaxed">
          The dispute file could not be rendered completely. You may re-initialize the docket session or return to the main case register.
        </p>

        <div className="pt-2 flex items-center gap-4 text-xs font-mono">
          <button
            type="button"
            onClick={() => reset()}
            className="px-3 py-1.5 bg-ink text-sheet font-medium hover:opacity-90 transition-opacity focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
          >
            Retry session
          </button>
          <Link
            href="/"
            className="underline text-ink hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
          >
            Return to docket
          </Link>
        </div>
      </article>
    </div>
  );
}
