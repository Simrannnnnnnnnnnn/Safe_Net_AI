import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_gmail_service():
    creds = None
    
    # Token already hai toh use karo
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Token nahi hai ya expire ho gaya
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Token save karo
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('gmail', 'v1', credentials=creds)
    return service


def get_recent_emails(max_results=10):
    try:
        service = get_gmail_service()
        
        # Last 10 emails fetch karo
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            # Full message fetch karo
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # Headers se sender aur subject nikalo
            headers = message['payload']['headers']
            sender = ""
            subject = ""
            
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                if header['name'] == 'Subject':
                    subject = header['value']
            
            # Body nikalo
            body = get_email_body(message)
            
            emails.append({
                'id': msg['id'],
                'sender': sender,
                'subject': subject,
                'body': body[:500]  # first 500 chars
            })
        
        return emails
    
    except Exception as e:
        return []


def get_email_body(message):
    try:
        payload = message['payload']
        
        # Simple body
        if 'body' in payload and payload['body'].get('data'):
            data = payload['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Multipart body
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return "Could not extract email body"
    
    except Exception:
        return "Could not extract email body"


def block_sender(sender_email):
    try:
        service = get_gmail_service()
        
        # Sender ka email extract karo
        if '<' in sender_email:
            sender_email = sender_email.split('<')[1].split('>')[0]
        
        # Filter banao — is sender ke emails directly trash mein
        filter_body = {
            'criteria': {
                'from': sender_email
            },
            'action': {
                'addLabelIds': ['TRASH'],
                'removeLabelIds': ['INBOX']
            }
        }
        
        service.users().settings().filters().create(
            userId='me',
            body=filter_body
        ).execute()
        
        return True, f"{sender_email} successfully blocked!"
    
    except Exception as e:
        return False, f"Block failed: {str(e)}"
