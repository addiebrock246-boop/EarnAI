import os
import time
from playwright.sync_api import sync_playwright

WALLET = os.environ.get("WALLET_ADDRESS", "0xYourRealWalletAddress")

# Ek simple faucet task (FreeBitco.in) — wallet address maangta hai
FAUCET_TASKS = [
    {
        "name": "FreeBitco.in",
        "url": "https://freebitco.in",
        "wallet_selector": "#btcAddress",          # wallet input ka id
        "claim_selector": "#claim_button",         # claim button ka id
        "success_text": "BTC"                      # page mein aana chahiye
    }
]

def try_claim_faucet(page, task):
    print(f"⛏️ Trying: {task['name']}")
    try:
        page.goto(task["url"], timeout=30000)
        page.wait_for_timeout(3000)  # load hone do

        # Wallet address fill karo
        wallet_field = page.query_selector(task["wallet_selector"])
        if wallet_field:
            wallet_field.fill(WALLET)
            print(f"📝 Wallet filled: {WALLET[:10]}...")
        else:
            print("❌ Wallet input field nahi mila. Site structure change ho gayi.")
            return False

        # Claim button dabao
        claim_btn = page.query_selector(task["claim_selector"])
        if claim_btn:
            claim_btn.click()
            print("🖱️ Claim button click kiya")
            page.wait_for_timeout(5000)

            # Success check karo
            if task["success_text"] in page.content():
                print(f"✅ Claim successful! (Text '{task['success_text']}' found)")
                return True
            else:
                print("⚠️ Claim button dabaya, lekin success confirm nahi hua (captcha ya error).")
                return False
        else:
            print("❌ Claim button nahi mila.")
            return False
    except Exception as e:
        print(f"❌ Error in {task['name']}: {e}")
        return False

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌍 Starting EarnAI task execution...")
        success = 0
        for task in FAUCET_TASKS:
            if try_claim_faucet(page, task):
                success += 1
            time.sleep(10)  # rate limit se bachne ke liye

        print(f"🎯 Aaj {success}/{len(FAUCET_TASKS)} task attempt kiye.")
        browser.close()

if __name__ == "__main__":
    fly()
