import os
import json
import time
import random
from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

# ========== DuckDuckGo से 10 नई साइट्स ==========
def quick_search():
    queries = [
        "free BTC faucet wallet address instant",
        "free USDT claim wallet address",
        "free SOL faucet enter address"
    ]
    tasks = []
    seen = set()
    with DDGS() as ddgs:
        for q in queries:
            print(f"🔍 DuckDuckGo: '{q}'")
            try:
                results = list(ddgs.text(q, max_results=5))
                for r in results:
                    href = r.get("href")
                    if not href: continue
                    skip = ["academy","support","blog","faq","youtube","reddit","medium","twitter","facebook","news"]
                    if any(w in href for w in skip): continue
                    if href not in seen:
                        seen.add(href)
                        tasks.append(href)
                time.sleep(random.randint(2, 3))  # सम्मान
            except Exception as e:
                print(f"   ❌ {e}")
    return tasks

# ========== क्रिप्टो पहचान ==========
def detect_crypto_type(text):
    text = text.lower()
    if "solana" in text or "sol" in text.split(): return "SOL"
    if "toncoin" in text or "ton" in text.split(): return "TON"
    if "usdt" in text or "tether" in text: return "USDT"
    if "bnb" in text or "binance coin" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "eth" in text or "ethereum" in text: return "ETH"
    return "BTC"

# ========== साइट पर जाकर कोशिश ==========
def try_claim(page, url):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        body_text = page.inner_text("body").lower()
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))
        print(f"    ℹ️ '{crypto}' माँग")

        # इनपुट भरो
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']")
        filled = False
        for inp in inputs[:2]:
            try:
                inp.fill(wallet)
                print(f"    📝 {crypto} एड्रेस भरा")
                filled = True
                page.wait_for_timeout(random.randint(300, 600))
                break
            except: pass

        # बटन दबाओ
        for word in ["claim","roll","earn","start","free","get","submit","send","reward"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन दबाया")
                    page.wait_for_timeout(random.randint(800, 1500))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        print("    ✅ सफलता!")
                    return
                except: pass

        if filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    print("    ✅ सबमिट किया")
                except: pass
    except Exception as e:
        print(f"    ❌ {str(e)[:40]}")

# ========== MAIN ==========
def fly():
    print("🌍 DuckDuckGo टेस्ट 🚀")
    urls = quick_search()
    print(f"\n🎯 {len(urls)} साइटें मिलीं। पहली 5 पर कोशिश।\n")
    if not urls:
        print("❌ कोई साइट नहीं मिली।")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(urls[:5], 1):
            print(f"[{i}/5] {url[:70]}...")
            try_claim(page, url)
            time.sleep(random.randint(1, 2))
        browser.close()
    print("\n🏁 टेस्ट पूरा। DuckDuckGo सफल! अब फुल वर्ज़न चलाओ।")

if __name__ == "__main__":
    fly()
