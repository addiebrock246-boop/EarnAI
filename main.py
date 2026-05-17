import os, json, time, random, requests
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
WALLETS_JSON  = os.environ["WALLETS_JSON"]
wallets       = json.loads(WALLETS_JSON)

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

TEST_MODE     = False                # ✅ पूरा मोड — 10,000+ साइट/दिन
AI_ENABLED    = True                 # AI का उपयोग करें
MAX_AI_CALLS_PER_RUN = 30           # हर रन में AI कॉल की अधिकतम संख्या

# ========== 300+ NO‑LOGIN / TASK / TESTNET SITES ==========
FIXED_SITES = [
    # ── MULTI‑FAUCET ──
    "https://firefaucet.win", "https://faucetcrypto.com", "https://allcoins.pw",
    "https://cointiply.com/ptc-ads", "https://rollercoin.com", "https://dutchycorp.space",
    "https://freefaucet.io", "https://claimfreecoins.io", "https://coindiversity.io",
    "https://fastcoin.ga", "https://autofaucet.org", "https://viperfaucet.com",
    "https://faucetpay.io", "https://faucethub.io",
    # ── BTC ──
    "https://freebitco.in", "https://satoshihero.com", "https://btcclicks.com",
    "https://coinpayu.com", "https://adbtc.top", "https://bitcoinker.com",
    "https://moonbit.co.in", "https://moonbitcoin.xyz", "https://bitfun.co",
    "https://cryptowin.io", "https://earncrypto.com/faucet", "https://freebitcoin.io",
    # ── ETH & USDT ──
    "https://free-usdt.com", "https://free-tether.com", "https://freeeth.io",
    "https://ethereum-faucet.org", "https://fauceth.io",
    "https://sepolia-faucet.pk910.de", "https://www.alchemy.com/faucets/ethereum-sepolia",
    # ── BNB ──
    "https://free-bnb.com", "https://freebnbco.in", "https://stakely.io/en/faucet/binance-bnb",
    "https://testnet.bnbchain.org/faucet-smart",
    # ── SOL ──
    "https://free-solana.com", "https://faucet.solana.com", "https://solfaucet.com",
    # ── DOGE ──
    "https://freedogecoin.net", "https://dogefaucet.com", "https://free-doge.com",
    "https://moondogecoin.com", "https://freedoge.co.in",
    # ── OTHER COINS ──
    "https://freecardano.com", "https://free-litecoin.com", "https://free-tron.com",
    "https://free-zcash.com", "https://free-dash.com", "https://moonliteco.in",
    "https://moondash.co.in", "https://free-ripple.com", "https://free-chainlink.com",
    "https://free-matic.com", "https://free-polkadot.com", "https://free-avalanche.com",
    "https://free-near.com", "https://free-aptos.com", "https://free-sui.com",
    "https://free-arbitrum.com", "https://free-optimism.com", "https://free-base.com",
    # ── TASK / QUEST PLATFORMS ──
    "https://app.layer3.xyz/quests", "https://zealy.io/c/explore",
    "https://galxe.com/explore", "https://app.dework.xyz/explore",
    "https://questn.com/explore", "https://taskon.xyz/quests",
    "https://superteam.fun/earn", "https://www.rabbithole.gg/quests",
    "https://kleoverse.com/explore", "https://earn.superteam.fun",
    "https://crew3.xyz", "https://intract.io",
    # ── AIRDROP / GIVEAWAY ──
    "https://onepapel.com", "https://warsonsol.com", "https://www.binance.com/en/activity",
    "https://coinmarketcap.com/airdrop/", "https://airdropalert.com",
    "https://airdrops.io", "https://www.airdropking.io",
    # ── MICROTASK ──
    "https://jumptask.io", "https://earncrypto.com", "https://freecash.com/earn",
    "https://getpaidto.click", "https://timebucks.com", "https://picoworkers.com",
    "https://microworkers.com", "https://rapidworkers.com",
    # ── TESTNET FAUCETS ──
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

# ========== DuckDuckGo SEARCH — अनलिमिटेड नई साइटें ==========
def ddg_search_new_sites(num_queries=500):
    if TEST_MODE:
        num_queries = 10
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

    tasks = []
    seen = set()
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
                        seen.add(href)
                        tasks.append(href)
                time.sleep(random.randint(2, 4))
            except:
                continue
    return tasks

# ========== AI CALL — तीन-स्तरीय सुरक्षा कवच ==========
def call_ai(prompt, max_tokens=200):
    """Groq → GitHub Models → Pollinations.AI (कभी बंद नहीं)"""
    # 1. Groq
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "llama-3.3-70b-versatile",
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass

    # 2. GitHub Models
    if GITHUB_TOKEN:
        try:
            resp = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"},
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "gpt-4o",
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                },
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass

    # 3. Pollinations.AI — हमेशा फ्री, बिना API Key
    try:
        resp = requests.get(
            "https://text.pollinations.ai/openai",
            params={"prompt": prompt, "model": "gpt-4o-mini"},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        pass

    return None

# ========== AI PRE-CHECK ==========
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

# ========== AI POST-CHECK ==========
def ai_post_check(text, url):
    prompt = f"""Did the bot successfully claim free crypto on this page? URL: {url}
Page text (first 1200 chars): {text[:1200]}
Strong indicators: transaction hash, "reward sent", "coins added", "claim successful", "credited to your wallet", balance updated.
Reply ONLY with "true" or "false"."""
    resp = call_ai(prompt, 10)
    if resp: return resp.strip().lower() == "true"
    return None

# ========== HELPERS ==========
def handle_cookie(page):
    for w in ["accept", "ok", "agree", "close", "consent", "allow", "got it"]:
        try:
            btn = page.query_selector(f"button:has-text('{w}'),a:has-text('{w}')")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
                return
        except: pass

def handle_dropdown(page, crypto):
    for sel in page.query_selector_all("select"):
        opts = sel.query_selector_all("option")
        for o in opts:
            if crypto.lower() in (o.get_attribute("value") or "").lower() or \
               crypto.lower() in (o.inner_text() or "").lower():
                o.select_option()
                return
        if opts:
            opts[0].select_option()

def strict_success_check(content, url):
    c = content.lower()
    if any(k in c for k in ["login","sign in","register","kyc"]):
        return False
    strong = ["transaction hash","tx id","reward sent","payment successful",
              "coins added","credited to your wallet","claim successful"]
    return any(s in c for s in strong) or any(p in url.lower() for p in ["/success","/thank","/dashboard"])

# ========== SITE VISITOR ==========
def try_claim(page, url, success_list, ai_counter):
    try:
        page.goto(url, timeout=8000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie(page)
        page.wait_for_timeout(300)
        body = page.locator("body").inner_text(timeout=5000).lower()

        # 1. तेज़ कीवर्ड फ़िल्टर
        if any(k in body for k in ["login","sign in","register","create account","kyc","verify identity"]):
            return

        # 2. AI प्री-चेक (5% साइटों पर)
        ai_decision = None
        crypto_used = None
        if AI_ENABLED and ai_counter[0] < MAX_AI_CALLS_PER_RUN and random.random() < 0.05:
            ai_decision = ai_pre_check(body, url)
            ai_counter[0] += 1
            if ai_decision and not ai_decision.get("can_claim"):
                return
            elif ai_decision and ai_decision.get("can_claim"):
                pass  # आगे बढ़ो

        # 3. क्लेम एक्शन
        wallet = None
        claimed = False
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
        else:
            # फ़ॉलबैक
            crypto = "BTC"
            for c in ["SOL","USDT","BNB","DOGE","ETH","BTC"]:
                if c.lower() in body: crypto = c; break
            wallet = wallets.get(crypto, wallets.get("BTC", ""))
            crypto_used = crypto
            handle_dropdown(page, crypto)
            inputs = page.query_selector_all("input[type='text'],input[type='email'],input[name*='address'],input[name*='wallet']")
            for inp in inputs[:2]:
                try:
                    if inp.get_attribute("type") == "number" or "amount" in (inp.get_attribute("name") or "").lower():
                        inp.fill("1")
                    else:
                        inp.fill(wallet)
                    page.wait_for_timeout(random.randint(300, 600))
                    break
                except: pass
            for w in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
                btn = page.query_selector(f"button:has-text('{w}'),a:has-text('{w}'),input[value*='{w}' i]")
                if btn:
                    try:
                        btn.click()
                        page.wait_for_timeout(random.randint(800, 1500))
                        claimed = True
                        break
                    except: pass
            if not claimed:
                submit = page.query_selector("button[type='submit'],input[type='submit']")
                if submit:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                    claimed = True

        # 4. सफलता जाँच
        if claimed and wallet:
            post_text = page.locator("body").inner_text(timeout=5000)
            if AI_ENABLED and ai_counter[0] < MAX_AI_CALLS_PER_RUN and ai_decision:
                if ai_post_check(post_text, url):
                    success_list.append((url, crypto_used))
                    ai_counter[0] += 1
            else:
                if strict_success_check(post_text, url):
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

    success = []
    ai_cnt = [0]

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
    for u, c in success:
        print(f"   + {u[:60]}... ({c})")
    print(f"🧠 AI कॉल: {ai_cnt[0]} बार")
    print("💰 तेरा Trust Wallet चेक कर – बूँद-बूँद से घड़ा भरेगा!")

if __name__ == "__main__":
    fly()
