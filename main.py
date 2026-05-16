import os
import json
import time
import random
from playwright.sync_api import sync_playwright

# कुकीज़ GitHub Secret से लोड
COOKIES_JSON = os.environ["COINTIPLY_COOKIES"]
cookies = json.loads(COOKIES_JSON)

def surf_ads(page):
    print("📡 सीधे सर्फ ऐड्स पेज पर जा रहे हैं (कुकीज़ से लॉगिन)...")
    page.goto("https://cointiply.com/surf-ads", timeout=30000)
    page.wait_for_timeout(random.randint(5000, 8000))

    # स्टार्ट सर्फिंग बटन
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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🔐 कुकीज़ सेट करके ऑटो-लॉगिन...")
        page.goto("https://cointiply.com", timeout=30000)
        page.context.add_cookies(cookies)  # एक्सपोर्ट की हुई कुकीज़
        page.reload()
        page.wait_for_timeout(random.randint(3000, 5000))

        surf_ads(page)
        browser.close()

if __name__ == "__main__":
    fly()
