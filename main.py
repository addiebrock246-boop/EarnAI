import os
import json
import time
import random
from ddgs import DDGS
from playwright.sync_api import sync_playwright

WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

# =====================================================================
# 300+ FIXED FAUCET/TASK SITES (हर कॉइन के लिए)
# =====================================================================
FIXED_SITES = [
    # ... (तेरी पूरी लिस्ट पहले जैसी ही रखो)
]

# =====================================================================
# DDG SEARCH (500 queries, 10 results each) → ~5000 URLs
# =====================================================================
def ddg_search_new_sites(num_queries=500):
    coins = list(wallets.keys())
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
                results = list(ddgs.text(q, max_results=10))
                for r in results:
                    href = r.get("href")
                    if not href: continue
                    skip = ["academy","support","blog","faq","youtube","reddit","medium","twitter","facebook","news"]
                    if any(w in href for w in skip): continue
                    if href not in seen:
                        seen.add(href)
                        tasks.append(href)
                time.sleep(random.randint(2, 4))
            except Exception as e:
                continue
    return tasks

# =====================================================================
# CRYPTO DETECTOR (FIRO, KSM, MNT, POL जोड़े गए)
# =====================================================================
def detect_crypto_type(text):
    text = text.lower()
    # नए कॉइन्स पहले
    if "firo" in text: return "FIRO"
    if "kusama" in text or "ksm" in text.split(): return "KSM"
    if "mantle" in text or "mnt" in text.split(): return "MNT"
    if "polygon" in text or "pol" in text.split(): return "POL"
    # बाकी पुराने
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
    # ... (तेरे बाकी पुराने कॉइन्स की लाइनें)
    return "BTC"

# =====================================================================
# SITE VISITOR + CLAIMER (तेज़, एरर-प्रूफ)
# =====================================================================
def try_claim(page, url):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        body_text = page.inner_text("body").lower()
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))
        
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='address'], input[name*='wallet']")
        filled = False
        for inp in inputs[:2]:
            try:
                inp.fill(wallet)
                filled = True
                page.wait_for_timeout(random.randint(300, 600))
                break
            except: pass
        
        for word in ["claim","roll","earn","start","free","get","submit","send","reward","spin","mine","bonus"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    page.wait_for_timeout(random.randint(800, 1500))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        pass
                    return
                except: pass
        
        if filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                except: pass
    except:
        pass

# =====================================================================
# MAIN
# =====================================================================
def fly():
    print("🌍 EarnAI MEGA FAUCET HUNTER v5.0 🚀")
    print("🎯 Target: 10,000 Sites/Day | 20+ Coins")
    
    all_urls = list(FIXED_SITES)
    print(f"📋 Fixed Sites: {len(all_urls)}")
    
    new_urls = ddg_search_new_sites(500)
    all_urls.extend(new_urls)
    print(f"🆕 DDG New Sites: {len(new_urls)}")
    
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"🎯 Total Unique Sites: {total}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(all_urls, 1):
            if i % 100 == 0:
                print(f"📊 Progress: {i}/{total}")
            try_claim(page, url)
            time.sleep(random.uniform(0.3, 0.8))
        browser.close()
    
    print(f"\n🏁 Mission Complete: {total} sites attempted!")
    print("💰 Check your Trust Wallet: BTC, ETH, USDT, BNB, SOL, DOGE, TON, XRP, ADA, TRX, AVAX, DOT, BCH, LTC, MNT, APT, POL, USDC, FIRO, KSM...")

if __name__ == "__main__":
    fly()
