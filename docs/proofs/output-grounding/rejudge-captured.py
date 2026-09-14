"""Rejudge unchanged captured outputs; never regenerate or overwrite evidence."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
from evals.run import judge_narrative, get_llm_judge_client
source = root / 'evals/results/2026-09-14-fbaf06f-full.json'
out = root / os.environ['REJUDGE_REPORT_PATH']
original_bytes = source.read_bytes()
data = json.loads(original_bytes)
assert data['completed'] is True and len(data['results']) == 20, 'Source benchmark must be complete'
assert not out.exists() and not out.with_suffix('.md').exists(), 'Preserve prior reports'
# Changed judge code is expected; generation/data changes invalidate this replay.
assert data['source_dirty'] is False, 'Reproduction requires a committed source snapshot'
for name, digest in data['source_manifest'].items():
    recorded = subprocess.check_output(['git', 'show', f"{data['code_revision']}:{name}"], cwd=root)
    assert hashlib.sha256(recorded).hexdigest() == digest, f'Recorded generation source mismatch: {name}'
assert len({r['case_id'] for r in data['results']}) == 20
if '--check-only' in sys.argv:
    print('20-case source completion and generation manifest verified; no model call')
    raise SystemExit(0)
report = {'source_report': str(source.relative_to(root)),
          'source_report_sha256': hashlib.sha256(original_bytes).hexdigest(),
          'generation_revision': data['code_revision'],
          'generation_source_snapshot_sha256': data['source_snapshot_sha256'],
          'evaluator_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
          'evaluator_sha256': hashlib.sha256((root / 'evals/run.py').read_bytes()).hexdigest(),
          'rubric': os.environ['REJUDGE_RUBRIC'], 'completed': False, 'results': []}
client = get_llm_judge_client()
for prior in data['results']:
    row = dict(prior)
    case = json.loads(subprocess.check_output(['git', 'show', f"{data['code_revision']}:evals/cases/{row['case_id']}.json"], cwd=root, text=True))
    row['original_judge_details'] = prior['judge_details']
    if not row.get('pipeline_error'):
        verdict = judge_narrative(client, row['narrative'], case['reason'], case['must_cite'],
                                  json.dumps(row['case_facts']), row['supporting_output'])
        row['judge_details'] = verdict
        row['judge_pass'] = verdict['overall_pass']
    row['overall_pass'] = all(row[k] for k in ('action_match', 'gate_match', 'judge_pass', 'ev_sign'))
    report['results'].append(row)
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(row['case_id'], row['judge_pass'], flush=True)
report['completed'] = True
metrics = {k: sum(r[k] for r in report['results']) for k in ('action_match', 'gate_match', 'judge_pass', 'ev_sign')}
passed = metrics['action_match'] >= 18 and metrics['gate_match'] == 20 and metrics['judge_pass'] >= 18 and metrics['ev_sign'] == 20
report['metrics'] = metrics
report['thresholds_pass'] = passed
out.write_text(json.dumps(report, indent=2) + '\n')
lines = ['# Exact-source rejudgment', '', 'Generated outputs are unchanged from the linked source report. No generation was repeated.', '',
         f"Generation revision: {report['generation_revision']}", f"Evaluator revision: {report['evaluator_revision']}",
         f"Source SHA256: {report['source_report_sha256']}", '',
         '| Check | Observed | Threshold |', '|---|---:|---:|']
for key, threshold in [('action_match', '>=18'), ('gate_match', '20'), ('judge_pass', '>=18'), ('ev_sign', '20')]:
    lines.append(f'| {key} | {metrics[key]}/20 | {threshold} |')
lines += ['', f'Exit status: {0 if passed else 1}', '', '| Case | Output judge |', '|---|---|']
lines += [f"| {r['case_id']} | {'PASS' if r['judge_pass'] else 'FAIL'} |" for r in report['results']]
out.with_suffix('.md').write_text('\n'.join(lines) + '\n')
assert hashlib.sha256(source.read_bytes()).hexdigest() == report['source_report_sha256']
print(metrics, 'thresholds_pass', passed)
raise SystemExit(0 if passed else 1)
