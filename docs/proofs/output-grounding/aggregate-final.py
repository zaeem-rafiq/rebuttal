"""Check preserved final evidence without inference or reclassifying verdicts."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def read(path):
    data = json.loads((root / path).read_text())
    assert data['completed'], f'Incomplete: {path}'
    return data


replay_paths = [f'evals/results/2026-09-14-source-formatted-final-v2-{part}.json' for part in 'abc']
control_paths = [f'evals/results/2026-09-14-sonnet-controls-v18{part}.json' for part in 'abc']
live_path = 'evals/results/2026-09-14-source-formatted-final-v2-live.json'
replays, controls = [read(p) for p in replay_paths], [read(p) for p in control_paths]
live = read(live_path)
for report in replays:
    assert report['processing_revision'].startswith('4371ebf')
    assert report['generation_revision'] == 'ccd5616'
    assert report['processor_sha256'] == digest('agent/factual_output.py')
    assert report['evaluator_sha256'] == digest('evals/run.py')
    for path, expected in report['source_reports'].items():
        assert digest(path) == expected, path
for report in [*controls, live]:
    for path, expected in report['source_manifest'].items():
        assert digest(path) == expected, path
rows = sorted([r for report in replays for r in report['results']], key=lambda r: r['case_id'])
assert [r['case_id'] for r in rows] == [f'case_{i:02}' for i in range(1, 21)]
assert all(r['judge_details']['judge_valid'] is True for r in rows)
control_rows = [r for report in controls for r in report['results']]
assert len(control_rows) == len({r['name'] for r in control_rows}) == 52
assert all(r['result']['judge_valid'] is True for r in control_rows)
control_passes = sum(all(r['result'].get(k) is v for k, v in r['expected_checks'].items()) for r in control_rows)
assert live['code_revision'] == '4371ebf' and live['source_dirty'] is False
assert {r['case_id'] for r in live['results']} == {'case_03', 'case_18'}
assert all(r['judge_details']['judge_valid'] is True for r in live['results'])
test_path = 'docs/proofs/output-grounding/4371ebf-tests.json'
tests = json.loads((root / test_path).read_text())
assert tests['exit_status'] == 0 and digest(tests['log']) == tests['log_sha256']
for path, expected in tests['source_manifest'].items():
    assert digest(path) == expected, path
counts = {key: sum(r[key] is True for r in rows) for key in ('action_match', 'gate_match', 'judge_pass', 'ev_sign')}
passed = (counts['action_match'] >= 18 and counts['gate_match'] == 20
          and counts['judge_pass'] >= 18 and counts['ev_sign'] == 20
          and control_passes == 52 and all(r['overall_pass'] is True for r in live['results']))
summary = {
    'completed': True, 'acceptance_pass': passed,
    'scope': '20 captured ccd5616 model outputs reprocessed at 4371ebf and newly judged; separate fresh full-graph cases 03/18 at 4371ebf. No Stripe action tools run.',
    'processing_revision': '4371ebf', 'generation_revision': 'ccd5616',
    'rubric': 'grounded-v17', 'cases': 20, 'counts': counts,
    'thresholds': {'action_match': '>=18', 'gate_match': '20', 'judge_pass': '>=18', 'ev_sign': '20'},
    'valid_judgments': 20, 'controls': {'matched': control_passes, 'total': 52},
    'fresh_graph_cases': {r['case_id']: r['overall_pass'] for r in live['results']},
    'tests': tests['result'],
    'raw_judge_failures': [r['case_id'] for r in rows if not r['judge_pass']],
    'report_sha256': {p: digest(p) for p in [*replay_paths, *control_paths, live_path, test_path]},
}
out = root / 'docs/proofs/output-grounding/final-acceptance.json'
out.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if passed else 1)
