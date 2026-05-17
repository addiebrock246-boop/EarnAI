import os
import json
import time
import random
import requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

TEST_MODE = True          # टेस्ट मोड — 5 फिक्स्ड + 10 DDG = 15 साइट
AI_ENABLED = True         # AI प्री-चेक चालू

# छोटी फिक्स्ड लिस्ट (टेस्ट)
FIXED_SITES = [
    "https://firefaucet.win",
    "https://cointiply.com/ptc-ads",
    "https://freebitco.in",
    "https://freedogecoin.net",
    "https://free-solana.com"
]

# ========== DDG SEARCH (टेस्ट में 10 साइट) ==========
def ddg_search_new_sites(num_queries=5):
    coins = list(wallets.keys())[:3]
    actions = ["faucet","claim","earn","airdrop","giveaway"]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"free {coin} {act} wallet address instant 2026")
    queries = list(set(queries))[:num_queries]
    
    tasks = []
    seen = set()
    with DDGS() as ddgs:
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=2))
                for r in results:
                    href = r.get("href")
                    if not href: continue
                    skip = ["academy","support","blog","faq","youtube","reddit","medium","twitter","facebook","news"]
                    if any(w in href for w in skip): continue
                    if href not in seen:
                        seen.add(href)
                        tasks.append(href)
                time.sleep(random.randint(2, 3))
            except:
                continue
    return tasks[:10]  # सिर्फ 10 साइट

# ========== GitHub Models AI ==========
def ask_github_ai(prompt):
    if not GITHUB_TOKEN: return None
    try:
        resp = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": "Reply with ONLY 'yes' or 'no'."},
                    {"role": "user", "content": prompt}
                ],
                "model": "gpt-4o", "max_tokens": 5, "temperature": 0.1
            }, timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip().lower()
    except: pass
    return None

# ========== Groq AI (बैकअप) ==========
def ask_groq_ai(prompt):
    if not GROQ_API_KEY: return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "llama-3.3-70b-versatile", "max_tokens": 5, "temperature": 0.1
            }, timeout=5
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip().lower()
    except: pass
    return None

# ========== AI प्री-चेक ==========
def ai_pre_check(page_text, url, ai_call_counter):
    prompt = f"""Analyze this webpage text. Can a bot claim free crypto here by ONLY filling a wallet address?
Page URL: {url}
Page text (first 1200 chars): {page_text[:1200]}

Criteria for "yes":
- No login, sign up, registration, or KYC required
- No captcha or human verification mentioned
- A wallet address or email input field exists
- A claim, earn, roll, or start button exists
- The site promises free crypto instantly

Reply with ONLY one word: "yes" or "no"."""
    
    # 1. GitHub Models
    answer = ask_github_ai(prompt)
    if answer is not None:
        ai_call_counter[0] += 1
        print(f"    🤖 GitHub AI → '{answer}'")
        return answer.startswith("yes")
    
    # 2. Groq बैकअप
    answer = ask_groq_ai(prompt)
    if answer is not None:
        ai_call_counter[0] += 1
        print(f"    🤖 Groq AI → '{answer}'")
        return answer.startswith("yes")
    
    print("    🤖 AI उपलब्ध नहीं, कीवर्ड फ़िल्टर पर छोड़ रहे हैं")
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
        except: pass
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

# ========== साइट विज़िटर + क्लेमर ==========
def try_claim(page, url, success_list, ai_call_counter):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        body_text = page.locator("body").inner_text(timeout=5000).lower()

        # ===== 0. AI प्री-चेक (30% साइटों पर) =====
        if AI_ENABLED and (GITHUB_TOKEN or GROQ_API_KEY) and random.random() < 0.3:
            ai_verdict = ai_pre_check(body_text, url, ai_call_counter)
            if ai_verdict is False:
                print(f"    ❌ AI ने मना किया — छोड़ रहे हैं")
                return
            elif ai_verdict is True:
                print(f"    ✅ AI ने हाँ कही — आगे बढ़ रहे हैं")

        # ===== 1. लॉगिन/KYC कीवर्ड फ़िल्टर =====
        login_keywords = ["login", "sign in", "register", "create account", "kyc", "verify identity"]
        if any(kw in body_text for kw in login_keywords):
            print(f"    🚫 लॉगिन/KYC कीवर्ड मिला — छोड़ रहे हैं")
            return

        # ===== 2. क्रिप्टो पहचान और इनपुट भरो =====
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))
        handle_dropdown(page, crypto)

        inputs = page.query_selector_all(
            "input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']"
        )
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
            except: pass

        # ===== 3. बटन दबाओ =====
        for word in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    page.wait_for_timeout(random.randint(800, 1500))
                    content = page.content().lower()
                    if any(w in content for w in ["success","credited","sent","thank","congrat"]) \
                       and not any(kw in content for kw in login_keywords):
                        success_list.append((url, crypto))
                        print(f"    💰 सफलता! ({crypto})")
                    return
                except: pass

        # ===== 4. सबमिट =====
        if filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                    content = page.content().lower()
                    if any(w in content for w in ["success","credited","sent","thank","congrat"]) \
                       and not any(kw in content for kw in login_keywords):
                        success_list.append((url, crypto))
                        print(f"    💰 सफलता! ({crypto})")
                except: pass
    except: pass

# ========== MAIN ==========
def fly():
    print("🌍 EarnAI AI-Test (DDG + GitHub AI) 🚀")
    
    all_urls = list(FIXED_SITES)
    new_urls = ddg_search_new_sites()
    all_urls.extend(new_urls)
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    
    print(f"📋 Fixed: {len(FIXED_SITES)} | 🆕 DDG: {len(new_urls)} | 🎯 Total: {total}\n")
    if GITHUB_TOKEN: print("🔑 GitHub Models AI उपलब्ध")
    if GROQ_API_KEY: print("🔑 Groq AI बैकअप उपलब्ध")
    print()

    success_list = []
    ai_call_counter = [0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        for i, url in enumerate(all_urls, 1):
            print(f"[{i}/{total}] {url[:70]}...")
            try_claim(page, url, success_list, ai_call_counter)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    print(f"\n🏁 किया गया: {total} sites")
    print(f"✅ सफल: {len(success_list)}")
    for url, coin in success_list:
        print(f"   + {url} ({coin})")
    print(f"🧠 AI कॉल: {ai_call_counter[0]} बार")

if __name__ == "__main__":
    fly()
