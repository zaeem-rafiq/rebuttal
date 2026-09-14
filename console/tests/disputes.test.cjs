const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');

function loadTypeScript(relativePath, overrides = {}) {
  const filename = path.resolve(__dirname, relativePath);
  const { outputText } = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.React, esModuleInterop: true },
  });
  const loadedModule = new Module(filename);
  loadedModule.filename = filename;
  loadedModule.paths = Module._nodeModulePaths(path.dirname(filename));
  const originalRequire = loadedModule.require.bind(loadedModule);
  loadedModule.require = (name) => Object.hasOwn(overrides, name) ? overrides[name] : originalRequire(name);
  loadedModule._compile(outputText, filename);
  return loadedModule.exports;
}
const { getCaseFileMemo, getDecision, getCaseState, sendOwnerReply, getCaseHref } = loadTypeScript('../src/lib/disputes.ts');
const pending = { id: 'decision-new', dispute_id: 'dp_live', action: 'fight', status: 'pending', created_at: '2026-09-14T10:00:00Z' };
function makeCase() {
  return {
    id: 'dp_live', amount_cents: 12345, currency: 'usd', reason: 'fraudulent', status: 'needs_response',
    order_id: 'ORD-A', evidence_due_by: '2026-09-17T10:00:00Z', decision: [pending],
    order: {
      id: 'ORD-A', customer_id: 'CUST-A', currency: 'usd', status: 'shipped', created_at: '2026-09-02T13:00:00Z',
      billing_address: { line1: '10 Billing St', country: 'US' }, shipping_address: { line1: '20 Shipping St', country: 'US' },
      customer: { id: 'CUST-A', name: 'Alex Morgan', email: 'alex@example.test', customer_value: 'repeat', order_count: 3, lifetime_value_cents: 45678 },
      items: [{ id: 'item-A', product_name: 'Lamp', quantity: 1 }],
      shipments: [{ id: 'ship-A', order_id: 'ORD-A', carrier: 'UPS', tracking_number: 'TRACK-A', status: 'delivered', shipped_at: '2026-09-03T13:00:00Z', delivered_at: '2026-09-05T10:00:00Z', signed_by: 'Delivered in Mailbox', shipping_address: { line1: '20 Shipping St' }, events: [{ timestamp: '2026-09-05T10:00:00Z', status: 'delivered', location: 'Boston' }] }],
      messages: [{ id: 'msg-A', order_id: 'ORD-A', customer_id: 'CUST-A', direction: 'inbound', created_at: '2026-09-06T10:00:00Z', subject: 'Question', body: 'Please check the address.' }],
    },
  };
}

test('case facts, real dates and source records replace scenario-specific canned content', () => {
  const input = makeCase();
  const memo = getCaseFileMemo(input, Date.parse('2026-09-14T10:00:00Z'));
  assert.equal(memo.customerName, 'Alex Morgan');
  assert.equal(memo.headlineAmount, '$123.45');
  assert.equal(memo.respondByDate, '17 Sept 2026');
  assert.equal(memo.respondByDays, 3);
  assert.match(memo.briefNarrative, /3 total orders/);
  assert.match(memo.briefNarrative, /\$456.78/);
  const text = JSON.stringify(memo);
  for (const expected of ['TRACK-A', 'Delivered in Mailbox', 'Please check the address.', '10 Billing St', '20 Shipping St']) assert.ok(text.includes(expected));
  for (const invented of ['Sarah Jenkins', '4820', '3D Secure 2.2', 'cryptographic', 'fee avoided', '4471']) assert.ok(!text.includes(invented));
  assert.ok(memo.exhibits.every(exhibit => exhibit.status !== 'attached'));
  assert.equal(memo.smsText, null);
  assert.equal(memo.smsTime, null);
});

for (const reason of ['fraudulent', 'product_not_received', 'subscription_canceled']) {
  test(`reason ${reason} cannot create evidence or completed outcomes`, () => {
    const input = { id: 'dp_S2', amount_cents: 6000, currency: 'usd', reason, status: 'needs_response' };
    const memo = getCaseFileMemo(input);
    assert.equal(memo.customerName, 'Customer not recorded');
    assert.equal(memo.respondByDays, null);
    assert.equal(memo.recommendation, 'No agent recommendation recorded.');
    assert.ok(memo.exhibits.every(exhibit => exhibit.status === 'missing'));
    assert.deepEqual(getCaseState(input), { label: 'NEEDS RESPONSE', variant: 'pending', awaitingReply: false });
  });
}

test('missing and mismatched linked identities do not leak another case into the memo', () => {
  const input = makeCase();
  input.order.id = 'ORD-OTHER';
  let text = JSON.stringify(getCaseFileMemo(input));
  assert.ok(!text.includes('Alex Morgan'));
  assert.ok(!text.includes('TRACK-A'));
  input.order.id = input.order_id;
  input.order.customer.id = 'CUST-OTHER';
  assert.equal(getCaseFileMemo(input).customerName, 'Customer not recorded');
  input.order.messages.push({ id: 'wrong', order_id: 'OTHER', customer_id: 'CUST-A', body: 'UNRELATED CONTENT' });
  text = JSON.stringify(getCaseFileMemo(input));
  assert.ok(!text.includes('UNRELATED CONTENT'));
});

