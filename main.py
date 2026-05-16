import os
import requests
from playwright.sync_api import sync_playwright

WALLET = os.environ.get("WALLET_ADDRESS", "0x123...")
HF_TOKEN = os.environ["HF_API_TOKEN"]
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt):
    """Mistral AI se free suggestion lo"""
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 80, "temperature": 0.7}
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    result = response.json()
    if isinstance(result, list) and len(result) > 0:
        return result[0]["generated_text"].strip()
    else:
        raise Exception(f"AI error: {result}")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🌍 Visiting Google...")
        page.goto("https://www.google.com")
        title = page.title()
        print(f"📄 Page title: {title}")

        prompt = (
            f"[INST] Current website title: '{title}'. "
            "Mere bot ka mission hai daily crypto tasks dhundhna bina KYC ke. "
            "Aaj ke liye ek short crypto earning idea suggest karo (1 line). [/INST]"
        )
        suggestion = ask_ai(prompt)
        print(f"🧠 AI suggestion: {suggestion}")

        browser.close()

if __name__ == "__main__":
    fly()
