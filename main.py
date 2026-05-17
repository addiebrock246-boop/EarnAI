import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

# ========== CONFIG ==========
SERPER_API_KEY = os.environ["SERPER_API_KEY"]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
WALLET = os.environ.get("WALLET_ADDRESS", "0x...")

# ========== AI: Groq (सबसे तेज़) → Gemini (बैकअप) → None ==========
def ask_ai_fast(prompt):
    # 1. Groq – रॉकेट की रफ़्तार, 5 सेकंड टाइमआउट
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

    # 2. Gemini – 5 सेकंड टाइमआउट
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

# ========== Serper सर्च ==========
def serper_search():
    queries = [
        "crypto earn task no KYC 2026",
        "web3 bounty for AI agent",
        "free crypto airdrop quest",
        "simple crypto task complete earn"
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
                    if link and link not in seen:
                        seen.add(link)
                        tasks.append({"url": link, "title": item.get("title", "")[:80]})
            elif resp.status_code == 429:
                print("   ⚠️ Quota खत्म"); break
        except Exception as e:
            print(f"   ❌ {e}")
        time.sleep(1)
    return tasks

# ========== AI से राय + Fallback ==========
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
                return decision.get("can_do", False), decision.get("action", "click")
        except:
            pass
    # Fallback: AI न बोले तो हर टास्क पर क्लिक + फ़ॉर्म
    return True, "click"

# ========== एक्ज़ीक्यूटर ==========
def execute_task(page, url, action):
    print(f"  🌐 {url[:60]}...")
    try:
        page.goto(url, timeout=10000)
        page.wait_for_timeout(1500)
        if action in ("click", "form"):
            btns = page.query_selector_all("button, a.btn, input[type='submit']")
            for btn in btns[:2]:
                try:
                    btn.click()
                    print("    🖱️ Clicked")
                    page.wait_for_timeout(500)
                except:
                    pass
            inputs = page.query_selector_all("input[type='text'], input[type='email']")
            for inp in inputs[:1]:
                try:
                    inp.fill(WALLET)
                    print(f"    📝 Filled {WALLET[:6]}...")
                except:
                    pass
            submit = page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                submit.click()
                print("    ✅ Submitted")
    except Exception as e:
        print(f"    ❌ {e}")

def fly():
    print("🌍 EarnAI – Groq+Gemini+Fallback जॉब हंटर 🚀")
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
            time.sleep(1)
        browser.close()
        print("🏁 मिशन पूरा।")

if __name__ == "__main__":
    fly()
