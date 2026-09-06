import { NextRequest, NextResponse } from 'next/server';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const replyBody = body.Body || body.answer || '1';
    const disputeId = body.dispute_id || 'dp_S2';

    const formData = new URLSearchParams();
    formData.append('Body', replyBody);
    formData.append('From', '+18129551686');
    formData.append('dispute_id', disputeId);

    const resp = await fetch(TWILIO_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    const text = await resp.text();
    return NextResponse.json({ success: true, response: text }, { status: resp.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || 'Failed to send reply' },
      { status: 500 }
    );
  }
}
