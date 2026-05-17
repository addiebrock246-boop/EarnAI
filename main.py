import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")

def ask_ai_fast(prompt):
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"messages": [{"role": "user", "content": prompt}], "model": "llama-3.3-70b-versatile", "max_tokens": 150},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass
    if GEMINI_API_KEY:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            pass
    return None

def serper_search():
    # सीधे प्लेटफ़ॉर्म के टास्क पेज ढूँढो
    queries = [
        "site:app.layer3.xyz quest",
        "site:zealy.io quest crypto",
        "site:app.dework.xyz task web3",
        "site:galxe.com campaign",
        "site:questn.com task",
        "site:intract.io quest",
        "free crypto task platform 2026",
        "simple crypto task complete earn Satoshi"
    ]
    tasks = []
    seen = set()
    for q in queries:
        print(f"🔍 Serper: '{q}'")
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5},
                timeout=10
            )
            if resp.status_code == 200:
                items = resp.json().get("organic", [])
                print(f"   ↳ {len(items)} लिंक")
                for item in items:
                    link = item.get("link")
                    # सिर्फ काम के लिंक लो (कोई youtube, reddit नहीं)
                    if link and link not in seen and "youtube.com" not in link and "reddit.com" not in link:
                        seen.add(link)
                        tasks.append({"url": link, "title": item.get("title", "")[:80]})
            elif resp.status_code == 429:
                print("   ⚠️ Quota खत्म"); break
        except Exception as e:
            print(f"   ❌ {e}")
        time.sleep(1)
    return tasks

def evaluate_task_with_fallback(task):
    prompt = f"""Task URL: {task['url']}
Task title: {task['title']}
Can an AI agent do this with only browser automation (click/type)?
Reply with JSON: {{"can_do": true/false, "action": "click"/"form"/"other", "reason": "short"}}
If unsure, just say false."""
    ai_response = ask_ai_fast(prompt)
    if ai_response:
        try:
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            if json_start != -1:
                decision = json.loads(ai_response[json_start:json_end])
                action = decision.get("action", "click")
                print(f"    🤖 AI: {decision.get('reason', '')}")
                return True, action
        except:
            pass
    return True, "click"

def execute_task(page, url, action):
    print(f"  🌐 {url[:70]}...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)

        # स्मार्ट बटन सर्च
        keywords = ["claim", "earn", "roll", "start", "free", "get", "receive", "quest", "participate", "join"]
        for word in keywords:
            btn = page.query_selector(f"button:has-text('{word}'), a:has-text('{word}'), input[value*='{word}' i]")
            if btn:
                try:
                    btn.click()
                    print(f"    🖱️ '{word}' बटन क्लिक किया")
                    page.wait_for_timeout(2000)
                    return
                except:
                    pass

        # वॉलेट / ईमेल फ़ील्ड
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name*='wallet'], input[name*='address']")
        for inp in inputs[:2]:
            try:
                inp.fill(WALLET)
                print(f"    📝 {WALLET[:6]}... भरा")
                page.wait_for_timeout(1000)
            except:
                pass

        # सबमिट बटन
        submit = page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            try:
                submit.click()
                print("    ✅ सबमिट किया")
                page.wait_for_timeout(2000)
            except:
                pass
    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – Direct Platform जॉब हंटर 🚀")
    tasks = serper_search()
    print(f"\n🎯 {len(tasks)} टास्क मिले। पहले 5 पर कोशिश।\n")
    if not tasks:
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        for i, task in enumerate(tasks[:5]):
            print(f"[{i+1}/5]")
            can_do, action = evaluate_task_with_fallback(task)
            if can_do:
                execute_task(page, task["url"], action)
            else:
                print("  ❌ AI ने मना कर दिया।")
            time.sleep(3)
        browser.close()
        print("🏁 मिशन पूरा।")

if __name__ == "__main__":
    fly()
