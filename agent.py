import os
import re
import json
import time
import traceback
from groq import Groq
from database import save_log

# ===== CLIENTS SETUP =====
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# IBM Watson NLU (will be used if credentials are set)
watson_available = False
try:
    from ibm_watson import NaturalLanguageUnderstandingV1
    from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions, KeywordsOptions, CategoriesOptions, EmotionOptions
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

    watson_api_key = os.environ.get("IBM_WATSON_API_KEY")
    watson_url = os.environ.get("IBM_WATSON_URL")

    if watson_api_key and watson_url:
        authenticator = IAMAuthenticator(watson_api_key)
        nlu = NaturalLanguageUnderstandingV1(
            version='2022-04-07',
            authenticator=authenticator
        )
        nlu.set_service_url(watson_url)
        watson_available = True
        print("✅ IBM Watson NLU connected successfully")
    else:
        print("⚠️ IBM Watson keys not found — running without Watson")
except Exception as e:
    print(f"⚠️ IBM Watson not available: {str(e)}")
    watson_available = False


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


# ===== IBM WATSON ANALYSIS =====
def watson_analyze(message_text):
    """Uses IBM Watson NLU to analyze sentiment, keywords and emotions"""
    if not watson_available:
        return None

    try:
        response = nlu.analyze(
            text=message_text,
            features=Features(
                sentiment=SentimentOptions(),
                keywords=KeywordsOptions(sentiment=True, limit=10),
                emotion=EmotionOptions(),
                categories=CategoriesOptions(limit=3)
            )
        ).get_result()

        # Extract useful info
        sentiment = response.get('sentiment', {}).get('document', {})
        emotion = response.get('emotion', {}).get('document', {}).get('emotion', {})
        keywords = response.get('keywords', [])
        categories = response.get('categories', [])

        # Build risk signals from Watson data
        watson_risk = 0
        watson_flags = []

        # Negative sentiment = suspicious
        sentiment_score = sentiment.get('score', 0)
        if sentiment_score < -0.3:
            watson_risk += 15
            watson_flags.append(f"Negative sentiment detected ({sentiment_score:.2f})")

        # High fear/disgust emotions = suspicious
        fear_score = emotion.get('fear', 0)
        if fear_score > 0.5:
            watson_risk += 20
            watson_flags.append(f"High fear emotion: {fear_score:.2f}")

        # Suspicious keywords
        scam_keywords = ['money', 'win', 'prize', 'click', 'verify', 'account', 'bank', 'otp', 'urgent']
        matched_keywords = [kw['text'] for kw in keywords if kw['text'].lower() in scam_keywords]
        if matched_keywords:
            watson_risk += len(matched_keywords) * 10
            watson_flags.append(f"Scam keywords detected: {', '.join(matched_keywords)}")

        return {
            "watson_risk_boost": min(watson_risk, 40),
            "watson_flags": watson_flags,
            "sentiment": sentiment.get('label', 'neutral'),
            "dominant_emotion": max(emotion, key=emotion.get) if emotion else "neutral",
            "top_keywords": [kw['text'] for kw in keywords[:5]],
            "categories": [c['label'] for c in categories[:2]]
        }

    except Exception as e:
        print(f"Watson analysis error: {str(e)}")
        return None


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
    steps.append({"step": 1, "title": "INITIAL PATTERN SCAN", "status": "running"})
    time.sleep(0.5)
    links, suspicious_links = extract_links(message_text)
    steps[0]["finding"] = f"Found {len(links)} link(s), {len(suspicious_links)} suspicious"
    steps[0]["status"] = "done"

    # Step 2 — Sender reputation
    steps.append({"step": 2, "title": "SENDER REPUTATION CHECK", "status": "running"})
    time.sleep(0.5)
    rep_score, rep_flags = check_sender_reputation(message_text)
    steps[1]["finding"] = f"Reputation score: {rep_score}% suspicious. {len(rep_flags)} flag(s)"
    steps[1]["status"] = "done"

    # Step 3 — IBM Watson Analysis (NEW!)
    watson_result = None
    if watson_available:
        steps.append({"step": 3, "title": "IBM WATSON NLU ANALYSIS", "status": "running"})
        time.sleep(0.5)
        watson_result = watson_analyze(message_text)
        if watson_result:
            steps[2]["finding"] = f"Sentiment: {watson_result['sentiment']} | Emotion: {watson_result['dominant_emotion']} | Risk boost: +{watson_result['watson_risk_boost']}%"
            steps[2]["status"] = "done"
        else:
            steps[2]["finding"] = "Watson analysis unavailable"
            steps[2]["status"] = "error"
        step_offset = 1
    else:
        step_offset = 0

    # Step 3/4 — Groq AI Deep Analysis
    steps.append({"step": 3 + step_offset, "title": "GROQ AI DEEP ANALYSIS", "status": "running"})

    prompt = f"""
    You are SafeNet, an expert AI cybersecurity agent detecting digital scams in India.

    Analyze this message thoroughly and return ONLY valid JSON:
    {{
        "risk_score": (0-100 integer),
        "threat_type": ("PHISHING" | "BANK FRAUD" | "FAKE JOB" | "LOTTERY SCAM" | "CREDENTIAL THEFT" | "IMPERSONATION" | "SAFE"),
        "reasoning": "2-3 lines of detailed analysis",
        "action": ("BLOCKED" | "WARNING" | "CLEAR"),
        "confidence": (0-100 integer),
        "red_flags": ["flag1", "flag2"],
        "recommendation": "What user should do"
    }}

    Message: \"\"\"{message_text}\"\"\"

    Return ONLY JSON. No preamble, no explanation, no markdown.
    """

    groq_success = False
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert. Respond in valid JSON only. No markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )

        result_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] Groq raw response: {result_text[:200]}")

        # Clean markdown if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        groq_success = True

        # Boost risk score with Watson data if available
        if watson_result:
            original_score = result['risk_score']
            result['risk_score'] = min(original_score + watson_result['watson_risk_boost'], 100)
            result['red_flags'] = result.get('red_flags', []) + watson_result['watson_flags']

        steps[-1]["finding"] = f"AI confidence: {result.get('confidence', 'N/A')}% | Threat: {result['threat_type']}"
        steps[-1]["status"] = "done"

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"[GROQ ERROR FULL]: {error_detail}")
        print(f"[GROQ ERROR SHORT]: {str(e)}")

        result = {
            "risk_score": 50,
            "threat_type": "UNKNOWN",
            "reasoning": f"AI Error: {str(e)[:100]}",
            "action": "WARNING",
            "confidence": 0,
            "red_flags": [f"Groq error: {str(e)[:80]}"],
            "recommendation": "Exercise caution with this message."
        }

        # If Watson succeeded, use its data even if Groq failed
        if watson_result:
            result['risk_score'] = min(50 + watson_result['watson_risk_boost'], 100)
            result['red_flags'] += watson_result['watson_flags']
            result['reasoning'] = f"Watson detected: sentiment={watson_result['sentiment']}, emotion={watson_result['dominant_emotion']}"

        steps[-1]["finding"] = f"Groq failed: {str(e)[:60]}"
        steps[-1]["status"] = "error"

    # Step 4/5 — Confidence breakdown
    steps.append({"step": len(steps) + 1, "title": "CONFIDENCE BREAKDOWN", "status": "running"})
    time.sleep(0.3)
    breakdown = get_confidence_breakdown(message_text, result)
    steps[-1]["finding"] = f"{len(breakdown)} risk factor(s) identified"
    steps[-1]["status"] = "done"

    # Step 5/6 — Final verdict
    steps.append({"step": len(steps) + 1, "title": "FINAL VERDICT", "status": "running"})
    time.sleep(0.3)
    engine = "Groq + Watson" if (groq_success and watson_available) else ("Watson Only" if watson_available else "Groq Only")
    steps[-1]["finding"] = f"Risk Score: {result['risk_score']}% — Action: {result['action']} [{engine}]"
    steps[-1]["status"] = "done"

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
