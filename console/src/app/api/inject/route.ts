import { NextRequest, NextResponse } from 'next/server';
import { INJECT_URL, CONSOLE_KEY } from '@/lib/config';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const scenario = body.scenario || 'S1';

    const resp = await fetch(INJECT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Console-Key': CONSOLE_KEY,
      },
      body: JSON.stringify({ scenario }),
    });

    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: message || 'Failed to inject scenario' },
      { status: 500 }
    );
  }
}
