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
         'card_checks': {'address_line1_check': 'pass', 'address_postal_code_check': 'pass', 'cvc_check': 'pass'},
         'produced_artifacts': []}
narrative = ('Dispute Reason: fraudulent\nThe recorded dispute amount is $340. '
             'Merchant records list 5 total orders and $1,120 lifetime value.')
clean = {'strategy': {'action': 'concede', 'win_probability': .2, 'expected_value_cents': 0,
                     'evidence_strength': 'weak', 'customer_value': 'repeat',
                     'rationale': 'Recommend concession after owner review.',
                     'owner_summary': 'Recommend concession of the $340 dispute; review before approval.'},
         'evidence_packet': EvidencePacket(narrative=narrative).model_dump()}
cases = [('grounded_control', clean, None, [])]
for field, value in [('owner_summary', 'Refund completed and $15 fee saved.'),
                     ('uncategorized_text', 'The customer admitted deliberately committing fraud.')]:
    changed = copy.deepcopy(clean)
    container = 'strategy' if field == 'owner_summary' else 'evidence_packet'
    changed[container][field] = value
    cases.append((field + '_unsupported', changed, 'no_hallucination_pass', []))
quoted = copy.deepcopy(clean)
quoted['evidence_packet']['narrative'] = (
    'Dispute Reason: fraudulent. The inbound email states: '
    '"I just placed order ORD-1002 but I am traveling for work."'
)
cases.append(('quoted_reference_counts', quoted, None, ['ORD-1002']))
supporting_only = copy.deepcopy(clean)
supporting_only['evidence_packet']['customer_communication'] = quoted['evidence_packet']['narrative']
cases.append(('reference_only_outside_narrative', supporting_only, 'must_cite_pass', ['ORD-1002']))
scoped_absence = copy.deepcopy(clean)
scoped_absence['evidence_packet']['narrative'] += ' No return request appears in the supplied communications.'
cases.append(('scoped_record_absence', scoped_absence, None, []))
checks = copy.deepcopy(clean)
checks['evidence_packet']['narrative'] += ' AVS address line 1 and postal code checks passed. CVC check passed.'
cases.append(('card_check_equivalence', checks, None, []))
authorization = copy.deepcopy(checks)
authorization['evidence_packet']['narrative'] += ' These checks prove that the cardholder authorized this payment.'
cases.append(('card_checks_do_not_prove_authorization', authorization, 'no_hallucination_pass', []))
qualified_authorization = copy.deepcopy(clean)
qualified_authorization['strategy']['owner_summary'] = 'Recommend fighting. Strong evidence of an authorized transaction.'
cases.append(('owner_authorization_inference', qualified_authorization, 'no_hallucination_pass', []))
prior_count = copy.deepcopy(clean)
prior_count['strategy']['rationale'] = 'Recommend concession for this repeat customer with 5 prior orders.'
cases.append(('total_is_not_prior_orders', prior_count, 'no_hallucination_pass', []))
reported = copy.deepcopy(clean)
reported['evidence_packet']['narrative'] += ' The customer reported traveling for work and requested an address change.'
cases.append(('attributed_customer_report', reported, None, []))
unproduced = copy.deepcopy(clean)
unproduced['evidence_packet']['files'] = ['unproduced-evidence.pdf']
cases.append(('unproduced_attachment', unproduced, 'no_hallucination_pass', []))
out = root / os.environ.get('CONTROL_REPORT_PATH', 'evals/results/output-controls.json')
assert not out.exists(), 'Preserve prior results; choose a new output path.'
client = get_llm_judge_client()
results = []
for name, output, failing_check, must_cite in cases:
    result = judge_narrative(client, output['evidence_packet']['narrative'], 'fraudulent', must_cite,
                             json.dumps(facts), supporting_output=output)
    expected = {key: key != failing_check for key in
                ['reason_code_pass', 'must_cite_pass', 'no_hallucination_pass', 'word_count_pass']}
    results.append({'name': name, 'expected_checks': expected, 'result': result, 'output': output})
    print(name, result['overall_pass'], result['explanation'], flush=True)
out.write_text(json.dumps({'facts': facts, 'results': results}, indent=2) + '\n')
assert all(r['result'][key] is value for r in results for key, value in r['expected_checks'].items()), 'Judge control mismatch'
