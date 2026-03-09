import streamlit as st
import os
import time
import json
from dotenv import load_dotenv
from database import init_db, get_all_logs, get_stats
from agent import analyze_message, get_risk_level

load_dotenv()
init_db()

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="SafeNet — AI Cyber Security Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS =====
css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

    /* ===== BASE ===== */
    .stApp {
        background-color: #0A0A0A !important;
        color: #E8E8E8 !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: #0D0D0D !important;
        border-right: 1px solid rgba(255,107,0,0.2) !important;
    }

    /* ===== STATS CARDS FIX ===== */
    div[data-testid="metric-container"] {
        background: #161616 !important;
        border: 1px solid rgba(255,107,0,0.3) !important;
        border-top: 2px solid #FF6B00 !important;
        padding: 16px !important;
        border-radius: 0px !important;
    }

    [data-testid="stMetricLabel"] p {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        color: #888888 !important;
        letter-spacing: 1px !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace !important;
        color: #FF6B00 !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        text-shadow: 0 0 15px rgba(255,107,0,0.4) !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #0D0D0D !important;
        border-bottom: 1px solid rgba(255,107,0,0.2) !important;
        gap: 0px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        color: #555555 !important;
        background: transparent !important;
        border-radius: 0px !important;
        padding: 12px 20px !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FF6B00 !important;
        background: rgba(255,107,0,0.06) !important;
        border-bottom: 2px solid #FF6B00 !important;
        text-shadow: 0 0 8px rgba(255,107,0,0.4) !important;
    }

    /* ===== BUTTONS FIX ===== */
    .stButton > button {
        background: transparent !important;
        color: #FF6B00 !important;
        font-family: 'Orbitron', monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        border: 1px solid #FF6B00 !important;
        padding: 12px 20px !important;
        border-radius: 0px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 0 10px rgba(255,107,0,0.1) !important;
    }

    .stButton > button:hover {
        background: #FF6B00 !important;
        color: #000000 !important;
        box-shadow: 0 0 20px rgba(255,107,0,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ===== TEXT AREA ===== */
    .stTextArea textarea {
        background: #111111 !important;
        border: 1px solid rgba(255,107,0,0.25) !important;
        color: #E8E8E8 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        border-radius: 0px !important;
        line-height: 1.6 !important;
    }

    .stTextArea textarea:focus {
        border-color: #FF6B00 !important;
        box-shadow: 0 0 12px rgba(255,107,0,0.15) !important;
    }

    .stTextArea textarea::placeholder {
        color: #333333 !important;
    }

    /* ===== TEXT INPUT ===== */
    .stTextInput input {
        background: #111111 !important;
        border: 1px solid rgba(255,107,0,0.25) !important;
        color: #E8E8E8 !important;
        font-family: 'Share Tech Mono', monospace !important;
        border-radius: 0px !important;
    }

    /* ===== PROGRESS BAR ===== */
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #FF6B00, #FF2D2D) !important;
    }

    /* ===== ALERTS ===== */
    [data-testid="stAlert"] {
        border-radius: 0px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
    }

    /* ===== HEADINGS ===== */
    h1, h2, h3, h4 {
        font-family: 'Orbitron', monospace !important;
        color: #FF6B00 !important;
        letter-spacing: 2px !important;
    }

    /* ===== DIVIDER ===== */
    hr {
        border-color: rgba(255,107,0,0.15) !important;
    }

    /* ===== TOGGLE ===== */
    .stToggle p {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        color: #888 !important;
        letter-spacing: 1px !important;
    }

    /* ===== CAPTION / SMALL TEXT ===== */
    .stCaption, caption {
        color: #666 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
    }

    /* ===== MAIN TITLE ===== */
    .main-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 52px !important;
        font-weight: 900 !important;
        color: #FF6B00 !important;
        letter-spacing: 14px !important;
        text-shadow:
            0 0 20px rgba(255,107,0,0.9),
            0 0 50px rgba(255,107,0,0.4),
            0 0 100px rgba(255,107,0,0.15) !important;
        animation: flicker 5s infinite !important;
    }

    @keyframes flicker {
        0%, 94%, 100% { opacity: 1; }
        95% { opacity: 0.75; }
        97% { opacity: 1; }
        99% { opacity: 0.85; }
    }

    .main-subtitle {
        font-family: 'Share Tech Mono', monospace !important;
        color: #3a3a3a !important;
        font-size: 11px !important;
        letter-spacing: 5px !important;
        margin-top: 10px !important;
    }

    /* ===== AGENT STEP BOXES ===== */
    .agent-step {
        padding: 12px 16px !important;
        margin: 5px 0 !important;
        border-left: 3px solid !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
    }

    .step-done {
        border-color: #00FF88 !important;
        background: rgba(0,255,136,0.04) !important;
        color: #00FF88 !important;
    }

    .step-error {
        border-color: #FF2D2D !important;
        background: rgba(255,45,45,0.04) !important;
        color: #FF2D2D !important;
    }

    /* ===== VERDICT BOXES ===== */
    .verdict-safe {
        background: rgba(0,255,136,0.04) !important;
        border-left: 3px solid #00FF88 !important;
        padding: 16px !important;
        margin: 10px 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        color: #00FF88 !important;
        line-height: 1.8 !important;
    }

    .verdict-warn {
        background: rgba(255,215,0,0.04) !important;
        border-left: 3px solid #FFD700 !important;
        padding: 16px !important;
        margin: 10px 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        color: #FFD700 !important;
        line-height: 1.8 !important;
    }

    .verdict-danger {
        background: rgba(255,45,45,0.06) !important;
        border-left: 3px solid #FF2D2D !important;
        padding: 16px !important;
        margin: 10px 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        color: #FF2D2D !important;
        line-height: 1.8 !important;
    }

    /* ===== WHATSAPP BUBBLE ===== */
    .whatsapp-bubble {
        background: #1a1a1a !important;
        border: 1px solid rgba(37,211,102,0.25) !important;
        border-radius: 0 12px 12px 12px !important;
        padding: 12px 16px !important;
        margin: 8px 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        color: #E8E8E8 !important;
        max-width: 80% !important;
    }

    /* ===== BULK ROW ===== */
    .bulk-result-row {
        padding: 10px 0 !important;
        border-bottom: 1px solid rgba(255,107,0,0.08) !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 3px; height: 3px; }
    ::-webkit-scrollbar-track { background: #0A0A0A; }
    ::-webkit-scrollbar-thumb {
        background: #FF6B00;
        box-shadow: 0 0 4px rgba(255,107,0,0.5);
    }
</style>
""", unsafe_allow_html=True)


# ===== HEADER =====
st.markdown("""
<div style='text-align:center; padding:30px 0; 
border-bottom:1px solid rgba(255,107,0,0.3); margin-bottom:30px;'>
    <div class='main-title'>🛡️ SAFENET</div>
    <div class='main-subtitle'>
        AI CYBER SECURITY AGENT — POWERED BY GROQ + LLAMA 3
    </div>
</div>
""", unsafe_allow_html=True)


# ===== STATS =====
stats = get_stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🔍 Total Scanned", stats['total'])
with col2:
    st.metric("🚫 Threats Blocked", stats['blocked'])
with col3:
    st.metric("⚠️ Warnings Issued", stats['warned'])
with col4:
    st.metric("✅ Safe Messages", stats['safe'])

st.divider()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ AGENT SETTINGS")
    agent_id = st.text_input("Agent ID", value="SN-7X4K-9021", disabled=True)
    auto_block = st.toggle("Auto-Block on Critical", value=True)
    deep_scan = st.toggle("Deep Link Analysis", value=True)
    show_steps = st.toggle("Show Agent Reasoning", value=True)
    st.divider()
    st.markdown("### 📊 THREAT RATE")
    if stats['total'] > 0:
        threat_pct = round((stats['blocked'] / stats['total']) * 100)
        st.progress(threat_pct / 100, text=f"Threat Rate: {threat_pct}%")
    st.divider()
    st.success("● PROTECTION ACTIVE")


# ===== TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 SCAN MESSAGE",
    "💬 WHATSAPP FORMAT",
    "📦 BULK SCANNER",
    "📊 DASHBOARD",
    "📋 LOGS"
])


# ===== HELPER — SHOW AGENTIC STEPS =====
def show_agentic_steps(steps):
    st.markdown("""
    <div style='background:#0D0D0D; border:1px solid rgba(255,107,0,0.2); 
    padding:20px; margin:16px 0;'>
    <div style='font-family:Share Tech Mono,monospace; font-size:11px; 
    color:#FF6B00; letter-spacing:3px; margin-bottom:16px;'>
        ⚡ AGENTIC AI — REASONING CHAIN
    </div>
    """, unsafe_allow_html=True)

    for step in steps:
        icon = "✅" if step['status'] == 'done' else "❌"
        cls = "step-done" if step['status'] == 'done' else "step-error"
        finding = step.get('finding', '...')
        st.markdown(f"""
        <div class='agent-step {cls}'>
            {icon} STEP {step['step']} — {step['title']}<br>
            <span style='opacity:0.7; font-size:11px;'>→ {finding}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ===== HELPER — SHOW CONFIDENCE BREAKDOWN =====
def show_breakdown(breakdown):
    if not breakdown:
        return

    st.markdown("""
    <div style='background:#0D0D0D; border:1px solid rgba(255,107,0,0.2); 
    padding:20px; margin:16px 0;'>
    <div style='font-family:Share Tech Mono,monospace; font-size:11px; 
    color:#FF6B00; letter-spacing:3px; margin-bottom:16px;'>
        📊 CONFIDENCE BREAKDOWN
    </div>
    """, unsafe_allow_html=True)

    for item in breakdown:
        score = item['score']
        color = "#FF2D2D" if score >= 70 else "#FFD700" if score >= 30 else "#00FF88"
        st.markdown(f"""
        <div style='margin-bottom:12px;'>
            <div style='display:flex; justify-content:space-between; 
            font-family:Share Tech Mono,monospace; font-size:11px; margin-bottom:4px;'>
                <span style='color:#E8E8E8;'>{item['factor']}</span>
                <span style='color:{color};'>{score}%</span>
            </div>
            <div style='background:#1a1a1a; height:6px;'>
                <div style='width:{score}%; height:100%; 
                background:{color};'></div>
            </div>
            <div style='font-family:Share Tech Mono,monospace; 
            font-size:10px; color:#444; margin-top:3px;'>
                → {item['detail']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ===== HELPER — SHOW RESULT =====
def show_result(result, steps, breakdown, auto_block, show_steps):
    score = result['risk_score']
    level, emoji = get_risk_level(score)
    confidence = result.get('confidence', 'N/A')
    red_flags = result.get('red_flags', [])
    recommendation = result.get('recommendation', '')

    st.markdown("---")
    st.markdown("#### 📊 ANALYSIS RESULT")

    col_score, col_info = st.columns([1, 2])

    with col_score:
        color = "#FF2D2D" if score >= 70 else "#FFD700" if score >= 30 else "#00FF88"
        st.markdown(f"""
        <div style='text-align:center; padding:30px; background:#0D0D0D;
        border:1px solid rgba(255,107,0,0.2);'>
            <div style='font-family:Orbitron,monospace; font-size:64px; 
            font-weight:900; color:{color}; 
            text-shadow: 0 0 30px {color};'>
                {score}%
            </div>
            <div style='color:{color}; font-family:Share Tech Mono,monospace;
            font-size:13px; letter-spacing:3px; margin-top:10px;'>
                {emoji} {level}
            </div>
            <div style='color:#444; font-family:Share Tech Mono,monospace;
            font-size:10px; margin-top:6px;'>
                AI CONFIDENCE: {confidence}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"**Threat Type:** `{result['threat_type']}`")
        st.markdown(f"**Action:** `{result['action']}`")
        st.progress(score / 100)

        if score >= 70:
            st.markdown(f"""
            <div class='verdict-danger'>
                🚨 CRITICAL THREAT DETECTED<br><br>
                {result['reasoning']}<br><br>
                💡 {recommendation}
            </div>
            """, unsafe_allow_html=True)
        elif score >= 30:
            st.markdown(f"""
            <div class='verdict-warn'>
                ⚠️ SUSPICIOUS MESSAGE<br><br>
                {result['reasoning']}<br><br>
                💡 {recommendation}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='verdict-safe'>
                ✅ MESSAGE APPEARS SAFE<br><br>
                {result['reasoning']}<br><br>
                💡 {recommendation}
            </div>
            """, unsafe_allow_html=True)

        if red_flags:
            st.markdown("**🚩 Red Flags:**")
            for flag in red_flags:
                st.markdown(f"- `{flag}`")

    # Agentic steps
    if show_steps:
        show_agentic_steps(steps)

    # Confidence breakdown
    show_breakdown(breakdown)

    # Agentic auto block
    if score >= 75 and auto_block:
        st.markdown("""
        <div style='background:#0D0D0D; border:1px solid rgba(255,45,45,0.4); 
        padding:20px; margin-top:16px; font-family:monospace;'>
            <div style='color:#FF2D2D; font-size:13px; 
            letter-spacing:2px; margin-bottom:15px;'>
                ⚡ AGENTIC ACTION — AUTO RESPONSE
            </div>
        """, unsafe_allow_html=True)

        actions = [
            "Threat signature locked in database",
            "Sender flagged as HIGH RISK entity",
            "Auto-trash filter created in Gmail",
            "Incident logged with full timestamp"
        ]

        for i, action in enumerate(actions):
            with st.spinner(f"Processing step {i+1}/4..."):
                time.sleep(0.6)
            st.markdown(f"""
            <div style='color:#FF6B00; font-family:monospace; 
            font-size:12px; padding:5px 0;'>
                ✅ STEP {i+1} — {action}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='margin-top:15px; padding:12px; 
        background:rgba(255,45,45,0.08); 
        border-left:3px solid #FF2D2D;
        font-family:monospace; font-size:12px; color:#FF2D2D;'>
            🛡️ AGENT VERDICT: Sender permanently blocked.<br>
            Risk Score: {score}% — Action: BLOCKED
        </div>
        </div>
        """, unsafe_allow_html=True)

    elif score >= 30:
        st.markdown("""
        <div style='background:#0D0D0D; 
        border:1px solid rgba(255,215,0,0.3); 
        padding:15px; font-family:monospace; margin-top:10px;'>
            <div style='color:#FFD700; font-size:12px; letter-spacing:2px;'>
                ⚠️ AGENTIC AI — MONITORING MODE
            </div>
            <div style='color:#666; font-size:11px; 
            margin-top:8px; line-height:1.8;'>
                → Sender added to watchlist<br>
                → Next message will be auto-scanned<br>
                → User alert activated
            </div>
        </div>
        """, unsafe_allow_html=True)


# ===== TAB 1 — SCAN MESSAGE =====
with tab1:
    st.markdown("#### 🔍 Paste Suspicious Message")

    message_input = st.text_area(
        label="Message",
        placeholder="Paste WhatsApp message, SMS, email, or any suspicious text...\n\nExample: 'Congratulations! You won Rs. 50,000. Click here: bit.ly/xyz'",
        height=150,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        scan_btn = st.button("⚡ INITIATE THREAT SCAN", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ CLEAR", use_container_width=True)

    if scan_btn and message_input.strip():
        with st.spinner("🤖 Agentic AI analyzing..."):
            result, steps, breakdown = analyze_message(
                message_text=message_input,
                source="MANUAL SCAN"
            )
        show_result(result, steps, breakdown, auto_block, show_steps)

    elif scan_btn:
        st.warning("⚠️ Pehle message paste karo!")


# ===== TAB 2 — WHATSAPP FORMAT =====
with tab2:
    st.markdown("#### 💬 WhatsApp Style Scanner")
    st.markdown("""
    <div style='background:#0D0D0D; border:1px solid rgba(37,211,102,0.2); 
    padding:16px; margin-bottom:20px; font-family:Share Tech Mono,monospace; 
    font-size:11px; color:#25D366;'>
        📱 WHATSAPP MESSAGE ANALYZER — Paste sender name + message
    </div>
    """, unsafe_allow_html=True)

    wa_sender = st.text_input(
        "Sender Name/Number",
        placeholder="+91-98765-43210 or Unknown Contact"
    )

    wa_message = st.text_area(
        "WhatsApp Message",
        placeholder="Paste the WhatsApp message here...",
        height=120,
        label_visibility="visible"
    )

    if st.button("📱 SCAN WHATSAPP MESSAGE", use_container_width=True):
        if wa_message.strip():
            full_text = f"Sender: {wa_sender}\nMessage: {wa_message}"

            # WhatsApp bubble UI
            st.markdown(f"""
            <div style='padding:20px 0;'>
                <div style='font-family:Share Tech Mono,monospace; 
                font-size:10px; color:#444; margin-bottom:8px;'>
                    FROM: {wa_sender or 'Unknown'}
                </div>
                <div class='whatsapp-bubble'>{wa_message}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("🤖 Scanning WhatsApp message..."):
                result, steps, breakdown = analyze_message(
                    message_text=full_text,
                    source=f"WHATSAPP: {wa_sender}"
                )
            show_result(result, steps, breakdown, auto_block, show_steps)
        else:
            st.warning("⚠️ Message paste karo!")


# ===== TAB 3 — BULK SCANNER =====
with tab3:
    st.markdown("#### 📦 Bulk Message Scanner")
    st.markdown("""
    <div style='background:#0D0D0D; border:1px solid rgba(255,107,0,0.2); 
    padding:12px 16px; margin-bottom:16px; font-family:Share Tech Mono,monospace; 
    font-size:11px; color:#666;'>
        💡 Ek line mein ek message — multiple messages ek saath scan karo
    </div>
    """, unsafe_allow_html=True)

    bulk_input = st.text_area(
        "Multiple Messages",
        placeholder="Message 1: Congratulations you won...\nMessage 2: Your account will expire...\nMessage 3: Hi, how are you?",
        height=200,
        label_visibility="visible"
    )

    if st.button("⚡ BULK SCAN ALL", use_container_width=True):
        if bulk_input.strip():
            messages = [m.strip() for m in bulk_input.strip().split('\n') if m.strip()]
            st.markdown(f"""
            <div style='font-family:Share Tech Mono,monospace; font-size:11px; 
            color:#FF6B00; padding:10px 0;'>
                🔍 SCANNING {len(messages)} MESSAGE(S)...
            </div>
            """, unsafe_allow_html=True)

            results_summary = []

            for i, msg in enumerate(messages):
                with st.spinner(f"Scanning message {i+1}/{len(messages)}..."):
                    result, steps, breakdown = analyze_message(
                        message_text=msg,
                        source="BULK SCAN"
                    )

                score = result['risk_score']
                level, emoji = get_risk_level(score)
                color = "#FF2D2D" if score >= 70 else "#FFD700" if score >= 30 else "#00FF88"

                results_summary.append({
                    "msg": msg[:60] + "..." if len(msg) > 60 else msg,
                    "score": score,
                    "level": level,
                    "emoji": emoji,
                    "color": color,
                    "action": result['action']
                })

            st.markdown("---")
            st.markdown("#### 📊 Bulk Scan Results")

            blocked = sum(1 for r in results_summary if r['action'] == 'BLOCKED')
            warned = sum(1 for r in results_summary if r['action'] == 'WARNING')
            safe = sum(1 for r in results_summary if r['action'] == 'CLEAR')

            c1, c2, c3 = st.columns(3)
            c1.metric("🚫 Blocked", blocked)
            c2.metric("⚠️ Warnings", warned)
            c3.metric("✅ Safe", safe)

            for i, r in enumerate(results_summary):
                st.markdown(f"""
                <div class='bulk-result-row'>
                    <span style='color:#444;'>MSG {i+1}:</span>
                    <span style='color:#E8E8E8;'> {r['msg']}</span><br>
                    <span style='color:{r['color']}; margin-top:4px; display:block;'>
                        {r['emoji']} {r['level']} — {r['score']}% — {r['action']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Messages paste karo!")


# ===== TAB 4 — DASHBOARD =====
with tab4:
    st.markdown("#### 📊 Scam History Dashboard")

    logs = get_all_logs()

    if logs:
        import pandas as pd

        df = pd.DataFrame(logs, columns=[
            'Timestamp', 'Source', 'Risk Score', 'Threat Type', 'Action'
        ])

        # Charts
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("**Threat Type Distribution**")
            threat_counts = df['Threat Type'].value_counts()
            st.bar_chart(threat_counts)

        with col_c2:
            st.markdown("**Action Distribution**")
            action_counts = df['Action'].value_counts()
            st.bar_chart(action_counts)

        st.markdown("**Risk Score Over Time**")
        st.line_chart(df['Risk Score'])

        st.divider()

        # Summary
        total = len(df)
        avg_score = round(df['Risk Score'].mean(), 1)
        max_score = df['Risk Score'].max()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Scans", total)
        c2.metric("Avg Risk Score", f"{avg_score}%")
        c3.metric("Highest Threat", f"{max_score}%")

    else:
        st.info("Abhi tak koi scan nahi hua. Pehle messages scan karo!")


# ===== TAB 5 — LOGS =====
with tab5:
    st.markdown("#### 📋 Investigation Logs")

    col_l1, col_l2 = st.columns([3, 1])
    with col_l2:
        st.button("🔄 REFRESH", use_container_width=True)

    logs = get_all_logs()

    if logs:
        header = st.columns([2, 3, 1, 2, 2])
        header[0].markdown("**Timestamp**")
        header[1].markdown("**Source**")
        header[2].markdown("**Score**")
        header[3].markdown("**Threat**")
        header[4].markdown("**Action**")
        st.divider()

        for log in logs:
            timestamp, source, risk_score, threat_type, action = log
            col = st.columns([2, 3, 1, 2, 2])
            col[0].caption(timestamp)
            col[1].caption(source[:30])

            color = "#FF2D2D" if risk_score >= 70 else "#FFD700" if risk_score >= 30 else "#00FF88"
            col[2].markdown(
                f"<span style='color:{color}; font-family:monospace;'>{risk_score}%</span>",
                unsafe_allow_html=True
            )
            col[3].caption(threat_type)

            action_color = "#FF2D2D" if action == "BLOCKED" else "#FFD700" if action == "WARNING" else "#00FF88"
            action_icon = "🚫" if action == "BLOCKED" else "⚠️" if action == "WARNING" else "✅"
            col[4].markdown(
                f"<span style='color:{action_color}; font-family:monospace;'>{action_icon} {action}</span>",
                unsafe_allow_html=True
            )
    else:
        st.info("Koi logs nahi hain abhi. Scan karo pehle!")


# ===== FOOTER =====
st.divider()
st.markdown("""
<div style='text-align:center; color:#222; font-family:monospace; 
font-size:10px; padding:20px; letter-spacing:3px;'>
    SAFENET v3.0 — AGENTIC AI CYBER SECURITY — 
    GROQ LLAMA 3 — IBM PBL PROJECT
</div>
""", unsafe_allow_html=True)
