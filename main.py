import os
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync  # stealth इंपोर्ट

EMAIL = os.environ["COINTIPLY_EMAIL"]
PASSWORD = os.environ["COINTIPLY_PASSWORD"]

def login(page):
    """Stealth मोड के साथ Cointiply लॉगिन"""
    print("🔐 लॉगिन पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/login", timeout=30000)
    page.wait_for_timeout(random.randint(3000, 5000))

    # फ़ील्ड भरो (सही सेलेक्टर)
    email_field = page.wait_for_selector("input[name='email'], input[type='email']", timeout=10000)
    pass_field = page.wait_for_selector("input[name='password'], input[type='password']", timeout=10000)
    email_field.fill(EMAIL)
    pass_field.fill(PASSWORD)
    print("📧 ईमेल/पासवर्ड भरे")

    # लॉगिन बटन दबाओ
    login_btn = page.wait_for_selector("button:has-text('Login'), input[value='Login']", timeout=5000)
    login_btn.click()
    print("🔘 लॉगिन बटन दबाया")

    # लॉगिन सफल होने का इंतज़ार (Logout लिंक दिखे)
    try:
        page.wait_for_selector("a:has-text('Logout'), button:has-text('Logout'), .user-menu", timeout=15000)
        print("✅ लॉगिन सफल! (Logout दिखा)")
        return True
    except:
        print("❌ लॉगिन विफल – कैप्चा या गलत पासवर्ड")
        return False

def surf_ads(page):
    print("📡 सर्फ ऐड्स पर जा रहे हैं...")
    page.goto("https://cointiply.com/surf-ads", timeout=30000)
    page.wait_for_timeout(random.randint(5000, 8000))

    # स्टार्ट सर्फिंग बटन (ज़रूरत पड़ी तो)
    try:
        start_btn = page.wait_for_selector("button:has-text('Start Surfing')", timeout=5000)
        start_btn.click()
        print("✅ स्टार्ट सर्फिंग क्लिक किया")
        page.wait_for_timeout(random.randint(4000, 6000))
    except:
        print("ℹ️ स्टार्ट बटन नहीं मिला, शायद पहले से सर्फिंग चालू है")

    ads_done = 0
    max_ads = random.randint(5, 7)

    while ads_done < max_ads:
        ad_frame = page.query_selector("iframe#adFrame, iframe")
        if ad_frame:
            ad_url = ad_frame.get_attribute("src")
            print(f"📺 ऐड: {str(ad_url)[:60]}")
            wait_time = random.randint(18000, 35000)
            print(f"⏳ {wait_time//1000}s इंतज़ार...")
            page.wait_for_timeout(wait_time)
            ads_done += 1

            # अगला बटन ढूँढें, नहीं तो अपने आप बढ़ें
            try:
                next_btn = page.wait_for_selector("button:has-text('Next'), a:has-text('Next')", timeout=4000)
                next_btn.click()
                page.wait_for_timeout(random.randint(2000, 4000))
            except:
                page.wait_for_timeout(random.randint(3000, 6000))
        else:
            print("🔄 कोई ऐड फ्रेम नहीं, रिफ्रेश कर रहे हैं")
            page.reload()
            page.wait_for_timeout(random.randint(8000, 12000))
            if ads_done == 0:
                print("❌ शायद आज के ऐड खत्म")
                break

    print(f"🎯 कुल {ads_done} विज्ञापन देखे।")
    return ads_done

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = context.new_page()
        stealth_sync(page)  # <-- यहाँ stealth लगाया!

        if login(page):
            surf_ads(page)
        else:
            print("❌ लॉगिन नहीं हो पाया, रन रद्द।")

        browser.close()

if __name__ == "__main__":
    fly()
