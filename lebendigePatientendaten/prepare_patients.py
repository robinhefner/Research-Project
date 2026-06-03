import os
import json
import sqlite3
import glob
from datetime import datetime, timedelta
from dateutil import parser
import re

INPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Generierte_Patienten'))
DB_PATH = os.path.join(os.path.dirname(__file__), 'queue.db')

# ZEITRAFFER-FAKTOR:
# 1.0 = Echtzeit (1 Tag in den Daten = 1 Tag Wartezeit)
# 1440.0 = 1 Minute Wartezeit entspricht 1 Tag in den Daten (24 * 60)
TIME_SPEEDUP_FACTOR = 1.0

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fhir_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            internal_uuid TEXT,
            resource_type TEXT,
            payload TEXT,
            scheduled_time DATETIME,
            status TEXT DEFAULT 'pending',
            http_response TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS id_mapping (
            internal_uuid TEXT PRIMARY KEY,
            bahmni_id TEXT
        )
    ''')
    conn.commit()
    return conn

def extract_time(resource):
    """Versucht, den relevanten Zeitstempel einer Ressource zu finden."""
    r_type = resource.get('resourceType')
    
    if r_type == 'Encounter':
        start = resource.get('period', {}).get('start')
        if start: return parser.isoparse(start)
    elif r_type == 'Condition':
        rec = resource.get('recordedDate')
        if rec: return parser.isoparse(rec)
    elif r_type == 'MedicationRequest':
        auth = resource.get('authoredOn')
        if auth: return parser.isoparse(auth)
    elif r_type == 'Observation':
        eff = resource.get('effectiveDateTime')
        if eff: return parser.isoparse(eff)
    
    return None

def process_file(filepath, conn):
    with open(filepath, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
        
    entries = bundle.get('entry', [])
    if not entries:
        return
        
    t_base = None
    for entry in entries:
        resource = entry.get('resource', {})
        time = extract_time(resource)
        if time:
            if t_base is None or time < t_base:
                t_base = time

    if not t_base:
        t_base = datetime.now(tz=parser.isoparse('2000-01-01T00:00:00Z').tzinfo)

    t_sim_start = datetime.now()
    c = conn.cursor()

    for entry in entries:
        full_url = entry.get('fullUrl', '')
        resource = entry.get('resource', {})
        r_type = resource.get('resourceType')
        
        internal_uuid = full_url if full_url.startswith('urn:uuid:') else f"urn:uuid:{resource.get('id', '')}"
        
        r_time = extract_time(resource)
        if r_time:
            delta = r_time - t_base
        else:
            delta = timedelta(seconds=0)
            
        scaled_delta_seconds = delta.total_seconds() / TIME_SPEEDUP_FACTOR
        scheduled_time = t_sim_start + timedelta(seconds=scaled_delta_seconds)
        
        c.execute('''
            INSERT INTO fhir_queue (internal_uuid, resource_type, payload, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (internal_uuid, r_type, json.dumps(resource), scheduled_time.isoformat(), 'pending'))
        
    conn.commit()
    print(f"Datei verarbeitet: {os.path.basename(filepath)} ({len(entries)} Ressourcen eingereiht)")

def main():
    print(f"Suche nach JSON-Dateien in {INPUT_DIR}...")
    files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
    if not files:
        print("Keine JSON-Dateien gefunden.")
        return
        
    conn = setup_db()
    for file in files:
        process_file(file, conn)
        
    conn.close()
    print("Pre-Processing abgeschlossen. Warteschlange ist gefüllt.")

if __name__ == '__main__':
    main()
