import os, json, time, random, requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
WALLETS_JSON  = os.environ["WALLETS_JSON"]
wallets       = json.loads(WALLETS_JSON)

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

TEST_MODE     = True
AI_ENABLED    = True
MAX_AI_CALLS  = 15

# ========== 100% NO‑LOGIN FAUCETS (टेस्ट के लिए छोटी लिस्ट) ==========
FIXED_SITES = [
    # ── Sepolia ETH ──
    "https://sepolia-faucet.pk910.de",        # PoW माइनिंग, बस एड्रेस डालो
    "https://www.alchemy.com/faucets/ethereum-sepolia",
    # ── Solana ──
    "https://solfaucet.com",                  # SOL डेवनेट
    "https://faucet.solana.com",              # Solana डेवनेट
    # ── Polygon ──
    "https://faucet.polygon.technology",      # MATIC टेस्टनेट
    # ── QuickNode Multi-chain ──
    "https://faucet.quicknode.com",           # बस एड्रेस डालो
    # ── अन्य टेस्टनेट ──
    "https://faucet.avax.network",            # AVAX टेस्टनेट
    "https://sui.io/faucet",                 # SUI टेस्टनेट
    "https://faucet.arbitrum.io",            # ARB टेस्टनेट
]

# ========== DDG SEARCH (सख्त No‑Login कीवर्ड) ==========
def ddg_search_new_sites(num_queries=3):
    coins = list(wallets.keys())[:3]
    # कीवर्ड में "no login", "no signup", "no captcha" ज़रूर रखो
    actions = [
        "faucet no login no signup no captcha wallet address",
        "free claim without account instant",
        "no registration no kyc faucet 2026",
    ]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"{coin} {act}")
    queries = list(set(queries))[:num_queries]
    tasks = []; seen = set()
    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=3):
                    href = r.get("href")
                    if not href: continue
                    # फ़ालतू साइटों को सख्ती से हटाओ
                    skip = ["academy","support","blog","faq","youtube","reddit","medium",
                            "twitter","facebook","news","telegram","t.me"]
                    if any(w in href for w in skip): continue
                    if href not in seen:
                        seen.add(href); tasks.append(href)
                time.sleep(random.randint(2,3))
            except: pass
    return tasks[:5]

# ========== AI CALL ==========
def call_ai(prompt, max_tokens=200):
    if GITHUB_TOKEN:
        try:
            resp = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization":f"Bearer {GITHUB_TOKEN}","Content-Type":"application/json"},
                json={"messages":[{"role":"user","content":prompt}],"model":"gpt-4o",
                      "max_tokens":max_tokens,"temperature":0.1}, timeout=10
            )
            if resp.status_code==200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"},
                json={"messages":[{"role":"user","content":prompt}],"model":"llama-3.3-70b-versatile",
                      "max_tokens":max_tokens,"temperature":0.1}, timeout=5
            )
            if resp.status_code==200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass
    return None

def ai_pre_check(text, url):
    prompt = f"""Analyze this webpage. Can a bot claim free crypto by ONLY entering a wallet address (NO login/signup/KYC/captcha)?
URL: {url}
Text (first 1200 chars): {text[:1200]}
Reply ONLY with valid JSON:
{{"can_claim":true/false,"crypto":"BTC/ETH/USDT/SOL/DOGE/BNB/other",
  "wallet_selector":"CSS selector","button_text":"exact button text"}}
If login/KYC/captcha or blog, set can_claim=false."""
    resp = call_ai(prompt, 150)
    if resp:
        try: return json.loads(resp)
        except: pass
    return None

def ai_post_check(text, url):
    prompt = f"""Was the claim successful? URL: {url}
Text (first 1200 chars): {text[:1200]}
Look for: transaction hash, "reward sent", "coins added", "claim successful", balance updated.
Reply ONLY with "true" or "false"."""
    resp = call_ai(prompt, 10)
    if resp: return resp.strip().lower()=="true"
    return None

# ========== HELPERS ==========
def handle_cookie(page):
    for w in ["accept","ok","agree","close","consent","allow","got it"]:
        try:
            btn=page.query_selector(f"button:has-text('{w}'),a:has-text('{w}')")
            if btn: btn.click(); page.wait_for_timeout(500); return
        except: pass

def handle_dropdown(page, crypto):
    for sel in page.query_selector_all("select"):
        opts=sel.query_selector_all("option")
        for o in opts:
            if crypto.lower() in (o.get_attribute("value") or "").lower() or \
               crypto.lower() in (o.inner_text() or "").lower():
                o.select_option(); return
        if opts: opts[0].select_option()

def strict_success_check(content, url):
    c=content.lower()
    if any(k in c for k in ["login","sign in","register","kyc"]): return False
    strong=["transaction hash","tx id","reward sent","payment successful",
            "coins added","credited to your wallet","claim successful"]
    return any(s in c for s in strong) or any(p in url.lower() for p in ["/success","/thank","/dashboard"])

