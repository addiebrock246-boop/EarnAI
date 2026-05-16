import os
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# ==== CONFIG ====
WALLET = os.environ.get("WALLET_ADDRESS", "0x123...")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

def ask_ai(prompt):
    """Gemini 1.5 Flash se free suggestion"""
    response = model.generate_content(prompt)
    return response.text.strip()

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🌍 Visiting Google...")
        page.goto("https://www.google.com")
        title = page.title()
        print(f"📄 Page title: {title}")

        # AI Brain sochta hai
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
