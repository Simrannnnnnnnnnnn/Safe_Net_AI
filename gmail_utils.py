import os
import re
import base64
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


def get_secret(key, default=""):
    """Read from st.secrets first, then os.environ — works on both local + Streamlit Cloud"""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)


def get_client_config():
    """Build CLIENT_CONFIG fresh every time — ensures secrets are loaded"""
    return {
        "web": {
            "client_id":     get_secret("GMAIL_CLIENT_ID"),
            "client_secret": get_secret("GMAIL_CLIENT_SECRET"),
            "redirect_uris": [get_secret("GMAIL_REDIRECT_URI", "https://safenet-ai.streamlit.app")],
            "auth_uri":  "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }


# ===== AUTH =====
def get_auth_url():
    import hashlib, secrets as sec, base64 as b64, urllib.parse

    config       = get_client_config()
    redirect_uri = get_secret("GMAIL_REDIRECT_URI", "https://safenet-ai.streamlit.app")

    # Generate PKCE
    code_verifier  = sec.token_urlsafe(64)
    digest         = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = b64.urlsafe_b64encode(digest).rstrip(b'=').decode()

    # Encode verifier in state so it survives redirect
    state = b64.urlsafe_b64encode(code_verifier.encode()).decode()

    st.session_state['code_verifier']  = code_verifier
    st.session_state['oauth_redirect'] = redirect_uri
    st.session_state['oauth_config']   = get_client_config()

    params = {
        'client_id':             config['web']['client_id'],
        'redirect_uri':          redirect_uri,
        'response_type':         'code',
        'scope':                 ' '.join(SCOPES),
        'access_type':           'offline',
        'prompt':                'consent',
        'code_challenge':        code_challenge,
        'code_challenge_method': 'S256',
        'state':                 state,
    }
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)


def get_credentials_from_code(code):
    try:
        import requests as req, base64 as b64, urllib.parse

        config       = get_client_config()
        redirect_uri = get_secret("GMAIL_REDIRECT_URI", "https://safenet-ai.streamlit.app")
        client_id    = config['web']['client_id']
        client_secret= config['web']['client_secret']

        # Try session_state first, then fallback to state param from URL
        code_verifier = st.session_state.get('code_verifier', '')

        if not code_verifier:
            # Recover from state param in URL
            state = st.query_params.get('state', '')
            if state:
                try:
                    # Add padding if needed
                    pad = 4 - len(state) % 4
                    if pad != 4:
                        state += '=' * pad
                    code_verifier = b64.urlsafe_b64decode(state.encode()).decode()
                except Exception:
                    code_verifier = ''

        token_response = req.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code':          code,
                'client_id':     client_id,
                'client_secret': client_secret,
                'redirect_uri':  redirect_uri,
                'grant_type':    'authorization_code',
                'code_verifier': code_verifier,
            }
        )
        token_data = token_response.json()

        if 'error' in token_data:
            st.error(f"Token error: {token_data.get('error_description', token_data['error'])}")
            return False

        st.session_state['gmail_token'] = {
            'token':         token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'token_uri':     'https://oauth2.googleapis.com/token',
            'client_id':     client_id,
            'client_secret': client_secret,
            'scopes':        SCOPES
        }
        return True

    except Exception as e:
        st.error(f"Auth error: {str(e)}")
        return False


def get_gmail_service():
    token_data = st.session_state.get('gmail_token')
    if not token_data:
        return None
    try:
        creds = Credentials(
            token=         token_data.get('token'),
            refresh_token= token_data.get('refresh_token'),
            token_uri=     token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=     token_data.get('client_id'),
            client_secret= token_data.get('client_secret'),
            scopes=        token_data.get('scopes', SCOPES)
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state['gmail_token']['token'] = creds.token
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        st.error(f"Gmail service error: {str(e)}")
        return None


def get_user_email():
    service = get_gmail_service()
    if not service:
        return None
    try:
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress')
    except:
        return None


# ===== EMAIL HELPERS =====
def extract_email_address(from_field):
    match = re.search(r'<(.+?)>', from_field)
    if match:
        return match.group(1).strip()
    match2 = re.search(r'\S+@\S+\.\S+', from_field)
    if match2:
        return match2.group(0).strip()
    return from_field.strip()


def get_email_body(payload):
    try:
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        return re.sub(r'<[^>]+>', ' ', text)
        return ""
    except:
        return ""


# ===== FETCH EMAILS =====
def get_recent_emails(max_results=10):
    service = get_gmail_service()
    if not service:
        return []
    try:
        results = service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX']
        ).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            try:
                msg_data = service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                headers = msg_data.get('payload', {}).get('headers', [])
                hd = {h['name']: h['value'] for h in headers}
                sender_full = hd.get('From', 'Unknown')
                emails.append({
                    'id':           msg_data.get('id'),
                    'subject':      hd.get('Subject', '(No Subject)'),
                    'sender':       sender_full,
                    'sender_email': extract_email_address(sender_full),
                    'date':         hd.get('Date', ''),
                    'snippet':      msg_data.get('snippet', ''),
                    'body':         get_email_body(msg_data.get('payload', {}))[:800],
                    'label_ids':    msg_data.get('labelIds', [])
                })
            except:
                continue
        return emails
    except Exception as e:
        st.error(f"Error fetching emails: {str(e)}")
        return []


