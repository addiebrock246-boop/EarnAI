import os
import json
import time
import random
from ddgs import DDGS
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

# 🔥 TEST MODE: True रखोगे तो सिर्फ 10 साइटें चेक होंगी, False करोगे तो 5000+ साइटें
TEST_MODE = True

# ========== FIXED SITES (300+) ==========
FIXED_SITES = [
    # Multi
    "https://firefaucet.win", "https://faucetcrypto.com", "https://allcoins.pw",
    "https://cointiply.com/ptc-ads", "https://rollercoin.com", "https://dutchycorp.space",
    "https://freefaucet.io", "https://claimfreecoins.io", "https://coindiversity.io",
    "https://fastcoin.ga", "https://autofaucet.org", "https://viperfaucet.com",
    "https://faucetpay.io", "https://faucethub.io",
    # BTC
    "https://freebitco.in", "https://satoshihero.com", "https://btcclicks.com",
    "https://coinpayu.com", "https://adbtc.top", "https://bitcoinker.com",
    "https://moonbit.co.in", "https://moonbitcoin.xyz", "https://bitfun.co",
    "https://cryptowin.io", "https://earncrypto.com/faucet", "https://freebitcoin.io",
    # ... (बाकी सब वही, पूरी लिस्ट मत काटना, बस टेस्ट में 10 लेंगे)
]

# ========== DDG SEARCH ==========
def ddg_search_new_sites(num_queries=500):
    if TEST_MODE:
        num_queries = 2  # टेस्ट के लिए सिर्फ 2 क्वेरी
    coins = list(wallets.keys())[:5]  # टेस्ट में सिर्फ 5 कॉइन
    actions = ["faucet","claim","earn","task","quest","airdrop","giveaway","bonus","reward","free"]
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

# ========== CRYPTO DETECTOR (पहले जैसा) ==========
def detect_crypto_type(text):
    text = text.lower()
    # नए कॉइन पहले
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

# ========== नया: कुकी बैनर हैंडलर ==========
def handle_cookie_banner(page):
    """'Accept', 'OK', 'Agree', 'Close' जैसे बटन ढूँढकर दबाओ"""
    for word in ["accept", "ok", "agree", "close", "consent", "allow", "got it"]:
        try:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), "
                                     f"input[value*='{word}' i]")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
                return True
        except:
            pass
    return False

# ========== नया: ड्रॉपडाउन हैंडलर ==========
def handle_dropdown(page, crypto):
    """<select> में से सही क्रिप्टो वाला ऑप्शन चुनो, या पहला"""
    selects = page.query_selector_all("select")
    for sel in selects:
        options = sel.query_selector_all("option")
        for opt in options:
            val = (opt.get_attribute("value") or "").lower()
            text = (opt.inner_text() or "").lower()
            if crypto.lower() in val or crypto.lower() in text:
                opt.select_option()
                return True
        # नहीं मिला तो पहला ऑप्शन सेलेक्ट करो
        if options:
            options[0].select_option()
            return True
    return False

# ========== SITE VISITOR + CLAIMER (सुधारों के साथ) ==========
def try_claim(page, url, success_list):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))

        # पहले कुकी/पॉप-अप बंद करो
        handle_cookie_banner(page)
        page.wait_for_timeout(300)

        body_text = page.inner_text("body").lower()
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))

        # ड्रॉपडाउन हैंडल करो (अगर कोई हो)
        handle_dropdown(page, crypto)

        # इनपुट फील्ड भरो
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']")
        filled = False
        for inp in inputs[:2]:
            try:
                # अगर अमाउंट/नंबर टाइप का फील्ड है, तो "1" डालो और छोड़ो
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
                    content = page.content().lower()
                    if any(w in content for w in ["success","credited","sent","thank","congrat"]):
                        success_list.append((url, crypto))
                    return
                except:
                    pass

        # सबमिट बटन (अगर कोई एक्शन बटन नहीं मिला)
        if filled:
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
    print("🌍 EarnAI Mega Faucet Hunter (Test Mode)" if TEST_MODE else "🌍 EarnAI Mega Faucet Hunter (Full Mode)")
    
    # फिक्स्ड साइट्स
    all_urls = list(FIXED_SITES)
    if TEST_MODE:
        all_urls = all_urls[:10]  # टेस्ट में सिर्फ 10
    print(f"📋 Fixed Sites: {len(all_urls)}")
    
    # DDG सर्च
    new_urls = ddg_search_new_sites()
    all_urls.extend(new_urls)
    print(f"🆕 DDG New Sites: {len(new_urls)}")
    
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"🎯 Total Sites to Visit: {total}\n")
    
    success_list = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(all_urls, 1):
            if i % 10 == 0:
                print(f"📊 Progress: {i}/{total}")
            try_claim(page, url, success_list)
            time.sleep(random.uniform(0.3, 0.8))
        browser.close()
    
    print(f"\n🏁 Mission Complete: {total} sites attempted!")
    print(f"✅ सफलता: {len(success_list)} sites")
    for url, coin in success_list:
        print(f"   + {url[:60]}... ({coin})")
    
    print("💰 Check your Trust Wallet for: BTC, ETH, USDT, BNB, SOL, DOGE, TON...")

if __name__ == "__main__":
    fly()
