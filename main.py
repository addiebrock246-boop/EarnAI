import os
import json
import time
import random
from playwright.sync_api import sync_playwright

# ========== कुकीज़ लोड और sameSite फिक्स ==========
COOKIES_JSON = os.environ["COINTIPLY_COOKIES"]
cookies = json.loads(COOKIES_JSON)

for cookie in cookies:
    if 'sameSite' in cookie:
        if cookie['sameSite'].lower() not in ['strict', 'lax', 'none']:
            cookie['sameSite'] = 'Lax'
        else:
            cookie['sameSite'] = cookie['sameSite'].capitalize()
    else:
        cookie['sameSite'] = 'Lax'

def ptc_ads(page):
    print("📡 PTC Ads पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/ptc-ads", timeout=30000)
    page.wait_for_timeout(random.randint(5000, 8000))

    # क्या हम लॉग्ड इन हैं?
    if "login" in page.url.lower():
        print("❌ PTC पेज पर लॉगिन माँग रहा, कुकीज़ शायद गलत।")
        return 0

    print_page_info(page, "PTC Ads पेज")

    # सारे क्लिक करने लायक लिंक ढूँढो
    click_buttons = page.query_selector_all("a[href*='/ptc/'], a:has-text('Visit'), a:has-text('View')")
    if not click_buttons:
        # वैकल्पिक सेलेक्टर
        click_buttons = page.query_selector_all("a.btn, a.button")
    print(f"🔘 {len(click_buttons)} ऐड लिंक मिले")

    ads_clicked = 0
    for btn in click_buttons:
        try:
            href = btn.get_attribute("href")
            print(f"👉 क्लिक कर रहे: {href[:60]}")
            btn.click()
            page.wait_for_timeout(random.randint(8000, 12000))
            # मान लो कि नया टैब खुलता है, तो उसे बंद करो और वापस आओ
            # अगर एक ही टैब में खुलता है तो वापस जाओ
            if page.url != "https://cointiply.com/ptc-ads":
                page.go_back()
                page.wait_for_timeout(3000)
            ads_clicked += 1
            if ads_clicked >= 5:  # एक बार में 5 ऐड काफी
                break
        except Exception as e:
            print(f"⚠️ ऐड क्लिक में दिक्कत: {e}")

    print(f"🎯 कुल {ads_clicked} PTC ऐड पर क्लिक किया।")
    return ads_clicked

def print_page_info(page, step_name=""):
    print(f"\n--- {step_name} ---")
    print(f"📍 URL: {page.url}")
    logout_btn = page.query_selector("a:has-text('Logout')")
    print(f"🔑 लॉगिन: {'लॉग्ड इन' if logout_btn else 'लॉग्ड आउट'}")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")

        print("🔐 कुकीज़ सेट करके लॉगिन...")
        page.goto("https://cointiply.com", timeout=30000)
        page.context.add_cookies(cookies)
        page.reload()
        page.wait_for_timeout(5000)

        ptc_ads(page)
        browser.close()

if __name__ == "__main__":
    fly()
