import os
import time
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")

def serper_search():
    queries = [
        "crypto earn task no KYC 2026",
        "web3 bounty for AI agent",
        "free crypto airdrop quest",
        "simple crypto task complete earn"
    ]
    tasks = []
    seen = set()
    for q in queries:
        print(f"🔍 Serper: '{q}'")
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("organic", [])
                print(f"   ↳ {len(items)} लिंक")
                for item in items:
                    link = item.get("link")
                    if link and link not in seen:
                        seen.add(link)
                        tasks.append(link)
            elif resp.status_code == 429:
                print("   ⚠️ Quota खत्म"); break
            else:
                print(f"   ❌ {resp.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ {e}")
    return tasks

def try_click_form(page, url):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)
        # हर तरह के बटन क्लिक करो
        btns = page.query_selector_all("button, a.btn, input[type='submit']")
        for btn in btns[:3]:
            try:
                btn.click()
                print("    🖱️ Clicked")
                page.wait_for_timeout(1000)
            except:
                pass
        # हर तरह के इनपुट में वॉलेट भरो
        inputs = page.query_selector_all("input[type='text'], input[type='email']")
        for inp in inputs[:2]:
            try:
                inp.fill(WALLET)
                print(f"    📝 Filled {WALLET[:6]}...")
                page.wait_for_timeout(500)
            except:
                pass
        # सबमिट बटन
        submit = page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            try:
                submit.click()
                print("    ✅ Submitted")
                page.wait_for_timeout(2000)
            except:
                pass
    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI - AI रहित स्पीड टेस्ट")
    urls = serper_search()
    print(f"\n🎯 {len(urls)} URLs मिले। केवल पहले 5 पर कोशिश करेंगे।\n")
    if not urls:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(urls[:5]):
            print(f"[{i+1}/5]")
            try_click_form(page, url)
            time.sleep(2)
        browser.close()
        print("🏁 टेस्ट पूरा।")

if __name__ == "__main__":
    fly()
