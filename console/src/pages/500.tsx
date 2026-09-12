import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Space_Grotesk, IBM_Plex_Mono } from 'next/font/google';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  weight: ['400', '500', '600', '700'],
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
  weight: ['400', '500', '600', '700'],
});

/**
 * Next.js 14 Static Export Requirement:
 * In Pages router under `output: 'export'`, custom error pages (500.tsx) MUST export
 * getStaticProps. Without it, Next.js attempts Automatic Static Optimization, mutates
 * pages-manifest.json to 'pages/500.html', and fails during secondary static generation
 * with ENOENT rename/open errors.
 */
export const getStaticProps = () => {
  return {
    props: {},
  };
};

export default function Custom500() {
  return (
    <>
      <Head>
        <title>500 · Server error — Rebuttal</title>
        <meta name="robots" content="noindex" />
      </Head>
      <div
        className={`${spaceGrotesk.variable} ${ibmPlexMono.variable} min-h-screen bg-[#EDECE6] text-[#111418] font-sans flex items-center justify-center p-4 sm:p-6`}
        style={{
          backgroundColor: '#EDECE6',
          color: '#111418',
          fontFamily: 'var(--font-sans), Space Grotesk, -apple-system, sans-serif',
        }}
      >
        <article
          className="w-full max-w-xl bg-[#FFFFFF] border-t-2 border-[#111418] border-x border-b border-[#D4D4D8] p-6 sm:p-8 space-y-5 rounded-none shadow-none"
          style={{
            backgroundColor: '#FFFFFF',
            borderTop: '2px solid #111418',
            borderRight: '1px solid #D4D4D8',
            borderBottom: '1px solid #D4D4D8',
            borderLeft: '1px solid #D4D4D8',
            borderRadius: '0px',
            boxShadow: 'none',
          }}
          role="alert"
          aria-live="assertive"
        >
          {/* Case Header */}
          <div
            className="border-b border-[#D4D4D8] pb-3"
            style={{ borderBottom: '1px solid #D4D4D8' }}
          >
            <div
              className="text-[14px] leading-[20px] font-mono text-[#5C6370] mb-1 tabular-nums"
              style={{
                fontFamily: 'var(--font-mono), IBM Plex Mono, monospace',
                color: '#5C6370',
              }}
            >
              500 · Server exception
            </div>
            <h1
              className="text-[27px] leading-[34px] font-medium text-[#111418] tracking-[-0.02em]"
              style={{
                fontSize: '27px',
                lineHeight: '34px',
                letterSpacing: '-0.02em',
                color: '#111418',
              }}
            >
              An unexpected condition interrupted the docket.
            </h1>
          </div>

          {/* Diagnostic Memo Block */}
          <div
            className="space-y-2 text-[14px] leading-[20px] font-mono text-[#5C6370] bg-[#EDECE6]/40 p-3 border border-[#D4D4D8] rounded-none"
            style={{
              fontFamily: 'var(--font-mono), IBM Plex Mono, monospace',
              backgroundColor: 'rgba(237, 236, 230, 0.4)',
              border: '1px solid #D4D4D8',
              borderRadius: '0px',
            }}
          >
            <p className="text-[#111418] font-semibold">
              Status: 500 Internal Server Error
            </p>
            <p className="text-[12px] text-[#5C6370] tabular-nums">
              The case management system failed to process this request.
            </p>
          </div>

          {/* Narrative Memo (≤ 75ch measure) */}
          <p
            className="text-[14px] leading-[22px] text-[#5C6370] max-w-[75ch]"
            style={{
              color: '#5C6370',
              maxWidth: '75ch',
              lineHeight: '1.55',
            }}
          >
            The dispute file could not be generated or retrieved from the server.
            You may re-initialize your session or return to the active case register.
          </p>

          {/* Action Row: Link is ink, underlined, 2px focus offset */}
          <div className="pt-2 flex items-center gap-4 text-[14px] font-mono">
            <Link
              href="/"
              className="underline text-[#111418] font-medium hover:text-[#111418] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#111418] focus-visible:outline-offset-2"
              style={{
                color: '#111418',
                fontFamily: 'var(--font-mono), IBM Plex Mono, monospace',
                textUnderlineOffset: '3px',
              }}
            >
              Return to docket
            </Link>
          </div>
        </article>
      </div>
    </>
  );
}