# ===== SEND EMAIL =====
def send_email(to_email, subject, body_html):
    service = get_gmail_service()
    if not service:
        return False, "Gmail not connected"
    try:
        msg = MIMEMultipart('alternative')
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return True, "Sent successfully"
    except Exception as e:
        return False, str(e)


# ===== WARNING → FAKE SENDER =====
def send_warning_to_fake_sender(sender_email, original_subject, threat_type, risk_score):
    subject   = f"⚠️ SafeNet Alert: Your email was flagged as {threat_type}"
    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
    background:#0f0c29;color:white;padding:30px;border-radius:12px;">
      <h1 style="color:#ff4d6d;text-align:center;">🛡️ SAFENET SECURITY ALERT</h1>
      <p style="color:#9b6dff;text-align:center;">AI-Powered Cybersecurity Agent</p>
      <div style="background:rgba(255,77,109,0.1);border:1px solid #ff4d6d;
      border-radius:8px;padding:20px;margin:20px 0;">
        <h2 style="color:#ff4d6d;">⚠️ Your Email Was Flagged</h2>
        <p>An email from <b>{sender_email}</b> was flagged as potentially malicious by SafeNet AI.</p>
      </div>
      <table style="width:100%;border-collapse:collapse;margin:20px 0;">
        <tr style="background:rgba(255,255,255,0.05);">
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Subject:</td>
          <td style="padding:10px;">{original_subject}</td>
        </tr>
        <tr>
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Threat:</td>
          <td style="padding:10px;color:#ff4d6d;font-weight:bold;">{threat_type}</td>
        </tr>
        <tr style="background:rgba(255,255,255,0.05);">
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Risk Score:</td>
          <td style="padding:10px;color:#ffb830;font-weight:bold;">{risk_score}%</td>
        </tr>
      </table>
      <div style="background:rgba(61,255,160,0.1);border:1px solid #3dffa0;
      border-radius:8px;padding:15px;margin:20px 0;">
        <p style="color:#3dffa0;margin:0;">
          ℹ️ If you did NOT send this email, your account may be compromised.<br>
          Please change your password immediately and enable 2-factor authentication.
        </p>
      </div>
      <p style="color:#555;font-size:12px;text-align:center;">
        SafeNet AI | IBM PBL Project | Groq Llama 3 + IBM Watson NLU
      </p>
    </div>
    """
    return send_email(sender_email, subject, body_html)


# ===== NOTIFICATION → USER =====
def send_user_notification(user_email, sender_email, original_subject,
                           threat_type, risk_score, reasoning, action):
    action_color = {"BLOCKED": "#ff4d6d", "WARNING": "#ffb830", "CLEAR": "#3dffa0"}.get(action, "#9b6dff")
    action_emoji = {"BLOCKED": "🚫", "WARNING": "⚠️", "CLEAR": "✅"}.get(action, "🔍")
    subject      = f"{action_emoji} SafeNet: Suspicious Email in Your Inbox"

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
    background:#0f0c29;color:white;padding:30px;border-radius:12px;">
      <h1 style="color:#3dffa0;text-align:center;">🛡️ SAFENET</h1>
      <p style="color:#9b6dff;text-align:center;">Your AI Cybersecurity Guardian</p>
      <div style="background:rgba(255,184,48,0.1);border:1px solid #ffb830;
      border-radius:8px;padding:20px;margin:20px 0;">
        <h2 style="color:#ffb830;">⚠️ Suspicious Email Detected!</h2>
        <p>SafeNet AI scanned your inbox and found a potentially dangerous email.</p>
      </div>
      <table style="width:100%;border-collapse:collapse;margin:20px 0;">
        <tr style="background:rgba(255,255,255,0.05);">
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">From:</td>
          <td style="padding:10px;">{sender_email}</td>
        </tr>
        <tr>
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Subject:</td>
          <td style="padding:10px;">{original_subject}</td>
        </tr>
        <tr style="background:rgba(255,255,255,0.05);">
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Threat:</td>
          <td style="padding:10px;color:#ff4d6d;font-weight:bold;">{threat_type}</td>
        </tr>
        <tr>
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Risk Score:</td>
          <td style="padding:10px;color:#ffb830;font-weight:bold;">{risk_score}%</td>
        </tr>
        <tr style="background:rgba(255,255,255,0.05);">
          <td style="padding:10px;color:#9b6dff;font-weight:bold;">Action:</td>
          <td style="padding:10px;color:{action_color};font-weight:bold;">{action_emoji} {action}</td>
        </tr>
      </table>
      <div style="background:rgba(155,109,255,0.1);border:1px solid #9b6dff;
      border-radius:8px;padding:15px;margin:20px 0;">
        <p style="color:#9b6dff;font-weight:bold;">🤖 AI Analysis:</p>
        <p style="margin:0;">{reasoning}</p>
      </div>
      <div style="background:rgba(61,255,160,0.1);border:1px solid #3dffa0;
      border-radius:8px;padding:15px;margin:20px 0;">
        <p style="color:#3dffa0;font-weight:bold;">💡 What to do:</p>
        <ul style="margin:0;padding-left:20px;">
          <li>Do NOT click any links in that email</li>
          <li>Do NOT reply or share personal info</li>
          <li>Mark it as spam</li>
          <li>Visit SafeNet dashboard for full analysis</li>
        </ul>
      </div>
      <p style="color:#555;font-size:12px;text-align:center;">
        SafeNet AI | IBM PBL Project | Groq Llama 3 + IBM Watson NLU
      </p>
    </div>
    """
    return send_email(user_email, subject, body_html)


