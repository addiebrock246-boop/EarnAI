import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")
AI_URL = "https://text.pollinations.ai/openai"

def ask_ai(prompt):
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a crypto task evaluator. Reply ONLY with valid JSON, no other text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 250
    }
    for attempt in range(3):
        try:
            resp = requests.post(AI_URL, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"].strip()
                elif "content" in data:
                    return data["content"].strip()
                else:
                    print(f"   ⚠️ Unexpected: {str(data)[:100]}")
            else:
                print(f"   ⚠️ AI Error {resp.status_code}")
            time.sleep(3)
        except Exception as e:
            print(f"   ❌ AI Exception: {e}")
            time.sleep(3)
    return ""

def serper_search():
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
            elif resp.status_code == 429:
                print("   ⚠️ Serper quota खत्म, अगले महीने रीसेट।")
                break
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

Can an AI agent complete this using ONLY browser automation (clicking, typing, visiting pages)?
Reply in VALID JSON format exactly like this example:
{{"can_do": true, "action": "click", "reason": "Claim button present"}}
or
{{"can_do": false, "reason": "Requires KYC or complex captcha"}}

The "action" field can be "click", "form", or "other"."""
    
    response = ask_ai(prompt)
    print(f"    🤖 AI RAW: {response[:200]}")
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
        else:
            return {"can_do": False, "reason": "AI response not JSON"}
    except:
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
                    print("    ✅ Clicked something")
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
                print("    ✅ Submitted form")
                page.wait_for_timeout(3000)
    except Exception as e:
        print(f"    ❌ Execution error: {e}")

def fly():
    print("🌍 EarnAI Job Hunter (Serper + Pollinations.AI) शुरू!")
    tasks = serper_search()
    print(f"\n🎯 कुल {len(tasks)} potential tasks मिले\n")
    if not tasks:
        print("कोई टास्क नहीं मिला।")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        completed = 0
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] {task['url'][:70]}...")
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
