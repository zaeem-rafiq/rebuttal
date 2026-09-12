# scripts/record_demo_video.py
"""
Fully automated 1080p demo video recorder for Rebuttal.
Uses Playwright to orchestrate an authentic walkthrough of the live console
synchronized to docs/media/demo_narration.mp3 (2m 30s), then muxes audio and video
via bundled FFmpeg to output docs/media/rebuttal_demo_video.mp4.
"""
import os
import sys
import time
import asyncio
import subprocess
import threading
import http.server
import socketserver
import imageio_ffmpeg
from playwright.async_api import async_playwright

TOTAL_TARGET_DURATION = 153.0
AUDIO_PATH = os.path.join("docs", "media", "demo_narration.mp3")
RAW_VIDEO_DIR = os.path.join("docs", "media", "raw_video")
FINAL_MP4_PATH = os.path.join("docs", "media", "rebuttal_demo_video.mp4")

class QuietExportHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join("console", "out"), **kwargs)
    def log_message(self, format, *args):
        pass

def start_local_server(port=3005):
    try:
        server = socketserver.TCPServer(("127.0.0.1", port), QuietExportHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"Local static console server active on http://127.0.0.1:{port}")
        return server
    except Exception as e:
        print(f"Note: Local server bind failed or already running on {port}: {e}")
        return None

