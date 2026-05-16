import os
import time
import requests
from playwright.sync_api import sync_playwright

WALLET = os.environ.get("WALLET_ADDRESS", "0x123...")
HF_TOKEN = os.environ["HF_API_TOKEN"]
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ai(prompt, max_retries=3):
    # wait_for_model = True: API khud wait karegi model ready hone tak
    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 80, "temperature": 0.7},
        "options": {"wait_for_model": True, "use_cache": True}
    }
    for attempt in range(max_retries):
        try:
            # timeout 120 seconds set kiya, taki wait ke dauran connection na toote
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code != 200:
                print(f"⚠️ Status {response.status_code}: {response.text[:300]}")
                time.sleep(20)
                continue
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]["generated_text"]
            elif isinstance(result, dict):
                if "generated_text" in result:
                    return result["generated_text"]
                elif "error" in result:
                    print(f"⏳ Model error: {result['error']}")
                    time.sleep(20)
                    continue
            else:
                print(f"❓ Unexpected: {result}")
                time.sleep(20)
        except requests.exceptions.Timeout:
            print("⌛ Request timeout, retrying...")
            time.sleep(30)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(20)
    raise Exception("AI fail ho gaya, baad mein try karega")

def fly():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🌍 Visiting Google...")
        page.goto("https://www.google.com", timeout=30000)
        title = page.title()
        print(f"📄 Page title: {title}")

        prompt = "Suggest one crypto earning task without KYC for today. Keep answer short."
        suggestion = ask_ai(prompt)
        print(f"🧠 AI suggestion: {suggestion}")

        browser.close()

if __name__ == "__main__":
    fly()
