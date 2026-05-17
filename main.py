import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ["WALLET_ADDRESS"]

def serper_search():
    # हर तरह के माइक्रो-टास्क, PTC, क्वेस्ट, और फौसेट को टारगेट करें
    queries = [
        "microtask earn crypto wallet address no login 2026",
        "PTC ads earn Bitcoin without account wallet only 2026",
        "crypto quest complete and earn BTC wallet address 2026",
        "free bitcoin claim wallet address no registration instant",
        "best bitcoin faucets direct wallet no signup 2026",
        "earn satoshi without login just enter address 2026",
        "crypto task get reward wallet address only 2026",
        "simple crypto task complete earn Satoshi 2026"
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
                    skip = ["academy", "support", "blog", "faq", "youtube", "reddit", "medium", "twitter", "facebook"]
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

def try_task(page, url):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(random.randint(2000, 4000))

        # पेज की बॉडी का टेक्स्ट स्कैन करो ताकि पता चले कि यहाँ क्या है
        body_text = page.inner_text("body").lower()

        # 1. अगर पेज पर FaucetPay या Microwallet का जिक्र है, तो सीधे वॉलेट एड्रेस भरो
        if "faucetpay" in body_text or "microwallet" in body_text or "faucethub" in body_text:
            print("    ℹ️ FaucetPay/Microwallet साइट लग रही है।")
            # ईमेल या एड्रेस फील्ड ढूंढो
            email_input = page.query_selector("input[type='email'], input[name='email'], input[placeholder*='email']")
            if email_input:
                # यहाँ पर हम वॉलेट एड्रेस को ही डाल देंगे
                email_input.fill(WALLET)
                print(f"    📧 वॉलेट एड्रेस डाला: {WALLET[:10]}...")
                page.wait_for_timeout(500)
                # Submit/Claim बटन दबाओ
                claim_btn = page.query_selector("button:has-text('Claim'), a:has-text('Claim'), input[value*='Claim' i]")
                if claim_btn:
                    claim_btn.click()
                    print("    🖱️ Claim बटन दबाया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                    if any(w in page.content().lower() for w in ["success", "credited", "sent"]):
                        print("    ✅ सफलता मिली!")
                    return
            return  # FaucetPay वाली साइट पर और कुछ नहीं करना

        # 2. अगर पेज पर कोई माइक्रो-टास्क या क्वेस्ट का जिक्र है
        if any(w in body_text for w in ["microtask", "ptc", "quest", "task", "offer"]):
            print("    ℹ️ माइक्रो-टास्क/क्वेस्ट साइट लग रही है।")
            # 'Earn', 'Complete', 'Start' जैसे बटन खोजो
            action_words = ["earn", "start", "complete", "get", "free", "quest"]
            for word in action_words:
                btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}')")
                if btn:
                    try:
                        btn.click()
                        print(f"    🖱️ '{word}' बटन दबाया")
                        page.wait_for_timeout(random.randint(1500, 3000))
                        return
                    except:
                        pass
            # अगर कोई बटन नहीं मिला, तो वॉलेट एड्रेस भरके देखो
            wallet_input = page.query_selector("input[type='text'], input[name*='address'], input[name*='wallet']")
            if wallet_input:
                wallet_input.fill(WALLET)
                print(f"    📝 वॉलेट एड्रेस भरा")
                page.wait_for_timeout(500)
                submit = page.query_selector("button[type='submit'], input[type='submit']")
                if submit:
                    submit.click()
                    print("    ✅ सबमिट किया")
                    page.wait_for_timeout(random.randint(1500, 3000))
            return

        # 3. सामान्य फौसेट साइट (सिर्फ एड्रेस और क्लेम)
        print("    ℹ️ सामान्य फौसेट साइट लग रही है।")
        wallet_input = page.query_selector("input[type='text'], input[name*='address'], input[name*='wallet']")
        if wallet_input:
            wallet_input.fill(WALLET)
            print(f"    📝 वॉलेट एड्रेस भरा: {WALLET[:10]}...")
            page.wait_for_timeout(random.randint(500, 1000))
        # Claim/Roll/Earn बटन दबाओ
        claim_words = ["claim", "roll", "earn", "get", "start", "free", "reward", "spin"]
        for word in claim_words:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन दबाया")
                    page.wait_for_timeout(random.randint(2000, 3000))
                    if any(w in page.content().lower() for w in ["success", "credited", "sent", "thank"]):
                        print("    ✅ कमाई सफल लग रही है!")
                    return
                except:
                    pass

        # 4. अगर कुछ भी नहीं मिला, तो जो भी बटन हो, दबा दो
        all_btns = page.query_selector_all("button, a.btn")
        for btn in all_btns[:3]:
            try:
                btn.click()
                print("    🖱️ एक बटन दबाया")
                page.wait_for_timeout(1000)
            except:
                pass

    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – Universal Micro-Task + Faucet Hunter 🚀")
    urls = serper_search()
    print(f"\n🎯 {len(urls)} साइटें मिलीं। पहले 15 पर कोशिश।\n")
    if not urls:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(urls[:15]):
            print(f"[{i+1}/15]")
            try_task(page, url)
            time.sleep(random.randint(2, 4))
        browser.close()
        print("🏁 मिशन पूरा।")

if __name__ == "__main__":
    fly()
