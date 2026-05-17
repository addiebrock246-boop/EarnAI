import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")

def serper_search():
    queries = [
        "site:freecash.com earn offers",
        "site:firefaucet.win claim faucet",
        "site:jumptask.io microtask",
        "site:superteam.fun bounty",
        "site:taskon.xyz quest earn",
        "site:galxe.com campaign reward",
        "site:layer3.xyz quest",
        "faucet crypto claim instant no KYC 2026",
        "microtask earn crypto no KYC instant payout",
        "crypto task complete earn Satoshi 2026",
        "free crypto ptc ads 2026"
    ]
    tasks = []
    seen = set()
    for q in queries:
        print(f"🔍 Serper: '{q}'")
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 3},
                timeout=10
            )
            if resp.status_code == 200:
                items = resp.json().get("organic", [])
                print(f"   ↳ {len(items)} लिंक")
                for item in items:
                    link = item.get("link")
                    if not link:
                        continue
                    skip_words = ["academy", "support", "blog", "faq", "about", "press", "career", "contact"]
                    if any(f"/{w}/" in link or f"/{w}" in link for w in skip_words):
                        continue
                    if "youtube.com" in link or "reddit.com" in link or "medium.com" in link:
                        continue
                    if link not in seen:
                        seen.add(link)
                        tasks.append({"url": link, "title": item.get("title", "")[:80]})
            elif resp.status_code == 429:
                print("   ⚠️ Serper quota खत्म, अगले महीने रीसेट होगा।")
                break
        except Exception as e:
            print(f"   ❌ {e}")
        time.sleep(random.uniform(0.5, 1.5))
    return tasks

def execute_task(page, url):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(random.randint(2000, 4000))

        # 1. सबसे पहले, जाने-माने बटन शब्द खोजो
        action_words = ["claim", "earn", "roll", "start", "free", "get", "receive",
                        "quest", "participate", "join", "complete", "surf", "view"]
        for word in action_words:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन दबाया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                    return
                except:
                    pass

        # 2. अगर कोई बटन नहीं मिला, तो वॉलेट एड्रेस भरो
        inputs = page.query_selector_all(
            "input[type='text'], input[type='email'], input[name*='wallet'], input[name*='address']"
        )
        if inputs:
            for inp in inputs[:2]:
                try:
                    inp.fill(WALLET)
                    print(f"    📝 {WALLET[:6]}... भरा")
                    page.wait_for_timeout(random.randint(800, 1500))
                except:
                    pass
            # सबमिट बटन दबाओ
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    print("    ✅ सबमिट किया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                except:
                    pass

    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – आत्मनिर्भर जॉब हंटर 🚀")
    tasks = serper_search()
    print(f"\n🎯 {len(tasks)} टास्क मिले। पहले 8 पर कोशिश करते हैं।\n")
    if not tasks:
        print("कोई टास्क नहीं मिला।")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        for i, task in enumerate(tasks[:8]):
            print(f"[{i+1}/8]")
            execute_task(page, task["url"])
            time.sleep(random.randint(2, 4))

        browser.close()
        print("🏁 मिशन पूरा।")

if __name__ == "__main__":
    fly()
