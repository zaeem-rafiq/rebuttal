"""Live positive/negative controls for whole-output judge sensitivity."""
import copy
import json
import os
from pathlib import Path
from evals.run import judge_narrative, get_llm_judge_client
from agent.models import EvidencePacket
from agent.tools.evidence_tools import get_order_evidence, get_shipping_evidence, get_customer_comms, get_merchant_history_and_policy

root = Path(__file__).resolve().parent.parent
facts = {'order': get_order_evidence('ORD-1002'), 'shipment': get_shipping_evidence('ORD-1002'),
         'communications': get_customer_comms('CUST-002', 'ORD-1002'),
         'history_and_policy': get_merchant_history_and_policy('CUST-002'),
         'dispute': {'id': 'dp_S2', 'amount_cents': 34000, 'currency': 'usd', 'reason': 'fraudulent', 'status': 'needs_response'},
         'produced_artifacts': []}
narrative = ('Dispute Reason: fraudulent\nThe recorded dispute amount is $340. '
             'Merchant records list 5 total orders and $1,120 lifetime value.')
clean = {'strategy': {'action': 'concede', 'win_probability': .2, 'expected_value_cents': 0,
                     'evidence_strength': 'weak', 'customer_value': 'repeat',
                     'rationale': 'Recommend concession after owner review.',
                     'owner_summary': 'Recommend concession of the $340 dispute; review before approval.'},
         'evidence_packet': EvidencePacket(narrative=narrative).model_dump()}
cases = [('grounded_control', clean, True)]
for field, value in [('owner_summary', 'Refund completed and $15 fee saved.'),
                     ('uncategorized_text', 'The customer admitted deliberately committing fraud.')]:
    changed = copy.deepcopy(clean)
    container = 'strategy' if field == 'owner_summary' else 'evidence_packet'
    changed[container][field] = value
    cases.append((field + '_unsupported', changed, False))
source = Path(os.environ.get('CAPTURED_WORKFLOW', str(root / 'docs/proofs/output-grounding/rejected-workflow.json')))
captured = {event['stage']: event['data'] for event in json.loads(source.read_text())}
cases.append(('captured_bad_output', {'strategy': captured['strategy'], 'evidence_packet': captured['evidence']}, False))
out = root / os.environ.get('CONTROL_REPORT_PATH', 'evals/results/output-controls.json')
assert not out.exists(), 'Preserve prior results; choose a new output path.'
client = get_llm_judge_client()
results = []
for name, output, expected in cases:
    result = judge_narrative(client, output['evidence_packet']['narrative'], 'fraudulent', [],
                             json.dumps(facts), supporting_output=output)
    results.append({'name': name, 'expected_pass': expected, 'result': result, 'output': output})
    print(name, result['overall_pass'], result['explanation'], flush=True)
out.write_text(json.dumps({'facts': facts, 'results': results}, indent=2) + '\n')
assert all(r['result']['overall_pass'] is r['expected_pass'] for r in results), 'Judge control mismatch'
