import os
import time
import random
from playwright.sync_api import sync_playwright

EMAIL = os.environ["COINTIPLY_EMAIL"]
PASSWORD = os.environ["COINTIPLY_PASSWORD"]

def login(page):
    """Cointiply पर ईमेल/पासवर्ड से लॉगिन करें"""
    print("🔐 लॉगिन पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/login", timeout=30000)
    page.wait_for_timeout(random.randint(2000, 4000))

    # ईमेल और पासवर्ड फील्ड खोजें
    email_field = page.query_selector("input[type='email'], input[name='email']")
    pass_field = page.query_selector("input[type='password'], input[name='password']")

    if not email_field or not pass_field:
        # शायद पहले से लॉगिन है (अगर कुकी सेव थी तो)
        print("ℹ️ लॉगिन फील्ड नहीं मिले, शायद पहले से सेशन है")
        page.goto("https://cointiply.com")
        page.wait_for_timeout(3000)
        return True

    email_field.fill(EMAIL)
    pass_field.fill(PASSWORD)
    print("📧 ईमेल/पासवर्ड भरे")

    # लॉगिन बटन दबाओ (आमतौर पर "Login" या "Sign In")
    login_btn = page.query_selector("button:has-text('Login'), button:has-text('Sign In'), input[type='submit']")
    if login_btn:
        login_btn.click()
        print("🔘 लॉगिन बटन दबाया")
        page.wait_for_timeout(random.randint(4000, 7000))
        # चेक करें कि लॉगिन सफल हुआ या कैप्चा/एरर आया
        if "logout" in page.content().lower() or "dashboard" in page.url:
            print("✅ लॉगिन सफल")
            return True
        else:
            print("⚠️ लॉगिन में कुछ दिक्कत, कैप्चा या गलत पासवर्ड")
            return False
    else:
        print("❌ लॉगिन बटन नहीं मिला")
        return False

def surf_ads(page):
    """सर्फ ऐड्स करें"""
    print("📡 सर्फ ऐड्स पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/surf-ads", timeout=30000)
    page.wait_for_timeout(random.randint(4000, 7000))

    # स्टार्ट सर्फिंग बटन (अगर हो)
    start_btn = page.query_selector("button:has-text('Start Surfing'), a:has-text('Start')")
    if start_btn:
        start_btn.click()
        print("✅ स्टार्ट सर्फिंग क्लिक किया")
        page.wait_for_timeout(random.randint(4000, 6000))

    ads_done = 0
    max_ads = random.randint(5, 7)

    while ads_done < max_ads:
        # विज्ञापन फ्रेम ढूँढें
        ad_frame = page.query_selector("iframe#adFrame, iframe")
        if ad_frame:
            ad_url = ad_frame.get_attribute("src")
            print(f"📺 ऐड: {str(ad_url)[:50]}...")
            wait = random.randint(18000, 40000)
            print(f"⏳ {wait//1000} सेकंड इंतज़ार")
            page.wait_for_timeout(wait)
            ads_done += 1
            # अगला बटन
            next_btn = page.query_selector("button:has-text('Next'), a:has-text('Next')")
            if next_btn:
                next_btn.click()
                page.wait_for_timeout(random.randint(2000, 4000))
            else:
                page.wait_for_timeout(random.randint(3000, 6000))
        else:
            print("🔄 कोई ऐड फ्रेम नहीं, रिफ्रेश कर रहे हैं")
            page.reload()
            page.wait_for_timeout(random.randint(8000, 12000))
            if ads_done == 0:
                print("❌ शायद आज के ऐड खत्म")
                break

    print(f"🎯 {ads_done} विज्ञापन देखे गए।")
    return ads_done

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        if login(page):
            surf_ads(page)
        else:
            print("❌ लॉगिन विफल, रन रद्द। अगले रन में फिर कोशिश होगी।")

        browser.close()

if __name__ == "__main__":
    fly()
