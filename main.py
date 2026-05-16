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

def print_page_info(page, step_name=""):
    """पेज की अहम जानकारी प्रिंट करो"""
    print(f"\n--- {step_name} ---")
    print(f"📍 URL: {page.url}")
    print(f"📄 टाइटल: {page.title()}")

    # क्या 'Logout' जैसा कुछ दिख रहा है? (लॉगिन चेक)
    logout_btn = page.query_selector("a:has-text('Logout'), button:has-text('Logout')")
    print(f"🔑 लॉगिन स्टेटस: {'लॉग्ड इन' if logout_btn else 'लॉग्ड आउट (या Logout बटन नहीं)'} ")

    # iframes गिनो
    iframes = page.query_selector_all("iframe")
    print(f"🖼️ iframes की संख्या: {len(iframes)}")
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src")
        print(f"   iframe {i+1}: src={src[:100] if src else 'none'}")

    # 'Start Surfing' बटन की मौजूदगी
    start_btn = page.query_selector("button:has-text('Start Surfing'), a:has-text('Start')")
    print(f"▶️ Start Surfing बटन: {'मिला' if start_btn else 'नहीं मिला'}")

    # पेज के टेक्स्ट का एक हिस्सा (500 अक्षर)
    body_text = page.inner_text("body")[:600]
    print(f"📝 पेज टेक्स्ट (शुरुआत):\n{body_text}")
    print("-" * 50)

def surf_ads(page):
    print("📡 सर्फ ऐड्स पेज पर जा रहे हैं...")
    page.goto("https://cointiply.com/surf-ads", timeout=30000)
    page.wait_for_timeout(random.randint(7000, 10000))
    print_page_info(page, "सर्फ ऐड्स पेज")

    # स्टार्ट बटन दबाने की कोशिश
    start_btn = page.query_selector("button:has-text('Start Surfing')")
    if start_btn:
        start_btn.click()
        print("✅ Start Surfing क्लिक किया")
        page.wait_for_timeout(5000)
        print_page_info(page, "Start क्लिक के बाद")

    # अब थोड़ी देर और रुककर iframes चेक करो
    for wait_attempt in range(3):
        print(f"\n⏳ {wait_attempt+1}वाँ इंतज़ार (10 सेकंड)...")
        page.wait_for_timeout(10000)
        print_page_info(page, f"इंतज़ार {wait_attempt+1} के बाद")

    # अगर iframes होते तो ऐड देखते, लेकिन हम सिर्फ जाँच रहे हैं
    print("🎯 डायग्नोस्टिक पूरा हुआ। ऊपर की जानकारी के आधार पर आगे बढ़ेंगे।")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # हम हेडलेस ही रखेंगे ताकि xvfb की ज़रूरत न पड़े
            args=["--no-sandbox", "--disable-dev-shm-usage"]
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
        """)

        print("🔐 कुकीज़ सेट करके लॉगिन...")
        page.goto("https://cointiply.com", timeout=30000)
        page.context.add_cookies(cookies)
        page.reload()
        page.wait_for_timeout(5000)
        print_page_info(page, "लॉगिन के बाद होम पेज")

        surf_ads(page)
        browser.close()

if __name__ == "__main__":
    fly()