test('latest decision is selected deterministically without mutating the joined array', () => {
  const input = makeCase();
  input.decision = [{ ...pending, id: 'old', action: 'concede', created_at: '2026-09-01T10:00:00Z' }, { ...pending }, { ...pending, id: 'other', dispute_id: 'dp_other', created_at: '2026-09-20T10:00:00Z' }];
  const before = JSON.stringify(input.decision);
  assert.equal(getDecision(input).id, 'decision-new');
  assert.equal(JSON.stringify(input.decision), before);
});

test('an expired deadline is not shown as time left and foreign shipments stay missing', () => {
  const input = makeCase();
  input.order.shipments[0].order_id = 'OTHER';
  const memo = getCaseFileMemo(input, Date.parse('2026-09-17T10:30:00Z'));
  assert.equal(memo.respondByDays, -1);
  assert.ok(!JSON.stringify(memo).includes('TRACK-A'));
  assert.ok(memo.exhibits.some(exhibit => exhibit.field === 'shipment' && exhibit.status === 'missing'));
});

test('pending phone approval becomes closed only after a recorded outcome', () => {
  const input = makeCase();
  assert.equal(getCaseState(input).awaitingReply, true);
  input.decision = { ...pending, action: 'concede', status: 'overridden' };
  assert.equal(getCaseState(input).label, 'OWNER RESPONSE RECORDED');
  input.status = 'lost';
  input.audit_logs = [{ dispute_id: input.id, action: 'concede_dispute', created_at: '2026-09-14T10:01:00Z' }];
  assert.equal(getCaseState(input).label, 'CONCEDED · CLOSED');
  assert.equal(getCaseState(input).awaitingReply, false);
});

test('a proposed fight is never a won outcome and stale decisions cannot reopen a closed dispute', () => {
  const input = makeCase();
  assert.notEqual(getCaseState(input).label, 'WON');
  input.status = 'under_review';
  assert.equal(getCaseState(input).label, 'UNDER REVIEW');
  input.status = 'won';
  assert.equal(getCaseState(input).label, 'WON');
  assert.equal(getCaseState(input).awaitingReply, false);
  input.status = 'lost';
  input.audit_logs = [{ dispute_id: input.id, action: 'concede_dispute', created_at: '2026-09-01T10:00:00Z' }];
  assert.equal(getCaseState(input).label, 'LOST');
});

test('exhibit headers render as stored records, not fictitious uploaded attachments', () => {
  const React = require('react');
  const { renderToStaticMarkup } = require('react-dom/server');
  const { ExhibitInspector } = loadTypeScript('../src/components/ExhibitInspector.tsx');
  const html = renderToStaticMarkup(React.createElement(ExhibitInspector, { exhibits: getCaseFileMemo(makeCase()).exhibits }));
  assert.match(html, /TRACK-A/);
  assert.match(html, /recorded/);
  assert.match(html, /aria-expanded="false"/);
  assert.ok(!html.includes('attached'));
});

test('static console sends directly to the configured backend and awaits recorded state after opaque responses', async () => {
  const input = makeCase();
  const original = JSON.stringify(input);
  let captured;
  await sendOwnerReply('https://backend.example.test/reply', input.id, '2', async (url, options) => {
    captured = { url, options };
    return { type: 'opaque', ok: false, status: 0 };
  });
  assert.equal(captured.url, 'https://backend.example.test/reply');
  assert.equal(captured.options.method, 'POST');
  assert.equal(captured.options.mode, 'no-cors');
  assert.equal(captured.options.headers['Content-Type'], 'application/x-www-form-urlencoded');
  const body = new URLSearchParams(captured.options.body);
  assert.equal(body.get('dispute_id'), input.id);
  assert.equal(body.get('Body'), '2');
  assert.equal(JSON.stringify(input), original);
  assert.equal(getCaseState(input).awaitingReply, true);
  await assert.rejects(sendOwnerReply('https://backend.example.test/reply', input.id, '1', async () => { throw new Error('offline'); }), /offline/);
});

test('static case links forward arbitrary query IDs to the existing detail view without seeded routes', () => {
  const React = require('react');
  const { renderToStaticMarkup } = require('react-dom/server');
  const id = 'du_fresh/&?=value';
  const href = getCaseHref(id);
  assert.equal(href, '/case?id=du_fresh%2F%26%3F%3Dvalue');
  let search = new URL(href, 'https://console.example.test').searchParams;
  const { default: CasePage } = loadTypeScript('../src/app/case/page.tsx', {
    'next/navigation': { useSearchParams: () => search },
    'next/link': ({ href, children }) => React.createElement('a', { href }, children),
    './[id]/CaseDetailsClient': ({ disputeId }) => React.createElement('div', { 'data-dispute-id': disputeId }),
  });
  assert.match(renderToStaticMarkup(React.createElement(CasePage)), /data-dispute-id="du_fresh\/&amp;\?=value"/);
  search = new URLSearchParams();
  const missing = renderToStaticMarkup(React.createElement(CasePage));
  assert.match(missing, /No case ID supplied/);
  assert.ok(!missing.includes('data-dispute-id'));
});
