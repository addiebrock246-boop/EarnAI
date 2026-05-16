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
        # अगर "unspecified" या कोई और अवैध वैल्यू हो, तो "Lax" कर दो
        if cookie['sameSite'].lower() not in ['strict', 'lax', 'none']:
            cookie['sameSite'] = 'Lax'
        else:
            # सही capitalization करो (Lax, Strict, None)
            cookie['sameSite'] = cookie['sameSite'].capitalize()
    else:
        # अगर sameSite है ही नहीं, तो डिफ़ॉल्ट "Lax" डाल दो
        cookie['sameSite'] = 'Lax'

def ptc_ads(context, page):
    print("📡 PTC Ads पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/ptc-ads", timeout=30000)
    page.wait_for_timeout(random.randint(5000, 8000))

    # पुष्टि करो कि लॉगिन है
    if "login" in page.url.lower():
        print("❌ लॉगिन नहीं हुआ — कुकीज़ अपडेट करो")
        return 0
    logout_btn = page.query_selector("a:has-text('Logout')")
    if not logout_btn:
        print("❌ Logout बटन नहीं दिखा, लॉग्ड इन नहीं")
        return 0
    print("✅ लॉगिन सफल")

    # सारे PTC ऐड लिंक ढूँढो
    ad_links = page.query_selector_all("a[href*='/ptc/'], a:has-text('Visit'), a:has-text('View')")
    if not ad_links:
        # वैकल्पिक सेलेक्टर
        ad_links = page.query_selector_all("a.btn, a.button")
    print(f"🔘 {len(ad_links)} PTC लिंक मिले")

    ads_clicked = 0
    for btn in ad_links:
        if ads_clicked >= 5:
            break
        try:
            href = btn.get_attribute("href")
            # अगर href खाली या होमपेज है तो छोड़ो
            if not href or (href.startswith("https://cointiply.com") and "ptc" not in href):
                continue
            print(f"👉 क्लिक: {href[:60]}")
            # नए टैब (पेज) में खोलो ताकि मूल पेज सुरक्षित रहे
            new_page = context.new_page()
            new_page.goto(href, timeout=30000)
            new_page.wait_for_timeout(random.randint(8000, 12000))
            new_page.close()
            ads_clicked += 1
            page.wait_for_timeout(random.randint(2000, 4000))
        except Exception as e:
            print(f"⚠️ इस ऐड में दिक्कत: {e}")

    print(f"🎯 कुल {ads_clicked} PTC ऐड खोले गए।")
    return ads_clicked

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

        ptc_ads(context, page)
        browser.close()

if __name__ == "__main__":
    fly()