# ===== BLOCK SENDER =====
def block_sender(sender_email):
    try:
        service = get_gmail_service()
        if not service:
            return False, "Gmail not connected"
        if '<' in sender_email:
            sender_email = sender_email.split('<')[1].split('>')[0].strip()
        filter_body = {
            'criteria': {'from': sender_email},
            'action':   {'addLabelIds': ['TRASH'], 'removeLabelIds': ['INBOX']}
        }
        service.users().settings().filters().create(userId='me', body=filter_body).execute()
        return True, f"✅ {sender_email} blocked!"
    except Exception as e:
        return False, f"Block failed: {str(e)}"


# ===== AUTO SCAN + ACT =====
def auto_scan_and_act(email, analysis_result, auto_block=False):
    """
    Automatically take action after scanning:
    - score >= 60: warn sender + notify user + optional block
    - score 30-59: notify user only
    - score < 30:  safe, no action
    """
    actions_taken = []
    user_email    = get_user_email()
    risk_score    = analysis_result.get('risk_score', 0)
    threat_type   = analysis_result.get('threat_type', 'UNKNOWN')
    action        = analysis_result.get('action', 'WARNING')
    reasoning     = analysis_result.get('reasoning', '')
    sender_email  = email.get('sender_email', '')
    subject       = email.get('subject', '(No Subject)')

    if risk_score >= 60 and sender_email:
        ok1, msg1 = send_warning_to_fake_sender(sender_email, subject, threat_type, risk_score)
        actions_taken.append(f"{'✅' if ok1 else '❌'} Warning sent to: {sender_email}")

        if user_email:
            ok2, msg2 = send_user_notification(
                user_email, sender_email, subject,
                threat_type, risk_score, reasoning, action
            )
            actions_taken.append(f"{'✅' if ok2 else '❌'} You notified at: {user_email}")

        if auto_block or action == "BLOCKED":
            ok3, msg3 = block_sender(sender_email)
            actions_taken.append(f"🚫 {msg3}")

    elif risk_score >= 30:
        if user_email:
            ok2, msg2 = send_user_notification(
                user_email, sender_email, subject,
                threat_type, risk_score, reasoning, action
            )
            actions_taken.append(f"{'✅' if ok2 else '❌'} Warning notification sent to: {user_email}")
        else:
            actions_taken.append("⚠️ Medium risk — connect Gmail for full protection")
    else:
        actions_taken.append("✅ Email safe — no action needed")

    return actions_taken
