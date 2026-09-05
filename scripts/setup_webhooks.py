import os
import sys
from dotenv import load_dotenv

load_dotenv("c:/Users/zaeem/Documents/Rebuttal/.env")

stripe_key = os.getenv("STRIPE_SECRET_KEY")
assert stripe_key and stripe_key.startswith("sk_test_"), "Live-key guard: STRIPE_SECRET_KEY must start with sk_test_"

stripe_wh_url = "https://qsmgbb5rtmmgnmry6u55uanxy40pwvhq.lambda-url.us-east-1.on.aws/"
twilio_wh_url = "https://n2g4gh2yjripct4y4sre3lnx2e0ivggv.lambda-url.us-east-1.on.aws/"

print(f"Configuring Stripe webhook endpoint -> {stripe_wh_url}")
import stripe
stripe.api_key = stripe_key

# 1. Check existing endpoints
endpoints = stripe.WebhookEndpoint.list(limit=10)
existing_ep = None
for ep in endpoints.data:
    if ep.url == stripe_wh_url:
        existing_ep = ep
        break

if existing_ep:
    print(f"Stripe webhook endpoint already exists: {existing_ep.id}")
    wh_secret = getattr(existing_ep, "secret", None)
else:
    new_ep = stripe.WebhookEndpoint.create(
        url=stripe_wh_url,
        enabled_events=[
            "charge.dispute.created",
            "charge.dispute.closed",
            "charge.dispute.updated"
        ],
        description="Rebuttal Bedrock AgentCore Stripe Webhook"
    )
    print(f"Created Stripe webhook endpoint: {new_ep.id}")
    wh_secret = getattr(new_ep, "secret", None)

if wh_secret:
    print(f"Webhook signing secret prefix: {wh_secret[:8]}...")

# 2. Configure Twilio Phone Number SMS Webhook
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_FROM")

if account_sid and auth_token and twilio_from:
    print(f"Configuring Twilio messaging webhook for {twilio_from} -> {twilio_wh_url}")
    from twilio.rest import Client
    tw_client = Client(account_sid, auth_token)
    
    # Find the incoming phone number SID
    numbers = tw_client.incoming_phone_numbers.list(phone_number=twilio_from)
    if numbers:
        phone_record = numbers[0]
        updated = tw_client.incoming_phone_numbers(phone_record.sid).update(
            sms_url=twilio_wh_url,
            sms_method="POST"
        )
        print(f"Updated Twilio phone number {phone_record.phone_number} (SID: {phone_record.sid}) sms_url to: {updated.sms_url}")
    else:
        print(f"Warning: Twilio number {twilio_from} not found in account incoming phone numbers.")
else:
    print("Twilio credentials or TWILIO_FROM not set.")
