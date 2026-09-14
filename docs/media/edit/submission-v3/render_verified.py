"""Render supplied, verified run excerpts; this script does not invent or verify evidence.

Usage: .venv/bin/python docs/media/edit/submission-v3/render_verified.py SCENE_FOLDER
       Add --storyboard for static review without audio or provider calls.
Inputs: scenes.json [{label,title,lines:[str],note,speech}], voice-N.mp3,
        voice-N.json (Edge WordBoundary records, offsets in 100-nanosecond ticks).
        Optional scene.tag and scene.panel_label distinguish explanatory slides.
        Optional scene.reveal_at lists narration-aligned reveal times in seconds.
Outputs: rebuttal-verified-preview.mp4, captions.srt, timeline.json, contact-sheet.jpg.
All intermediate files stay in SCENE_FOLDER/render/. No providers are called.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
PAPER, INK, GREEN = '#f2f1e9', '#182723', '#365e4b'
FPS, LEAD = 30, 0.4
DEFAULT_TAG = 'RECORDED LOCAL EXECUTION / STRIPE TEST MODE'
DEFAULT_PANEL_LABEL = 'RECORDED OUTPUT EXCERPT'


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ('Arial Bold.ttf' if bold else 'Arial.ttf')), size)


def wrap(text, face, width):
    """Wrap only at spaces or existing newlines; never truncate a recorded value."""
    result = []
    for line in text.split('\n'):
        while face.getlength(line) > width:
            spaces = [i for i, char in enumerate(line) if char == ' ' and face.getlength(line[:i]) <= width]
            if not spaces or spaces[-1] == 0:
                raise ValueError(f'Unbroken value is too wide to display: {line[:70]!r}')
            cut = spaces[-1]
            result.append(line[:cut])
            line = line[cut + 1:]
        result.append(line)
    return result


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)
    ]))


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def srt_text(cues, offset=0):
    return '\n'.join(
        f'{i}\n{stamp(start + offset)} --> {stamp(end + offset)}\n{text}\n'
        for i, (start, end, text) in enumerate(cues, 1)
    )


def captions(words, speech, length):
    words = [word for word in words if word.get('type', 'WordBoundary') == 'WordBoundary']
    if not words:
        raise ValueError('WordBoundary timing records are required; no estimated captions.')
    previous = -1
    for word in words:
        start, end = word['offset'] / 1e7, (word['offset'] + word['duration']) / 1e7
        if not word['text'] or not 0 <= start < end <= length + 0.15 or start < previous:
            raise ValueError('Invalid or out-of-order word timing.')
        previous = start
    # Keep authored punctuation when the Edge tokens align; otherwise use Edge's
    # actual spoken words (numbers and hyphenated words may be tokenized differently).
    spoken = speech.split()
    if len(spoken) != len(words) or any(
        ''.join(c for c in token.casefold() if c.isalnum()) !=
        ''.join(c for c in word['text'].casefold() if c.isalnum())
        for token, word in zip(spoken, words)
    ):
        spoken = [word['text'] for word in words]
    cues = []
    index = 0
    while index < len(words):
        stop = index + 1
        while stop < len(words) and stop - index < 7:
            if spoken[stop - 1].endswith(('.', ';', '?', '!')):
                break
            if len(' '.join(spoken[index:stop + 1])) > 64:
                break
            stop += 1
        first, last = words[index], words[stop - 1]
        cues.append((LEAD + first['offset'] / 1e7,
                     LEAD + (last['offset'] + last['duration']) / 1e7,
                     ' '.join(spoken[index:stop])))
        index = stop
    return cues


def background_frame(scene, index, count, title, note):
    background = Image.new('RGB', (1920, 1080), PAPER)
    draw = ImageDraw.Draw(background)
    draw.text((120, 49), 'REBUTTAL', font=font(29, True), fill=INK)
    tag = scene.get('tag', DEFAULT_TAG)
    draw.text((1800 - font(23, True).getlength(tag), 55), tag, font=font(23, True), fill=GREEN)
    draw.line((120, 108, 1800, 108), fill='#b8beb3', width=2)
    draw.text((120, 139), scene['label'], font=font(24, True), fill=GREEN)
    for j, line in enumerate(title):
        draw.text((120, 182 + j * 62), line, font=font(54, True), fill=INK)
    draw.rectangle((120, 337, 1800, 831), fill='#ffffff', outline='#bbc4b9', width=2)
    draw.text((151, 353), scene.get('panel_label', DEFAULT_PANEL_LABEL), font=font(21, True), fill=GREEN)
    draw.text((1675, 353), f'{index + 1:02} / {count:02}', font=font(21), fill=GREEN)
    draw.line((151, 391, 1769, 391), fill='#dfe3db', width=1)
    for j, line in enumerate(note):
        draw.text((140, 856 + j * 35), line, font=font(27), fill=GREEN)
    draw.rectangle((0, 947, 1920, 1080), fill=INK)
    return background


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--storyboard', action='store_true')
    args = parser.parse_args()
    root = args.folder.resolve()
    work = root / 'render'
    work.mkdir(exist_ok=True)
    scenes = json.loads((root / 'scenes.json').read_text())
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('scenes.json must be a nonempty array.')
    timeline, master_cues, offset = [], [], 0

    def run(arguments):
        with (work / 'render.log').open('a') as log:
            subprocess.run(arguments, cwd=work, check=True, stdout=subprocess.DEVNULL, stderr=log)

    prepared = []
    for i, scene in enumerate(scenes):
        for field in ('label', 'title', 'note', 'speech'):
            if not isinstance(scene.get(field), str):
                raise ValueError(f'Scene {i}: {field} must be a string.')
        for field, default, size, width in (
            ('tag', DEFAULT_TAG, 23, 1360),
            ('panel_label', DEFAULT_PANEL_LABEL, 21, 1440),
        ):
            value = scene.get(field, default)
            if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value or font(size, True).getlength(value) > width:
                raise ValueError(f'Scene {i}: {field} must fit on one nonempty line.')
        if not isinstance(scene.get('lines'), list) or not scene['lines'] or not all(isinstance(s, str) for s in scene['lines']):
            raise ValueError(f'Scene {i}: lines must be a nonempty list of literal output strings.')
        title = wrap(scene['title'], font(54, True), 1680)
        note = wrap(scene['note'], font(27), 1640)
        rows = [wrap(line, font(34), 1570) for line in scene['lines']]
        row_height = sum(len(row) * 43 + 13 for row in rows)
        if len(title) > 2 or len(note) > 2 or row_height > 408:
            raise ValueError(f'Scene {i} overflows the legible layout; split it into shorter scenes.')
        if font(24, True).getlength(scene['label']) > 1640:
            raise ValueError(f'Scene {i} label is too long.')
        if args.storyboard:
            prepared.append((scene, title, note, rows))
            continue
        if scene.get('pending_evidence'):
            raise ValueError(f'Scene {i} has pending evidence; only --storyboard is allowed.')
        voice = root / f'voice-{i}.mp3'
        length = float(probe(voice)['format']['duration'])
        total = math.ceil(max(length + LEAD + 1.2, 3.2) * FPS) / FPS
        reveal_at = scene.get('reveal_at')
        if reveal_at is not None and (
            not isinstance(reveal_at, list) or len(reveal_at) != len(scene['lines']) or
            any(not isinstance(value, (int, float)) or isinstance(value, bool) or
                not 0 <= value <= total - 1.3 for value in reveal_at) or
            any(right - left < .3 for left, right in zip(reveal_at, reveal_at[1:]))
        ):
            raise ValueError(f'Scene {i}: reveal_at must give ordered line timings with at least 0.3s between reveals and a final hold.')
        words_path = root / f'voice-{i}.json'
        cues = captions(json.loads(words_path.read_text()), scene['speech'], length)
        prepared.append((scene, voice, length, total, cues, title, note, rows))
    if args.storyboard:
        folder = root / 'storyboard'
        folder.mkdir(exist_ok=True)
        sheet = Image.new('RGB', (1920, math.ceil(len(scenes) / 3) * 390), PAPER)
        for i, (scene, title, note, rows) in enumerate(prepared):
            frame = background_frame(scene, i, len(scenes), title, note)
            draw, y = ImageDraw.Draw(frame), 408
            for row in rows:
                for j, line in enumerate(row):
                    draw.text((151, y + j * 43), line, font=font(34), fill=INK)
                y += len(row) * 43 + 13
            draw.text((120, 990), 'STATIC STORYBOARD / NOT THE FINAL VIDEO', font=font(28, True), fill='white')
            frame.save(folder / f'scene-{i + 1:02}.png')
            sheet.paste(frame.resize((640, 360), Image.Resampling.LANCZOS), (i % 3 * 640, i // 3 * 390))
            ImageDraw.Draw(sheet).text((i % 3 * 640 + 12, i // 3 * 390 + 364), f'Scene {i + 1}: {scene["label"]}', font=font(19), fill=INK)
        sheet.save(folder / 'contact-sheet.jpg', quality=93)
        print(f'Static storyboard complete: {folder}; no audio or video generated.', flush=True)
        return
    if sum(item[3] for item in prepared) >= 300:
        raise ValueError('The complete narration with padding must be under 300 seconds; shorten scenes, never cut words.')

    for i, (scene, voice, length, total, cues, title, note, rows) in enumerate(prepared):
        background = background_frame(scene, i, len(scenes), title, note)
        tag = scene.get('tag', DEFAULT_TAG)
        background.save(work / f'background-{i}.png')

        # Bound still inputs explicitly: FFmpeg 7.1 can stall when shifted,
        # infinitely looping overlays finish on different scheduler queues.
        still_input = ['-loop', '1', '-framerate', str(FPS), '-t', str(total), '-threads', '1']
        inputs = [*still_input, '-i', f'background-{i}.png']
        filters, current, y, reveals = [], '0:v', 408, []
        # Reveal order is editorial, not a claim about original execution timing.
        step = min(0.8, max(0.2, (total - 2.2) / max(1, len(rows))))
        for j, row in enumerate(rows):
            layer = Image.new('RGBA', (1580, len(row) * 43 + 8), (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            for k, line in enumerate(row):
                layer_draw.text((0, k * 43), line, font=font(34), fill=INK)
            layer.save(work / f'line-{i}-{j}.png')
            inputs += [*still_input, '-i', f'line-{i}-{j}.png']
            start = scene['reveal_at'][j] if scene.get('reveal_at') is not None else 0.65 + j * step
            filters.append(f'[{j + 1}:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,setpts=PTS-STARTPTS+{start}/TB[row{j}]')
            filters.append(f'[{current}][row{j}]overlay=151:{y}:eof_action=pass[v{j}]')
            current = f'v{j}'
            reveals.append({'text': scene['lines'][j], 'visual_reveal_seconds': start})
            y += len(row) * 43 + 13
        srt = work / f'captions-{i}.srt'
        srt.write_text(srt_text(cues))
        # Captions are the final visual filter. All synthesized words are retained.
        filters.append(f"[{current}]subtitles=filename='captions-{i}.srt':force_style='FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,Outline=0,Shadow=0,Alignment=2,MarginV=12',format=yuv420p[out]")
        audio_index = len(rows) + 1
        filters.append(f'[{audio_index}:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, length - .03)}:d=0.03,adelay=400:all=1,apad,atrim=duration={total},aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st={total - .03}:d=0.03[a]')
        run([FF, '-nostdin', '-y', '-v', 'error', *inputs, '-i', str(voice), '-filter_complex_threads', '1',
             '-filter_complex', ';'.join(filters), '-map', '[out]', '-map', '[a]', '-t', str(total),
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', f'segment-{i}.mp4'])
        master_cues.extend((start + offset, end + offset, text) for start, end, text in cues)
        timeline.append({'scene': i + 1, 'start': offset, 'end': offset + total,
                         'label': scene['label'], 'tag': tag,
                         'panel_label': scene.get('panel_label', DEFAULT_PANEL_LABEL),
                         'speech': scene['speech'], 'output_lines': reveals,
                         'reveal_timing': 'Editorial visualization; not original execution timing',
                         'voice_sha256': hashlib.sha256(voice.read_bytes()).hexdigest(),
                         'timings_sha256': hashlib.sha256((root / f'voice-{i}.json').read_bytes()).hexdigest()})
        offset += total
        print(f'Rendered scene {i + 1}/{len(scenes)}: {total:.2f}s', flush=True)

    (work / 'concat.txt').write_text(''.join(f"file 'segment-{i}.mp4'\n" for i in range(len(scenes))))
    output = root / 'rebuttal-verified-preview.mp4'
    run([FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'concat.txt', '-c', 'copy', '-movflags', '+faststart', str(output)])
    info = probe(output)
    actual = float(info['format']['duration'])
    video = next(stream for stream in info['streams'] if stream['codec_type'] == 'video')
    if actual >= 300 or abs(actual - offset) > 0.15 or (video['width'], video['height']) != (1920, 1080):
        raise ValueError(f'Output verification failed: duration={actual}, dimensions={video["width"]}x{video["height"]}')
    run([FF, '-v', 'error', '-i', str(output), '-f', 'null', '-'])
    (root / 'captions.srt').write_text(srt_text(master_cues))
    (root / 'timeline.json').write_text(json.dumps({'duration_seconds': actual,
        'scenes_sha256': hashlib.sha256((root / 'scenes.json').read_bytes()).hexdigest(),
        'scenes': timeline}, indent=2))
    sheet = Image.new('RGB', (1280, len(scenes) * 390), PAPER)
    sheet_draw = ImageDraw.Draw(sheet)
    for i, item in enumerate(timeline):
        for column, point in enumerate((item['start'] + 0.85, item['end'] - 0.65)):
            frame = work / f'check-{i}-{column}.png'
            run([FF, '-y', '-v', 'error', '-ss', str(point), '-i', str(output), '-frames:v', '1', str(frame)])
            with Image.open(frame) as source:
                sheet.paste(source.resize((640, 360), Image.Resampling.LANCZOS), (column * 640, i * 390))
            sheet_draw.text((column * 640 + 12, i * 390 + 364), f'Scene {i + 1} / {point:.2f}s', font=font(19), fill=INK)
    sheet.save(root / 'contact-sheet.jpg', quality=93)
    print(f'Complete: {output} ({actual:.2f}s); full decode passed.', flush=True)


if __name__ == '__main__':
    main()
