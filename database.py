import sqlite3
from datetime import datetime

# Database initialize karo
def init_db():
    conn = sqlite3.connect("safenet.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            message TEXT,
            risk_score INTEGER,
            threat_type TEXT,
            reasoning TEXT,
            action_taken TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Log save karo
def save_log(source, message, risk_score, threat_type, reasoning, action_taken):
    conn = sqlite3.connect("safenet.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scan_logs 
        (timestamp, source, message, risk_score, threat_type, reasoning, action_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source,
        message,
        risk_score,
        threat_type,
        reasoning,
        action_taken
    ))
    
    conn.commit()
    conn.close()

# Saare logs fetch karo
def get_all_logs():
    conn = sqlite3.connect("safenet.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, source, risk_score, threat_type, action_taken 
        FROM scan_logs 
        ORDER BY id DESC 
        LIMIT 50
    ''')
    
    logs = cursor.fetchall()
    conn.close()
    return logs

# Stats fetch karo
def get_stats():
    conn = sqlite3.connect("safenet.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM scan_logs")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scan_logs WHERE action_taken = 'BLOCKED'")
    blocked = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scan_logs WHERE action_taken = 'WARNING'")
    warned = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scan_logs WHERE action_taken = 'CLEAR'")
    safe = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total": total,
        "blocked": blocked,
        "warned": warned,
        "safe": safe
    }
