import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")
AI_URL = "https://models.inference.ai.azure.com/chat/completions"
AI_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def ask_ai(prompt):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a crypto task evaluator. Reply ONLY with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 250
    }
    for attempt in range(3):
        try:
            resp = requests.post(AI_URL, headers=AI_HEADERS, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                time.sleep(5)
        except:
            time.sleep(5)
    return ""

def serper_search():
    """Serper API से Google जैसे नतीजे लाओ — बिल्कुल फ्री!"""
    queries = [
        "crypto earn task no KYC 2026",
        "web3 bounty for AI agent",
        "free crypto airdrop quest",
        "simple crypto task complete earn"
    ]
    tasks = []
    seen_urls = set()

    for q in queries:
        print(f"🔍 Serper Search: '{q}'")
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("organic", [])
                print(f"   ↳ {len(items)} लिंक मिले")
                for item in items:
                    link = item.get("link")
                    title = item.get("title", "")
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        tasks.append({"url": link, "title": title[:80]})
            else:
                print(f"   ❌ Error: {resp.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    return tasks

def evaluate_task(task):
    prompt = f"""Analyze this crypto task:
URL: {task['url']}
Title: {task['title']}
Can an AI agent complete this using ONLY browser automation?
Reply in JSON: {{"can_do": true/false, "action": "click"/"form"/"other", "reason": "short"}}"""

    response = ask_ai(prompt)
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except:
        pass
    return {"can_do": False, "reason": "parse error"}

def execute_task(page, task_url, action):
    print(f"  🛠️ Executing: {task_url}")
    try:
        page.goto(task_url, timeout=20000)
        page.wait_for_timeout(5000)
        if action == "click":
            btns = page.query_selector_all("button, a.btn, input[type='submit']")
            for btn in btns[:3]:
                try:
                    btn.click()
                    print("    ✅ Clicked")
                    page.wait_for_timeout(2000)
                except:
                    pass
        elif action == "form":
            inputs = page.query_selector_all("input[type='text'], input[type='email']")
            for inp in inputs[:2]:
                try:
                    inp.fill(WALLET)
                    print(f"    ✅ Filled wallet")
                    page.wait_for_timeout(2000)
                except:
                    pass
            submit = page.query_selector("button[type='submit']")
            if submit:
                submit.click()
                print("    ✅ Submitted")
                page.wait_for_timeout(3000)
    except Exception as e:
        print(f"    ❌ Error: {e}")

def fly():
    print("🌍 EarnAI - Serper Job Hunter शुरू!")
    tasks = serper_search()
    print(f"\n🎯 कुल {len(tasks)} tasks मिले\n")
    if not tasks:
        print("कोई टास्क नहीं मिला।")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        completed = 0
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] {task['url'][:60]}...")
            decision = evaluate_task(task)
            if decision.get("can_do"):
                print(f"  ✅ AI: कर सकते हैं ({decision.get('reason', '')})")
                execute_task(page, task["url"], decision.get("action", "click"))
                completed += 1
            else:
                print(f"  ❌ छोड़ा ({decision.get('reason', '')})")
            time.sleep(2)
        browser.close()
        print(f"\n🏁 मिशन खत्म! {completed}/{len(tasks)} पर कोशिश।")

if __name__ == "__main__":
    fly()
