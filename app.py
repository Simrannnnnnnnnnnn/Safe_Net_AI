import streamlit as st
import os
from dotenv import load_dotenv
from database import init_db, get_all_logs, get_stats
from agent import analyze_message, get_risk_level
from gmail_utils import get_recent_emails, block_sender

# Environment variables load karo
load_dotenv()

# Database initialize karo
init_db()

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="SafeNet — AI Cyber Security Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
# ===== CUSTOM CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

    /* ===== GLOBAL ===== */
    .stApp {
        background-color: #0A0A0A;
        color: #E8E8E8;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Scanline overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
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

    /* Grid background */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-image:
            linear-gradient(rgba(255,107,0,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,107,0,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: #0D0D0D !important;
        border-right: 1px solid rgba(255,107,0,0.2) !important;
    }

    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #FF6B00, transparent);
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Orbitron', monospace !important;
        color: #FF6B00 !important;
        font-size: 11px !important;
        letter-spacing: 3px !important;
        text-shadow: 0 0 10px rgba(255,107,0,0.5);
    }

    /* ===== METRICS / STATS CARDS ===== */
    div[data-testid="metric-container"] {
        background: #111111 !important;
        border: 1px solid rgba(255,107,0,0.25) !important;
        border-top: 2px solid #FF6B00 !important;
        padding: 20px !important;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(255,107,0,0.05),
                    inset 0 0 20px rgba(255,107,0,0.02);
        transition: all 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        border-color: rgba(255,107,0,0.6) !important;
        box-shadow: 0 0 30px rgba(255,107,0,0.15),
                    inset 0 0 30px rgba(255,107,0,0.05);
        transform: translateY(-2px);
    }

    div[data-testid="metric-container"] label {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 10px !important;
        letter-spacing: 2px !important;
        color: #666 !important;
        text-transform: uppercase;
    }

    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace !important;
        font-size: 36px !important;
        font-weight: 900 !important;
        color: #FF6B00 !important;
        text-shadow: 0 0 20px rgba(255,107,0,0.6) !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #0D0D0D;
        border-bottom: 1px solid rgba(255,107,0,0.2);
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        letter-spacing: 2px !important;
        color: #444 !important;
        padding: 12px 24px !important;
        border-right: 1px solid rgba(255,107,0,0.1) !important;
        background: transparent !important;
        transition: all 0.2s;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #FF6B00 !important;
        background: rgba(255,107,0,0.05) !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FF6B00 !important;
        background: rgba(255,107,0,0.08) !important;
        border-bottom: 2px solid #FF6B00 !important;
        text-shadow: 0 0 10px rgba(255,107,0,0.5);
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #FF6B00, #CC5500) !important;
        color: #000 !important;
        font-family: 'Orbitron', monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        border: none !important;
        width: 100% !important;
        padding: 14px !important;
        clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
        transition: all 0.2s !important;
        box-shadow: 0 4px 15px rgba(255,107,0,0.3) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #FF8C00, #FF6B00) !important;
        box-shadow: 0 6px 25px rgba(255,107,0,0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* ===== TEXT AREA ===== */
    .stTextArea textarea {
        background: #111111 !important;
        border: 1px solid rgba(255,107,0,0.2) !important;
        color: #E8E8E8 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        border-radius: 0 !important;
        transition: border-color 0.2s !important;
    }

    .stTextArea textarea:focus {
        border-color: #FF6B00 !important;
        box-shadow: 0 0 15px rgba(255,107,0,0.1) !important;
    }

    /* ===== HEADER ===== */
    .main-header {
        text-align: center;
        padding: 30px 0;
        border-bottom: 1px solid rgba(255,107,0,0.3);
        margin-bottom: 30px;
        position: relative;
    }

    .main-header::before {
        content: '';
        position: absolute;
        bottom: -1px; left: 50%;
        transform: translateX(-50%);
        width: 200px; height: 1px;
        background: #FF6B00;
        box-shadow: 0 0 20px #FF6B00;
    }

    .main-title {
        font-family: 'Orbitron', monospace;
        font-size: 48px;
        font-weight: 900;
        color: #FF6B00;
        letter-spacing: 12px;
        text-shadow:
            0 0 20px rgba(255,107,0,0.8),
            0 0 40px rgba(255,107,0,0.4),
            0 0 80px rgba(255,107,0,0.2);
        animation: flicker 4s infinite;
    }

    @keyframes flicker {
        0%, 95%, 100% { opacity: 1; }
        96% { opacity: 0.8; }
        97% { opacity: 1; }
        98% { opacity: 0.9; }
    }

    .main-subtitle {
        font-family: 'Share Tech Mono', monospace;
        color: #444;
        font-size: 11px;
        letter-spacing: 4px;
        margin-top: 8px;
    }

    /* ===== RISK DISPLAY ===== */
    .risk-display {
        text-align: center;
        padding: 30px;
        background: #0D0D0D;
        border: 1px solid rgba(255,107,0,0.2);
        position: relative;
        overflow: hidden;
    }

    .risk-display::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 1px;
        background: linear-gradient(90deg, transparent, #FF6B00, transparent);
    }

    .risk-score-big {
        font-family: 'Orbitron', monospace;
        font-size: 72px;
        font-weight: 900;
        line-height: 1;
        animation: glow-pulse 2s infinite;
    }

    @keyframes glow-pulse {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }

    /* ===== VERDICT BOXES ===== */
    .verdict-safe {
        background: rgba(0,255,136,0.04);
        border-left: 3px solid #00FF88;
        border-bottom: 1px solid rgba(0,255,136,0.1);
        padding: 16px;
        margin: 10px 0;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px;
        color: #00FF88;
        line-height: 1.8;
        box-shadow: inset 0 0 20px rgba(0,255,136,0.02);
    }

    .verdict-warn {
        background: rgba(255,215,0,0.04);
        border-left: 3px solid #FFD700;
        border-bottom: 1px solid rgba(255,215,0,0.1);
        padding: 16px;
        margin: 10px 0;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px;
        color: #FFD700;
        line-height: 1.8;
        box-shadow: inset 0 0 20px rgba(255,215,0,0.02);
    }

    .verdict-danger {
        background: rgba(255,45,45,0.05);
        border-left: 3px solid #FF2D2D;
        border-bottom: 1px solid rgba(255,45,45,0.1);
        padding: 16px;
        margin: 10px 0;
        font-family: 'Share Tech Mono', monospace;
        font-size: 12px;
        color: #FF2D2D;
        line-height: 1.8;
        box-shadow: inset 0 0 20px rgba(255,45,45,0.03);
        animation: danger-pulse 1.5s infinite;
    }

    @keyframes danger-pulse {
        0%, 100% { box-shadow: inset 0 0 20px rgba(255,45,45,0.03); }
        50% { box-shadow: inset 0 0 30px rgba(255,45,45,0.08); }
    }

    /* ===== DIVIDER ===== */
    hr {
        border-color: rgba(255,107,0,0.15) !important;
    }

    /* ===== SUCCESS / ERROR / WARNING ===== */
    .stSuccess {
        background: rgba(0,255,136,0.05) !important;
        border: 1px solid rgba(0,255,136,0.3) !important;
        color: #00FF88 !important;
        font-family: 'Share Tech Mono', monospace !important;
        border-radius: 0 !important;
    }

    .stError {
        background: rgba(255,45,45,0.05) !important;
        border: 1px solid rgba(255,45,45,0.3) !important;
        border-radius: 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    .stWarning {
        background: rgba(255,215,0,0.05) !important;
        border: 1px solid rgba(255,215,0,0.3) !important;
        border-radius: 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    .stInfo {
        background: rgba(255,107,0,0.05) !important;
        border: 1px solid rgba(255,107,0,0.2) !important;
        border-radius: 0 !important;
        font-family: 'Share Tech Mono', monospace !important;
        color: #FF6B00 !important;
    }

    /* ===== TOGGLE ===== */
    .stToggle label {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
        color: #666 !important;
    }

    /* ===== FOOTER ===== */
    .footer-text {
        text-align: center;
        color: #222;
        font-family: 'Share Tech Mono', monospace;
        font-size: 10px;
        padding: 20px;
        letter-spacing: 3px;
        border-top: 1px solid rgba(255,107,0,0.1);
    }

    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-top-color: #FF6B00 !important;
    }

    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #FF6B00, #FF2D2D) !important;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }

    ::-webkit-scrollbar-track { background: #0A0A0A; }

    ::-webkit-scrollbar-thumb {
        background: #FF6B00;
        box-shadow: 0 0 6px rgba(255,107,0,0.5);
    }
</style>
""", unsafe_allow_html=True)
</style>
""", unsafe_allow_html=True)


# ===== HEADER =====
st.markdown("""
<div class="main-header">
    <div class="main-title">🛡️ SAFENET</div>
    <div class="main-subtitle">AI CYBER SECURITY AGENT — POWERED BY GROQ + LLAMA 3</div>
</div>
""", unsafe_allow_html=True)


# ===== STATS ROW =====
stats = get_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🔍 Total Scanned",
        value=stats['total']
    )
with col2:
    st.metric(
        label="🚫 Threats Blocked",
        value=stats['blocked']
    )
with col3:
    st.metric(
        label="⚠️ Warnings Issued",
        value=stats['warned']
    )
with col4:
    st.metric(
        label="✅ Safe Messages",
        value=stats['safe']
    )

st.divider()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### ⚙️ AGENT SETTINGS")
    
    agent_id = st.text_input(
        "Agent ID",
        value="SN-7X4K-9021",
        disabled=True
    )
    
    auto_block = st.toggle(
        "Auto-Block on Critical",
        value=True
    )
    
    check_links = st.toggle(
        "Deep Link Analysis",
        value=True
    )
    
    st.divider()
    st.markdown("### 📊 QUICK STATS")
    
    if stats['total'] > 0:
        threat_percent = round((stats['blocked'] / stats['total']) * 100)
        st.progress(
            threat_percent / 100,
            text=f"Threat Rate: {threat_percent}%"
        )
    
    st.divider()
    st.markdown("### 🔴 STATUS")
    st.success("● PROTECTION ACTIVE")


# ===== MAIN TABS =====
tab1, tab2, tab3 = st.tabs([
    "🔍 SCAN MESSAGE",
    "📧 GMAIL SCANNER",
    "📋 INVESTIGATION LOGS"
])


# ===== TAB 1 — SCAN MESSAGE =====
with tab1:
    st.markdown("#### Paste Suspicious Message")
    
    message_input = st.text_area(
        label="Message",
        placeholder="""Paste WhatsApp message, SMS, or any suspicious text here...

Example: 'Congratulations! You won Rs. 50,000. Click here: bit.ly/xyz — Send bank details immediately!'""",
        height=150,
        label_visibility="collapsed"
    )
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        scan_clicked = st.button(
            "⚡ INITIATE THREAT SCAN",
            use_container_width=True
        )
    
    with col_btn2:
        clear_clicked = st.button(
            "🗑️ CLEAR",
            use_container_width=True
        )
    
    # Scan karo
    if scan_clicked and message_input.strip():
        with st.spinner("🤖 AI Analyzing threat vectors..."):
            result = analyze_message(
                message_text=message_input,
                source="MANUAL SCAN"
            )
        
        score = result['risk_score']
        level, emoji = get_risk_level(score)
        
        # Risk Score Display
        st.markdown("---")
        st.markdown("#### 📊 RISK ANALYSIS RESULT")
        
        col_score, col_info = st.columns([1, 2])
        
        with col_score:
            if score >= 70:
                color = "#FF2D2D"
            elif score >= 30:
                color = "#FFD700"
            else:
                color = "#00FF88"
            
            st.markdown(f"""
            <div class="risk-display">
                <div class="risk-score-big" style="color:{color}">
                    {score}%
                </div>
                <div style="color:{color}; font-size:14px; 
                letter-spacing:3px; margin-top:10px;">
                    {emoji} {level}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info:
            st.markdown(f"**Threat Type:** `{result['threat_type']}`")
            st.markdown(f"**Action Taken:** `{result['action']}`")
            
            # Progress bar
            st.progress(score / 100)
            
            # Verdict
            if score >= 70:
                st.markdown(f"""
                <div class="verdict-danger">
                    🚨 CRITICAL THREAT DETECTED<br><br>
                    {result['reasoning']}
                </div>
                """, unsafe_allow_html=True)
            elif score >= 30:
                st.markdown(f"""
                <div class="verdict-warn">
                    ⚠️ SUSPICIOUS MESSAGE<br><br>
                    {result['reasoning']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="verdict-safe">
                    ✅ MESSAGE APPEARS SAFE<br><br>
                    {result['reasoning']}
                </div>
                """, unsafe_allow_html=True)
        
        # Auto block action
        if score >= 75 and auto_block:
            st.error("🚫 AGENTIC ACTION: This message has been flagged. Sender would be auto-blocked via Gmail API.")
    
    elif scan_clicked and not message_input.strip():
        st.warning("⚠️ Pehle message paste karo!")


# ===== TAB 2 — GMAIL SCANNER =====
with tab2:
    st.markdown("#### 📧 Gmail Inbox Scanner")
    
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.info("""
        **Gmail Scanner Setup:**
        1. Google Cloud Console mein project banao
        2. Gmail API enable karo
        3. `credentials.json` download karo
        4. Root folder mein daalo
        """)
    
    with col_g2:
        gmail_scan = st.button(
            "📥 SCAN INBOX",
            use_container_width=True
        )
    
    if gmail_scan:
        with st.spinner("Gmail inbox scan ho raha hai..."):
            emails = get_recent_emails(max_results=10)
        
        if emails:
            st.success(f"✅ {len(emails)} emails fetched!")
            
            for email in emails:
                with st.expander(
                    f"📧 {email['sender'][:50]} — {email['subject'][:40]}"
                ):
                    st.write(f"**From:** {email['sender']}")
                    st.write(f"**Subject:** {email['subject']}")
                    st.write(f"**Preview:** {email['body'][:200]}...")
                    
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        if st.button(
                            f"🔍 Scan This Email",
                            key=f"scan_{email['id']}"
                        ):
                            with st.spinner("Scanning..."):
                                result = analyze_message(
                                    message_text=email['body'],
                                    source=email['sender']
                                )
                            
                            score = result['risk_score']
                            level, emoji = get_risk_level(score)
                            
                            st.write(f"**Risk Score:** {score}%")
                            st.write(f"**Level:** {emoji} {level}")
                            st.write(f"**Threat:** {result['threat_type']}")
                            
                            # Auto block
                            if score >= 75 and auto_block:
                                success, msg = block_sender(email['sender'])
                                if success:
                                    st.error(f"🚫 {msg}")
                    
                    with col_e2:
                        if st.button(
                            f"🚫 Block Sender",
                            key=f"block_{email['id']}"
                        ):
                            success, msg = block_sender(email['sender'])
                            if success:
                                st.success(f"✅ {msg}")
                            else:
                                st.error(f"❌ {msg}")
        else:
            st.warning("No emails found. Check credentials.json setup.")


# ===== TAB 3 — LOGS =====
with tab3:
    st.markdown("#### 📋 Investigation Logs")
    
    col_l1, col_l2 = st.columns([3, 1])
    
    with col_l2:
        refresh = st.button("🔄 REFRESH", use_container_width=True)
    
    logs = get_all_logs()
    
    if logs:
        # Table header
        header = st.columns([2, 3, 1, 2, 2])
        header[0].markdown("**Timestamp**")
        header[1].markdown("**Source**")
        header[2].markdown("**Score**")
        header[3].markdown("**Threat Type**")
        header[4].markdown("**Action**")
        
        st.divider()
        
        for log in logs:
            timestamp, source, risk_score, threat_type, action = log
            
            col = st.columns([2, 3, 1, 2, 2])
            col[0].caption(timestamp)
            col[1].caption(source[:30])
            
            # Score color
            if risk_score >= 70:
                col[2].markdown(
                    f"<span style='color:#FF2D2D'>{risk_score}%</span>",
                    unsafe_allow_html=True
                )
            elif risk_score >= 30:
                col[2].markdown(
                    f"<span style='color:#FFD700'>{risk_score}%</span>",
                    unsafe_allow_html=True
                )
            else:
                col[2].markdown(
                    f"<span style='color:#00FF88'>{risk_score}%</span>",
                    unsafe_allow_html=True
                )
            
            col[3].caption(threat_type)
            
            # Action color
            if action == "BLOCKED":
                col[4].markdown(
                    "<span style='color:#FF2D2D'>🚫 BLOCKED</span>",
                    unsafe_allow_html=True
                )
            elif action == "WARNING":
                col[4].markdown(
                    "<span style='color:#FFD700'>⚠️ WARNING</span>",
                    unsafe_allow_html=True
                )
            else:
                col[4].markdown(
                    "<span style='color:#00FF88'>✅ CLEAR</span>",
                    unsafe_allow_html=True
                )
    else:
        st.info("Abhi tak koi scan nahi hua. Pehle koi message scan karo!")


# ===== FOOTER =====
st.divider()
st.markdown("""
<div style='text-align:center; color:#333; 
font-family:monospace; font-size:11px; padding:10px;'>
    SAFENET v2.1 — AI CYBER SECURITY AGENT — 
    POWERED BY GROQ LLAMA 3 — BUILT FOR IBM PBL
</div>
""", unsafe_allow_html=True)
