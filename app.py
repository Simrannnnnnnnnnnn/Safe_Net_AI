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
    /* Main background */
    .stApp {
        background-color: #0A0A0A;
        color: #E8E8E8;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #111111;
    }
    
    /* Cards */
    .metric-card {
        background: #111111;
        border: 1px solid rgba(255,107,0,0.3);
        padding: 20px;
        border-radius: 4px;
        text-align: center;
    }
    
    /* Risk badges */
    .badge-safe {
        background: rgba(0,255,136,0.1);
        color: #00FF88;
        border: 1px solid #00FF88;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .badge-warn {
        background: rgba(255,215,0,0.1);
        color: #FFD700;
        border: 1px solid #FFD700;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .badge-danger {
        background: rgba(255,45,45,0.1);
        color: #FF2D2D;
        border: 1px solid #FF2D2D;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Buttons */
    .stButton > button {
        background: #FF6B00;
        color: black;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 12px;
        letter-spacing: 2px;
    }
    
    .stButton > button:hover {
        background: #FF8C00;
        color: black;
    }
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid rgba(255,107,0,0.3);
        margin-bottom: 30px;
    }
    
    .main-title {
        font-size: 42px;
        font-weight: 900;
        color: #FF6B00;
        letter-spacing: 8px;
        text-shadow: 0 0 30px rgba(255,107,0,0.5);
    }
    
    .main-subtitle {
        color: #666;
        font-size: 12px;
        letter-spacing: 3px;
        margin-top: 5px;
    }
    
    /* Risk meter */
    .risk-display {
        text-align: center;
        padding: 30px;
        background: #111111;
        border: 1px solid rgba(255,107,0,0.2);
        margin: 20px 0;
    }
    
    .risk-score-big {
        font-size: 72px;
        font-weight: 900;
        line-height: 1;
    }
    
    /* Verdict box */
    .verdict-safe {
        background: rgba(0,255,136,0.05);
        border-left: 3px solid #00FF88;
        padding: 15px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 13px;
        color: #00FF88;
    }
    
    .verdict-warn {
        background: rgba(255,215,0,0.05);
        border-left: 3px solid #FFD700;
        padding: 15px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 13px;
        color: #FFD700;
    }
    
    .verdict-danger {
        background: rgba(255,45,45,0.05);
        border-left: 3px solid #FF2D2D;
        padding: 15px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 13px;
        color: #FF2D2D;
    }
    
    /* Log table */
    .log-table {
        font-family: monospace;
        font-size: 12px;
        width: 100%;
    }
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