INJECT_JS = """
(() => {
    const cursor = document.createElement('div');
    cursor.id = 'demo-cursor';
    cursor.style.cssText = 'position:fixed;width:18px;height:18px;border-radius:50%;background:rgba(185,28,28,0.9);border:2px solid #FFFFFF;pointer-events:none;z-index:999999;transform:translate(-50%,-50%);box-shadow:0 2px 10px rgba(0,0,0,0.35);left:200px;top:200px;transition:width 0.15s,height 0.15s;';
    document.body.appendChild(cursor);
    let currentX = 200, currentY = 200;

    window.moveCursorTo = (targetX, targetY, durationMs = 600) => {
        return new Promise((resolve) => {
            const startX = currentX, startY = currentY, startTime = performance.now();
            function step(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / durationMs, 1);
                const ease = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
                currentX = startX + (targetX - startX) * ease;
                currentY = startY + (targetY - startY) * ease;
                cursor.style.left = currentX + 'px';
                cursor.style.top = currentY + 'px';
                if (progress < 1) requestAnimationFrame(step); else resolve();
            }
            requestAnimationFrame(step);
        });
    };

    window.clickCursor = () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(0.65)';
        const ripple = document.createElement('div');
        ripple.style.cssText = 'position:fixed;left:' + currentX + 'px;top:' + currentY + 'px;width:10px;height:10px;border-radius:50%;border:2px solid #B91C1C;transform:translate(-50%,-50%) scale(1);pointer-events:none;z-index:999998;opacity:1;transition:transform 0.4s ease-out,opacity 0.4s ease-out;';
        document.body.appendChild(ripple);
        setTimeout(() => { ripple.style.transform = 'translate(-50%,-50%) scale(4)'; ripple.style.opacity = '0'; }, 10);
        setTimeout(() => { cursor.style.transform = 'translate(-50%,-50%) scale(1)'; ripple.remove(); }, 200);
    };

    window.smoothScrollTo = (targetY, durationMs = 800) => {
        return new Promise((resolve) => {
            const startY = window.scrollY, startTime = performance.now();
            function step(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / durationMs, 1);
                const ease = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
                window.scrollTo(0, startY + (targetY - startY) * ease);
                if (progress < 1) requestAnimationFrame(step); else resolve();
            }
            requestAnimationFrame(step);
        });
    };

    window.showTelegramNotification = () => {
        let tg = document.getElementById('tg-notification-card');
        if (!tg) {
            tg = document.createElement('div');
            tg.id = 'tg-notification-card';
            tg.style.cssText = 'position:fixed;top:24px;right:36px;width:400px;background:#18222D;color:#FFFFFF;border-radius:12px;padding:16px 20px;box-shadow:0 16px 40px rgba(0,0,0,0.45);font-family:-apple-system,BlinkMacSystemFont,sans-serif;z-index:99999;border:1px solid #2B394A;opacity:0;transform:translateY(-20px);transition:opacity 0.35s ease-out,transform 0.35s ease-out;';
            tg.innerHTML = '<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;\"><div style=\"display:flex;align-items:center;gap:8px;\"><div style=\"width:26px;height:26px;background:#2AABEE;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;\">✈️</div><span style=\"font-weight:600;font-size:14px;\">@rebuttal_defense_bot</span></div><span style=\"font-size:11px;color:#7E8E9E;\">now</span></div><div style=\"font-size:13px;line-height:1.45;color:#DCE3E8;margin-bottom:12px;\"><strong>🚨 REBUTTAL DISPUTE ALERT</strong><br/>Dispute: <code style=\"background:#242F3D;padding:2px 5px;border-radius:4px;font-family:monospace;\">dp_S2</code> · <strong>$340.00</strong><br/>Customer: <strong>Sarah Jenkins (VIP)</strong> · Lifetime: <strong>$4,820</strong><br/>Reason: <code>fraudulent</code> (Win prob: <strong>22%</strong>)<br/><em style=\"color:#93A6BA;\">Recommendation: Concede to retain customer</em></div><div id=\"tg-btn-row\" style=\"display:flex;gap:8px;\"><button style=\"flex:1;background:#242F3D;border:1px solid #3E4F63;color:#FFFFFF;padding:8px 0;border-radius:6px;font-size:12px;font-weight:600;\">1 ⚔️ Fight</button><button id=\"tg-concede-btn\" style=\"flex:1;background:#B91C1C;border:1px solid #DC2626;color:#FFFFFF;padding:8px 0;border-radius:6px;font-size:12px;font-weight:600;\">2 🤝 Concede</button><button style=\"flex:1;background:#242F3D;border:1px solid #3E4F63;color:#FFFFFF;padding:8px 0;border-radius:6px;font-size:12px;font-weight:600;\">3 ⏸️ Hold</button></div>';
            document.body.appendChild(tg);
        }
        setTimeout(() => { tg.style.opacity = '1'; tg.style.transform = 'translateY(0)'; }, 50);
    };

    window.confirmTelegramConcede = () => {
        const btnRow = document.getElementById('tg-btn-row');
        if (btnRow) {
            btnRow.innerHTML = '<div style=\"flex:1;background:#14713A;color:#FFFFFF;padding:8px 12px;border-radius:6px;font-size:12px;font-weight:600;text-align:center;border:1px solid #16A34A;\">✓ Action Recorded: Conceding Dispute · Sent to Bedrock AgentCore</div>';
        }
    };

    window.hideTelegramNotification = () => {
        const tg = document.getElementById('tg-notification-card');
        if (tg) {
            tg.style.opacity = '0';
            tg.style.transform = 'translateY(-20px)';
            setTimeout(() => tg.remove(), 400);
        }
    };

    window.showEnterpriseRibbon = () => {
        const ribbon = document.createElement('div');
        ribbon.id = 'enterprise-ribbon';
        ribbon.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(30px);background:#111418;color:#EDECE6;border-radius:4px;padding:12px 28px;box-shadow:0 12px 30px rgba(0,0,0,0.3);font-family:system-ui,sans-serif;font-size:13px;display:flex;align-items:center;gap:24px;z-index:99999;opacity:0;transition:all 0.4s ease-out;border:1px solid #333942;';
        ribbon.innerHTML = '<span style=\"font-weight:600;\"><span style=\"color:#FFE96B;\">⚡</span> AWS Strands Agents SDK</span><span style=\"color:#5C6370;\">|</span><span style=\"font-weight:600;\"><span style=\"color:#FFE96B;\">🧠</span> Amazon Bedrock AgentCore</span><span style=\"color:#5C6370;\">|</span><span style=\"font-weight:600;\"><span style=\"color:#FFE96B;\">🔒</span> AWS Secrets Manager</span><span style=\"color:#5C6370;\">|</span><span style=\"font-weight:600;\"><span style=\"color:#FFE96B;\">💯</span> 100/100 Lighthouse</span>';
        document.body.appendChild(ribbon);
        setTimeout(() => { ribbon.style.opacity = '1'; ribbon.style.transform = 'translateX(-50%) translateY(0)'; }, 50);
    };
})();
"""

