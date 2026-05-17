import os, json, time, random, requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
WALLETS_JSON  = os.environ["WALLETS_JSON"]
wallets       = json.loads(WALLETS_JSON)

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

TEST_MODE     = True               # ✅ टेस्ट (10 साइटें)
AI_ENABLED    = True               # AI पूरी तरह चालू
MAX_AI_CALLS_PER_RUN = 15          # टेस्ट/रन में 15 AI कॉल

# ========== NO‑LOGIN FAUCETS (टेस्ट) ==========
FIXED_SITES = [
    "https://sepolia-faucet.pk910.de",
    "https://solfaucet.com",
    "https://faucet.solana.com",
    "https://faucet.polygon.technology",
    "https://faucet.quicknode.com",
]

# ========== DDG SEARCH (टेस्ट) ==========
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
    return tasks[:5]

# ========== AI CALL FUNCTIONS ==========
def call_ai(prompt, max_tokens=200):
    """पहले GitHub Models, फिर Groq"""
    # GitHub Models
    if GITHUB_TOKEN:
        try:
            resp = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "gpt-4o", "max_tokens": max_tokens, "temperature": 0.1
                }, timeout=10
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass

    # Groq
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "llama-3.3-70b-versatile", "max_tokens": max_tokens, "temperature": 0.1
                }, timeout=5
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass
    return None

def ai_analyze_page(page_text, url):
    """AI प्री-चेक: क्या और कैसे क्लेम करें"""
    prompt = f"""You are a crypto faucet bot. Analyze this webpage and determine if you can claim free crypto by ONLY entering a wallet address (NO login, NO KYC, NO signup, NO captcha).
Page URL: {url}
Page text (first 1500 chars): {page_text[:1500]}

Reply with JSON only (no extra text):
{{"can_claim": true/false, "reason": "short", "crypto": "BTC/ETH/USDT/SOL/DOGE/BNB/other",
  "wallet_field_selector": "CSS selector for the wallet address input field (e.g., 'input[name=address]')",
  "button_selector": "CSS selector for the claim/earn/submit button",
  "button_text": "exact visible text of that button"}}

If login/signup/KYC/captcha required, or the page is just a blog/news, set can_claim=false."""
    resp = call_ai(prompt, 200)
    if resp:
        try: return json.loads(resp)
        except: pass
    return None

def ai_verify_success(page_text_after_action, url):
    """AI पोस्ट-चेक: क्या सच में कमाई हुई?"""
    prompt = f"""You are a crypto faucet bot. You have just attempted to claim free crypto on the following page. Analyze the page text and decide if the claim was SUCCESSFUL (reward was actually sent/credited).

Page URL: {url}
Page text (first 1500 chars): {page_text_after_action[:1500]}

Indicators of a SUCCESSFUL claim (choose true only if at least one strong indicator is present):
- Transaction hash / TX ID / confirmation code is shown
- Message like "Reward sent", "Payment successful", "Coins added", "Claim successful", "Successfully sent"
- Balance updated on screen
- Explicit confirmation that the reward was credited to the provided wallet address

Indicators of FAILURE (choose false):
- The page is a blog, news article, or general info site with no claim form
- Login / sign up / KYC / captcha is required
- Error messages like "403 Forbidden", "Blocked", "Something went wrong"
- The page just shows generic info without any personal claim confirmation

Reply with ONLY one word: "true" or "false"."""
    resp = call_ai(prompt, 10)  # छोटा जवाब
    if resp:
        return resp.strip().lower() == "true"
    return False

# ========== HELPERS ==========
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

# ========== SITE VISITOR (FULLY AI) ==========
def try_claim(page, url, success_list, ai_call_counter):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        body_text = page.locator("body").inner_text(timeout=5000).lower()

        # 1. Quick keyword filter (no AI call needed)
        login_kw = ["login", "sign in", "register", "create account", "kyc", "verify identity"]
        if any(k in body_text for k in login_kw):
            print(f"    🚫 लॉगिन/KYC कीवर्ड → छोड़ा")
            return

        # 2. AI Pre‑check (if quota available)
        ai_decision = None
        if AI_ENABLED and ai_call_counter[0] < MAX_AI_CALLS_PER_RUN:
            ai_decision = ai_analyze_page(body_text, url)
            ai_call_counter[0] += 1

            if ai_decision and not ai_decision.get("can_claim"):
                print(f"    ❌ AI → नहीं कर सकते ({ai_decision.get('reason','')[:40]})")
                return
            elif ai_decision and ai_decision.get("can_claim"):
                print(f"    🧠 AI बोला: कर सकते हैं → {ai_decision.get('reason','')[:40]}")

        # 3. Execute claim (either AI-guided or fallback)
        crypto_used = None
        if ai_decision and ai_decision.get("can_claim"):
            crypto = ai_decision.get("crypto", "BTC")
            wallet = wallets.get(crypto, wallets.get("BTC", ""))
            crypto_used = crypto

            # Fill wallet
            sel = ai_decision.get("wallet_field_selector", "input[type='text']")
            inp = page.query_selector(sel)
            if inp:
                inp.fill(wallet)
                print(f"    📝 {crypto} एड्रेस भरा")
                page.wait_for_timeout(random.randint(400, 800))

            # Click button
            btext = ai_decision.get("button_text", "")
            if btext:
                btn = page.query_selector(f"button:has-text('{btext}'), a:has-text('{btext}')")
            else:
                btn = page.query_selector(ai_decision.get("button_selector", "button, input[type='submit']"))
            if btn:
                btn.click()
                print(f"    🖱️ AI बटन दबाया: '{btext}'")
                page.wait_for_timeout(random.randint(1500, 2500))

                # 4. AI POST-CHECK – सबसे अहम बदलाव
                if AI_ENABLED and ai_call_counter[0] < MAX_AI_CALLS_PER_RUN:
                    post_text = page.locator("body").inner_text(timeout=5000)
                    if ai_verify_success(post_text, url):
                        success_list.append((url, crypto_used))
                        print(f"    💰 AI पुष्टि: असली कमाई हुई! ({crypto_used})")
                        ai_call_counter[0] += 1
                    else:
                        print(f"    ❌ AI पुष्टि: कोई कमाई नहीं हुई")
                else:
                    # AI quota ख़त्म, तो डिफ़ॉल्ट कोई सफ़लता नहीं
                    pass
                return
            else:
                # बटन नहीं मिला
                pass

        # 5. Fallback (बिना AI या AI फेल)
        # (पुराना कीवर्ड‑बटन लॉजिक, लेकिन अब सफ़लता सिर्फ़ AI से पुष्टि करेंगे)
        # हम फ़ॉलबैक में भी AI वेरिफिकेशन करेंगे, लेकिन संक्षिप्त रखेंगे।
        # अगर कोई बटन अपने आप दब गया और AI उपलब्ध नहीं, तो सुरक्षित रहें।
        # यहाँ हम फ़ॉलबैक का पूरा कोड नहीं लिख रहे, क्योंकि अब AI मुख्य है।
        # अगर AI ने काम नहीं किया, तो हम कुछ नहीं मानते।
    except: pass

# ========== MAIN ==========
def fly():
    mode = "🧪 TEST" if TEST_MODE else "🌍 FULL"
    print(f"🌍 Fully AI Bot – {mode} 🚀")
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
    print(f"✅ AI-पुष्टि सफलता: {len(success_list)}")
    for u, c in success_list:
        print(f"   + {u[:60]}... ({c})")
    print(f"🧠 AI कॉल: {ai_counter[0]} बार")
    print("💰 Trust Wallet खोलो – असली कमाई देखो!")

if __name__ == "__main__":
    fly()
