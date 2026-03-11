<div align="center">

<img src="https://img.shields.io/badge/SafeNet-AI%20Cyber%20Security-3dffa0?style=for-the-badge&logo=shield&logoColor=white"/>

# 🛡️ SAFENET
### AI-Powered Agentic Cyber Security Agent

[![Live Demo](https://img.shields.io/badge/🌐%20Live%20Demo-safenet--ai.streamlit.app-3dffa0?style=for-the-badge)](https://safenet-ai.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3--70B-orange?style=for-the-badge)](https://groq.com)
[![IBM Watson](https://img.shields.io/badge/IBM-Watson%20NLU-052FAD?style=for-the-badge&logo=ibm)](https://ibm.com/watson)

> **IBM PBL Project** | Agentic AI that autonomously detects, analyzes, and blocks digital scams across WhatsApp, Telegram, Gmail & SMS — without any human intervention.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why Agentic AI?](#-why-agentic-ai)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [IBM Watson Integration](#-ibm-watson-integration)
- [Project Structure](#-project-structure)
- [Team](#-team)

---

## 🔍 Overview

**SafeNet** is an Agentic AI cybersecurity agent that protects users from digital scams, phishing attacks, and fraud messages. Unlike traditional rule-based systems, SafeNet uses a multi-step AI reasoning chain combining **Groq LLaMA 3.3-70B** and **IBM Watson NLU** to autonomously:

- 🔍 **Detect** — Scan messages from WhatsApp, Telegram, Gmail, and SMS
- 🧠 **Analyze** — Multi-step AI reasoning with confidence scoring
- ⚡ **Act** — Auto-block senders, send warnings, notify users
- 📊 **Report** — Dashboard with threat intelligence and trend analysis

---

## 🤖 Why Agentic AI?

SafeNet qualifies as **Agentic AI** because it demonstrates all four core agentic properties:

| Property | SafeNet Implementation |
|----------|----------------------|
| **Perception** | Reads emails via Gmail API, accepts message input from multiple sources |
| **Reasoning** | 6-step multi-model reasoning chain (Pattern → Watson NLU → Groq LLaMA 3) |
| **Decision Making** | Autonomously decides: `BLOCKED` / `WARNING` / `CLEAR` — no human input |
| **Action** | Auto-blocks senders, sends warning emails, notifies users, logs incidents |

> *"SafeNet perceives threats, reasons through evidence, makes decisions, and takes real-world actions — completely autonomously."*

---

## ✨ Features

### 🔍 Multi-Source Scanning
- **WhatsApp** — Paste suspicious messages with sender number
- **Telegram** — Scan forwarded channel/group messages  
- **Gmail Auto-Scanner** — One-click connect, inbox scanned automatically
- **SMS / Manual** — Any suspicious text message

### 🧠 Dual AI Engine
- **Groq LLaMA 3.3-70B** — Deep contextual threat analysis
- **IBM Watson NLU** — Sentiment, emotion, keyword & category analysis
- Combined risk score with up to **+40% Watson boost**

### ⚡ Agentic Auto-Actions
- 🚫 **Auto-block** critical senders via Gmail filter
- ⚠️ **Warning email** sent to fake/scam sender automatically
- 📧 **User notification** with full AI analysis report
- 📝 **Incident logging** with timestamp and full reasoning

### 📊 Threat Intelligence Dashboard
- Real-time stats: Scanned / Blocked / Warned / Safe
- Source breakdown: WhatsApp | Telegram | Gmail | Other
- Risk score trends and threat type distribution charts

### 📋 Investigation Logs
- Separate log tables per source (WhatsApp, Telegram, Gmail)
- Risk score, threat type, and action history
- Full audit trail for all scans

---

## 🛠️ Tech Stack

```
┌─────────────────────────────────────────────────────┐
│                    SAFENET v4.0                      │
├─────────────────────────────────────────────────────┤
│  Frontend     │  Streamlit (Python)                  │
│  AI Engine 1  │  Groq API — LLaMA 3.3-70B           │
│  AI Engine 2  │  IBM Watson NLU (Lite Plan)          │
│  Email API    │  Gmail API (OAuth 2.0 + PKCE)        │
│  Database     │  SQLite (local persistence)          │
│  Hosting      │  Streamlit Cloud                     │
│  Auth         │  Google OAuth 2.0                    │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
User Input (WhatsApp / Telegram / Gmail / SMS)
           │
           ▼
┌─────────────────────┐
│   Pattern Scanner   │  ← Step 1: Keywords, links, red flags
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Sender Reputation  │  ← Step 2: Domain/sender trust check
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  IBM Watson NLU     │  ← Step 3: Sentiment, emotion, categories
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Groq LLaMA 3.3-70B │  ← Step 4: Deep contextual AI analysis
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Confidence Score   │  ← Step 5: Multi-factor breakdown (0-100%)
└────────┬────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         AGENTIC DECISION ENGINE              │
│   BLOCKED (≥75%) │ WARNING (≥30%) │ CLEAR   │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│            AUTO-ACTIONS                      │
│  • Block sender in Gmail                     │
│  • Send warning email to fake sender         │
│  • Notify user with full AI report           │
│  • Log incident to database                  │
└─────────────────────────────────────────────┘
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- Groq API Key (free at [console.groq.com](https://console.groq.com))
- IBM Watson NLU API Key (free Lite plan)
- Google Cloud Project with Gmail API enabled

### Clone & Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/safe_net_ai.git
cd safe_net_ai

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in your API keys in .env
```

### Run Locally

```bash
streamlit run app.py
```

---

## 🔑 Configuration

### Environment Variables

Create a `.env` file or add to **Streamlit Secrets**:

```toml
# Groq AI
GROQ_API_KEY = "gsk_your_groq_api_key"

# IBM Watson NLU
IBM_WATSON_API_KEY = "your_watson_api_key"
IBM_WATSON_URL = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/your_id"

# Gmail OAuth
GMAIL_CLIENT_ID = "your_client_id.apps.googleusercontent.com"
GMAIL_CLIENT_SECRET = "GOCSPX-your_client_secret"
GMAIL_REDIRECT_URI = "https://safenet-ai.streamlit.app"
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials (Web Application type)
4. Add authorized redirect URI: `https://safenet-ai.streamlit.app`
5. Publish OAuth consent screen

---

## 🚀 Usage

### 1. Manual Message Scan
```
SCAN tab → Select source (WhatsApp/Telegram/Gmail/SMS)
→ Paste suspicious message → Click "INITIATE THREAT SCAN"
→ View AI analysis, risk score, and agentic actions
```

### 2. Gmail Auto-Scanner
```
GMAIL tab → Click "CONNECT GMAIL →"
→ Select Google account → Allow permissions
→ SafeNet automatically scans inbox
→ Results sorted by risk score (highest first)
→ Agentic actions taken automatically for threats
```

### 3. WhatsApp Scanner
```
WHATSAPP tab → Enter sender number
→ Paste message → Click "SCAN WHATSAPP MESSAGE"
→ View WhatsApp-style bubble with AI verdict
```

---

## 📊 Risk Score System

| Score | Level | Action |
|-------|-------|--------|
| 75–100% | 🚨 CRITICAL | Auto-blocked + Warning sent + User notified |
| 30–74% | ⚠️ WARNING | User notified + Sender watchlisted |
| 0–29% | ✅ SAFE | Logged as safe, no action needed |

---

## 🔬 IBM Watson Integration

SafeNet uses IBM Watson Natural Language Understanding for enhanced threat detection:

```python
# Watson analyzes:
features = Features(
    sentiment=SentimentOptions(),      # Urgency/pressure detection
    emotion=EmotionOptions(),          # Fear/anger manipulation
    keywords=KeywordsOptions(),        # Scam keyword extraction
    categories=CategoriesOptions()     # Content category classification
)

# Watson risk boost: adds up to +40% to base Groq score
# High fear + negative sentiment = scam indicator
```

**Watson NLU provides:**
- Sentiment analysis (positive/negative/neutral)
- Emotion detection (joy, fear, anger, disgust, sadness)
- Keyword extraction with relevance scoring
- Content category classification

---

## 📁 Project Structure

```
safe_net_ai/
├── app.py              # Main Streamlit application
├── agent.py            # Agentic AI reasoning engine
├── gmail_utils.py      # Gmail API + OAuth integration
├── database.py         # SQLite database handler
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (local)
└── README.md           # This file
```

---

## 📦 Requirements

```
streamlit
groq
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
python-dotenv
ibm-watson
ibm-cloud-sdk-core
pandas
requests
```

---

## 🏆 IBM PBL Context

This project was built as part of the **IBM Project Based Learning (PBL)** program through **CSRBOX Institution**.

**Key IBM Technologies Used:**
- ✅ IBM Watson Natural Language Understanding (NLU)
- ✅ IBM Cloud (Lite Plan)
- ✅ IBM SkillsBuild certification

**Agentic AI Justification for IBM PBL:**
SafeNet demonstrates all pillars of Agentic AI — autonomous perception, multi-step reasoning, independent decision-making, and real-world action execution — making it a true AI agent rather than a simple classifier.

---

## 👥 Team

| Role | Details |
|------|---------|
| **Project** | SafeNet — AI Cyber Security Agent |
| **Institution** | CSRBOX (IBM PBL Partner) |
| **Program** | IBM Project Based Learning |
| **Tech Stack** | Groq + IBM Watson + Streamlit + Gmail API |

---

## 🔗 Links

| Resource | Link |
|----------|------|
| 🌐 Live App | [safenet-ai.streamlit.app](https://safenet-ai.streamlit.app) |
| 💻 GitHub | [safe_net_ai](https://github.com/YOUR_USERNAME/safe_net_ai) |
| 🤖 Groq Console | [console.groq.com](https://console.groq.com) |
| 🔬 IBM Watson | [ibm.com/watson](https://www.ibm.com/watson) |

---

<div align="center">

**Built with ❤️ for IBM PBL**

`SafeNet v4.0` · `Agentic AI` · `Groq LLaMA 3` · `IBM Watson NLU` · `Gmail API`

⭐ **Star this repo if SafeNet helped you!** ⭐

</div>
