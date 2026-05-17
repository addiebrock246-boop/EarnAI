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

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TEST_MODE = True          # टेस्ट (5 साइट) → बाद में False करो
AI_ENABLED = True         # Groq AI का इस्तेमाल करना है

# ========== FIXED SITES (टेस्ट vs फुल) ==========
if TEST_MODE:
    FIXED_SITES = [
        "https://firefaucet.win",
        "https://cointiply.com/ptc-ads",
        "https://freebitco.in",
        "https://freedogecoin.net",
        "https://free-solana.com"
    ]
else:
    # फुल लिस्ट (300+ sites) - नीचे अपनी पूरी लिस्ट रखो
    FIXED_SITES = [
        # ── MULTI-FAUCET ──
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
        "https://ethereum-faucet.org", "https://fauceth.io", "https://sepoliafaucet.com",
        "https://sepolia-faucet.pk910.de",
        # ── BNB ──
        "https://free-bnb.com", "https://freebnbco.in", "https://stakely.io/en/faucet/binance-bnb",
        "https://testnet.bnbchain.org/faucet-smart",
        # ── SOL ──
        "https://free-solana.com", "https://faucet.solana.com", "https://solanafaucet.com",
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
        # ── TASK/QUEST PLATFORMS ──
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

# ========== DDG SEARCH ==========
def ddg_search_new_sites(num_queries=500):
    if TEST_MODE:
        num_queries = 2
    coins = list(wallets.keys())[:5] if TEST_MODE else list(wallets.keys())
    actions = ["faucet","claim","earn","task","quest","airdrop","giveaway","bonus","reward","free"]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"free {coin} {act} wallet address instant 2026")
            queries.append(f"{coin} faucet claim no login no KYC")
    queries = list(set(queries))[:num_queries]

    tasks = []
    seen = set()
    with DDGS() as ddgs:
        for q in queries:
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
                time.sleep(random.randint(2, 4))
            except:
                continue
    return tasks

# ========== CRYPTO DETECTOR ==========
def detect_crypto_type(text):
    text = text.lower()
    if "firo" in text: return "FIRO"
    if "kusama" in text or "ksm" in text.split(): return "KSM"
    if "mantle" in text or "mnt" in text.split(): return "MNT"
    if "polygon" in text or "pol" in text.split(): return "POL"
    if "solana" in text or "sol" in text.split(): return "SOL"
    if "toncoin" in text or "ton" in text.split(): return "TON"
    if "usdt" in text or "tether" in text: return "USDT"
    if "usdc" in text or "usd coin" in text: return "USDC"
    if "bnb" in text or "binance coin" in text or "bsc" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "ethereum" in text or "eth" in text.split(): return "ETH"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "litecoin" in text or "ltc" in text.split(): return "LTC"
    if "tron" in text or "trx" in text.split(): return "TRX"
    if "cardano" in text or "ada" in text.split(): return "ADA"
    if "ripple" in text or "xrp" in text.split(): return "XRP"
    if "avalanche" in text or "avax" in text.split(): return "AVAX"
    if "polkadot" in text or "dot" in text.split(): return "DOT"
    if "bitcoin cash" in text or "bch" in text.split(): return "BCH"
    if "aptos" in text or "apt" in text.split(): return "APT"
    return "BTC"

# ========== COOKIE / POPUP HANDLER ==========
def handle_cookie_banner(page):
    for word in ["accept", "ok", "agree", "close", "consent", "allow", "got it"]:
        try:
            btn = page.query_selector(
                f"button:has-text('{word}'), a:has-text('{word}'), "
                f"input[value*='{word}' i]"
            )
            if btn:
                btn.click()
                page.wait_for_timeout(500)
                return True
        except:
            pass
    return False

# ========== DROPDOWN HANDLER ==========
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

