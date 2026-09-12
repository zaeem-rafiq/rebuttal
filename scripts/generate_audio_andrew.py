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
        "delay_ms": 0,
        "text": (
            "For small, independent e-commerce merchants selling on Stripe, chargebacks are a silent, brutal bleed. "
            "Every single dispute comes with an immediate, non-refundable fifteen-dollar penalty fee from the card network. "
            "Merchants are given a narrow window, often just seven days, to assemble evidentiary packets across Shopify, shipping carriers, and customer support threads. "
            "Because gathering this evidence by hand is tedious and confusing, over eighty percent of merchants either forfeit by default or paste together weak rebuttals that get denied. "
            "That is billions of dollars lost annually to friendly fraud. "
            "Meet Rebuttal: the autonomous chargeback defense agent built on the AWS Strands Agents SDK and Amazon Bedrock AgentCore."
        ),
    },
    {
        "id": 2,
        "name": "Act 2: Architecture & Case File",
        "delay_ms": 22000,
        "text": (
            "Rebuttal acts as an autonomous legal paralegal working on the merchant's behalf overnight. "
            "When designing Rebuttal, we rejected generic SaaS dashboards and built The Case File. "
            "Inspired by judicial bench dockets, our interface is disciplined and distraction-free: genuine paper-and-ink contrast, strict monospace typography for financial identifiers, and a clear desk policy. "
            "Everything on screen is either verified evidence, an active decision, or a deadline. "
            "Under the hood, an event-driven ingestion pipeline powered by AWS SAM, Amazon API Gateway, and Lambda captures Stripe webhooks, while a multi-agent state graph orchestrated by Bedrock AgentCore Runtime executes autonomous investigation routines against Shopify, UPS, and customer communication channels."
        ),
    },
    {
        "id": 3,
        "name": "Act 3: Scenario S1 Autonomous Carrier Win",
        "delay_ms": 45000,
        "text": (
            "Let us watch Scenario One unfold in real time. "
            "A customer files a forty-eight-dollar dispute claiming product not received. "
            "Within milliseconds of receiving the Stripe webhook, Rebuttal's triage agent classifies the claim and initiates an evidence sweep. "
            "It queries the merchant's order system, retrieves carrier tracking from UPS, pulls the signed proof of delivery, and verifies the delivery coordinates match the customer's billing address. "
            "On the docket, you can see Rebuttal assembling Exhibits A through E: the original order, carrier tracking, signed delivery receipt, customer purchase history, and store refund policy. "
            "Rebuttal calculates an eighty-eight percent win probability. "
            "Because this exceeds the merchant's policy threshold, the agent acts autonomously: it formats the evidence into Stripe's strict arbitration schema and submits the rebuttal directly to the Stripe API. "
            "The dispute is stamped WON, protecting forty-eight dollars without requiring a single second of merchant effort."
        ),
    },
    {
        "id": 4,
        "name": "Act 4: Scenario S2 Human Gate & Telegram",
        "delay_ms": 74000,
        "text": (
            "Autonomous systems must also know when not to fight. "
            "In Scenario Two, a three-hundred-forty-dollar chargeback arrives marked as fraudulent. "
            "Rebuttal's investigation reveals that this is a repeat VIP customer who has spent thousands in the store. "
            "Our win probability model projects only a twenty-two percent chance of victory against friendly fraud claims of this type. "
            "Fighting aggressively could permanently alienate a loyal customer and incur arbitration penalties. "
            "Here, Rebuttal halts execution at an Approval Gate. "
            "It generates a concise executive brief and dispatches an interactive push notification directly to the merchant's phone via Telegram and Twilio SMS. "
            "Notice the action buttons: Fight, Concede, or Hold. "
            "The merchant reviews the memo on their phone, recognizes the VIP customer, and taps Concede. "
            "Instantly, our AWS Lambda webhook captures the callback, securely verifies the origin, and routes the decision into the Amazon Bedrock AgentCore runtime. "
            "The dispute is conceded gracefully, preventing an adversarial dispute and retaining the customer."
        ),
    },
    {
        "id": 5,
        "name": "Act 5: Scenario S3 Pre-Dispute Inquiry",
        "delay_ms": 106000,
        "text": (
            "Scenario Three demonstrates proactive dispute prevention. "
            "Before a customer files a formal chargeback, payment networks issue a pre-dispute inquiry or early fraud warning. "
            "Most merchants miss these alerts because they arrive quietly in Stripe notifications. "
            "Rebuttal monitors inquiries in real time. "
            "Here, an active subscriber was confused about their annual renewal and initiated an inquiry for one hundred twenty-nine dollars. "
            "Rebuttal detects that the account is in good standing and that the customer simply requested cancellation. "
            "Instead of allowing this inquiry to escalate into a formal dispute, which would trigger a fifteen-dollar penalty fee, Rebuttal automatically issues a prompt refund and cancels the recurring billing. "
            "The dispute is prevented before it ever starts, saving the merchant fifteen dollars and safeguarding their Stripe dispute ratio."
        ),
    },
    {
        "id": 6,
        "name": "Act 6: Hardening & Closing",
        "delay_ms": 131000,
        "text": (
            "Rebuttal is engineered with enterprise discipline. "
            "Every tool call enforces strict Pydantic schemas. "
            "All secrets resolve at runtime via AWS Secrets Manager with zero context leakage. "
            "Our automated decision evals harness tests forty-eight distinct dispute permutations, proving a one hundred percent policy compliance rate, and our web console achieved a perfect one hundred accessibility score on Google Lighthouse. "
            "Rebuttal gives small Stripe merchants the same sophisticated, data-driven legal defense that Fortune 500 retailers possess. "
            "Rebuttal: autonomous chargeback defense, with human oversight when it matters most. "
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
        comm = edge_tts.Communicate(act["text"], VOICE, rate="+1%")
        await comm.save(act_file)
        print(f"  -> Saved {act_file}")


def mix_master_audio():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print("\nMixing audio tracks with exact scene delays...")

    # Build input arguments
    inputs = []
    filter_delays = []
    filter_inputs = []

    for idx, act in enumerate(ACTS):
        act_file = os.path.join(ACTS_DIR, f"act_{act['id']}.mp3")
        inputs.extend(["-i", act_file])
        delay = act["delay_ms"]
        filter_delays.append(f"[{idx}:a]adelay={delay}|{delay}[a{idx}]")
        filter_inputs.append(f"[a{idx}]")

    filter_graph = f"{'; '.join(filter_delays)}; {''.join(filter_inputs)}amix=inputs={len(ACTS)}:normalize=0[aout]"

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
