'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import CaseDetailsClient from './[id]/CaseDetailsClient';

function CaseQuery() {
  const disputeId = useSearchParams()?.get('id');
  if (!disputeId) {
    return <div className="font-mono text-xs space-y-3">
      <p>No case ID supplied.</p>
      <Link href="/" className="underline">Return to docket</Link>
    </div>;
  }
  // Remount when the query changes so records from the previous case cannot linger.
  return <CaseDetailsClient key={disputeId} disputeId={disputeId} />;
}

export default function CasePage() {
  return <Suspense fallback={<p className="font-mono text-xs">Loading case file…</p>}>
    <CaseQuery />
  </Suspense>;
}
