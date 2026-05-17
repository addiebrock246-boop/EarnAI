import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")
AI_URL = "https://models.inference.ai.azure.com/chat/completions"
AI_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ========== TRUSTED JOB PLATFORMS (scrape या API) ==========
PLATFORMS = [
    {
        "name": "Layer3",
        "url": "https://app.layer3.xyz/quests?type=all&status=active",
        "method": "scrape",  # Playwright से खोलकर टास्क लिंक निकालेंगे
        "selector": "a[href*='/quest/']"
    },
    {
        "name": "Zealy",
        "url": "https://zealy.io/c/explore",  # सार्वजनिक क्वेस्ट
        "method": "scrape",
        "selector": "a[href*='/quest/']"
    },
    {
        "name": "Dework",
        "url": "https://app.dework.xyz/explore?type=all",
        "method": "scrape",
        "selector": "a[href*='/task/']"
    },
    # और प्लेटफ़ॉर्म जोड़ सकते हैं
]

# ========== GITHUB MODELS AI CALL ==========
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

# ========== PLATFORM SCANNER ==========
def scan_platforms(context):
    all_tasks = []
    for plat in PLATFORMS:
        print(f"🌐 Scanning {plat['name']}...")
        try:
            page = context.new_page()
            page.goto(plat["url"], timeout=30000)
            page.wait_for_timeout(5000)
            # टास्क लिंक ढूँढ़ो
            links = page.query_selector_all(plat["selector"])
            print(f"   ↳ {len(links)} potential tasks found")
            for link in links:
                href = link.get_attribute("href")
                if href:
                    # पूरा URL बनाओ अगर रिश्तेदार हो
                    if href.startswith("/"):
                        base = plat["url"].split("/")[0] + "//" + plat["url"].split("/")[2]
                        href = base + href
                    all_tasks.append({
                        "platform": plat["name"],
                        "url": href,
                        "title": link.inner_text().strip() or href.split("/")[-1]
                    })
            page.close()
        except Exception as e:
            print(f"   ❌ Error: {e}")
        time.sleep(2)
    return all_tasks

# ========== AI EVALUATOR ==========
def evaluate_task(task):
    prompt = f"""Analyze this crypto task:
Platform: {task['platform']}
URL: {task['url']}
Title: {task['title']}

Can an AI agent complete this using only browser automation (clicking, typing, visiting pages)? 
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

# ========== TASK EXECUTOR ==========
def execute_task(page, task):
    print(f"  🛠️ Executing: {task['url']}")
    try:
        page.goto(task['url'], timeout=20000)
        page.wait_for_timeout(5000)
        action = task.get("action", "click")
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
                    print(f"    ✅ Filled: {WALLET[:10]}...")
                    page.wait_for_timeout(2000)
                except:
                    pass
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                submit.click()
                print("    ✅ Submitted")
                page.wait_for_timeout(3000)
        else:
            print("    ⚠️ Unknown action")
    except Exception as e:
        print(f"    ❌ Error: {e}")

# ========== MAIN ==========
def fly():
    print("🌍 EarnAI Multi-Platform Job Hunter शुरू!")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context()
        tasks = scan_platforms(context)
        print(f"\n🎯 कुल {len(tasks)} tasks मिले")
        
        completed = 0
        page = context.new_page()
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] {task['platform']}: {task['title'][:50]}...")
            decision = evaluate_task(task)
            if decision.get("can_do"):
                print(f"  ✅ AI: कर सकते हैं ({decision.get('reason', '')})")
                task["action"] = decision.get("action", "click")
                execute_task(page, task)
                completed += 1
            else:
                print(f"  ❌ छोड़ा ({decision.get('reason', '')})")
            time.sleep(2)
        page.close()
        browser.close()
        print(f"\n🏁 मिशन ख़त्म! {completed}/{len(tasks)} पर कोशिश।")

if __name__ == "__main__":
    fly()
