import os
import time
import random
from playwright.sync_api import sync_playwright

EMAIL = os.environ["COINTIPLY_EMAIL"]
PASSWORD = os.environ["COINTIPLY_PASSWORD"]

def login(page):
    print("🔐 लॉगिन पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/login", timeout=30000)
    page.wait_for_timeout(random.randint(4000, 6000))

    email_field = page.wait_for_selector(
        "input[name='email'], input[type='email']", timeout=10000
    )
    pass_field = page.wait_for_selector(
        "input[name='password'], input[type='password']", timeout=10000
    )
    email_field.fill(EMAIL)
    pass_field.fill(PASSWORD)
    print("📧 ईमेल/पासवर्ड भरे")

    pass_field.press("Enter")
    print("↩️ एंटर दबाया, इंतज़ार...")
    page.wait_for_timeout(random.randint(5000, 8000))

    login_btn = page.query_selector(
        "button:has-text('Login'), input[value='Login'], button[type='submit'], a:has-text('Login')"
    )
    if login_btn:
        try:
            login_btn.click()
            print("🔘 लॉगिन बटन क्लिक किया (दूसरा तरीका)")
            page.wait_for_timeout(random.randint(3000, 5000))
        except:
            print("⚠️ बटन क्लिक नहीं हो पाया, लेकिन एंटर ट्राई हो चुका")
    else:
        print("ℹ️ कोई भी लॉगिन बटन नहीं मिला, सिर्फ एंटर से कोशिश की")

    try:
        page.wait_for_selector(
            "a:has-text('Logout'), button:has-text('Logout'), .user-menu",
            timeout=20000
        )
        print("✅ लॉगिन सफल! (Logout दिखा)")
        return True
    except:
        print("❌ लॉगिन विफल – कैप्चा या गलत पासवर्ड")
        return False

def surf_ads(page):
    print("📡 सर्फ ऐड्स पर जा रहे हैं...")
    page.goto("https://cointiply.com/surf-ads", timeout=30000)
    page.wait_for_timeout(random.randint(5000, 8000))

    try:
        start_btn = page.wait_for_selector(
            "button:has-text('Start Surfing')", timeout=5000
        )
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

            try:
                next_btn = page.wait_for_selector(
                    "button:has-text('Next'), a:has-text('Next')", timeout=4000
                )
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
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)
        page.goto("https://cointiply.com", timeout=30000)
        page.wait_for_timeout(2000)

        if login(page):
            surf_ads(page)
        else:
            print("❌ लॉगिन नहीं हो पाया, रन रद्द।")

        browser.close()

if __name__ == "__main__":
    fly()
