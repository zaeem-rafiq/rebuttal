# Submission verification — September 14, 2026

## Source and reproducibility

Application source tested at `9cf06e39477978dbf3e141174591a81166233c33`. Submission changes after this point are documentation and images only.

A fresh local Git clone, with no local `.env`, was checked using the installed Python 3.12 environment:

```sh
PYTHON_DOTENV_DISABLED=1 /Users/zaeemkhan/Documents/Rebuttal/.venv/bin/python scripts/seed_supabase.py --local-only --verify
PYTHON_DOTENV_DISABLED=1 /Users/zaeemkhan/Documents/Rebuttal/.venv/bin/python -m pytest -q
```

Local fixture seed: exit 0, 10 customers, 12 orders, 11 shipments, 10 messages, one policy. Test suite: **232 passed**, 20 dependency warnings, exit 0, 20.83 seconds. For another machine, replace the interpreter path with that clone's virtual-environment Python. The evaluator's provenance checks require a Git clone; a ZIP without Git metadata is insufficient. The scenario tests require the local seed command.

An initial source-only archive check failed because Git metadata and the seeded SQLite store were absent. Repeating the documented setup in a real clone resolved all ten failures. Nine separate local preflight tests in the working checkout are outside this submission commit and are not included in the 232-test count.

Console verification for the same application source: `node --test tests/disputes.test.cjs` passed 12 tests; TypeScript checking and an isolated production build exited 0. No new paid evaluation was run during submission preparation. The earlier bounded grounding results and their scope are recorded in [final-acceptance.json](output-grounding/final-acceptance.json).

## Recorded phone outcome

The published video uses synthetic merchant evidence and a $340 Stripe test dispute, `du_1UFez9Emho7ai02fWOXDjBLJ`. The owner selected Concede on their physical phone. A September 14, 20:08 UTC provider readback showed the same Stripe and Supabase dispute as `lost`, a matching owner `concede_dispute` audit at 20:07:00 UTC, and a closure-webhook audit at 20:07:04 UTC. The local console displayed **CONCEDED · CLOSED**.

The graph and console ran locally; the owner reply used the existing cloud callback. The case required recovery before generation. Automatic cloud ingestion and deployment of the latest local repairs are not established by the recording. The separate decision row remained pending, and closure-memory action metadata was inconsistent. The terminal dispute and owner audit support the recorded concession; no broader session-resume claim is made.

## Public media and assets

- [Public video](https://www.youtube.com/watch?v=ZlGc15UzTbU): 177.054667 seconds, 1920×1080, 30 fps, H.264/AAC.
- Final MP4 SHA-256: `a49da50bb6208730fbb24a3184d2ea19ad1ae858c5147c7fcfb2afe46d572893`.
- Full media decode exited 0. Public playback was observed signed out in Chrome Guest, with video time advancing and audio playing.
- English captions and AI-generated narration disclosure were included.
- [Architecture](../architecture-submission.png): 1709×2936 PNG, 299,501 bytes, rendered from the included Mermaid source; render exited 0 and labels were visually checked.
- [Project thumbnail](../submission-thumbnail.jpg): an actual frame extracted from the published video.

Raw recovery logs, account credentials, and private authentication receipts are excluded from the submission commit.
