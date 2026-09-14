"""Verify newly formatted outputs from exact captured model runs; no generation replay."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
from agent.factual_output import render_factual_output
from agent.models import DisputeStrategy, EvidencePacket
from agent.graph import validate_evidence_attachments
from evals.run import judge_narrative, get_llm_judge_client, observe_gate

sources = [root / f'evals/results/2026-09-14-ccd5616-{part}.json' for part in ('a', 'b')]
data = [json.loads(path.read_text()) for path in sources]
assert all(item['completed'] for item in data)
assert data[0]['source_manifest'] == data[1]['source_manifest']
assert data[0]['code_revision'] == data[1]['code_revision'] == 'ccd5616'
for name, digest in data[0]['source_manifest'].items():
    original = subprocess.check_output(['git', 'show', f'ccd5616:{name}'], cwd=root)
    assert hashlib.sha256(original).hexdigest() == digest, name
rows = sorted([row for item in data for row in item['results']], key=lambda row: row['case_id'])
assert [row['case_id'] for row in rows] == [f'case_{index:02}' for index in range(1, 21)]
batch = int(os.environ.get('REPLAY_BATCH', '0'))
assert batch in (0, 1, 2)
rows = [row for index, row in enumerate(rows) if index % 3 == batch]
out = root / os.environ['REPLAY_REPORT_PATH']
assert not out.exists(), 'Preserve earlier evidence'
report = {
    'scope': 'Final deterministic formatting and new judgments of captured model outputs; no new model generation.',
    'source_reports': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    'generation_revision': 'ccd5616', 'processing_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'processor_sha256': hashlib.sha256((root / 'agent/factual_output.py').read_bytes()).hexdigest(),
    'evaluator_sha256': hashlib.sha256((root / 'evals/run.py').read_bytes()).hexdigest(),
    'rubric': 'grounded-v17', 'selected_cases': [row['case_id'] for row in rows], 'completed': False, 'results': [],
}
def save():
    out.write_text(json.dumps(report, indent=2) + '\n')

save()
client = get_llm_judge_client()
for prior in rows:
    row = dict(prior)
    row['raw_generated_output'] = prior['supporting_output']
    row['original_judge_details'] = prior['judge_details']
    row.pop('generation_usage', None)  # Original report owns that usage; never count it twice.
    validate_evidence_attachments(EvidencePacket.model_validate(prior['supporting_output']['evidence_packet']))
    strategy, packet = render_factual_output(DisputeStrategy.model_validate(prior['supporting_output']['strategy']), prior['case_facts']['source_tool_records'])
    row.update(supporting_output={'strategy': strategy.model_dump(), 'evidence_packet': packet.model_dump()},
               narrative=packet.narrative, rationale=strategy.rationale,
               computed_gate=observe_gate(row['amount_cents'], strategy.model_dump()))
    row['gate_match'] = row['computed_gate'] is row['expected_gate']
    case = json.loads((root / f"evals/cases/{row['case_id']}.json").read_text())
    row['judge_details'] = judge_narrative(client, packet.narrative, case['reason'], case['must_cite'], json.dumps(row['case_facts']), row['supporting_output'])
    row['judge_pass'] = row['judge_details']['overall_pass']
    row['overall_pass'] = all(row[key] for key in ('action_match', 'gate_match', 'judge_pass', 'ev_sign'))
    report['results'].append(row)
    save()
    print(row['case_id'], 'judge', row['judge_pass'], 'valid', row['judge_details']['judge_valid'], flush=True)
    if not row['judge_details']['judge_valid']:
        raise RuntimeError('Judge response invalid; preserve partial replay')
report['completed'] = True
save()
raise SystemExit(0 if all(row['overall_pass'] for row in report['results']) else 1)
