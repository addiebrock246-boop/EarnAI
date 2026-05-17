import os, json, time, random, requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
WALLETS_JSON  = os.environ["WALLETS_JSON"]
wallets       = json.loads(WALLETS_JSON)

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

TEST_MODE     = True              # ✅ टेस्ट मोड (10 साइटें)
AI_ENABLED    = True              # AI प्री-चेक चालू
MAX_AI_CALLS_PER_RUN = 5         # टेस्ट में सिर्फ 5 AI कॉल

# ========== NO‑LOGIN FAUCETS (टेस्ट के लिए छोटी लिस्ट) ==========
FIXED_SITES = [
    "https://sepolia-faucet.pk910.de",       # Sepolia ETH – बस एड्रेस डालो
    "https://solfaucet.com",                 # SOL faucet
    "https://faucet.solana.com",             # Solana Devnet
    "https://faucet.polygon.technology",     # Polygon
    "https://faucet.quicknode.com",          # QuickNode Multi-chain
]

# ========== DDG SEARCH (टेस्ट में 5 नई साइटें) ==========
def ddg_search_new_sites(num_queries=3):
    coins = list(wallets.keys())[:3] if TEST_MODE else list(wallets.keys())
    actions = [
        "faucet no login no registration",
        "claim free without account",
        "earn instantly wallet address only",
    ]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"{coin} {act} 2026")
    queries = list(set(queries))[:num_queries]

    tasks = []
    seen = set()
    with DDGS() as ddgs:
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=2))   # हर क्वेरी से 2 ही लो
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
    return tasks[:5]   # सिर्फ 5

# ========== AI FUNCTIONS (GitHub Models → Groq) ==========
def ask_github_ai(prompt):
    if not GITHUB_TOKEN: return None
    try:
        resp = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "gpt-4o", "max_tokens": 200, "temperature": 0.1
            }, timeout=10
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def ask_groq_ai(prompt):
    if not GROQ_API_KEY: return None
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "llama-3.3-70b-versatile", "max_tokens": 200, "temperature": 0.1
            }, timeout=5
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return None

def ai_analyze_page(page_text, url):
    prompt = f"""You are a crypto faucet bot. Analyze this webpage and determine if you can claim free crypto by ONLY entering a wallet address (NO login, NO KYC, NO signup).
Page URL: {url}
Page text (first 1500 chars): {page_text[:1500]}

Reply with JSON only:
{{"can_claim": true/false, "reason": "short", "crypto": "BTC/ETH/USDT/SOL/DOGE/BNB/other",
  "wallet_field_selector": "CSS selector", "button_selector": "CSS selector", "button_text": "exact button text"}}
If login/signup/KYC/captcha required, set can_claim=false."""

    answer = ask_github_ai(prompt)   # पहले GitHub
    if answer:
        try: return json.loads(answer)
        except: pass
    answer = ask_groq_ai(prompt)      # फिर Groq
    if answer:
        try: return json.loads(answer)
        except: pass
    return None

# ========== HELPERS ==========
def detect_crypto_type(text):
    text = text.lower()
    if "solana" in text or "sol" in text.split(): return "SOL"
    if "usdt" in text or "tether" in text: return "USDT"
    if "bnb" in text or "binance coin" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "ethereum" in text or "eth" in text.split(): return "ETH"
    return "BTC"

def handle_cookie_banner(page):
    for word in ["accept", "ok", "agree", "close", "consent", "allow", "got it"]:
        try:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}')")
            if btn:
                btn.click(); page.wait_for_timeout(500)
                return True
        except: pass
    return False

def handle_dropdown(page, crypto):
    selects = page.query_selector_all("select")
    for sel in selects:
        options = sel.query_selector_all("option")
        for opt in options:
            if crypto.lower() in (opt.get_attribute("value") or "").lower() or \
               crypto.lower() in (opt.inner_text() or "").lower():
                opt.select_option(); return True
        if options:
            options[0].select_option(); return True
    return False

