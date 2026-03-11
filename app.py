import streamlit as st
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from database import init_db, get_all_logs, get_stats
from agent import analyze_message, get_risk_level

load_dotenv()
init_db()

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="SafeNet — AI Cyber Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS =====
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@300;400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

:root {
    --bg-deep:    #070711;
    --bg-mid:     #0e0e1f;
    --bg-card:    rgba(255,255,255,0.04);
    --border:     rgba(255,255,255,0.08);
    --mint:       #3dffa0;
    --cyan:       #00c8ff;
    --purple:     #9b6dff;
    --danger:     #ff4d6d;
    --warn:       #ffb830;
    --safe:       #3dffa0;
    --text:       rgba(255,255,255,0.88);
    --muted:      rgba(255,255,255,0.35);
}

/* BASE */
.stApp {
    background: var(--bg-deep) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Scanline overlay */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0a0a18 !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--muted) !important; }
section[data-testid="stSidebar"] h3 {
    color: var(--mint) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 3px !important;
}
section[data-testid="stSidebar"] .stSuccess p { color: var(--mint) !important; }

/* METRICS */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--mint) !important;
    border-radius: 10px !important;
    padding: 18px !important;
    transition: transform 0.2s !important;
}
div[data-testid="metric-container"]:hover { transform: translateY(-3px) !important; }
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    color: var(--mint) !important;
    font-size: 42px !important;
    letter-spacing: 2px !important;
}
[data-testid="stMetricLabel"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    color: var(--muted) !important;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    color: var(--muted) !important;
    background: transparent !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--mint) !important;
    border-bottom: 2px solid var(--mint) !important;
    background: rgba(61,255,160,0.04) !important;
}

/* BUTTONS */
.stButton > button {
    background: transparent !important;
    color: var(--mint) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 3px !important;
    border: 1px solid rgba(61,255,160,0.3) !important;
    padding: 14px !important;
    border-radius: 6px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(61,255,160,0.08) !important;
    border-color: var(--mint) !important;
    color: #fff !important;
    box-shadow: 0 0 20px rgba(61,255,160,0.15) !important;
}

/* TEXT AREA */
.stTextArea textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    caret-color: var(--mint) !important;
}
.stTextArea textarea:focus {
    border-color: rgba(61,255,160,0.4) !important;
    box-shadow: 0 0 15px rgba(61,255,160,0.07) !important;
}
.stTextArea textarea::placeholder { color: rgba(255,255,255,0.18) !important; }
.stTextArea label { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }

/* TEXT INPUT */
.stTextInput input {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 6px !important;
}
.stTextInput label { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }

/* SELECT/TOGGLE */
.stToggle label p { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }
.stSelectbox label { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.03) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

/* HEADINGS */
h1,h2,h3,h4 { font-family: 'DM Sans', sans-serif !important; color: var(--text) !important; }
.stMarkdown h4 { color: var(--mint) !important; font-size: 16px !important; letter-spacing: 3px !important; font-family: 'JetBrains Mono', monospace !important; }
.stMarkdown p { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; }
.stMarkdown strong { color: #fff !important; }

/* ALERTS */
[data-testid="stAlert"] {
    background: rgba(61,255,160,0.04) !important;
    border: 1px solid rgba(61,255,160,0.12) !important;
    border-left: 3px solid var(--mint) !important;
    border-radius: 8px !important;
}
[data-testid="stAlert"] p { color: var(--mint) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 11px !important; }

/* PROGRESS */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--mint), var(--cyan)) !important;
}

/* DATAFRAME */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 8px !important; overflow: hidden !important; }

/* CAPTIONS */
.stCaption, caption { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; }

/* DIVIDER */
hr { border-color: var(--border) !important; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(61,255,160,0.25); border-radius: 4px; }

/* CUSTOM COMPONENTS */
.sn-header {
    padding: 48px 0 36px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.sn-header::before {
    content: '';
    position: absolute;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(61,255,160,0.06) 0%, transparent 65%);
    top: -300px; right: -100px;
    pointer-events: none;
}
.sn-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 80px;
    letter-spacing: 16px;
    background: linear-gradient(135deg, #3dffa0 0%, #00c8ff 50%, #9b6dff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.sn-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 6px;
    margin-top: 10px;
}
.sn-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(61,255,160,0.06);
    border: 1px solid rgba(61,255,160,0.18);
    padding: 5px 16px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: var(--mint);
    letter-spacing: 2px;
    margin-top: 16px;
}
.sn-dot { width: 6px; height: 6px; background: var(--mint); border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }

