import os
import json
import time
import random
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

# ========== फिक्स्ड साइट्स (60+ भरोसेमंद) ==========
FIXED_SITES = [
    # MULTI-FAUCET
    "https://firefaucet.win", "https://faucetcrypto.com", "https://allcoins.pw",
    "https://freefaucet.io", "https://cointiply.com/ptc-ads", "https://claimfreecoins.io",
    "https://coindiversity.io", "https://fastcoin.ga",
    # BTC
    "https://freebitco.in", "https://satoshihero.com", "https://btcclicks.com",
    "https://coinpayu.com", "https://adbtc.top", "https://bitcoinker.com",
    "https://moonbit.co.in", "https://moonbitcoin.xyz", "https://bitfun.co",
    "https://cryptowin.io", "https://earncrypto.com/faucet",
    # USDT
    "https://free-usdt.com", "https://free-tether.com",
    # BNB
    "https://free-bnb.com", "https://stakely.io/en/faucet/binance-bnb",
    "https://freebnbco.in", "https://testnet.bnbchain.org/faucet-smart",
    # SOL
    "https://free-solana.com", "https://faucet.solana.com", "https://solanafaucet.com",
    # DOGE
    "https://freedogecoin.net", "https://dogefaucet.com", "https://free-doge.com",
    "https://moondogecoin.com", "https://freedoge.co.in",
    # TON
    "https://free-ton.com",
    # OTHER
    "https://freecardano.com", "https://free-litecoin.com", "https://free-tron.com",
    "https://moonliteco.in", "https://moondash.co.in", "https://freebitcoin.io",
    # TASK PLATFORMS
    "https://app.layer3.xyz/quests", "https://zealy.io/c/explore",
    "https://galxe.com/explore", "https://app.dework.xyz/explore",
    "https://questn.com/explore", "https://taskon.xyz/quests",
    "https://superteam.fun/earn", "https://www.rabbithole.gg/quests",
    "https://kleoverse.com/explore",
    # MORE
    "https://dutchycorp.space", "https://rollercoin.com",
    "https://free-dash.com", "https://free-zcash.com",
]

def serper_search():
    coins = ["BTC", "Bitcoin", "USDT", "BNB", "SOL", "TON", "DOGE", "ETH", "LTC", "TRX"]
    actions = ["faucet", "claim", "earn", "task", "quest", "ptc", "microtask", "reward"]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"{coin} {act} instant no login wallet address 2026")
    queries = list(set(queries))[:50]
    tasks = []
    seen = set()
    for q in queries:
        print(f"🔍 Serper: '{q}'")
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5}, timeout=10
            )
            if resp.status_code == 200:
                for item in resp.json().get("organic", []):
                    link = item.get("link", "")
                    skip = ["academy","support","blog","faq","youtube","reddit","medium","twitter","facebook","news"]
                    if any(w in link for w in skip): continue
                    if link and link not in seen:
                        seen.add(link)
                        tasks.append(link)
            elif resp.status_code == 429:
                print("   ⚠️ Serper quota खत्म"); break
        except Exception as e:
            print(f"   ❌ {e}")
        time.sleep(random.uniform(0.3, 1.0))
    return tasks

def detect_crypto_type(page_text):
    text = page_text.lower()
    if "solana" in text or "sol" in text: return "SOL"
    if "toncoin" in text or "ton" in text.split(): return "TON"
    if "usdt" in text or "tether" in text: return "USDT"
    if "bnb" in text or "binance coin" in text or "bsc" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "eth" in text or "ethereum" in text: return "ETH"
    if "ltc" in text or "litecoin" in text: return "LTC"
    if "trx" in text or "tron" in text: return "TRX"
    return "BTC"

def try_claim(page, url):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(random.randint(2000, 4000))
        body_text = page.inner_text("body")
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))
        print(f"    ℹ️ '{crypto}' की माँग लग रही है।")

        # इनपुट फील्ड
        input_fields = page.query_selector_all(
            "input[type='text'], input[type='email'], input[name*='address'], "
            "input[name*='wallet'], input[placeholder*='address'], input[placeholder*='wallet']"
        )
        filled = False
        for inp in input_fields[:3]:
            try:
                inp.fill(wallet)
                print(f"    📝 {crypto} एड्रेस भरा: {wallet[:10]}...")
                filled = True
                page.wait_for_timeout(random.randint(500, 1000))
            except: pass

        # बटन
        for word in ["claim","roll","earn","start","free","get","receive","submit","send","reward"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन दबाया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        print("    ✅ सफलता मिली!")
                    return
                except: pass

        if filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    print("    ✅ सबमिट किया")
                    page.wait_for_timeout(random.randint(1500, 3000))
                except: pass
    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – मेगा मल्टी-कॉइन हंटर (60+ साइट्स) 🚀")
    all_urls = list(FIXED_SITES)
    new_urls = serper_search()
    all_urls.extend(new_urls)
    all_urls = list(dict.fromkeys(all_urls))
    print(f"\n🎯 कुल {len(all_urls)} साइटें (फिक्स्ड + सर्च)। पहले 150 पर कोशिश।\n")
    urls_to_visit = all_urls[:150]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, url in enumerate(urls_to_visit):
            print(f"[{i+1}/{len(urls_to_visit)}]")
            try_claim(page, url)
            time.sleep(random.randint(1, 2))
        browser.close()
    print("🏁 आज का मिशन पूरा। अलग-अलग वॉलेट्स चेक करो।")

if __name__ == "__main__":
    fly()
