"""Offline QA for this final candidate; generates frame contacts for manual review."""
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
VIDEO = ROOT / 'rebuttal-final-candidate.mp4'
QA = ROOT / 'qa'
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(seconds, name):
    path = QA / name
    subprocess.run([FF, '-nostdin', '-y', '-v', 'error', '-ss', str(round(seconds, 6)),
                    '-i', str(VIDEO), '-frames:v', '1', str(path)], check=True)
    with Image.open(path) as source:
        return source.convert('RGB')


def contact(samples, name, columns=2, width=640):
    height = width * 9 // 16
    sheet = Image.new('RGB', (columns * width, math.ceil(len(samples) / columns) * (height + 30)), '#f2f1e9')
    draw = ImageDraw.Draw(sheet)
    for index, (seconds, label) in enumerate(samples):
        source = frame(seconds, f'{name}-{index:02}.png')
        x, y = index % columns * width, index // columns * (height + 30)
        sheet.paste(source.resize((width, height), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 10, y + height + 3), label, font=FONT, fill='#182723')
    sheet.save(QA / f'{name}.jpg', quality=94)


def main():
    QA.mkdir(exist_ok=True)
    scenes = json.loads((ROOT / 'scenes.json').read_text())
    timeline = json.loads((ROOT / 'timeline.json').read_text())
    assert len(scenes) == len(timeline['scenes']) == 9
    assert not any(scene.get('pending_evidence') for scene in scenes)
    assert timeline['scenes_sha256'] == sha(ROOT / 'scenes.json')
    for index, item in enumerate(timeline['scenes']):
        assert item['speech'] == scenes[index]['speech']
        assert item['voice_sha256'] == sha(ROOT / f'voice-{index}.mp3')
        assert item['timings_sha256'] == sha(ROOT / f'voice-{index}.json')
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(VIDEO)]))
    (QA / 'ffprobe.json').write_text(json.dumps(info, indent=2) + '\n')
    duration = float(info['format']['duration'])
    video = next(stream for stream in info['streams'] if stream['codec_type'] == 'video')
    audio = next(stream for stream in info['streams'] if stream['codec_type'] == 'audio')
    assert (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '30/1')
    assert duration < 300 and abs(duration - timeline['duration_seconds']) < .05
    subprocess.run([FF, '-nostdin', '-v', 'error', '-i', str(VIDEO), '-f', 'null', '-'], check=True)
    validation = timeline['scenes'][7]
    samples = [(validation['start'] + start + .35, f'Validation row {index + 1} / local {start + .35:.2f}s')
               for index, start in enumerate(scenes[7]['reveal_at'])]
    contact(samples, 'validation-reveals')
    cuts, peaks = [], []
    for index, item in enumerate(timeline['scenes'][1:], 1):
        point = item['start']
        cuts.extend((point + delta, f'Cut {index} / {delta:+.1f}s / {point + delta:.2f}s') for delta in (-.1, .1, 1.5))
        raw = subprocess.check_output([FF, '-nostdin', '-v', 'error', '-ss', str(point - .03), '-i', str(VIDEO),
                                       '-t', '0.06', '-vn', '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'])
        waveform = array.array('f')
        waveform.frombytes(raw)
        peak = max(abs(value) for value in waveform)
        dbfs = 20 * math.log10(peak) if peak else None
        assert dbfs is None or dbfs < -60, f'Unexpected cut peak at {point}: {dbfs}'
        peaks.append({'seconds': point, 'peak_dbfs_within_30ms': round(dbfs, 2) if dbfs is not None else None})
    contact(cuts, 'all-cut-boundaries', columns=3, width=480)
    bookends = [.15, 1.5, 72, 115, 146, duration - 1.5, duration - .1]
    contact([(point, f'Output {point:.2f}s') for point in bookends], 'bookends-and-midpoints')
    report = {'video': VIDEO.name, 'sha256': sha(VIDEO), 'duration_seconds': duration,
              'dimensions': [video['width'], video['height']], 'fps': video['r_frame_rate'],
              'audio': {key: audio[key] for key in ('codec_name', 'sample_rate', 'channels')},
              'full_decode_exit_status': 0, 'scene_and_voice_hashes_match_timeline': True,
              'cut_audio_checks': peaks, 'frame_review': 'PENDING manual image inspection',
              'independent_listening': 'NOT VERIFIED',
              'limitation': 'Provider word timings are not independent ASR; technical QA is not listening acceptance.'}
    (QA / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('video', 'sha256', 'duration_seconds', 'full_decode_exit_status')}, indent=2))


if __name__ == '__main__':
    main()
