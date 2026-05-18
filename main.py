import os, json, time, random, requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
WALLETS_JSON  = os.environ["WALLETS_JSON"]
wallets       = json.loads(WALLETS_JSON)

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

TEST_MODE     = False                # FULL MODE (10,000+ साइट/दिन)
AI_ENABLED    = True
MAX_AI_CALLS_PER_RUN = 30           # हर रन में 30 AI कॉल

# ========== 300+ NO‑LOGIN / TASK / TESTNET SITES ==========
FIXED_SITES = [
    # ... (तेरी पूरी लिस्ट पहले जैसी ही रखो, मैं यहाँ छोटा कर रहा हूँ)
    "https://firefaucet.win", "https://faucetcrypto.com", "https://allcoins.pw",
    "https://cointiply.com/ptc-ads", "https://rollercoin.com", "https://dutchycorp.space",
    "https://freefaucet.io", "https://claimfreecoins.io", "https://coindiversity.io",
    "https://fastcoin.ga", "https://autofaucet.org", "https://viperfaucet.com",
    "https://faucetpay.io", "https://faucethub.io",
    "https://freebitco.in", "https://satoshihero.com", "https://btcclicks.com",
    "https://coinpayu.com", "https://adbtc.top", "https://bitcoinker.com",
    "https://moonbit.co.in", "https://moonbitcoin.xyz", "https://bitfun.co",
    "https://cryptowin.io", "https://earncrypto.com/faucet", "https://freebitcoin.io",
    "https://free-usdt.com", "https://free-tether.com", "https://freeeth.io",
    "https://ethereum-faucet.org", "https://fauceth.io",
    "https://sepolia-faucet.pk910.de", "https://www.alchemy.com/faucets/ethereum-sepolia",
    "https://free-bnb.com", "https://freebnbco.in", "https://stakely.io/en/faucet/binance-bnb",
    "https://testnet.bnbchain.org/faucet-smart",
    "https://free-solana.com", "https://faucet.solana.com", "https://solfaucet.com",
    "https://freedogecoin.net", "https://dogefaucet.com", "https://free-doge.com",
    "https://moondogecoin.com", "https://freedoge.co.in",
    "https://freecardano.com", "https://free-litecoin.com", "https://free-tron.com",
    "https://free-zcash.com", "https://free-dash.com", "https://moonliteco.in",
    "https://moondash.co.in", "https://free-ripple.com", "https://free-chainlink.com",
    "https://free-matic.com", "https://free-polkadot.com", "https://free-avalanche.com",
    "https://free-near.com", "https://free-aptos.com", "https://free-sui.com",
    "https://free-arbitrum.com", "https://free-optimism.com", "https://free-base.com",
    "https://app.layer3.xyz/quests", "https://zealy.io/c/explore",
    "https://galxe.com/explore", "https://app.dework.xyz/explore",
    "https://questn.com/explore", "https://taskon.xyz/quests",
    "https://superteam.fun/earn", "https://www.rabbithole.gg/quests",
    "https://kleoverse.com/explore", "https://earn.superteam.fun",
    "https://crew3.xyz", "https://intract.io",
    "https://onepapel.com", "https://warsonsol.com", "https://www.binance.com/en/activity",
    "https://coinmarketcap.com/airdrop/", "https://airdropalert.com",
    "https://airdrops.io", "https://www.airdropking.io",
    "https://jumptask.io", "https://earncrypto.com", "https://freecash.com/earn",
    "https://getpaidto.click", "https://timebucks.com", "https://picoworkers.com",
    "https://microworkers.com", "https://rapidworkers.com",
    "https://docs.wormhole.com/wormhole/quick-start/testnet-faucets",
    "https://chainstack.com/faucets", "https://www.alchemy.com/faucets",
    "https://infura.io/faucet", "https://quicknode.com/faucet",
    "https://faucet.quicknode.com", "https://faucet.metamask.io",
    "https://faucet.polygon.technology", "https://faucets.chain.link",
    "https://faucet.avax.network", "https://faucet.aptoslabs.com",
    "https://sui.io/faucet", "https://faucet.near.org",
    "https://faucet.arbitrum.io", "https://app.optimism.io/faucet",
    "https://bridge.base.org/faucet", "https://faucet.roninchain.com",
    "https://faucet.immutable.com", "https://faucet.zksync.io",
    "https://faucet.linea.build", "https://faucet.scroll.io",
    "https://faucet.mantle.xyz", "https://faucet.celo.org",
]

