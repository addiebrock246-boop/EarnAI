import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ["WALLET_ADDRESS"]   # तेरा BTC एड्रेस (bc1q...)

def serper_search():
    queries = [
        "bitcoin faucet instant payout no login no captcha wallet address only",
        "free BTC claim wallet address 2026 no KYC",
        "faucet BTC direct wallet no registration 2026",
        "earn Satoshi without login just enter address",
        "PTC ads earn Bitcoin without account wallet only",
        "crypto task get reward wallet address only",
        "free bitcoin click ads enter wallet address",
        "btc faucet no email wallet address claim 2026",
        "instant bitcoin faucet wallet only 2026",
        "micro task earn BTC wallet address only no login"
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
                timeout=10
            )
            if resp.status_code == 200:
                items = resp.json().get("organic", [])
                print(f"   ↳ {len(items)} लिंक")
                for item in items:
                    link = item.get("link")
                    if not link:
                        continue
                    # बेकार लिंक हटाओ
                    skip = ["academy", "support", "blog", "faq", "youtube", "reddit", "medium", "twitter"]
                    if any(w in link for w in skip):
                        continue
                    if link not in seen:
                        seen.add(link)
                        tasks.append(link)
            elif resp.status_code == 429:
                print("   ⚠️ Serper quota खत्म, अगले महीने रीसेट।")
                break
        except Exception as e:
            print(f"   ❌ {e}")
        time.sleep(random.uniform(0.5, 1.5))
    return tasks

def try_claim(page, url):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(random.randint(2000, 4000))

        # 1. सबसे पहले BTC वॉलेट एड्रेस डालने की जगह ढूँढो
        wallet_input = page.query_selector(
            "input[type='text'], input[name*='address'], input[name*='wallet'], input[placeholder*='address'], input[placeholder*='wallet'], input[placeholder*='BTC']"
        )
        if wallet_input:
            wallet_input.fill(WALLET)
            print(f"    📝 BTC एड्रेस भरा: {WALLET[:10]}...")
            page.wait_for_timeout(random.randint(500, 1000))
        else:
            print("    ℹ️ कोई एड्रेस फ़ील्ड नहीं मिला।")

        # 2. अब Claim/Roll/Earn/Get/Start जैसा कोई भी बटन दबाओ
        claim_words = ["claim", "roll", "earn", "get", "start", "free", "receive", "reward", "spin"]
        for word in claim_words:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन दबाया")
                    page.wait_for_timeout(random.randint(2000, 3000))
                    # सफलता की जाँच
                    content = page.content().lower()
                    if any(w in content for w in ["success", "credited", "sent", "thank", "congrat", "reward", "paid"]):
                        print("    ✅ लगता है कमाई हो गई!")
                    else:
                        print("    ⚠️ सफलता की पुष्टि नहीं हुई।")
                    return
                except:
                    pass

        # 3. अगर कोई बटन नहीं मिला, लेकिन एड्रेस डाला था, तो सबमिट बटन दबाओ
        if wallet_input:
            submit_btn = page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Submit'), button:has-text('Send')")
            if submit_btn:
                try:
                    submit_btn.click()
                    print("    ✅ फ़ॉर्म सबमिट किया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                except:
                    pass

    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – BTC Address-Only AutoClaimer 🚀")
    urls = serper_search()
    print(f"\n🎯 {len(urls)} साइटें मिलीं। पहले 15 पर कोशिश।\n")
    if not urls:
        print("कोई साइट नहीं मिली।")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(urls[:15]):
            print(f"[{i+1}/15]")
            try_claim(page, url)
            time.sleep(random.randint(2, 4))
        browser.close()
        print("🏁 मिशन पूरा। कुछ साइटों ने सीधे बैलेंस दिया होगा, तो अपने BTC वॉलेट की हिस्ट्री देखो।")

if __name__ == "__main__":
    fly()
