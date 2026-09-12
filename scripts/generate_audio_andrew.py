#!/usr/bin/env python3
"""scripts/generate_audio_andrew.py
Synthesizes professional, natural human-like narration for the Rebuttal demo video
using Microsoft Azure / Edge Neural TTS (en-US-AndrewMultilingualNeural).
Aligns each act to exact scene timestamps:
- Act 1: 00:00 (The Problem)
- Act 2: 00:22 (Architecture & Case File)
- Act 3: 00:45 (Scenario S1 Autonomous Win)
- Act 4: 01:14 (Scenario S2 Human Gate & Telegram)
- Act 5: 01:46 (Scenario S3 Pre-Dispute Inquiry)
- Act 6: 02:11 (Hardening & Closing)
"""

import os
import sys
import asyncio
import subprocess
import imageio_ffmpeg
import edge_tts

VOICE = "en-US-AndrewMultilingualNeural"
OUTPUT_DIR = os.path.join("docs", "media")
ACTS_DIR = os.path.join(OUTPUT_DIR, "acts")
MASTER_AUDIO = os.path.join(OUTPUT_DIR, "demo_narration.mp3")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "rebuttal_demo_video.mp4")
TEMP_VIDEO = os.path.join(OUTPUT_DIR, "rebuttal_demo_video_temp.mp4")

ACTS = [
    {
        "id": 1,
        "name": "Act 1: The Problem",
        "text": (
            "For small Stripe merchants, chargebacks are a silent, brutal bleed. "
            "Every dispute brings an immediate fifteen-dollar network fee, tight seven-day deadlines, "
            "and hours of evidence gathering across Shopify and carriers. Over eighty percent forfeit by default. "
            "Meet Rebuttal: autonomous chargeback defense built on the AWS Strands Agents SDK and Amazon Bedrock AgentCore."
        ),
    },
    {
        "id": 2,
        "name": "Act 2: Architecture & Case File",
        "text": (
            "Rebuttal acts as an autonomous legal paralegal working overnight. "
            "We rejected generic SaaS dashboards and built The Case File: genuine paper-and-ink contrast, "
            "strict monospace typography, and a clear desk policy. "
            "Under the hood, an event-driven AWS Lambda pipeline captures Stripe webhooks, "
            "while a Bedrock AgentCore multi-agent graph coordinates evidence collection."
        ),
    },
    {
        "id": 3,
        "name": "Act 3: Scenario S1 Autonomous Carrier Win",
        "text": (
            "In Scenario One, a customer claims product not received for forty-eight dollars. "
            "Rebuttal's triage agent immediately sweeps Shopify and UPS tracking, "
            "retrieving GPS coordinates and cardholder delivery signatures for Exhibit B. "
            "Projecting an eighty-eight percent win rate, Rebuttal submits arbitration evidence directly to Stripe. "
            "The dispute is stamped WON, saving forty-eight dollars with zero merchant effort."
        ),
    },
    {
        "id": 4,
        "name": "Act 4: Scenario S2 Human Gate & Telegram",
        "text": (
            "Autonomous systems must also know when not to fight. "
            "In Scenario Two, a three-hundred-forty-dollar chargeback arrives for a repeat VIP customer. "
            "With a low win probability, fighting risks relationship damage. "
            "Rebuttal triggers an Approval Gate, sending an interactive Telegram push alert. "
            "The merchant taps Concede, and Bedrock AgentCore gracefully closes the case, preserving customer loyalty."
        ),
    },
    {
        "id": 5,
        "name": "Act 5: Scenario S3 Pre-Dispute Inquiry",
        "text": (
            "Scenario Three demonstrates proactive dispute prevention. "
            "When an active subscriber initiated an inquiry for one hundred twenty-nine dollars after requesting cancellation, "
            "Rebuttal intercepts it before it becomes a formal chargeback. "
            "It issues a prompt refund and cancels billing, preventing the dispute, saving the merchant fifteen dollars, "
            "and protecting their Stripe dispute ratio."
        ),
    },
    {
        "id": 6,
        "name": "Act 6: Enterprise Hardening & Closing",
        "text": (
            "Rebuttal is enterprise-hardened with strict Pydantic schemas, zero context leakage via AWS Secrets Manager, "
            "forty-eight automated evals, and a hundred out of a hundred on Lighthouse. "
            "Rebuttal: autonomous chargeback defense with human oversight when it matters most. "
            "Thank you."
        ),
    },
]