.sn-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sn-section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

.sn-score-ring {
    text-align: center;
    padding: 24px;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 12px;
}

.sn-step {
    padding: 10px 14px;
    margin: 5px 0;
    border-left: 2px solid;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    border-radius: 0 6px 6px 0;
    line-height: 1.7;
}
.sn-step-ok  { border-color: var(--mint);   background: rgba(61,255,160,0.04);  color: var(--mint);   }
.sn-step-err { border-color: var(--danger);  background: rgba(255,77,109,0.04);  color: var(--danger); }
.sn-step-run { border-color: var(--warn);    background: rgba(255,184,48,0.04);  color: var(--warn);   }

.sn-verdict {
    padding: 16px 20px;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    line-height: 1.8;
    margin: 12px 0;
    border-left: 3px solid;
}
.sn-verdict-safe   { background: rgba(61,255,160,0.05);  border-color: var(--safe);   color: rgba(255,255,255,0.8); }
.sn-verdict-warn   { background: rgba(255,184,48,0.05);  border-color: var(--warn);   color: rgba(255,255,255,0.8); }
.sn-verdict-danger { background: rgba(255,77,109,0.06);  border-color: var(--danger); color: rgba(255,255,255,0.8); animation: glow-danger 2s infinite; }
@keyframes glow-danger { 0%,100%{box-shadow:0 0 8px rgba(255,77,109,0.1);} 50%{box-shadow:0 0 18px rgba(255,77,109,0.2);} }

.sn-action-panel {
    background: rgba(255,77,109,0.04);
    border: 1px solid rgba(255,77,109,0.15);
    border-radius: 10px;
    padding: 20px;
    margin-top: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
}
.sn-monitor-panel {
    background: rgba(255,184,48,0.04);
    border: 1px solid rgba(255,184,48,0.15);
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--warn);
    line-height: 2;
}

.sn-breakdown-bar {
    margin-bottom: 14px;
}
.sn-breakdown-bar .label-row {
    display: flex;
    justify-content: space-between;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    margin-bottom: 5px;
}
.sn-breakdown-bar .track {
    height: 4px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
}
.sn-breakdown-bar .fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.8s ease;
}
.sn-breakdown-bar .detail {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: var(--muted);
    margin-top: 4px;
}

.sn-wa-bubble {
    background: rgba(37,211,102,0.07);
    border: 1px solid rgba(37,211,102,0.15);
    border-radius: 4px 14px 14px 14px;
    padding: 12px 16px;
    max-width: 75%;
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    color: var(--text);
    margin: 10px 0 20px;
    line-height: 1.6;
}