# ========== SITE VISITOR ==========
def try_claim(page, url, success_list, ai_counter):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800,1500))
        handle_cookie(page); page.wait_for_timeout(300)
        body=page.locator("body").inner_text(timeout=5000).lower()

        # 1. कीवर्ड फ़िल्टर
        if any(k in body for k in ["login","sign in","register","create account","kyc","verify identity"]):
            print(f"    🚫 लॉगिन/KYC → छोड़ा"); return

        # 2. AI प्री-चेक
        ai_decision=None; crypto_used=None
        if AI_ENABLED and ai_counter[0]<MAX_AI_CALLS:
            ai_decision=ai_pre_check(body,url); ai_counter[0]+=1
            if ai_decision and not ai_decision.get("can_claim"):
                print(f"    ❌ AI → नहीं ({ai_decision.get('reason','')[:40]})"); return
            elif ai_decision and ai_decision.get("can_claim"):
                print(f"    🧠 AI → कर सकते हैं")

        # 3. क्लेम एक्शन
        wallet=None; claimed=False
        if ai_decision and ai_decision.get("can_claim"):
            crypto=ai_decision.get("crypto","BTC")
            wallet=wallets.get(crypto, wallets.get("BTC",""))
            crypto_used=crypto
            sel=ai_decision.get("wallet_selector","input[type='text']")
            inp=page.query_selector(sel)
            if inp:
                inp.fill(wallet); print(f"    📝 {crypto} एड्रेस भरा"); page.wait_for_timeout(random.randint(400,800))
            btext=ai_decision.get("button_text","")
            if btext:
                btn=page.query_selector(f"button:has-text('{btext}'),a:has-text('{btext}')")
            else:
                btn=page.query_selector("button, input[type='submit']")
            if btn:
                btn.click(); print(f"    🖱️ AI बटन दबाया: '{btext}'")
                page.wait_for_timeout(random.randint(1500,2500))
                claimed=True
        else:
            # फ़ॉलबैक
            crypto="BTC"
            for c in ["SOL","USDT","BNB","DOGE","ETH","BTC"]:
                if c.lower() in body: crypto=c; break
            wallet=wallets.get(crypto, wallets.get("BTC",""))
            crypto_used=crypto
            handle_dropdown(page,crypto)
            inputs=page.query_selector_all("input[type='text'],input[type='email'],input[name*='address'],input[name*='wallet']")
            for inp in inputs[:2]:
                try:
                    if inp.get_attribute("type")=="number" or "amount" in (inp.get_attribute("name") or "").lower():
                        inp.fill("1")
                    else:
                        inp.fill(wallet)
                    page.wait_for_timeout(random.randint(300,600))
                    break
                except: pass
            for w in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
                btn=page.query_selector(f"button:has-text('{w}'),a:has-text('{w}'),input[value*='{w}' i]")
                if btn:
                    try:
                        btn.click(); print(f"    🖱️ '{w}' बटन दबाया (फ़ॉलबैक)")
                        page.wait_for_timeout(random.randint(800,1500))
                        claimed=True; break
                    except: pass
            if not claimed:
                submit=page.query_selector("button[type='submit'],input[type='submit']")
                if submit:
                    submit.click(); print("    ✅ सबमिट किया (फ़ॉलबैक)")
                    page.wait_for_timeout(random.randint(600,1200))
                    claimed=True

        # 4. सफलता जाँच
        if claimed and wallet:
            post_text=page.locator("body").inner_text(timeout=5000)
            if AI_ENABLED and ai_counter[0]<MAX_AI_CALLS:
                if ai_post_check(post_text, url):
                    success_list.append((url, crypto_used))
                    print(f"    💰 AI पुष्टि: कमाई हुई! ({crypto_used})")
                    ai_counter[0]+=1
                else:
                    print(f"    ❌ AI पुष्टि: कोई कमाई नहीं")
            else:
                if strict_success_check(post_text, url):
                    success_list.append((url, crypto_used))
                    print(f"    💰 बैकअप पुष्टि: कमाई हुई ({crypto_used})")
    except Exception as e:
        print(f"    ❌ एरर: {str(e)[:50]}")

# ========== MAIN ==========
def fly():
    print("🌍 No‑Login Faucet Hunter 🚀")
    all_urls=list(FIXED_SITES)
    new=ddg_search_new_sites(); all_urls.extend(new)
    all_urls=list(dict.fromkeys(all_urls))
    print(f"📋 Fixed:{len(FIXED_SITES)} 🆕 DDG:{len(new)} 🎯 Total:{len(all_urls)}\n")

    success=[]; ai_cnt=[0]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        page=browser.new_page()
        for i,url in enumerate(all_urls,1):
            print(f"[{i}/{len(all_urls)}] {url[:70]}...")
            try_claim(page,url,success,ai_cnt)
            time.sleep(random.uniform(0.5,1.2))
        browser.close()

    print(f"\n🏁 मिशन खत्म: {len(all_urls)} साइटें")
    print(f"✅ पुष्ट सफलता: {len(success)}")
    for u,c in success: print(f"   + {u[:60]}... ({c})")
    print(f"🧠 AI कॉल: {ai_cnt[0]} बार")

if __name__=="__main__":
    fly()