# ========== SITE VISITOR (Fully AI) ==========
def try_claim(page, url, success_list, ai_call_counter):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        body_text = page.locator("body").inner_text(timeout=5000).lower()

        # 1. तेज़ कीवर्ड फ़िल्टर
        login_kw = ["login", "sign in", "register", "create account", "kyc", "verify identity"]
        if any(k in body_text for k in login_kw):
            print(f"    🚫 लॉगिन/KYC कीवर्ड → छोड़ा")
            return

        # 2. AI प्री-चेक (30% साइटों पर, लेकिन कोटा के अंदर)
        ai_used = False
        if AI_ENABLED and (GITHUB_TOKEN or GROQ_API_KEY) and ai_call_counter[0] < MAX_AI_CALLS_PER_RUN:
            if random.random() < 0.3:   # 30% चांस
                ai = ai_analyze_page(body_text, url)
                ai_call_counter[0] += 1; ai_used = True
                if ai and ai.get("can_claim"):
                    print(f"    🧠 AI → YES ({ai.get('reason','')[:40]})")
                    crypto = ai.get("crypto", "BTC")
                    wallet = wallets.get(crypto, wallets.get("BTC", ""))
                    # AI के बताए फील्ड में एड्रेस भरो
                    sel = ai.get("wallet_field_selector", "input[type='text']")
                    inp = page.query_selector(sel)
                    if inp:
                        inp.fill(wallet)
                        print(f"    📝 {crypto} एड्रेस भरा"); page.wait_for_timeout(500)
                    # AI का बटन दबाओ
                    btext = ai.get("button_text", "")
                    if btext:
                        btn = page.query_selector(f"button:has-text('{btext}'), a:has-text('{btext}')")
                    else:
                        btn = page.query_selector(ai.get("button_selector", "button, input[type='submit']"))
                    if btn:
                        btn.click()
                        print(f"    🖱️ AI बटन दबाया: '{btext}'"); page.wait_for_timeout(random.randint(800,1500))
                        if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                            success_list.append((url, crypto))
                            print(f"    💰 सफलता! ({crypto})")
                        return
                elif ai and not ai.get("can_claim"):
                    print(f"    ❌ AI → NO ({ai.get('reason','')[:40]})")
                    return

        # 3. फॉलबैक (बिना AI)
        if not ai_used or not AI_ENABLED:
            crypto = detect_crypto_type(body_text)
            wallet = wallets.get(crypto, wallets.get("BTC", ""))
            handle_dropdown(page, crypto)
            inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']")
            filled = False
            for inp in inputs[:2]:
                try:
                    if inp.get_attribute("type")=="number" or "amount" in (inp.get_attribute("name") or "").lower():
                        inp.fill("1")
                    else:
                        inp.fill(wallet); filled = True
                    page.wait_for_timeout(random.randint(300,600))
                    break
                except: pass
            for word in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
                btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
                if btn:
                    try:
                        btn.click(); page.wait_for_timeout(random.randint(800,1500))
                        if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                            success_list.append((url, crypto))
                        return
                    except: pass
            if filled:
                submit = page.query_selector("button[type='submit'], input[type='submit']")
                if submit:
                    try:
                        submit.click(); page.wait_for_timeout(random.randint(600,1200))
                        if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                            success_list.append((url, crypto))
                    except: pass
    except: pass

# ========== MAIN ==========
def fly():
    print("🌍 Fully AI Bot – 🧪 TEST MODE (10 sites) 🚀")
    print(f"🧠 AI कॉल सीमा: {MAX_AI_CALLS_PER_RUN}")

    all_urls = list(FIXED_SITES)
    new = ddg_search_new_sites()
    all_urls.extend(new)
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"📋 Fixed: {len(FIXED_SITES)} | 🆕 DDG: {len(new)} | 🎯 Total: {total}\n")

    success_list = []
    ai_counter = [0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(all_urls, 1):
            print(f"[{i}/{total}] {url[:70]}...")
            try_claim(page, url, success_list, ai_counter)
            time.sleep(random.uniform(0.5, 1.2))
        browser.close()

    print(f"\n🏁 मिशन खत्म: {total} साइटें")
    print(f"✅ सफल दावे: {len(success_list)}")
    for u, c in success_list:
        print(f"   + {u[:60]}... ({c})")
    print(f"🧠 AI कॉल: {ai_counter[0]} बार")
    print("💰 Trust Wallet खोलो – कमाई शुरू!")

if __name__ == "__main__":
    fly()