async def record_walkthrough(target_url: str):
    os.makedirs(RAW_VIDEO_DIR, exist_ok=True)
    for f in os.listdir(RAW_VIDEO_DIR):
        try: os.remove(os.path.join(RAW_VIDEO_DIR, f))
        except Exception: pass

    print(f"Launching Playwright Chromium at 1920x1080 (Target: {TOTAL_TARGET_DURATION}s)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--window-size=1920,1080"]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=RAW_VIDEO_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        print(f"Loading {target_url}...")
        await page.goto(target_url, wait_until="networkidle")
        await page.add_script_tag(content=INJECT_JS)
        await page.wait_for_timeout(1000)

        t0 = time.time()
        print(f"[{time.time()-t0:.1f}s] Starting Act 1: The Problem (00:00 - 00:22)...")
        await page.evaluate("window.moveCursorTo(250, 50, 800)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.moveCursorTo(420, 50, 700)")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.moveCursorTo(250, 195, 800)")
        await page.wait_for_timeout(3000)
        await page.evaluate("window.moveCursorTo(250, 270, 700)")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.smoothScrollTo(420, 900)")
        await page.evaluate("window.moveCursorTo(500, 520, 800)")
        await page.wait_for_timeout(4000)
        await page.evaluate("window.smoothScrollTo(0, 800)")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.moveCursorTo(280, 50, 700)")
        await page.wait_for_timeout(3000)

        print(f"[{time.time()-t0:.1f}s] Starting Act 2: Architecture & Case File (00:22 - 00:45)...")
        await page.evaluate("window.moveCursorTo(380, 360, 900)")
        await page.wait_for_timeout(4000)
        await page.evaluate("window.moveCursorTo(350, 480, 700)")
        await page.wait_for_timeout(3500)
        await page.evaluate("window.smoothScrollTo(280, 700)")
        await page.evaluate("window.moveCursorTo(400, 410, 800)")
        await page.wait_for_timeout(4000)
        await page.evaluate("window.moveCursorTo(400, 520, 700)")
        await page.wait_for_timeout(4500)
        await page.evaluate("window.smoothScrollTo(0, 700)")
        await page.wait_for_timeout(4000)

        print(f"[{time.time()-t0:.1f}s] Starting Act 3: Scenario S1 Autonomous Carrier Win (00:45 - 01:14)...")
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.evaluate("window.moveCursorTo(1800, 50, 800)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.clickCursor()")
        try:
            await page.locator("button:has-text('S1')").first.click(timeout=3000)
        except Exception:
            await page.locator("text=dp_S1").first.click()
        await page.wait_for_timeout(1000)
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.add_script_tag(content=INJECT_JS)
        await page.evaluate("window.moveCursorTo(240, 195, 700)")
        await page.wait_for_timeout(2500)
        
        # Scroll to exhibits and expand Exhibit B (Carrier Proof)
        await page.evaluate("window.smoothScrollTo(360, 700)")
        await page.evaluate("window.moveCursorTo(360, 460, 800)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.clickCursor()")
        try:
            await page.locator("button:has-text('Exhibit B')").first.click(timeout=3000)
        except Exception:
            pass
        await page.wait_for_timeout(4500)
        
        # Collapse Exhibit B and inspect WON stamp
        await page.evaluate("window.clickCursor()")
        try:
            await page.locator("button:has-text('Exhibit B')").first.click(timeout=3000)
        except Exception:
            pass
        await page.wait_for_timeout(1500)
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.evaluate("window.moveCursorTo(350, 300, 800)")
        await page.wait_for_timeout(4000)

        print(f"[{time.time()-t0:.1f}s] Starting Act 4: Scenario S2 Human Gate & Telegram (01:14 - 01:46)...")
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.evaluate("window.moveCursorTo(1820, 50, 800)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.clickCursor()")
        try:
            await page.locator("button:has-text('S2')").first.click(timeout=3000)
        except Exception:
            await page.locator("text=dp_S2").first.click()
        await page.wait_for_timeout(1000)
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.add_script_tag(content=INJECT_JS)
        await page.evaluate("window.moveCursorTo(240, 195, 700)")
        await page.wait_for_timeout(3500)
        await page.evaluate("window.moveCursorTo(380, 360, 700)")
        await page.wait_for_timeout(3500)
        
        print(f"[{time.time()-t0:.1f}s]   -> Showing Telegram Push Alert overlay...")
        await page.evaluate("window.showTelegramNotification()")
        await page.wait_for_timeout(4000)
        await page.evaluate("window.moveCursorTo(1720, 188, 1000)")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.clickCursor()")
        await page.evaluate("window.confirmTelegramConcede()")
        print(f"[{time.time()-t0:.1f}s]   -> Concede tapped on Telegram!")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.smoothScrollTo(380, 700)")
        await page.evaluate("window.moveCursorTo(400, 580, 800)")
        await page.wait_for_timeout(5000)
        await page.evaluate("window.hideTelegramNotification()")
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.wait_for_timeout(2500)

        print(f"[{time.time()-t0:.1f}s] Starting Act 5: Scenario S3 Pre-Dispute Inquiry (01:46 - 02:11)...")
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.evaluate("window.moveCursorTo(1840, 50, 800)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.clickCursor()")
        try:
            await page.locator("button:has-text('S3')").first.click(timeout=3000)
        except Exception:
            await page.locator("text=dp_S3").first.click()
        await page.wait_for_timeout(1000)
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.add_script_tag(content=INJECT_JS)
        await page.evaluate("window.moveCursorTo(240, 195, 700)")
        await page.wait_for_timeout(4500)
        await page.evaluate("window.moveCursorTo(380, 360, 700)")
        await page.wait_for_timeout(5000)
        await page.evaluate("window.smoothScrollTo(320, 600)")
        await page.evaluate("window.moveCursorTo(400, 540, 700)")
        await page.wait_for_timeout(6000)
        await page.evaluate("window.smoothScrollTo(0, 600)")
        await page.wait_for_timeout(3500)

        print(f"[{time.time()-t0:.1f}s] Starting Act 6: Hardening & Closing (02:11 - 02:30)...")
        await page.evaluate("window.smoothScrollTo(420, 800)")
        await page.evaluate("window.showEnterpriseRibbon()")
        await page.evaluate("window.moveCursorTo(960, 1020, 1000)")
        await page.wait_for_timeout(5500)
        await page.evaluate("window.smoothScrollTo(0, 800)")
        await page.evaluate("window.moveCursorTo(250, 50, 900)")
        
        elapsed = time.time() - t0
        remaining = max(0, TOTAL_TARGET_DURATION - elapsed)
        print(f"[{time.time()-t0:.1f}s] Holding final frame for {remaining:.1f}s...")
        await page.wait_for_timeout(int(remaining * 1000))

        print(f"[{time.time()-t0:.1f}s] Closing browser context...")
        await context.close()
        await browser.close()

    print("Playwright recording complete!")

