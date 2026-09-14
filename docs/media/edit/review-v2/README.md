# Rebuttal corrected video preview

Owner approved a shorter cut with readable close-ups, synthetic-data labeling, removal of simulated Telegram delivery proof, and removal of unsupported/outdated claims.

## Output

`rebuttal-corrected-preview.mp4`: approximately 71 seconds, 1920x1080, 30 fps, H.264/AAC. New Microsoft Andrew neural narration and synchronized burned captions. Original recording remains untouched.

This is an annotated case-review walkthrough, not an end-to-end execution demonstration. Each scene uses six seconds of an authentic cropped source excerpt, then holds the final frame to allow reading. No new application state, outcome, notification, or interaction was fabricated. The earlier SMS interface is explicitly identified. Synthetic-data labeling remains visible throughout.

The old narration claimed a win while S1 visibly showed LOST. The cut omits that scenario and its claim. It also removes the simulated Telegram overlay, unverified statistics and fee savings, claims of GPS/carrier API retrieval, and old evaluation/security claims. It does not depend on Antigravity's unfinished changes.

## Sources and reproducibility

- Original: `../../rebuttal_demo_video.mp4`; source SHA-256 in `source.sha256`.
- `scenes.json`: corrected editorial text and exact crop/source coordinates.
- `narrate.py`: synthesizes whole scene narrations using `edge-tts` 7.2.8, the same voice named in the repository's existing production script. Only the newly written narration is sent to Microsoft's speech service.
- `voice-*.mp3` and `voice-*.json`: cached generated speech and provider word timing. These are synthesis timestamps, not an independent ASR transcript.
- `render.py`: composition and lossless segment concat; no speech words are cut; 30ms audio fades; captions applied last.
- `timeline.json` and `captions.srt`: output timeline and accessible captions.
- No stock music, third-party imagery, or added logos. Footage comes from the owner's existing recording; titles and layout were created for this edit. Voice-provider terms apply; no new license guarantee is claimed.

From the repository root:

```bash
UV_CACHE_DIR=docs/media/edit/review-v2/cache uv run --no-project --with edge-tts==7.2.8 python docs/media/edit/review-v2/narrate.py
.venv/bin/python docs/media/edit/review-v2/render.py
ffmpeg -v error -i docs/media/edit/review-v2/rebuttal-corrected-preview.mp4 -f null -
```

## Verification and limits

Rendered successfully. Full decode verification exited 0. Output timing, dimensions, codecs, caption timing/token alignment, and sampled frames at each scene boundary were checked. The caption-size issue in the first render was corrected. Audio was normalized to a -16 LUFS target with a -1.5 dB true-peak ceiling, then checked for clipping. Measured output: -16.7 LUFS integrated and -4.4 dBFS true peak.

`qa-sheet.jpg` records visual samples; `audio-qa.log` contains measured audio levels. These checks do not establish human-perceived voice quality. Full listening acceptance is still required. This is a review preview, not a published or submitted video. It cannot repair the original footage's lack of a demonstrated live end-to-end outcome; that needs a new recording after the build is settled.