# ========== DuckDuckGo SEARCH ==========
def ddg_search_new_sites(num_queries=500):
    if TEST_MODE: num_queries = 10
    coins = list(wallets.keys())[:10] if TEST_MODE else list(wallets.keys())
    actions = [
        "faucet no login no registration",
        "claim free without account",
        "earn instantly wallet address only",
        "no sign up no kyc instant payout",
        "free crypto just enter address",
        "crypto task wallet address 2026",
        "crypto airdrop instant claim wallet",
        "microtask earn crypto wallet address",
        "ptc earn bitcoin wallet address",
        "web3 quest wallet address reward"
    ]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"{coin} {act} 2026")
    queries = list(set(queries))[:num_queries]
    tasks = []; seen = set()
    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=5):
                    href = r.get("href")
                    if not href: continue
                    skip = ["academy","support","blog","faq","youtube","reddit","medium",
                            "twitter","facebook","news","telegram","t.me"]
                    if any(w in href for w in skip): continue
                    if href not in seen:
                        seen.add(href); tasks.append(href)
                time.sleep(random.randint(2, 4))
            except: continue
    return tasks

# ========== AI CALL (Three‑tier) ==========
def call_ai(prompt, max_tokens=200):
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"messages":[{"role":"user","content":prompt}],"model":"llama-3.3-70b-versatile","max_tokens":max_tokens,"temperature":0.1},
                timeout=5
            )
            if resp.status_code==200: return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass
    if GITHUB_TOKEN:
        try:
            resp = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
                json={"messages":[{"role":"user","content":prompt}],"model":"gpt-4o","max_tokens":max_tokens,"temperature":0.1},
                timeout=10
            )
            if resp.status_code==200: return resp.json()["choices"][0]["message"]["content"].strip()
        except: pass
    try:
        resp = requests.get("https://text.pollinations.ai/openai", params={"prompt":prompt,"model":"gpt-4o-mini"}, timeout=15)
        if resp.status_code==200: return resp.text.strip()
    except: pass
    return None

def ai_pre_check(text, url):
    prompt = f"""You are a crypto faucet bot. Analyze this webpage and decide if you can claim free crypto by ONLY entering a wallet address (NO login/signup/KYC/captcha).
Page URL: {url}
Page text (first 1200 chars): {text[:1200]}
Reply with JSON only:
{{"can_claim":true/false,"crypto":"BTC/ETH/USDT/SOL/DOGE/BNB/other",
  "wallet_selector":"CSS selector","button_text":"exact button text"}}
If login/KYC/captcha required, or page is just a blog/news, set can_claim=false."""
    resp = call_ai(prompt, 150)
    if resp:
        try: return json.loads(resp)
        except: pass
    return None

def ai_verify_success(text_after, url):
    prompt = f"""You are a crypto faucet bot. You have just attempted to claim free crypto. Analyze the page text and decide if the claim was SUCCESSFUL (reward actually sent).
Page URL: {url}
Page text (first 1500 chars): {text_after[:1500]}
NOT successful if: blog/news, login/signup/KYC/captcha, error messages (404, forbidden, etc.), connect wallet, generic success mention.
ONLY successful if: transaction hash, TX ID, "reward sent", "payment successful", "coins added", "claim successful", balance updated, credited to wallet.
Reply with ONLY one word: "true" or "false"."""
    resp = call_ai(prompt, 10)
    if resp: return resp.strip().lower()=="true"
    return False

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

