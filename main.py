import os
import json
import time
import random
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLETS_JSON = os.environ["WALLETS_JSON"]
wallets = json.loads(WALLETS_JSON)

# =====================================================================
# FIXED FAUCET LIST (~300 भरोसेमंद साइटें, हर कॉइन के लिए)
# =====================================================================
FIXED_SITES = [
    # ── MULTI-COIN FAUCETS (सबसे ज़्यादा कमाई) ──
    "https://firefaucet.win", "https://faucetcrypto.com", "https://allcoins.pw",
    "https://cointiply.com/ptc-ads", "https://rollercoin.com", "https://dutchycorp.space",
    "https://freefaucet.io", "https://claimfreecoins.io", "https://coindiversity.io",
    "https://fastcoin.ga", "https://autofaucet.org", "https://viperfaucet.com",
    "https://faucetpay.io", "https://faucethub.io",

    # ── BTC FAUCETS ──
    "https://freebitco.in", "https://satoshihero.com", "https://btcclicks.com",
    "https://coinpayu.com", "https://adbtc.top", "https://bitcoinker.com",
    "https://moonbit.co.in", "https://moonbitcoin.xyz", "https://bitfun.co",
    "https://cryptowin.io", "https://earncrypto.com/faucet", "https://freebitcoin.io",
    "https://btc-faucet.com", "https://bitcoingenerator.pw", "https://coinfaucet.eu/en/btc-testnet/",

    # ── ETH & USDT ──
    "https://free-usdt.com", "https://free-tether.com", "https://freeeth.io",
    "https://ethereum-faucet.org", "https://fauceth.io", "https://sepoliafaucet.com",
    "https://sepolia-faucet.pk910.de", "https://www.alchemy.com/faucets/ethereum-sepolia",

    # ── BNB ──
    "https://free-bnb.com", "https://freebnbco.in", "https://stakely.io/en/faucet/binance-bnb",
    "https://testnet.bnbchain.org/faucet-smart", "https://www.bnbchain.org/en/testnet-faucet",

    # ── SOL ──
    "https://free-solana.com", "https://faucet.solana.com", "https://solanafaucet.com",
    "https://solfaucet.togatech.org", "https://solfaucet.com",

    # ── DOGE ──
    "https://freedogecoin.net", "https://dogefaucet.com", "https://free-doge.com",
    "https://moondogecoin.com", "https://freedoge.co.in", "https://dogecoinfaucet.com",

    # ── TON ──
    "https://free-ton.com", "https://ton-faucet.com", "https://faucet.tonxapi.com",

    # ── OTHER COINS (LTC, ADA, TRX, DASH, ZEC, XRP, LINK, MATIC, DOT, AVAX, NEAR, APT, SUI, ARB, OP, BASE) ──
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

    # ── AIRDROP / GIVEAWAY PLATFORMS ──
    "https://onepapel.com", "https://warsonsol.com", "https://www.binance.com/en/activity",
    "https://coinmarketcap.com/airdrop/", "https://airdropalert.com",
    "https://airdrops.io", "https://www.airdropking.io",

    # ── MICROTASK PLATFORMS ──
    "https://jumptask.io", "https://earncrypto.com", "https://freecash.com/earn",
    "https://getpaidto.click", "https://timebucks.com", "https://picoworkers.com",
    "https://microworkers.com", "https://rapidworkers.com",

    # ── TESTNET FAUCETS (हर बड़े चेन के लिए) ──
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
    "https://faucet.flow.com", "https://faucet.hedera.com",
    "https://faucet.tezos.com", "https://faucet.cosmos.network",
    "https://faucet.osmosis.zone", "https://faucet.injective.network",
    "https://faucet.sei.io", "https://faucet.kava.io",
    "https://faucet.evmos.org", "https://faucet.axelar.network",
    "https://faucet.layerzero.network", "https://faucet.stargate.finance",
]