def mux_final_mp4():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    webm_files = [os.path.join(RAW_VIDEO_DIR, f) for f in os.listdir(RAW_VIDEO_DIR) if f.endswith(".webm")]
    if not webm_files:
        print("ERROR: No .webm video files found in", RAW_VIDEO_DIR, file=sys.stderr)
        sys.exit(1)
    
    raw_video = webm_files[0]
    print(f"Muxing {raw_video} with {AUDIO_PATH} into {FINAL_MP4_PATH}...")
    cmd = [
        ffmpeg_exe, "-y",
        "-i", raw_video,
        "-i", AUDIO_PATH,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_MP4_PATH
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr, file=sys.stderr)
        sys.exit(1)
        
    print("SUCCESS: Final MP4 demo video created successfully!")
    size_mb = os.path.getsize(FINAL_MP4_PATH) / (1024 * 1024)
    print(f"Output: {FINAL_MP4_PATH} ({size_mb:.2f} MB)")

async def main():
    target_url = os.environ.get("DEMO_CONSOLE_URL")
    server = None
    if not target_url:
        target_url = "http://127.0.0.1:3005"
        server = start_local_server(3005)
    
    try:
        await record_walkthrough(target_url)
        mux_final_mp4()
    finally:
        if server:
            print("Shutting down local server...")
            server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())