def detect_crypto_type(text):
    t = text.lower()
    if "solana" in t or "sol" in t.split(): return "SOL"
    if "usdt" in t or "tether" in t: return "USDT"
    if "bnb" in t or "binance coin" in t: return "BNB"
    if "btc" in t or "bitcoin" in t: return "BTC"
    if "doge" in t or "dogecoin" in t: return "DOGE"
    if "ethereum" in t or "eth" in t.split(): return "ETH"
    return "BTC"

def strict_success_check(content, url):
    c = content.lower()
    negative = ["404","not found","error","blocked","forbidden","something went wrong",
                "login","sign in","register","kyc","connect wallet"]
    if any(k in c for k in negative): return False
    strong = ["transaction hash","tx id","reward sent","payment successful",
              "coins added","credited to your wallet","claim successful","faucet pay"]
    return any(s in c for s in strong) or any(p in url.lower() for p in ["/success","/thank","/dashboard"])

# ========== SITE VISITOR (MULTI‑PAGE NAVIGATION) ==========
def try_claim(page, url, success_list, ai_counter):
    try:
        page.goto(url, timeout=8000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie(page)
        page.wait_for_timeout(300)

        visited_urls = {url}          # पहले से विज़िट किए हुए URL
        max_pages = 5                 # अधिकतम 5 पेजों तक फ़ॉलो करें
        pages_visited = 0
        claimed = False
        crypto_used = None
        wallet = None

        # AI प्री-चेक सिर्फ पहले पेज पर
        ai_decision = None
        body = page.locator("body").inner_text(timeout=5000).lower()
        if any(k in body for k in ["login","sign in","register","create account","kyc","verify identity"]):
            return

        if AI_ENABLED and ai_counter[0] < MAX_AI_CALLS_PER_RUN and random.random() < 0.05:
            ai_decision = ai_pre_check(body, url)
            ai_counter[0] += 1
            if ai_decision and not ai_decision.get("can_claim"):
                return
            # अगर AI ने हाँ कही तो उसके बताए अनुसार क्लेम करो
            if ai_decision and ai_decision.get("can_claim"):
                crypto = ai_decision.get("crypto", "BTC")
                wallet = wallets.get(crypto, wallets.get("BTC", ""))
                crypto_used = crypto
                sel = ai_decision.get("wallet_selector", "input[type='text']")
                inp = page.query_selector(sel)
                if inp:
                    inp.fill(wallet)
                    page.wait_for_timeout(random.randint(400, 800))
                btext = ai_decision.get("button_text", "")
                if btext:
                    btn = page.query_selector(f"button:has-text('{btext}'),a:has-text('{btext}')")
                else:
                    btn = page.query_selector("button, input[type='submit']")
                if btn:
                    btn.click()
                    page.wait_for_timeout(random.randint(1500, 2500))
                    claimed = True

        # अगर AI ने क्लेम नहीं किया (या फ़ॉलबैक की ज़रूरत है) तो फ़ॉलबैक लूप
        if not claimed:
            # फ़ॉलबैक पहले पेज पर ही शुरू करो
            current_url = url
            while pages_visited < max_pages and current_url in visited_urls and not claimed:
                # हर नए पेज पर बिना AI के कोशिश करो
                body = page.locator("body").inner_text(timeout=5000).lower()
                if any(k in body for k in ["login","sign in","register","kyc"]):
                    return  # लॉगिन आ गया तो छोड़ो

                crypto = detect_crypto_type(body)
                wallet = wallets.get(crypto, wallets.get("BTC", ""))
                if not crypto_used:
                    crypto_used = crypto
                handle_dropdown(page, crypto)

                # एड्रेस भरो
                inputs = page.query_selector_all(
                    "input[type='text'],input[type='email'],input[name*='address'],input[name*='wallet']")
                filled = False
                for inp in inputs[:2]:
                    try:
                        if inp.get_attribute("type") == "number" or "amount" in (inp.get_attribute("name") or "").lower():
                            inp.fill("1")
                        else:
                            inp.fill(wallet)
                            filled = True
                        page.wait_for_timeout(random.randint(300, 600))
                        break
                    except: pass

                # बटन दबाओ
                btn_clicked = False
                for w in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
                    btn = page.query_selector(f"button:has-text('{w}'),a:has-text('{w}'),input[value*='{w}' i]")
                    if btn:
                        try:
                            before_url = page.url
                            btn.click()
                            page.wait_for_timeout(random.randint(800, 1500))
                            btn_clicked = True
                            # अगर URL बदल गया तो नए पेज पर चले जाओ, नहीं तो यहीं रुक जाओ
                            after_url = page.url
                            if after_url != before_url and after_url not in visited_urls:
                                visited_urls.add(after_url)
                                current_url = after_url
                                pages_visited += 1
                                claimed = False  # नए पेज पर फिर से कोशिश होगी
                                break
                            else:
                                # URL नहीं बदला या पहले से देखा → यहीं रुक जाओ
                                claimed = True
                                break
                        except: pass
                if not btn_clicked:
                    # कोई बटन नहीं दबा, सबमिट करके देखो
                    submit = page.query_selector("button[type='submit'],input[type='submit']")
                    if submit:
                        try:
                            before_url = page.url
                            submit.click()
                            page.wait_for_timeout(random.randint(600, 1200))
                            after_url = page.url
                            if after_url != before_url and after_url not in visited_urls:
                                visited_urls.add(after_url)
                                current_url = after_url
                                pages_visited += 1
                                continue
                            else:
                                claimed = True
                        except: pass
                    else:
                        # कुछ भी नहीं कर पाए → अगला पेज नहीं है, रुक जाओ
                        claimed = filled  # अगर एड्रेस भरा था तो शायद काम हो गया
                        break

                # अगर बटन दबाने से पेज नहीं बदला तो लूप से बाहर निकल जाओ
                if claimed:
                    break
                if pages_visited >= max_pages:
                    break

        # अंतिम सफलता जाँच
        if claimed and wallet:
            post_text = page.locator("body").inner_text(timeout=5000)
            if AI_ENABLED and ai_counter[0] < MAX_AI_CALLS_PER_RUN and ai_decision:
                if ai_verify_success(post_text, page.url):
                    success_list.append((url, crypto_used))
                    ai_counter[0] += 1
            else:
                if strict_success_check(post_text, page.url):
                    success_list.append((url, crypto_used))
    except:
        pass

# ========== MAIN ==========
def fly():
    mode = "🌍 FULL (10,000+ साइट/दिन)" if not TEST_MODE else "🧪 TEST"
    print(f"🔥 EarnAI Eternal Faucet Hunter – {mode} 🚀")
    all_urls = list(FIXED_SITES)
    new = ddg_search_new_sites()
    all_urls.extend(new)
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"📋 Fixed: {len(FIXED_SITES)} | 🆕 DDG: {len(new)} | 🎯 Total: {total}\n")

    success = []; ai_cnt = [0]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(all_urls, 1):
            if i % 100 == 0:
                print(f"📊 Progress: {i}/{total}")
            try_claim(page, url, success, ai_cnt)
            time.sleep(random.uniform(0.3, 0.8))
        browser.close()

    print(f"\n🏁 मिशन खत्म: {total} साइटें देखीं")
    print(f"✅ पुष्ट सफलताएँ: {len(success)}")
    for u, c in success: print(f"   + {u[:60]}... ({c})")
    print(f"🧠 AI कॉल: {ai_cnt[0]} बार")
    print("💰 तेरा Trust Wallet चेक कर – बूँद-बूँद से घड़ा भरेगा!")

if __name__ == "__main__":
    fly()
