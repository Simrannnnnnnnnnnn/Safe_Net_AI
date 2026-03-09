import os
import re
import json
import time
from groq import Groq
from database import save_log

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ===== LINK EXTRACTOR =====
def extract_links(text):
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    shorteners = ['bit.ly', 'tinyurl', 'short.link', 'goo.gl', 't.co', 'ow.ly', 'rb.gy']
    links = re.findall(pattern, text)
    suspicious_links = []
    for link in links:
        for s in shorteners:
            if s in link:
                suspicious_links.append(link)
    return links, suspicious_links


# ===== SENDER REPUTATION CHECK =====
def check_sender_reputation(sender_text):
    suspicious_domains = [
        'xyz', 'tk', 'ml', 'ga', 'cf', 'gq',
        'win', 'prize', 'claim', 'free', 'lucky',
        'secure-', 'verify-', 'update-', 'alert-'
    ]
    score = 0
    flags = []

    for domain in suspicious_domains:
        if domain in sender_text.lower():
            score += 20
            flags.append(f"Suspicious domain pattern: '{domain}'")

    if re.search(r'\d{4,}', sender_text):
        score += 15
        flags.append("Excessive numbers in sender ID")

    if sender_text.count('-') > 2:
        score += 10
        flags.append("Multiple hyphens in domain")

    return min(score, 100), flags


# ===== CONFIDENCE BREAKDOWN =====
def get_confidence_breakdown(message, result):
    breakdown = []

    urgency_words = ['urgent', 'immediately', 'expire', 'last chance', 'hurry', 'now', 'today only']
    urgency_count = sum(1 for w in urgency_words if w in message.lower())
    if urgency_count > 0:
        breakdown.append({
            "factor": "Urgency Tactics",
            "score": min(urgency_count * 25, 100),
            "detail": f"{urgency_count} urgency trigger(s) found"
        })

    money_patterns = [r'rs\.?\s*\d+', r'inr\s*\d+', r'\$\d+', r'lakh', r'crore', r'win.*money', r'earn.*daily']
    money_count = sum(1 for p in money_patterns if re.search(p, message.lower()))
    if money_count > 0:
        breakdown.append({
            "factor": "Financial Bait",
            "score": min(money_count * 30, 100),
            "detail": f"{money_count} financial trigger(s) detected"
        })

    personal_patterns = ['bank account', 'otp', 'password', 'pin', 'aadhar', 'pan card', 'cvv']
    personal_count = sum(1 for p in personal_patterns if p in message.lower())
    if personal_count > 0:
        breakdown.append({
            "factor": "Personal Data Request",
            "score": min(personal_count * 40, 100),
            "detail": f"Requesting: {', '.join([p for p in personal_patterns if p in message.lower()])}"
        })

    links, suspicious = extract_links(message)
    if suspicious:
        breakdown.append({
            "factor": "Suspicious Links",
            "score": 85,
            "detail": f"{len(suspicious)} shortened/suspicious URL(s) found"
        })
    elif links:
        breakdown.append({
            "factor": "Links Present",
            "score": 30,
            "detail": f"{len(links)} link(s) found — verify before clicking"
        })

    return breakdown


# ===== MULTI STEP REASONING =====
def multi_step_reasoning(message_text):
    steps = []

    # Step 1 — Initial scan
    steps.append({
        "step": 1,
        "title": "INITIAL PATTERN SCAN",
        "status": "running"
    })
    time.sleep(0.5)

    links, suspicious_links = extract_links(message_text)
    step1_finding = f"Found {len(links)} link(s), {len(suspicious_links)} suspicious"
    steps[0]["finding"] = step1_finding
    steps[0]["status"] = "done"

    # Step 2 — Sender reputation
    steps.append({
        "step": 2,
        "title": "SENDER REPUTATION CHECK",
        "status": "running"
    })
    time.sleep(0.5)

    rep_score, rep_flags = check_sender_reputation(message_text)
    steps[1]["finding"] = f"Reputation score: {rep_score}% suspicious. {len(rep_flags)} flag(s)"
    steps[1]["status"] = "done"

    # Step 3 — AI Deep Analysis
    steps.append({
        "step": 3,
        "title": "GROQ AI DEEP ANALYSIS",
        "status": "running"
    })

    prompt = f"""
    You are SafeNet, an expert AI cybersecurity agent detecting digital scams in India.

    Analyze this message thoroughly and return ONLY valid JSON:
    {{
        "risk_score": (0-100),
        "threat_type": ("PHISHING" | "BANK FRAUD" | "FAKE JOB" | "LOTTERY SCAM" | "CREDENTIAL THEFT" | "IMPERSONATION" | "SAFE"),
        "reasoning": "2-3 lines of detailed analysis",
        "action": ("BLOCKED" | "WARNING" | "CLEAR"),
        "confidence": (0-100),
        "red_flags": ["flag1", "flag2"],
        "recommendation": "What user should do"
    }}

    Message: \"\"\"{message_text}\"\"\"

    Return ONLY JSON. No extra text.
    """

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert. Respond in valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )

        result_text = response.choices[0].message.content.strip()

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        steps[2]["finding"] = f"AI confidence: {result.get('confidence', 'N/A')}% | Threat: {result['threat_type']}"
        steps[2]["status"] = "done"

    except Exception as e:
        result = {
            "risk_score": 50,
            "threat_type": "UNKNOWN",
            "reasoning": "Analysis incomplete. Please retry.",
            "action": "WARNING",
            "confidence": 0,
            "red_flags": [],
            "recommendation": "Exercise caution with this message."
        }
        steps[2]["finding"] = "AI analysis failed — using fallback"
        steps[2]["status"] = "error"

    # Step 4 — Confidence breakdown
    steps.append({
        "step": 4,
        "title": "CONFIDENCE BREAKDOWN",
        "status": "running"
    })
    time.sleep(0.3)

    breakdown = get_confidence_breakdown(message_text, result)
    steps[3]["finding"] = f"{len(breakdown)} risk factor(s) identified"
    steps[3]["status"] = "done"

    # Step 5 — Final verdict
    steps.append({
        "step": 5,
        "title": "FINAL VERDICT",
        "status": "running"
    })
    time.sleep(0.3)

    steps[4]["finding"] = f"Risk Score: {result['risk_score']}% — Action: {result['action']}"
    steps[4]["status"] = "done"

    # Save to DB
    save_log(
        source="MANUAL SCAN",
        message=message_text[:200],
        risk_score=result['risk_score'],
        threat_type=result['threat_type'],
        reasoning=result['reasoning'],
        action_taken=result['action']
    )

    return result, steps, breakdown


# ===== MAIN ANALYZE FUNCTION =====
def analyze_message(message_text, source="MANUAL SCAN"):
    result, steps, breakdown = multi_step_reasoning(message_text)
    return result, steps, breakdown


def get_risk_level(score):
    if score >= 70:
        return "CRITICAL", "🚨"
    elif score >= 30:
        return "SUSPICIOUS", "⚠️"
    else:
        return "SAFE", "✅"
