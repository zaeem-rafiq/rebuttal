# scripts/generate_audio.py
"""
Synthesizes the comprehensive, professional Rebuttal demo video voiceover script
using AWS Polly Neural Text-to-Speech (VoiceId='Matthew').
Produces docs/media/demo_narration.mp3 (~3:45 target duration).
"""
import os
import sys
import boto3

ACTS = [
    {
        "name": "Act 1: The Problem — The $150 Billion Chargeback Trap",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "For small, independent e-commerce merchants selling on Stripe, chargebacks are a silent, brutal bleed. "
            "<break time=\"500ms\"/>"
            "Every single dispute comes with an immediate, non-refundable fifteen-dollar penalty fee from the card network. "
            "<break time=\"400ms\"/>"
            "Merchants are given a narrow window, often just seven days, to assemble evidentiary packets across Shopify, shipping carriers, and customer support threads. "
            "<break time=\"500ms\"/>"
            "Because gathering this evidence by hand is tedious and confusing, over eighty percent of merchants either forfeit by default or paste together weak, unformatted rebuttals that get denied. "
            "<break time=\"600ms\"/>"
            "That is billions of dollars lost annually to friendly fraud. "
            "<break time=\"700ms\"/>"
            "Meet Rebuttal: the autonomous chargeback defense agent built on the AWS Strands Agents SDK and Amazon Bedrock AgentCore."
            "</prosody>"
            "<break time=\"2200ms\"/>"
            "</speak>"
        )
    },
    {
        "name": "Act 2: The Architecture & The Case File Interface",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "Rebuttal acts as an autonomous legal paralegal working on the merchant's behalf overnight. "
            "<break time=\"500ms\"/>"
            "When designing Rebuttal, we rejected generic SaaS dashboards and built The Case File. "
            "<break time=\"400ms\"/>"
            "Inspired by judicial bench dockets, our interface is disciplined and distraction-free: genuine paper-and-ink contrast, strict monospace typography for financial identifiers, and a clear desk policy. "
            "<break time=\"500ms\"/>"
            "Everything on screen is either verified evidence, an active decision, or a deadline. "
            "<break time=\"600ms\"/>"
            "Under the hood, an event-driven ingestion pipeline powered by AWS SAM, Amazon API Gateway, and Lambda captures Stripe webhooks. "
            "<break time=\"500ms\"/>"
            "A multi-agent state graph orchestrated by Bedrock AgentCore Runtime executes autonomous investigation routines against Shopify, UPS, and customer communication channels."
            "</prosody>"
            "<break time=\"2200ms\"/>"
            "</speak>"
        )
    },
    {
        "name": "Act 3: Scenario S1 — Autonomous Defense & Instant Win",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "Let us watch Scenario One unfold in real time. "
            "<break time=\"500ms\"/>"
            "A customer files a forty-eight-dollar dispute claiming product not received. "
            "<break time=\"400ms\"/>"
            "Within milliseconds of receiving the Stripe webhook, Rebuttal's triage agent classifies the claim and initiates an evidence sweep. "
            "<break time=\"500ms\"/>"
            "It queries the merchant's order system, retrieves carrier tracking from UPS, pulls the signed proof of delivery, and verifies the delivery coordinates match the customer's billing address. "
            "<break time=\"500ms\"/>"
            "On the docket, you can see Rebuttal assembling Exhibits A through E: the original order, carrier tracking, signed delivery receipt, customer purchase history, and store refund policy. "
            "<break time=\"500ms\"/>"
            "Rebuttal calculates an eighty-eight percent win probability. "
            "<break time=\"400ms\"/>"
            "Because this exceeds the merchant's sixty percent policy threshold, the agent acts autonomously: it formats the evidence into Stripe's strict arbitration schema and submits the rebuttal directly to the Stripe API. "
            "<break time=\"500ms\"/>"
            "The dispute is stamped WON, protecting forty-eight dollars without requiring a single second of merchant effort."
            "</prosody>"
            "<break time=\"2500ms\"/>"
            "</speak>"
        )
    },
    {
        "name": "Act 4: Scenario S2 — Human-in-the-Loop via Telegram & SMS Gate",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "Autonomous systems must also know when not to fight. "
            "<break time=\"500ms\"/>"
            "In Scenario Two, a three-hundred-forty-dollar chargeback arrives marked as fraudulent. "
            "<break time=\"500ms\"/>"
            "Rebuttal's investigation reveals that this is a repeat VIP customer who has spent thousands in the store. "
            "<break time=\"400ms\"/>"
            "Our win probability model projects only a twenty-two percent chance of victory against friendly fraud claims of this type. "
            "<break time=\"500ms\"/>"
            "Fighting aggressively could permanently alienate a loyal customer and incur arbitration penalties. "
            "<break time=\"600ms\"/>"
            "Here, Rebuttal halts execution at an Approval Gate. "
            "<break time=\"400ms\"/>"
            "It generates a concise executive brief and dispatches an interactive push notification directly to the merchant's phone via Telegram and Twilio SMS. "
            "<break time=\"500ms\"/>"
            "Notice the action buttons: Fight, Concede, or Hold. "
            "<break time=\"400ms\"/>"
            "The merchant reviews the memo on their phone, recognizes the VIP customer, and taps Concede. "
            "<break time=\"500ms\"/>"
            "Instantly, our AWS Lambda webhook captures the callback, securely verifies the origin, and routes the decision into the Amazon Bedrock AgentCore runtime. "
            "<break time=\"500ms\"/>"
            "The dispute is conceded gracefully, preventing an adversarial dispute and retaining the customer."
            "</prosody>"
            "<break time=\"2500ms\"/>"
            "</speak>"
        )
    },
    {
        "name": "Act 5: Scenario S3 — Pre-Dispute Inquiry Prevention",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "Scenario Three demonstrates proactive dispute prevention. "
            "<break time=\"500ms\"/>"
            "Before a customer files a formal chargeback, payment networks issue a pre-dispute inquiry or early fraud warning. "
            "<break time=\"500ms\"/>"
            "Most merchants miss these alerts because they arrive quietly in Stripe notifications. "
            "<break time=\"400ms\"/>"
            "Rebuttal monitors inquiries in real time. "
            "<break time=\"400ms\"/>"
            "Here, an active subscriber was confused about their annual renewal and initiated an inquiry for one hundred twenty-nine dollars. "
            "<break time=\"500ms\"/>"
            "Rebuttal detects that the account is in good standing and that the customer simply requested cancellation. "
            "<break time=\"500ms\"/>"
            "Instead of allowing this inquiry to escalate into a formal dispute, which would trigger a fifteen-dollar penalty fee, Rebuttal automatically issues a prompt refund and cancels the recurring billing. "
            "<break time=\"500ms\"/>"
            "The dispute is prevented before it ever starts, saving the merchant fifteen dollars and safeguarding their Stripe dispute ratio."
            "</prosody>"
            "<break time=\"2200ms\"/>"
            "</speak>"
        )
    },
    {
        "name": "Act 6: Enterprise Hardening & Closing",
        "ssml": (
            "<speak>"
            "<prosody rate=\"95%\">"
            "Rebuttal is engineered with enterprise discipline. "
            "<break time=\"500ms\"/>"
            "Every tool call enforces strict Pydantic schemas. "
            "<break time=\"400ms\"/>"
            "All secrets resolve at runtime via AWS Secrets Manager with zero context leakage. "
            "<break time=\"500ms\"/>"
            "Our automated decision evals harness tests forty-eight distinct dispute permutations, proving a one hundred percent policy compliance rate. "
            "<break time=\"500ms\"/>"
            "And our web console achieved a perfect one hundred accessibility score on Google Lighthouse. "
            "<break time=\"600ms\"/>"
            "Rebuttal gives small Stripe merchants the same sophisticated, data-driven legal defense that Fortune 500 retailers possess. "
            "<break time=\"600ms\"/>"
            "Rebuttal: autonomous chargeback defense, with human oversight when it matters most. "
            "<break time=\"500ms\"/>"
            "Thank you."
            "</prosody>"
            "</speak>"
        )
    }
]

def main():
    print("Connecting to AWS Polly in us-east-1...")
    polly = boto3.client("polly", region_name="us-east-1")
    
    output_dir = os.path.join("docs", "media")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "demo_narration.mp3")
    
    total_audio = bytearray()
    
    for i, act in enumerate(ACTS, start=1):
        name = act["name"]
        ssml_text = act["ssml"]
        print(f"Synthesizing {name} with AWS Polly Neural (Matthew)...")
        try:
            resp = polly.synthesize_speech(
                Engine="neural",
                VoiceId="Matthew",
                OutputFormat="mp3",
                TextType="ssml",
                Text=ssml_text
            )
            audio_data = resp["AudioStream"].read()
            print(f"  -> Generated {len(audio_data)} bytes")
            total_audio.extend(audio_data)
        except Exception as e:
            print(f"ERROR synthesizing {name}: {e}", file=sys.stderr)
            sys.exit(1)
            
    with open(output_file, "wb") as f:
        f.write(total_audio)
        
    print(f"\nSUCCESS: Master voiceover audio written to {output_file}")
    print(f"Total Audio Size: {len(total_audio)} bytes (~{len(total_audio) / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
