"""Check cached narration; --generate sends the prepared text to Microsoft Edge TTS.

Generate only after the user approves narration-for-approval.md and that destination.
No workflow records or visual metrics are read or sent.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(value).hexdigest()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true')
    args = parser.parse_args()
    entries = json.loads((ROOT / 'outline.json').read_text())['scenes']
    manifest_path = ROOT / 'voice-manifest.json'
    manifest = {entry['index']: entry for entry in json.loads(manifest_path.read_text())}
    for entry in entries:
        index = entry['index']
        speech = entry['scene']['speech'] if 'scene' in entry else entry['speech']
        audio, timings = ROOT / f'voice-{index}.mp3', ROOT / f'voice-{index}.json'
        speech_hash = digest(speech.encode())
        if audio.exists():
            cached = manifest.get(index, {})
            if cached.get('speech_sha256') != speech_hash or cached.get('audio_sha256') != digest(audio.read_bytes()) or not timings.exists():
                raise RuntimeError(f'Cached narration {index} does not match; preserve it and resolve the mismatch before generating.')
            print(f'Scene {index + 1}: matching cached audio', flush=True)
            continue
        if not args.generate:
            print(f'Scene {index + 1}: voice pending; {len(speech.split())} authored words', flush=True)
            continue
        import edge_tts
        words = []
        temporary = ROOT / f'voice-{index}.tmp.mp3'
        try:
            with temporary.open('wb') as output:
                async for chunk in edge_tts.Communicate(speech, 'en-US-AndrewMultilingualNeural', rate='-4%', boundary='WordBoundary').stream():
                    if chunk['type'] == 'audio':
                        output.write(chunk['data'])
                    elif chunk['type'] == 'WordBoundary':
                        words.append(chunk)
            if not words or not temporary.stat().st_size:
                raise RuntimeError(f'Incomplete narration for scene {index + 1}')
            timings.write_text(json.dumps(words, indent=2))
            temporary.rename(audio)
        finally:
            temporary.unlink(missing_ok=True)
        manifest[index] = {'index': index, 'speech_sha256': speech_hash,
                           'audio_sha256': digest(audio.read_bytes()),
                           'source': 'Edge TTS; approved public-intended narration'}
        manifest_path.write_text(json.dumps(list(manifest.values()), indent=2) + '\n')
        print(f'Scene {index + 1}: generated', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
