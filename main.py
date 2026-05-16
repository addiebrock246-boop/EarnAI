import os
import time
import requests
from playwright.sync_api import sync_playwright

WALLET = os.environ.get("WALLET_ADDRESS", "0x123...")
HF_TOKEN = os.environ["HF_API_TOKEN"]

# Fast & free model — always ready, no cold start
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt, max_retries=3):
    """AI se suggestion lo, agar fail to wait karke retry"""
    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 80, "temperature": 0.7}
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            # Agar response JSON nahi hai, to text print karke wait
            if not response.text.strip():
                print(f"⚠️ Empty response, attempt {attempt+1}, retrying...")
                time.sleep(10)
                continue
            result = response.json()
            # Flan-T5 returns either list of dicts or plain dict
            if isinstance(result, list) and len(result) > 0:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                # shayad error object ho
                if "error" in result:
                    print(f"⏳ Model loading ya error: {result['error']}")
                    # Wait karega agle attempt tak
                else:
                    print(f"❓ Unexpected response: {result}")
                time.sleep(15)
        except Exception as e:
            print(f"❌ Attempt {attempt+1} failed: {e}")
            time.sleep(15)
    raise Exception("AI call failed after retries")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🌍 Visiting Google...")
        page.goto("https://www.google.com")
        title = page.title()
        print(f"📄 Page title: {title}")

        # Flan-T5 simple question format maangta hai (no special tags)
        prompt = f"Suggest one crypto earning task without KYC for today. Keep answer short."
        suggestion = ask_ai(prompt)
        print(f"🧠 AI suggestion: {suggestion}")

        browser.close()

if __name__ == "__main__":
    fly()