async def synthesize_acts():
    os.makedirs(ACTS_DIR, exist_ok=True)
    print(f"Synthesizing 6 acts with {VOICE}...")
    for act in ACTS:
        act_file = os.path.join(ACTS_DIR, f"act_{act['id']}.mp3")
        print(f"  Synthesizing {act['name']}...")
        comm = edge_tts.Communicate(act["text"], VOICE, rate="+4%")
        await comm.save(act_file)
        print(f"  -> Saved {act_file}")


def mix_master_audio():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print("\nConcatenating audio tracks sequentially with clean silence gaps (zero overlap)...")

    # Generate a 1.2s silence gap file
    silence_file = os.path.join(ACTS_DIR, "silence_gap.mp3")
    cmd_silence = [
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", "1.2",
        "-q:a", "9",
        "-acodec", "libmp3lame",
        silence_file
    ]
    subprocess.run(cmd_silence, check=True, capture_output=True)

    # Initial 0.8s silence at start
    start_silence = os.path.join(ACTS_DIR, "start_silence.mp3")
    subprocess.run([
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.8",
        "-q:a", "9",
        "-acodec", "libmp3lame",
        start_silence
    ], check=True, capture_output=True)

    # Final 2.0s silence at end
    end_silence = os.path.join(ACTS_DIR, "end_silence.mp3")
    subprocess.run([
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", "2.0",
        "-q:a", "9",
        "-acodec", "libmp3lame",
        end_silence
    ], check=True, capture_output=True)

    # Build sequential inputs: start_silence + (act_i + silence_gap)*5 + act_6 + end_silence
    inputs = ["-i", start_silence]
    for idx, act in enumerate(ACTS):
        act_file = os.path.join(ACTS_DIR, f"act_{act['id']}.mp3")
        inputs.extend(["-i", act_file])
        if idx < len(ACTS) - 1:
            inputs.extend(["-i", silence_file])
    inputs.extend(["-i", end_silence])

    # Number of streams = 1 + 6 + 5 + 1 = 13
    num_streams = 1 + len(ACTS) + (len(ACTS) - 1) + 1
    filter_graph = f"concat=n={num_streams}:v=0:a=1[aout]"

    cmd = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", filter_graph,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        MASTER_AUDIO
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg mixing error:", res.stderr, file=sys.stderr)
        sys.exit(1)
    print(f"SUCCESS: Master audio track written to {MASTER_AUDIO}")


def remux_video():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    if not os.path.exists(VIDEO_PATH):
        print("ERROR: Video not found at", VIDEO_PATH, file=sys.stderr)
        sys.exit(1)

    print(f"\nRemuxing {VIDEO_PATH} with new voiceover...")
    cmd = [
        ffmpeg_exe, "-y",
        "-i", VIDEO_PATH,
        "-i", MASTER_AUDIO,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        TEMP_VIDEO
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg remux error:", res.stderr, file=sys.stderr)
        sys.exit(1)

    os.replace(TEMP_VIDEO, VIDEO_PATH)
    print(f"SUCCESS: Remuxed demo video updated at {VIDEO_PATH}!")
    size_mb = os.path.getsize(VIDEO_PATH) / (1024 * 1024)
    print(f"Final video size: {size_mb:.2f} MB")


async def main():
    await synthesize_acts()
    mix_master_audio()
    remux_video()


if __name__ == "__main__":
    asyncio.run(main())