# ========== SITE VISITOR + CLAIMER (लॉगिन फ़िल्टर + AI) ==========
def try_claim(page, url, success_list, ai_call_counter):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        # पूरा पेज टेक्स्ट (5s timeout)
        body_text = page.locator("body").inner_text(timeout=5000).lower()

        # ===== 1. लॉगिन/रजिस्ट्रेशन/केवाईसी चेक =====
        login_keywords = ["login", "sign in", "register", "create account", "kyc", "verify identity"]
        if any(kw in body_text for kw in login_keywords):
            # अगर लॉगिन माँगे तो इस साइट को छोड़ दो (सफलता नहीं)
            return

        # ===== 2. क्रिप्टो पहचानो और एड्रेस भरो =====
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
            except:
                pass

        # ===== 3. बटन दबाओ =====
        button_pressed = False
        for word in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
            btn = page.query_selector(
                f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]"
            )
            if btn:
                try:
                    btn.click()
                    button_pressed = True
                    page.wait_for_timeout(random.randint(800, 1500))
                    # सफलता चेक करते वक्त भी लॉगिन शब्दों की अनुपस्थिति सुनिश्चित करो
                    content = page.content().lower()
                    if any(w in content for w in ["success","credited","sent","thank","congrat"]) \
                       and not any(kw in content for kw in login_keywords):
                        success_list.append((url, crypto))
                    return
                except:
                    pass

        # ===== 4. अगर कोई बटन नहीं मिला और फॉर्म नहीं भरा → AI से सलाह (सीमित) =====
        if not button_pressed and not filled:
            if ai_call_counter[0] < 100:  # हर रन में 100 AI कॉल
                ai = ask_ai_what_to_do(body_text, url)
                ai_call_counter[0] += 1
                if ai:
                    action = ai.get("action")
                    keyword = ai.get("keyword", "")
                    if action == "click_button" and keyword:
                        btn = page.query_selector(f"button:has-text('{keyword}'), a:has-text('{keyword}')")
                        if btn:
                            btn.click()
                            page.wait_for_timeout(2000)
                            content = page.content().lower()
                            if any(w in content for w in ["success","credited","sent","thank","congrat"]) \
                               and not any(kw in content for kw in login_keywords):
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
        # ===== 5. अगर फॉर्म भरा था तो सबमिट करो =====
        elif filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                    content = page.content().lower()
                    if any(w in content for w in ["success","credited","sent","thank","congrat"]) \
                       and not any(kw in content for kw in login_keywords):
                        success_list.append((url, crypto))
                except:
                    pass
    except:
        pass

# ========== MAIN ==========
def fly():
    mode_text = "TEST (5 sites)" if TEST_MODE else "FULL (5000+ sites)"
    print(f"🌍 EarnAI Mega Faucet Hunter – {mode_text} 🚀")
    if AI_ENABLED and GROQ_API_KEY:
        print("🧠 AI (Groq) सक्रिय है – ज़रूरत पड़ने पर सलाह देगा।")
    else:
        print("ℹ️ AI निष्क्रिय है।")

    # फिक्स्ड साइट्स
    all_urls = list(FIXED_SITES)
    print(f"📋 Fixed Sites: {len(all_urls)}")

    # DDG सर्च
    new_urls = ddg_search_new_sites()
    all_urls.extend(new_urls)
    print(f"🆕 DDG New Sites: {len(new_urls)}")

    # डुप्लीकेट हटाओ
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"🎯 Total Sites to Visit: {total}\n")

    success_list = []
    ai_call_counter = [0]   # AI कॉल की संख्या रखने के लिए

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        for i, url in enumerate(all_urls, 1):
            if i % 10 == 0 or (TEST_MODE and i % 3 == 0):
                print(f"📊 Progress: {i}/{total}")
            try_claim(page, url, success_list, ai_call_counter)
            time.sleep(random.uniform(0.3, 0.8))

        browser.close()

    print(f"\n🏁 Mission Complete: {total} sites attempted!")
    print(f"✅ सफलताएँ: {len(success_list)} sites")
    for url, coin in success_list:
        print(f"   + {url[:70]}... ({coin})")
    if AI_ENABLED and GROQ_API_KEY:
        print(f"🧠 AI कॉल की गईं: {ai_call_counter[0]} बार")
    print("💰 अपना Trust Wallet चेक करो – BTC, USDT, BNB, SOL, DOGE, TON... सबके लिए कमाई!")

if __name__ == "__main__":
    fly()