.sn-source-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 1px;
    font-weight: 700;
}
.tag-wa   { background: rgba(37,211,102,0.12); color: #25d366; border: 1px solid rgba(37,211,102,0.2); }
.tag-tg   { background: rgba(0,136,204,0.12);  color: #0088cc; border: 1px solid rgba(0,136,204,0.2); }
.tag-gm   { background: rgba(234,67,53,0.12);  color: #ea4335; border: 1px solid rgba(234,67,53,0.2); }
.tag-sms  { background: rgba(155,109,255,0.12);color: #9b6dff; border: 1px solid rgba(155,109,255,0.2); }
.tag-bulk { background: rgba(255,184,48,0.12); color: #ffb830; border: 1px solid rgba(255,184,48,0.2); }

.sn-log-row {
    display: grid;
    grid-template-columns: 160px 90px 1fr 80px 140px 100px;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    align-items: center;
    transition: background 0.15s;
}
.sn-log-row:hover { background: rgba(255,255,255,0.02); }
.sn-log-header {
    display: grid;
    grid-template-columns: 160px 90px 1fr 80px 140px 100px;
    gap: 12px;
    padding: 10px 16px;
    border-bottom: 2px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: var(--muted);
}

.sn-gmail-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin: 10px 0;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
}
.sn-gmail-card:hover {
    border-color: rgba(61,255,160,0.2);
    background: rgba(61,255,160,0.02);
}
.sn-risk-pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
}
.pill-safe   { background: rgba(61,255,160,0.1);  color: var(--mint);   border: 1px solid rgba(61,255,160,0.2);  }
.pill-warn   { background: rgba(255,184,48,0.1);   color: var(--warn);   border: 1px solid rgba(255,184,48,0.2);  }
.pill-danger { background: rgba(255,77,109,0.1);   color: var(--danger); border: 1px solid rgba(255,77,109,0.2);  }

.sn-actions-taken {
    background: rgba(61,255,160,0.03);
    border: 1px solid rgba(61,255,160,0.1);
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--mint);
    line-height: 2;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)


# ===== HEADER =====
st.markdown("""
<div class="sn-header">
  <div style="text-align:center;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
    color:rgba(255,255,255,0.15);letter-spacing:8px;margin-bottom:16px;">
      ◈ &nbsp; AUTHORIZED ACCESS ONLY &nbsp; ◈
    </div>
    <div class="sn-logo">SAFENET</div>
    <div class="sn-tagline">AI CYBER SECURITY AGENT &nbsp;·&nbsp; GROQ LLAMA 3 &nbsp;·&nbsp; IBM WATSON NLU</div>
    <div style="margin-top:18px;">
      <span class="sn-badge"><span class="sn-dot"></span> PROTECTION ACTIVE</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ===== STATS =====
stats = get_stats()
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("🔍 Total Scanned",   stats['total'])
with c2: st.metric("🚫 Threats Blocked", stats['blocked'])
with c3: st.metric("⚠️ Warnings Issued", stats['warned'])
with c4: st.metric("✅ Safe Messages",    stats['safe'])
st.divider()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ AGENT CONFIG")
    st.text_input("Agent ID", value="SN-7X4K-9021", disabled=True)
    auto_block  = st.toggle("Auto-Block Critical",    value=True)
    deep_scan   = st.toggle("Deep Link Analysis",      value=True)
    show_steps  = st.toggle("Show Reasoning Chain",    value=True)
    auto_notify = st.toggle("Auto Gmail Notifications",value=True)
    st.divider()
    st.markdown("### 📊 THREAT RATE")
    if stats['total'] > 0:
        pct = round((stats['blocked'] / stats['total']) * 100)
        st.progress(pct / 100, text=f"Threat Rate: {pct}%")
    else:
        st.progress(0.0, text="Threat Rate: 0%")
    st.divider()
    st.success("● PROTECTION ACTIVE")
    st.divider()
    st.markdown("### 🔌 AI ENGINES")
    st.markdown("""
    <div style='font-family:JetBrains Mono,monospace;font-size:9px;line-height:2.2;color:rgba(255,255,255,0.4);'>
    ✅ &nbsp;Groq Llama 3.3-70B<br>
    ✅ &nbsp;IBM Watson NLU<br>
    ✅ &nbsp;Pattern Engine v3<br>
    ✅ &nbsp;Sender Reputation DB
    </div>
    """, unsafe_allow_html=True)


# ===== TABS =====
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 SCAN",
    "📱 WHATSAPP",
    "✈️ TELEGRAM",
    "📧 GMAIL",
    "📊 DASHBOARD",
    "📋 LOGS"
])


# ===== HELPERS =====
def score_color(s):
    return "#ff4d6d" if s >= 70 else "#ffb830" if s >= 30 else "#3dffa0"

def score_pill_cls(s):
    return "pill-danger" if s >= 70 else "pill-warn" if s >= 30 else "pill-safe"

def source_tag_html(src):
    src_upper = src.upper()
    if "WHATSAPP" in src_upper:
        return f'<span class="sn-source-tag tag-wa">WhatsApp</span>'
    elif "TELEGRAM" in src_upper:
        return f'<span class="sn-source-tag tag-tg">Telegram</span>'
    elif "GMAIL" in src_upper or "EMAIL" in src_upper:
        return f'<span class="sn-source-tag tag-gm">Gmail</span>'
    elif "BULK" in src_upper:
        return f'<span class="sn-source-tag tag-bulk">Bulk</span>'
    else:
        return f'<span class="sn-source-tag tag-sms">Manual</span>'


def show_steps_ui(steps):
    st.markdown("""
    <div class="sn-section-label" style="margin-top:24px;">
      ⚡ &nbsp; AGENTIC REASONING CHAIN
    </div>
    """, unsafe_allow_html=True)
    for step in steps:
        cls     = "sn-step-ok" if step['status'] == 'done' else "sn-step-err"
        icon    = "✓" if step['status'] == 'done' else "✗"
        finding = step.get('finding', '...')
        st.markdown(f"""
        <div class="sn-step {cls}">
          {icon} &nbsp;<b>STEP {step['step']}</b> — {step['title']}<br>
          <span style="opacity:0.65;">→ {finding}</span>
        </div>
        """, unsafe_allow_html=True)


def show_breakdown_ui(breakdown):
    if not breakdown:
        return
    st.markdown("""
    <div class="sn-section-label" style="margin-top:24px;">
      📊 &nbsp; CONFIDENCE BREAKDOWN
    </div>
    """, unsafe_allow_html=True)
    for item in breakdown:
        s = item['score']
        c = score_color(s)
        st.markdown(f"""
        <div class="sn-breakdown-bar">
          <div class="label-row">
            <span style="color:rgba(255,255,255,0.7);">{item['factor']}</span>
            <span style="color:{c};">{s}%</span>
          </div>
          <div class="track"><div class="fill" style="width:{s}%;background:{c};"></div></div>
          <div class="detail">→ {item['detail']}</div>
        </div>
        """, unsafe_allow_html=True)


def show_result_full(result, steps, breakdown, source_label="MANUAL SCAN"):
    score     = result['risk_score']
    level, em = get_risk_level(score)
    confidence= result.get('confidence', 'N/A')
    red_flags = result.get('red_flags', [])
    rec       = result.get('recommendation', '')
    col_c     = score_color(score)

    st.markdown("---")
    st.markdown("""<div class="sn-section-label">📊 &nbsp; ANALYSIS RESULT</div>""", unsafe_allow_html=True)

    col_score, col_info = st.columns([1, 2])

    with col_score:
        st.markdown(f"""
        <div class="sn-score-ring">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:72px;
          color:{col_c};text-shadow:0 0 30px {col_c}80;line-height:1;">
            {score}%
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
          color:{col_c};letter-spacing:3px;margin-top:8px;">
            {em} {level}
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
          color:var(--muted);margin-top:6px;">
            AI CONFIDENCE: {confidence}%
          </div>
          <div style="margin-top:10px;">{source_tag_html(source_label)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"**Threat Type:** &nbsp;`{result['threat_type']}`")
        st.markdown(f"**Action:** &nbsp;`{result['action']}`")
        st.progress(score / 100)

        if score >= 70:
            cls = "sn-verdict-danger"
            header = "🚨 CRITICAL THREAT DETECTED"
        elif score >= 30:
            cls = "sn-verdict-warn"
            header = "⚠️ SUSPICIOUS MESSAGE"
        else:
            cls = "sn-verdict-safe"
            header = "✅ MESSAGE APPEARS SAFE"

        st.markdown(f"""
        <div class="sn-verdict {cls}">
          <b style="letter-spacing:2px;">{header}</b><br><br>
          {result['reasoning']}<br><br>
          <span style="opacity:0.7;">💡 {rec}</span>
        </div>
        """, unsafe_allow_html=True)

        if red_flags:
            st.markdown("**🚩 Red Flags Detected:**")
            for flag in red_flags:
                st.markdown(f"- `{flag}`")

    # Steps
    if show_steps:
        show_steps_ui(steps)

    # Breakdown
    show_breakdown_ui(breakdown)

    # Auto action block
    if score >= 75 and auto_block:
        st.markdown("""
        <div class="sn-action-panel">
          <div style="color:var(--danger);letter-spacing:3px;font-size:11px;margin-bottom:14px;">
            ⚡ AGENTIC AUTO-RESPONSE INITIATED
          </div>
        """, unsafe_allow_html=True)

        actions = [
            "Threat signature stored in database",
            "Sender flagged as HIGH RISK",
            "Auto-trash filter created",
            "Incident logged with timestamp"
        ]
        for i, act in enumerate(actions):
            with st.spinner(f"Processing {i+1}/4..."):
                time.sleep(0.5)
            st.markdown(f"""
            <div style="color:var(--warn);font-size:10px;padding:4px 0;">
              ✅ STEP {i+1} — {act}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:14px;padding:12px;
        background:rgba(255,77,109,0.06);border-left:3px solid var(--danger);
        color:var(--danger);font-size:10px;border-radius:0 6px 6px 0;">
          🛡️ VERDICT: Sender permanently blocked. Risk: {score}%
        </div>
        </div>
        """, unsafe_allow_html=True)

    elif score >= 30:
        st.markdown("""
        <div class="sn-monitor-panel">
          ⚠️ AGENTIC AI — MONITORING MODE<br>
          <span style="color:var(--muted);">
          → Sender added to watchlist<br>
          → Next message will be auto-scanned<br>
          → User alert activated
          </span>
        </div>
        """, unsafe_allow_html=True)


# ===== TAB 1 — SCAN =====
with tab1:
    st.markdown("""<div class="sn-section-label">🔍 &nbsp; PASTE SUSPICIOUS MESSAGE</div>""", unsafe_allow_html=True)

    source_type = st.selectbox(
        "Message Source",
        ["📱 WhatsApp", "✈️ Telegram", "📧 Email/Gmail", "💬 SMS", "🌐 Other"],
        label_visibility="visible"
    )

    msg_input = st.text_area(
        "Message Content",
        placeholder="Paste any suspicious message here — WhatsApp, SMS, email, scam text...\n\nExample: 'Congratulations! You won Rs.50,000. Claim now: bit.ly/xyz123'",
        height=160,
        label_visibility="collapsed"
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        scan_btn = st.button("⚡ INITIATE THREAT SCAN", use_container_width=True)
    with col_b:
        clear_btn = st.button("🗑️ CLEAR", use_container_width=True)

    if scan_btn and msg_input.strip():
        src_map = {
            "📱 WhatsApp":   "WHATSAPP",
            "✈️ Telegram":   "TELEGRAM",
            "📧 Email/Gmail":"GMAIL",
            "💬 SMS":        "SMS",
            "🌐 Other":      "MANUAL SCAN"
        }
        src = src_map.get(source_type, "MANUAL SCAN")

        with st.spinner("🤖 Agentic AI analyzing..."):
            result, steps, breakdown = analyze_message(msg_input, source=src)

        show_result_full(result, steps, breakdown, source_label=src)

    elif scan_btn:
        st.warning("⚠️ Pehle message paste karo!")


# ===== TAB 2 — WHATSAPP =====
with tab2:
    st.markdown("""
    <div class="sn-section-label">📱 &nbsp; WHATSAPP MESSAGE ANALYZER</div>
    <div style="background:rgba(37,211,102,0.05);border:1px solid rgba(37,211,102,0.12);
    border-radius:8px;padding:12px 16px;margin-bottom:20px;
    font-family:'JetBrains Mono',monospace;font-size:10px;color:#25d366;letter-spacing:1px;">
      📲 Paste sender number + WhatsApp message for targeted analysis
    </div>
    """, unsafe_allow_html=True)

    wa_sender = st.text_input("Sender Number/Name", placeholder="+91-98765-43210 or Unknown Contact")
    wa_msg    = st.text_area("WhatsApp Message", placeholder="Paste message here...", height=130)

    if st.button("📱 SCAN WHATSAPP MESSAGE", use_container_width=True):
        if wa_msg.strip():
            st.markdown(f"""
            <div style="padding:16px 0;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
              color:var(--muted);margin-bottom:8px;letter-spacing:2px;">
                FROM: {wa_sender or 'Unknown'}
              </div>
              <div class="sn-wa-bubble">{wa_msg}</div>
            </div>
            """, unsafe_allow_html=True)

            full_text = f"Sender: {wa_sender}\nMessage: {wa_msg}"
            with st.spinner("🤖 Scanning..."):
                result, steps, breakdown = analyze_message(full_text, source=f"WHATSAPP: {wa_sender}")
            show_result_full(result, steps, breakdown, "WHATSAPP")
        else:
            st.warning("⚠️ Message paste karo!")


# ===== TAB 3 — TELEGRAM =====
with tab3:
    st.markdown("""
    <div class="sn-section-label">✈️ &nbsp; TELEGRAM MESSAGE ANALYZER</div>
    <div style="background:rgba(0,136,204,0.05);border:1px solid rgba(0,136,204,0.12);
    border-radius:8px;padding:12px 16px;margin-bottom:20px;
    font-family:'JetBrains Mono',monospace;font-size:10px;color:#0088cc;letter-spacing:1px;">
      ✈️ Telegram channel/group messages, forwarded scam content
    </div>
    """, unsafe_allow_html=True)

    tg_sender  = st.text_input("Telegram Channel/Username", placeholder="@unknown_channel or +91-XXXXX")
    tg_message = st.text_area("Telegram Message", placeholder="Paste forwarded Telegram message here...", height=130)

    if st.button("✈️ SCAN TELEGRAM MESSAGE", use_container_width=True):
        if tg_message.strip():
            full_text = f"Telegram from: {tg_sender}\nMessage: {tg_message}"
            with st.spinner("🤖 Scanning Telegram message..."):
                result, steps, breakdown = analyze_message(full_text, source=f"TELEGRAM: {tg_sender}")
            show_result_full(result, steps, breakdown, "TELEGRAM")
        else:
            st.warning("⚠️ Message paste karo!")


# ===== TAB 4 — GMAIL =====
with tab4:
    st.markdown("""<div class="sn-section-label">📧 &nbsp; GMAIL AUTO-SCANNER</div>""", unsafe_allow_html=True)

    # Check Gmail connection
    gmail_connected = st.session_state.get('gmail_token') is not None

    if not gmail_connected:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;
        background:rgba(234,67,53,0.04);border:1px solid rgba(234,67,53,0.12);
        border-radius:12px;margin:20px 0;">
          <div style="font-size:40px;margin-bottom:16px;">📧</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
          color:rgba(255,255,255,0.5);letter-spacing:2px;">
            GMAIL NOT CONNECTED
          </div>
          <div style="font-family:'DM Sans',sans-serif;font-size:13px;
          color:rgba(255,255,255,0.4);margin-top:8px;">
            Connect your Gmail account to enable auto-scanning
          </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            from gmail_utils import get_auth_url, get_credentials_from_code

            col_gm1, col_gm2, col_gm3 = st.columns([1, 2, 1])
            with col_gm2:
                if st.button("🔗 CONNECT GMAIL ACCOUNT", use_container_width=True):
                    auth_url = get_auth_url()
                    st.markdown(f"""
                    <div style="margin-top:16px;padding:16px;
                    background:rgba(61,255,160,0.04);border:1px solid rgba(61,255,160,0.12);
                    border-radius:8px;font-family:'JetBrains Mono',monospace;font-size:10px;">
                      <div style="color:var(--mint);margin-bottom:10px;">
                        STEP 1 — Click the link below to authorize:
                      </div>
                      <a href="{auth_url}" target="_blank" style="color:#00c8ff;word-break:break-all;">
                        🔗 Open Gmail Authorization
                      </a>
                      <div style="color:var(--muted);margin-top:10px;">
                        STEP 2 — Paste the authorization code below ↓
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            auth_code = st.text_input("Paste Authorization Code here", placeholder="4/0AfGeXxx...")
            if st.button("✅ VERIFY & CONNECT", use_container_width=True) and auth_code:
                if get_credentials_from_code(auth_code.strip()):
                    st.success("✅ Gmail Connected Successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid code. Try again.")
        except Exception as e:
            st.error(f"Gmail module error: {str(e)}")

    else:
        # Gmail IS connected
        try:
            from gmail_utils import get_recent_emails, get_user_email, auto_scan_and_act

            user_email = get_user_email()
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
            background:rgba(61,255,160,0.04);border:1px solid rgba(61,255,160,0.12);
            border-radius:8px;padding:12px 18px;margin-bottom:20px;">
              <span style="color:var(--mint);font-size:18px;">✅</span>
              <div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                color:var(--mint);letter-spacing:2px;">GMAIL CONNECTED</div>
                <div style="font-family:'DM Sans',sans-serif;font-size:12px;
                color:rgba(255,255,255,0.5);margin-top:2px;">{user_email or 'Account linked'}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            col_gm_a, col_gm_b = st.columns([2, 1])
            with col_gm_a:
                n_emails = st.slider("How many emails to scan?", 1, 20, 5)
            with col_gm_b:
                st.markdown("<br>", unsafe_allow_html=True)
                fetch_btn = st.button("📬 SCAN MY INBOX", use_container_width=True)

            if fetch_btn:
                with st.spinner("📬 Fetching & scanning emails..."):
                    emails = get_recent_emails(max_results=n_emails)

                if not emails:
                    st.info("No emails found in inbox.")
                else:
                    st.markdown(f"""
                    <div class="sn-section-label" style="margin-top:20px;">
                      📬 &nbsp; SCANNED {len(emails)} EMAILS
                    </div>
                    """, unsafe_allow_html=True)

                    for email in emails:
                        # Scan each email
                        scan_text = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"
                        result, steps, breakdown = analyze_message(scan_text, source="GMAIL")

                        score = result['risk_score']
                        col_c = score_color(score)
                        pill_cls = score_pill_cls(score)
                        level, em = get_risk_level(score)

                        with st.expander(
                            f"{em} {email['subject'][:55]} — {score}% risk",
                            expanded=(score >= 60)
                        ):
                            # Email meta
                            col_em1, col_em2 = st.columns([3, 1])
                            with col_em1:
                                st.markdown(f"""
                                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                                line-height:2;color:rgba(255,255,255,0.5);">
                                  <b style="color:rgba(255,255,255,0.7);">FROM:</b> &nbsp;{email['sender']}<br>
                                  <b style="color:rgba(255,255,255,0.7);">DATE:</b> &nbsp;{email.get('date','N/A')}<br>
                                  <b style="color:rgba(255,255,255,0.7);">SUBJECT:</b> &nbsp;{email['subject']}
                                </div>
                                """, unsafe_allow_html=True)
                            with col_em2:
                                st.markdown(f"""
                                <div style="text-align:right;margin-top:10px;">
                                  <div style="font-family:'Bebas Neue',sans-serif;font-size:48px;
                                  color:{col_c};text-shadow:0 0 20px {col_c}60;">{score}%</div>
                                  <span class="sn-risk-pill {pill_cls}">{level}</span>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown(f"""
                            <div class="sn-verdict sn-verdict-{'danger' if score>=70 else 'warn' if score>=30 else 'safe'}"
                            style="margin-top:12px;">
                              <b>{em} {result['threat_type']}</b> &nbsp;·&nbsp; Action: <b>{result['action']}</b><br>
                              <span style="opacity:0.8;">{result['reasoning']}</span>
                            </div>
                            """, unsafe_allow_html=True)

                            # Auto actions
                            if auto_notify and score >= 30:
                                actions_taken = auto_scan_and_act(email, result, auto_block=(auto_block and score >= 75))
                                if actions_taken:
                                    actions_html = "<br>".join(actions_taken)
                                    st.markdown(f"""
                                    <div class="sn-actions-taken">
                                      <div style="letter-spacing:2px;margin-bottom:8px;">
                                        ⚡ ACTIONS TAKEN
                                      </div>
                                      {actions_html}
                                    </div>
                                    """, unsafe_allow_html=True)

                            # Show steps
                            if show_steps:
                                show_steps_ui(steps)

        except Exception as e:
            st.error(f"Gmail error: {str(e)}")
            if st.button("🔌 Reconnect Gmail"):
                del st.session_state['gmail_token']
                st.rerun()


# ===== TAB 5 — DASHBOARD =====
with tab5:
    st.markdown("""<div class="sn-section-label">📊 &nbsp; THREAT INTELLIGENCE DASHBOARD</div>""", unsafe_allow_html=True)

    logs = get_all_logs()

    if logs:
        df_all = pd.DataFrame(logs, columns=['Timestamp','Source','Risk Score','Threat Type','Action'])

        # Source breakdown
        wa_logs   = df_all[df_all['Source'].str.contains('WHATSAPP', case=False, na=False)]
        tg_logs   = df_all[df_all['Source'].str.contains('TELEGRAM', case=False, na=False)]
        gm_logs   = df_all[df_all['Source'].str.contains('GMAIL|EMAIL', case=False, na=False)]
        other_logs= df_all[~df_all['Source'].str.contains('WHATSAPP|TELEGRAM|GMAIL|EMAIL', case=False, na=False)]

        # Summary metrics
        total = len(df_all)
        avg_score = round(df_all['Risk Score'].mean(), 1)
        max_score = df_all['Risk Score'].max()
        blocked_count = len(df_all[df_all['Action'] == 'BLOCKED'])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scans",    total)
        c2.metric("Avg Risk Score", f"{avg_score}%")
        c3.metric("Highest Threat", f"{max_score}%")
        c4.metric("Auto Blocked",   blocked_count)

        st.divider()

        # Source breakdown cards
        st.markdown("""<div class="sn-section-label">📱 &nbsp; BY SOURCE</div>""", unsafe_allow_html=True)

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f"""
            <div style="background:rgba(37,211,102,0.05);border:1px solid rgba(37,211,102,0.15);
            border-radius:10px;padding:16px;text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
              color:#25d366;letter-spacing:2px;">📱 WHATSAPP</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:36px;color:#25d366;margin-top:8px;">
                {len(wa_logs)}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div style="background:rgba(0,136,204,0.05);border:1px solid rgba(0,136,204,0.15);
            border-radius:10px;padding:16px;text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
              color:#0088cc;letter-spacing:2px;">✈️ TELEGRAM</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:36px;color:#0088cc;margin-top:8px;">
                {len(tg_logs)}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div style="background:rgba(234,67,53,0.05);border:1px solid rgba(234,67,53,0.15);
            border-radius:10px;padding:16px;text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
              color:#ea4335;letter-spacing:2px;">📧 GMAIL</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:36px;color:#ea4335;margin-top:8px;">
                {len(gm_logs)}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""
            <div style="background:rgba(155,109,255,0.05);border:1px solid rgba(155,109,255,0.15);
            border-radius:10px;padding:16px;text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
              color:#9b6dff;letter-spacing:2px;">🌐 OTHER</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:36px;color:#9b6dff;margin-top:8px;">
                {len(other_logs)}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Charts
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Threat Type Distribution**")
            st.bar_chart(df_all['Threat Type'].value_counts())
        with col_c2:
            st.markdown("**Action Distribution**")
            st.bar_chart(df_all['Action'].value_counts())

        st.markdown("**Risk Score Trend**")
        st.line_chart(df_all['Risk Score'])

    else:
        st.info("Abhi koi scan nahi hua. Pehle koi message scan karo!")


# ===== TAB 6 — LOGS (SPLIT BY SOURCE) =====
with tab6:
    st.markdown("""<div class="sn-section-label">📋 &nbsp; INVESTIGATION LOGS</div>""", unsafe_allow_html=True)

    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        st.button("🔄 REFRESH LOGS", use_container_width=True)

    logs = get_all_logs()

    if not logs:
        st.info("Koi logs nahi hain. Scan karo pehle!")
    else:
        log_tab1, log_tab2, log_tab3, log_tab4 = st.tabs([
            "📱 WhatsApp", "✈️ Telegram", "📧 Gmail", "🌐 All Logs"
        ])

        all_logs_data = []
        for log in logs:
            timestamp, source, risk_score, threat_type, action = log
            all_logs_data.append({
                'timestamp': timestamp,
                'source': source,
                'risk_score': risk_score,
                'threat_type': threat_type,
                'action': action
            })

        def render_log_table(filtered_logs):
            if not filtered_logs:
                st.info("No logs for this source yet.")
                return

            # Header
            st.markdown("""
            <div class="sn-log-header">
              <span>TIMESTAMP</span>
              <span>SOURCE</span>
              <span>MESSAGE/SOURCE DETAIL</span>
              <span>RISK</span>
              <span>THREAT TYPE</span>
              <span>ACTION</span>
            </div>
            """, unsafe_allow_html=True)

            for log in filtered_logs:
                col_c   = score_color(log['risk_score'])
                a_color = "#ff4d6d" if log['action']=="BLOCKED" else "#ffb830" if log['action']=="WARNING" else "#3dffa0"
                a_icon  = "🚫" if log['action']=="BLOCKED" else "⚠️" if log['action']=="WARNING" else "✅"
                src_html= source_tag_html(log['source'])

                st.markdown(f"""
                <div class="sn-log-row">
                  <span style="color:var(--muted);">{log['timestamp'][:16]}</span>
                  <span>{src_html}</span>
                  <span style="color:rgba(255,255,255,0.6);overflow:hidden;
                  text-overflow:ellipsis;white-space:nowrap;">
                    {log['source'][:40]}
                  </span>
                  <span style="color:{col_c};font-weight:700;">{log['risk_score']}%</span>
                  <span style="color:rgba(255,255,255,0.6);">{log['threat_type']}</span>
                  <span style="color:{a_color};">{a_icon} {log['action']}</span>
                </div>
                """, unsafe_allow_html=True)

        with log_tab1:
            wa_filtered = [l for l in all_logs_data if 'WHATSAPP' in l['source'].upper()]
            render_log_table(wa_filtered)

        with log_tab2:
            tg_filtered = [l for l in all_logs_data if 'TELEGRAM' in l['source'].upper()]
            render_log_table(tg_filtered)

        with log_tab3:
            gm_filtered = [l for l in all_logs_data if any(x in l['source'].upper() for x in ['GMAIL','EMAIL'])]
            render_log_table(gm_filtered)

        with log_tab4:
            render_log_table(all_logs_data)


# ===== FOOTER =====
st.divider()
st.markdown("""
<div style="text-align:center;font-family:'JetBrains Mono',monospace;
font-size:9px;padding:20px;letter-spacing:4px;color:rgba(255,255,255,0.12);">
  SAFENET v4.0 &nbsp;·&nbsp; AGENTIC AI CYBERSECURITY &nbsp;·&nbsp;
  GROQ LLAMA 3 &nbsp;·&nbsp; IBM WATSON NLU &nbsp;·&nbsp; IBM PBL PROJECT
</div>
""", unsafe_allow_html=True)