# =====================================================================
# SERPER SEARCH QUERIES (80 queries → ~400 sites)
# =====================================================================
def serper_search():
    coins = ["BTC","Bitcoin","USDT","ETH","BNB","SOL","TON","DOGE","LTC","TRX","ADA","XRP","MATIC","AVAX","NEAR"]
    actions = ["faucet","claim","earn","task","quest","ptc","microtask","reward","airdrop","giveaway","bonus"]
    queries = []
    for coin in coins:
        for act in actions:
            queries.append(f"{coin} {act} wallet address instant 2026")
            queries.append(f"free {coin} {act} no login no KYC 2026")
    queries = list(set(queries))[:80]
    tasks = []
    seen = set()
    for q in queries:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5}, timeout=8
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
                break
        except:
            pass
        time.sleep(random.uniform(0.2, 0.5))
    return tasks

# =====================================================================
# CRYPTO DETECTOR (साइट पर जो कॉइन माँगा जा रहा है, वो पहचानो)
# =====================================================================
def detect_crypto_type(page_text):
    text = page_text.lower()
    if "solana" in text or "sol" in text.split(): return "SOL"
    if "toncoin" in text or "ton" in text.split(): return "TON"
    if "usdt" in text or "tether" in text: return "USDT"
    if "bnb" in text or "binance coin" in text or "bsc" in text: return "BNB"
    if "btc" in text or "bitcoin" in text: return "BTC"
    if "doge" in text or "dogecoin" in text: return "DOGE"
    if "eth" in text or "ethereum" in text: return "ETH"
    if "ltc" in text or "litecoin" in text: return "LTC"
    if "trx" in text or "tron" in text: return "TRX"
    if "ada" in text or "cardano" in text: return "ADA"
    if "xrp" in text or "ripple" in text: return "XRP"
    if "matic" in text or "polygon" in text: return "MATIC"
    if "avax" in text or "avalanche" in text: return "AVAX"
    if "near" in text.split(): return "NEAR"
    return "BTC"

# =====================================================================
# SITE VISITOR + CLAIMER (तेज़ और एरर-प्रूफ)
# =====================================================================
def try_claim(page, url, i, total):
    try:
        page.goto(url, timeout=6000, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(800, 1500))
        body_text = page.inner_text("body").lower()
        crypto = detect_crypto_type(body_text)
        wallet = wallets.get(crypto, wallets.get("BTC", ""))

        # इनपुट फील्ड
        input_fields = page.query_selector_all(
            "input[type='text'], input[type='email'], input[name*='address'], "
            "input[name*='wallet'], input[placeholder*='address'], input[placeholder*='wallet']"
        )
        filled = False
        for inp in input_fields[:2]:
            try:
                inp.fill(wallet)
                filled = True
                page.wait_for_timeout(random.randint(300, 600))
                break
            except: pass

        # बटन खोजो
        for word in ["claim","roll","earn","start","free","get","receive","submit","send","reward","spin","mine","bonus"]:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    page.wait_for_timeout(random.randint(800, 1500))
                    if any(w in page.content().lower() for w in ["success","credited","sent","thank","congrat"]):
                        print(f"[{i}/{total}] ✅ {url[:50]}... {crypto}")
                    return
                except: pass

        # अगर इनपुट भरा था, सबमिट करो
        if filled:
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                try:
                    submit.click()
                    page.wait_for_timeout(random.randint(600, 1200))
                except: pass
    except:
        pass  # silently skip dead sites

# =====================================================================
# MAIN FLIGHT
# =====================================================================
def fly():
    print("🌍 EarnAI Mega Faucet Hunter v3.0 🚀")
    print("🎯 Target: 1000 Sites/Day")

    # Fixed Sites
    all_urls = list(FIXED_SITES)
    print(f"📋 Fixed Sites: {len(all_urls)}")

    # Serper Search
    new_urls = serper_search()
    all_urls.extend(new_urls)
    print(f"🔍 Serper Sites: {len(new_urls)}")

    # Remove duplicates
    all_urls = list(dict.fromkeys(all_urls))
    total = len(all_urls)
    print(f"🎯 Total Unique Sites to Visit: {total}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        for i, url in enumerate(all_urls, 1):
            try_claim(page, url, i, total)
            time.sleep(random.uniform(0.3, 0.8))

        browser.close()

    print(f"\n🏁 Mission Complete: {total} sites attempted!")
    print("💰 Check your Trust Wallet - BTC, USDT, BNB, SOL, DOGE, TON")

if __name__ == "__main__":
    fly()
