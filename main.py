import os
import json
import time
import random
import requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TEST_MODE = True          # टेस्ट मोड (सिर्फ 5 साइट्स)
AI_ENABLED = True         # Groq AI इस्तेमाल करना है

# टेस्ट के लिए बहुत छोटी फिक्स्ड लिस्ट
FIXED_SITES = [
    "https://firefaucet.win",
    "https://cointiply.com/ptc-ads",
    "https://freebitco.in",
    "https://freedogecoin.net",
    "https://free-solana.com"
]

# ========== DDG SEARCH (टेस्ट के लिए बंद) ==========
def ddg_search_new_sites(num_queries=0):
    return []  # टेस्ट में कोई DDG नहीं

# ========== AI FALLBACK (Groq) ==========
def ask_ai_what_to_do(page_text, url):
    if not GROQ_API_KEY or not AI_ENABLED:
        return None
    prompt = f"""You are a crypto faucet bot. Analyze the webpage text and decide what action to take.
Page URL: {url}
Page text (first 1000 chars): {page_text[:1000]}

Reply with JSON: {{"action": "fill_and_claim"/"click_button"/"skip", "keyword": "button text"}}"""
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 100,
                "temperature": 0.3
            },
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return json.loads(content)
    except:
        pass
    return None

# ========== क्रिप्टो डिटेक्टर ==========
def detect_crypto_type(text):
    text = text.lower()
    if "solana" in text or "sol" in text.split(): return "SOL"
    if "usdt" in text or "tether" in text: return "USDT"
    if "bnb" in text or "binance coin" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "ethereum" in text or "eth" in text.split(): return "ETH"
    return "BTC"

# ========== कुकी बैनर ==========
def handle_cookie_banner(page):
    for word in ["accept", "ok", "agree", "close", "consent", "allow", "got it"]:
        try:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}')")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
                return True
        except:
            pass
    return False

# ========== ड्रॉपडाउन ==========
def handle_dropdown(page, crypto):
    selects = page.query_selector_all("select")
    for sel in selects:
        options = sel.query_selector_all("option")
        for opt in options:
            val = (opt.get_attribute("value") or "").lower()
            text = (opt.inner_text() or "").lower()
            if crypto.lower() in val or crypto.lower() in text:
                opt.select_option()
                return True
        if options:
            options[0].select_option()
            return True
    return False

# ========== साइट पर काम ==========
def try_claim(page, url, success_list):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        body_text = page.locator("body").inner_text(timeout=5000).lower()
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))
        handle_dropdown(page, crypto)

        # इनपुट भरो
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']")
        filled = False
        for inp in inputs[:2]:
            try:
                if inp.get_attribute("type") == "number" or "amount" in (inp.get_attribute("name") or "").lower():
                    inp.fill("1")
                    page.wait_for_timeout(300)
                else:
                    inp.fill(wallet)
                    filled = True
                    page.wait_for_timeout(random.randint(300, 600))
                break
            except:
                pass

        # बटन दबाओ
        for word in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    page.wait_for_timeout(random.randint(800, 1500))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        success_list.append((url, crypto))
                    return
                except:
                    pass

        # कोई बटन नहीं मिला → AI से पूछो
        if not filled:
            ai = ask_ai_what_to_do(body_text, url)
            if ai:
                action = ai.get("action")
                keyword = ai.get("keyword", "")
                if action == "click_button" and keyword:
                    btn = page.query_selector(f"button:has-text('{keyword}'), a:has-text('{keyword}')")
                    if btn:
                        btn.click()
                        page.wait_for_timeout(2000)
                        if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                            success_list.append((url, crypto))
                elif action == "fill_and_claim":
                    wallet_input = page.query_selector("input[type='text'], input[name*='wallet']")
                    if wallet_input:
                        wallet_input.fill(wallet)
                    for w in ["claim","roll","earn","start"]:
                        b = page.query_selector(f"button:has-text('{w}'), a:has-text('{w}')")
                        if b:
                            b.click()
                            page.wait_for_timeout(2000)
                            break
        else:
            # फॉर्म भरा था, सबमिट करो
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        success_list.append((url, crypto))
                except:
                    pass
    except:
        pass

# ========== MAIN ==========
def fly():
    print("🌍 EarnAI AI-Test 🚀 (5 Sites)")
    all_urls = list(FIXED_SITES)
    total = len(all_urls)
    print(f"🎯 Sites: {total}\n")

    success_list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        for i, url in enumerate(all_urls, 1):
            print(f"[{i}/{total}] {url}")
            try_claim(page, url, success_list)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    print(f"\n🏁 किया गया: {total} sites")
    print(f"✅ सफल: {len(success_list)}")
    for url, coin in success_list:
        print(f"   + {url} ({coin})")
    if GROQ_API_KEY and AI_ENABLED:
        print("🧠 AI तैयार था (ज़रूरत पड़ने पर)")
    else:
        print("ℹ️ AI नहीं था")

if __name__ == "__main__":
    fly()
