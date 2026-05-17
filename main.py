import os
import json
import time
import requests
from googlesearch import search
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")
AI_URL = "https://models.inference.ai.azure.com/chat/completions"
AI_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def ask_ai(prompt):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a crypto task evaluator. Reply ONLY with valid JSON, no other text."},
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
                print(f"⚠️ AI Error {resp.status_code}, retry {attempt+1}")
                time.sleep(5)
        except Exception as e:
            print(f"❌ AI Exception: {e}")
            time.sleep(5)
    return ""

def google_job_search():
    queries = [
        "crypto earn task no KYC 2026",
        "web3 bounty for AI agent",
        "free crypto airdrop quest",
        "simple crypto task complete earn"
    ]
    tasks = []
    seen_urls = set()
    for q in queries:
        print(f"🔍 Google Search: '{q}'")
        try:
            # असली ब्राउज़र जैसा user-agent
            results = search(q, num_results=5, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            count = 0
            for url in results:
                count += 1
                if url not in seen_urls:
                    seen_urls.add(url)
                    tasks.append({
                        "url": url,
                        "title": url.split("//")[-1].split("/")[0]
                    })
                time.sleep(2)
            print(f"   ↳ {count} लिंक मिले")
        except Exception as e:
            print(f"❌ Search error: {e}")
    return tasks

def evaluate_task(task):
    prompt = f"""Analyze this potential crypto earning task:
URL: {task['url']}
Title: {task['title']}

Can an AI bot complete this task using ONLY browser automation (clicking, typing, visiting URLs)? 
Reply in VALID JSON format exactly like this example:
{{"can_do": true, "action": "click", "reason": "Claim button present"}}
or
{{"can_do": false, "reason": "Requires KYC or complex captcha"}}

The "action" field can be "click", "form", or "other"."""
    
    response = ask_ai(prompt)
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
        else:
            return {"can_do": False, "reason": "AI response not JSON"}
    except:
        return {"can_do": False, "reason": "Parse error"}

def execute_task(page, task_url, action):
    print(f"  🛠️ Automating: {task_url}")
    try:
        page.goto(task_url, timeout=20000)
        page.wait_for_timeout(5000)
        
        if action == "click":
            clickable = page.query_selector_all("button, a.btn, input[type='submit'], a[href*='claim']")
            if clickable:
                for elem in clickable[:3]:
                    try:
                        elem.click()
                        print("    ✅ Clicked something")
                        page.wait_for_timeout(3000)
                    except:
                        pass
            else:
                print("    ❌ No clickable element found")
                
        elif action == "form":
            inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name='address']")
            if inputs:
                for inp in inputs[:2]:
                    try:
                        inp.fill(WALLET)
                        print(f"    ✅ Filled: {WALLET[:10]}...")
                        page.wait_for_timeout(2000)
                    except:
                        pass
                submit_btn = page.query_selector("button[type='submit'], input[type='submit']")
                if submit_btn:
                    try:
                        submit_btn.click()
                        print("    ✅ Submitted form")
                        page.wait_for_timeout(3000)
                    except:
                        pass
            else:
                print("    ❌ No form inputs found")
        else:
            print("    ⚠️ Unknown action, just visiting")
            
    except Exception as e:
        print(f"    ❌ Execution error: {e}")

def fly():
    print("🌍 EarnAI Google Job Hunter शुरू!")
    tasks = google_job_search()
    print(f"\n🎯 कुल {len(tasks)} potential tasks मिले\n")
    if not tasks:
        print("कोई टास्क नहीं मिला, अगले रन तक अलविदा।")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        completed = 0
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] {task['url'][:70]}...")
            decision = evaluate_task(task)
            if decision.get("can_do"):
                print(f"  ✅ AI: कर सकते हैं! ({decision.get('reason', '')})")
                action = decision.get("action", "click")
                execute_task(page, task["url"], action)
                completed += 1
            else:
                print(f"  ❌ AI: छोड़ो ({decision.get('reason', '')})")
            time.sleep(3)
        browser.close()
        print(f"\n🏁 मिशन ख़त्म! {completed}/{len(tasks)} टास्क पर कोशिश की गई।")

if __name__ == "__main__":
    fly()
