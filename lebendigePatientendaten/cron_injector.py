import os
import sqlite3
import json
import requests
from datetime import datetime
import re
import urllib3

DB_PATH = os.path.join(os.path.dirname(__file__), 'queue.db')
BAHMNI_FHIR_BASE_URL = 'https://kis-lab.mi.intern/openmrs/ws/fhir2/R4'
BAHMNI_AUTH = ('superman', 'Admin123')
VERIFY_SSL = False 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_db():
    return sqlite3.connect(DB_PATH)

def get_bahmni_id(internal_uuid, conn):
    c = conn.cursor()
    c.execute('SELECT bahmni_id FROM id_mapping WHERE internal_uuid = ?', (internal_uuid,))
    row = c.fetchone()
    return row[0] if row else None

def replace_references(payload_dict, conn):
    """Durchsucht das Dictionary rekursiv nach 'reference': 'urn:uuid:...' und ersetzt diese."""
    if isinstance(payload_dict, dict):
        for key, value in payload_dict.items():
            if key == 'reference' and isinstance(value, str) and value.startswith('urn:uuid:'):
                mapped_id = get_bahmni_id(value, conn)
                if mapped_id:
                    payload_dict[key] = mapped_id
                else:
                    raise Exception(f"Referenz {value} konnte nicht aufgelöst werden. Basis-Ressource fehlt.")
            else:
                replace_references(value, conn)
    elif isinstance(payload_dict, list):
        for item in payload_dict:
            replace_references(item, conn)

def process_queue():
    conn = setup_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT id, internal_uuid, resource_type, payload
        FROM fhir_queue
        WHERE status = 'pending' AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
    ''', (datetime.now().isoformat(),))
    
    rows = c.fetchall()
    if not rows:
        print("Keine fälligen Ressourcen in der Warteschlange.")
        conn.close()
        return

    for row in rows:
        row_id, internal_uuid, r_type, payload_str = row
        print(f"Verarbeite Ressource {r_type} ({internal_uuid})...")
        
        try:
            payload = json.loads(payload_str)
            
            replace_references(payload, conn)
            
            url = f"{BAHMNI_FHIR_BASE_URL}/{r_type}"
            headers = {'Content-Type': 'application/fhir+json'}
            response = requests.post(url, json=payload, auth=BAHMNI_AUTH, headers=headers, verify=VERIFY_SSL)
            if response.status_code in (200, 201):
                server_id = None
                if 'Location' in response.headers:
                    parts = response.headers['Location'].split('/')
                    try:
                        idx = parts.index(r_type)
                        server_id = f"{r_type}/{parts[idx+1]}"
                    except ValueError:
                        pass
                
                if not server_id:
                    resp_json = response.json()
                    server_id = f"{r_type}/{resp_json.get('id')}"
                
                if server_id:
                    c.execute('INSERT OR REPLACE INTO id_mapping (internal_uuid, bahmni_id) VALUES (?, ?)', 
                              (internal_uuid, server_id))
                
                c.execute("UPDATE fhir_queue SET status = 'success', http_response = 'OK' WHERE id = ?", (row_id,))
                print(f" -> Erfolg! Server-ID: {server_id}")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                c.execute("UPDATE fhir_queue SET status = 'error', http_response = ? WHERE id = ?", (error_msg, row_id))
                print(f" -> Fehler: {error_msg}")
            
                
        except Exception as e:
            c.execute("UPDATE fhir_queue SET status = 'error', http_response = ? WHERE id = ?", (str(e), row_id))
            print(f" -> Interner Fehler: {str(e)}")
            
        conn.commit()
        
    conn.close()

if __name__ == '__main__':
    process_queue()
