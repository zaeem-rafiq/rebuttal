# Final video preparation

This is an incomplete assembly plan, not a submission video. Target: 3:30–4:00.
The [outline](outline.json) contains five explanatory scenes and explicit evidence
requirements for four recorded-result scenes. The complete 437-word narration is
prepared in [narration-for-approval.md](narration-for-approval.md); it contains no
raw records, person names, addresses, object IDs, or pending scores.

| Index | Scene | Planned duration | State |
|---|---|---:|---|
| 0 | Problem and audience | 26.97 s | Existing narration reused |
| 1 | Strands architecture | 22.97 s | Existing narration reused |
| 2 | Local recording setup | 25 s | Script ready; voice pending |
| 3 | Retrieved facts and graph execution | 25 s | Captured from completed 616db5e run |
| 4 | Strategy and evidence draft | 25 s | Captured from completed 616db5e run |
| 5 | Developer CLI approval explanation | 29 s | Script ready; voice pending |
| 6 | Actual decision and Stripe readback | 20 s | CLI concede; Stripe test lost; one guarded call |
| 7 | Evaluation and tests | 20 s | Validation open: unchanged outputs 16/20, below 18 required; export blocked |
| 8 | Purpose and observed scope | 24 s | Script ready; voice pending |

The original opening was legible but exposed all text in the first few seconds.
The final outline adds narration-aligned reveal times, retains all speech, and
uses the full scene to guide the eye. Two added opening lines follow the existing
spoken review/control statements. Explanatory panels have authored-content labels;
recorded panels must use literal sanitized run excerpts. Playback timing is editorial.

The completed runtime recording is revision 616db5e, with selected fields linked
by hash in scene-sources.json. It is separate from the later benchmark generation
and evaluator revisions. Scene 8 now records the open validation state:

- Generation fbaf06f completed at output judge 9/20.
- The same unchanged outputs rejudged by evaluator d494d4e reached 16/20, below
  the required 18/20. Action, approval gate, and EV were 20/20 each; exit status 1.
- Controls v10 matched 21/23 expected judgments; exit status 1.
- Current checkout 6a756ed passed 146 offline tests; exit status 0. The prepared
  three-call follow-up has no paid model verification and has not established a
  new generation result.

Evidence: [generation report](../../../../../evals/results/2026-09-14-fbaf06f-full.md),
[unchanged-output rejudgment](../../../../../evals/results/2026-09-14-fbaf06f-final-rejudged.md),
and [control results](../../../../../evals/results/2026-09-14-sonnet-controls-v10.json).
There is no accepted final score. pending_evidence remains true, which blocks
video export. A Sonnet generation trial under a $15 cap and Microsoft Edge voice
generation both await approval. No provider calls are part of this media update.

After accepted validation is established, update that panel, generate approved
missing voice tracks, and resolve reveal_cues into reveal_at using actual
WordBoundary timestamps. All nine narration paragraphs remain unchanged. Then run:

```sh
.venv/bin/python docs/media/edit/submission-v3/render_verified.py docs/media/edit/submission-v3/final-cut
```

The full static review is in [storyboard/contact-sheet.jpg](storyboard/contact-sheet.jpg).
Regenerate it without narration or providers by adding --storyboard to the command.
That command passed for all nine scenes; the pending-evidence export guard passed.
The cached opening also rendered again after the shared layout refactor: exit 0,
49.954 seconds, full decode passed. Exact reveal timing for the seven missing
tracks remains unverified until their authorized voice generation finishes.

Audio: voice-0 and voice-1 match the unchanged opening narration; hashes are in
voice-manifest.json. Seven remaining authored scripts are ready. Automatic
approval review rejected sending new scripts to Microsoft Edge TTS because it
did not find specific authorization for that payload and destination. No new TTS
request executed. Obtain that authorization for the complete prepared text before
running narrate.py with --generate. With no arguments, narrate.py only checks
cached voice hashes and lists pending scenes; it makes no provider calls.

No phone UI, deployed-app footage, production outcome, invented score, upload, or
publication is represented by this preparation. Final export, complete visual review,
and listening remain pending.
