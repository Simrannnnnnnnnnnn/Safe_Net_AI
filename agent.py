import os
from groq import Groq
import json
from database import save_log

# Groq client setup
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def analyze_message(message_text, source="MANUAL SCAN"):
    
    prompt = f"""
    You are SafeNet, an AI cybersecurity agent specialized in detecting scams.
    
    Analyze this message carefully and return ONLY a JSON response with these exact fields:
    {{
        "risk_score": (number between 0-100),
        "threat_type": (one of: "PHISHING", "BANK FRAUD", "FAKE JOB", "LOTTERY SCAM", "CREDENTIAL THEFT", "SAFE"),
        "reasoning": (2-3 lines explaining why this score),
        "action": (one of: "BLOCKED", "WARNING", "CLEAR")
    }}
    
    Rules:
    - risk_score 0-29 = CLEAR (safe message)
    - risk_score 30-69 = WARNING (suspicious)
    - risk_score 70-100 = BLOCKED (definite scam)
    
    Message to analyze:
    \"\"\"{message_text}\"\"\"
    
    Return ONLY the JSON. No extra text.
    """
    
    try:
        # Groq API call
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a cybersecurity expert. Always respond in valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Response parse karo
        result_text = response.choices[0].message.content.strip()
        
        # JSON clean karo agar backticks hain toh
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        
        # Database mein save karo
        save_log(
            source=source,
            message=message_text[:200],  # first 200 chars save karo
            risk_score=result["risk_score"],
            threat_type=result["threat_type"],
            reasoning=result["reasoning"],
            action_taken=result["action"]
        )
        
        return result
        
    except json.JSONDecodeError:
        # Agar JSON parse na ho toh default return karo
        return {
            "risk_score": 50,
            "threat_type": "UNKNOWN",
            "reasoning": "Could not analyze message properly. Please try again.",
            "action": "WARNING"
        }
    
    except Exception as e:
        return {
            "risk_score": 0,
            "threat_type": "ERROR",
            "reasoning": f"Error occurred: {str(e)}",
            "action": "CLEAR"
        }


def get_risk_level(score):
    if score >= 70:
        return "CRITICAL", "🚨"
    elif score >= 30:
        return "SUSPICIOUS", "⚠️"
    else:
        return "SAFE", "✅"
