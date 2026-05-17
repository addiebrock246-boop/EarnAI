import os
import json
import time
import requests
from googlesearch import search
from playwright.sync_api import sync_playwright

# ========== CONFIGURATION ==========
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]          # GitHub Actions में अपने-आप मिलता है
WALLET = os.environ.get("WALLET_ADDRESS", "0x...") # तुम्हारा crypto wallet
AI_URL = "https://models.inference.ai.azure.com/chat/completions"
AI_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ========== GITHUB MODELS AI CALL ==========
def ask_ai(prompt):
    """GitHub Models (GPT-4o) को सवाल भेजो और JSON जवाब लो"""
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
    return ""  # तीन बार फ़ेल होने पर खाली

# ========== GOOGLE JOB SEARCH ==========
def google_job_search():
    """4 अलग-अलग कीवर्ड से Google सर्च करो और लिंक इकट्ठा करो"""
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
            # num=5 की जगह stop=5 करो (यही बदलाव है)
            for url in search(q, stop=5, user_agent="Mozilla/5.0"):
                if url not in seen_urls:
                    seen_urls.add(url)
                    tasks.append({
                        "url": url,
                        "title": url.split("//")[-1].split("/")[0]  # डोमेन नाम टाइटल की जगह
                    })
                time.sleep(2)  # Google को गुस्सा न दिलाएँ
        except Exception as e:
            print(f"❌ Search error: {e}")
    return tasks

# ========== AI TASK EVALUATOR ==========
def evaluate_task(task):
    """AI को टास्क का URL और टाइटल दो, वो बताएगा कि कर सकते हैं या नहीं"""
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
        # कभी-कभी AI के जवाब में एक्स्ट्रा टेक्स्ट होता है, JSON हिस्सा निकालो
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
        else:
            return {"can_do": False, "reason": "AI response not JSON"}
    except:
        return {"can_do": False, "reason": "Parse error"}

# ========== TASK EXECUTOR (BROWSER AUTOMATION) ==========
def execute_task(page, task_url, action):
    """AI के बताए अनुसार बटन क्लिक करो या फ़ॉर्म भरो"""
    print(f"  🛠️ Automating: {task_url}")
    try:
        page.goto(task_url, timeout=20000)
        page.wait_for_timeout(5000)
        
        if action == "click":
            # हर तरह के बटन / लिंक ढूँढ़ो और क्लिक करो
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
            # वॉलेट एड्रेस या ईमेल डालने की कोशिश करो
            inputs = page.query_selector_all("input[type='text'], input[type='email'], input[name='address']")
            if inputs:
                for inp in inputs[:2]:
                    try:
                        inp.fill(WALLET)
                        print(f"    ✅ Filled: {WALLET[:10]}...")
                        page.wait_for_timeout(2000)
                    except:
                        pass
                # सबमिट बटन ढूँढ़ो
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

# ========== MAIN FUNCTION ==========
def fly():
    print("🌍 EarnAI Google Job Hunter शुरू!")
    
    # 1. Google से टास्क खोजो
    tasks = google_job_search()
    print(f"\n🎯 कुल {len(tasks)} potential tasks मिले\n")
    
    if not tasks:
        print("कोई टास्क नहीं मिला, अगले रन तक अलविदा।")
        return
    
    # 2. Playwright शुरू करो
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        
        completed = 0
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{len(tasks)}] {task['url'][:70]}...")
            
            # 3. AI से राय लो
            decision = evaluate_task(task)
            if decision.get("can_do"):
                print(f"  ✅ AI: कर सकते हैं! ({decision.get('reason', '')})")
                action = decision.get("action", "click")
                # 4. अंजाम दो
                execute_task(page, task["url"], action)
                completed += 1
            else:
                print(f"  ❌ AI: छोड़ो ({decision.get('reason', '')})")
            
            time.sleep(3)  # हर टास्क के बीच थोड़ा आराम
        
        browser.close()
        print(f"\n🏁 मिशन ख़त्म! {completed}/{len(tasks)} टास्क पर कोशिश की गई।")

if __name__ == "__main__":
    fly()
