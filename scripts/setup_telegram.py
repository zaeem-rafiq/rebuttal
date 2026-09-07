import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
webhook_url = os.getenv(
    "TELEGRAM_WEBHOOK_URL",
    "https://n2g4gh2yjripct4y4sre3lnx2e0ivggv.lambda-url.us-east-1.on.aws/",
)

if not bot_token:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set in environment or .env")
    sys.exit(1)

if not chat_id:
    print("ERROR: TELEGRAM_CHAT_ID is not set in environment or .env")
    sys.exit(1)

print("1. Verifying Telegram Bot credentials...")
try:
    me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
    with urllib.request.urlopen(me_url, timeout=10) as resp:
        bot_info = json.loads(resp.read().decode("utf-8"))
        if bot_info.get("ok"):
            username = bot_info["result"].get("username")
            first_name = bot_info["result"].get("first_name")
            print(f"   SUCCESS: Connected to @{username} ({first_name})")
        else:
            print("   ERROR: Invalid bot token response:", bot_info)
            sys.exit(1)
except Exception as e:
    print("   ERROR connecting to Telegram Bot API:", e)
    sys.exit(1)

print("\n2. Configuring Telegram Webhook to Lambda...")
try:
    set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}&drop_pending_updates=True"
    with urllib.request.urlopen(set_url, timeout=10) as resp:
        wh_res = json.loads(resp.read().decode("utf-8"))
        if wh_res.get("ok"):
            print(f"   SUCCESS: Webhook registered -> {webhook_url}")
            print(f"   Details: {wh_res.get('description')}")
        else:
            print("   WARNING: Webhook registration issue:", wh_res)
except Exception as e:
    print("   ERROR setting webhook:", e)

print(f"\n3. Sending interactive test alert to Telegram Chat ID: {chat_id}")
try:
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": (
            "⚖️ *Rebuttal Defense Agent — Telegram Connected*\n\n"
            "Real-time dispute defense notifications with one-tap inline actions "
            "are now active for your store.\n\n"
            "*Test Dispute:* `dp_S2` (General Merchandise)\n"
            "*Amount:* $85.00 · *Reason:* `product_not_received`\n"
            "*Recommendation:* FIGHT (92% win probability)\n\n"
            "Tap a button below or reply with `1` (Fight), `2` (Concede), or `3` (Hold):"
        ),
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "1 ⚔️ Fight", "callback_data": "fight:dp_S2"},
                    {"text": "2 🤝 Concede", "callback_data": "concede:dp_S2"},
                    {"text": "3 ⏸️ Hold", "callback_data": "hold:dp_S2"},
                ]
            ]
        },
    }
    req = urllib.request.Request(
        send_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        send_res = json.loads(resp.read().decode("utf-8"))
        if send_res.get("ok"):
            print("   SUCCESS: Interactive test alert delivered to your Telegram app!")
        else:
            print("   ERROR sending test message:", send_res)
except Exception as e:
    print("   ERROR sending message to chat:", e)

print("\nTelegram integration setup complete.")
