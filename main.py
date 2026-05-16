import os
import time
from google import genai
from playwright.sync_api import sync_playwright

WALLET = os.environ.get("WALLET_ADDRESS", "0x123...")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def ask_ai(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",  # 1.5 Flash, zyada free quota
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                wait = 10
                print(f"⏳ Quota finish, {wait}s wait karta hoon...")
                time.sleep(wait)
            else:
                raise e
    raise Exception("AI call 3 baar fail ho gaya.")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🌍 Visiting Google...")
        page.goto("https://www.google.com")
        title = page.title()
        print(f"📄 Page title: {title}")

        prompt = (
            f"Current website title: '{title}'. "
            "Mere bot ka mission hai daily crypto tasks dhundhna bina KYC ke. "
            "Aaj ke liye ek short crypto earning idea suggest karo (1 line)."
        )
        suggestion = ask_ai(prompt)
        print(f"🧠 Gemini ka suggestion: {suggestion}")

        browser.close()

if __name__ == "__main__":
    fly()
