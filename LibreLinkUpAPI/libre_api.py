import requests
import json
import hashlib

EMAIL = ""
PASSWORD = ""
REGION = "de"

def get_libre_data():
    session = requests.Session()
    url_auth = f"https://api-{REGION}.libreview.io/llu/auth/login"
    headers = {
        "Content-Type": "application/json",
        "product": "llu.android",
        "version": "4.17.0",
        "distributor": "librelink",
        "installationId": "8ce6f446-7788-4687-9791-66380c356e9c"
    }
    payload = {"email": EMAIL, "password": PASSWORD}

    response = session.post(url_auth, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Login fehlgeschlagen: {response.status_code}")
        print(response.text)
        return

    auth_data = response.json()
    token = auth_data["data"]["authTicket"]["token"]
    user_id = auth_data["data"]["user"]["id"]
    
    account_id_hash = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
    
    url_connections = f"https://api-{REGION}.libreview.io/llu/connections"
    
    session.headers.update(headers)
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "account-id": account_id_hash
    })
    
    conn_response = session.get(url_connections)
    
    if "data" not in conn_response.json():
        print("Fehler beim Abrufen der Verbindungen.")
        return
        
    connections = conn_response.json()["data"]

    if not connections:
        patient_id = user_id
    else:
        patient_id = connections[0]["patientId"]

    url_readings = f"https://api-{REGION}.libreview.io/llu/connections/{patient_id}/graph"
    readings_response = session.get(url_readings)
    
    graph_data = readings_response.json()["data"]
    connection_data = graph_data["connection"]
    
    latest = connection_data["glucoseMeasurement"]
    print("\n--- Aktueller Wert ---")
    print(f"Wert:  {latest['Value']} mg/dL")
    print(f"Zeit:  {latest['Timestamp']}")
    trends = {1: "↓", 2: "↘", 3: "→", 4: "↗", 5: "↑"}
    print(f"Trend: {trends.get(latest['TrendArrow'], '??')}")

    print("\n--- Historische Werte (Graph) ---")
    history = graph_data.get("graphData", [])
    for entry in history:
        print(f"{entry['Timestamp']}: {entry['Value']} mg/dL")

    url_logbook = f"https://api-{REGION}.libreview.io/llu/connections/{patient_id}/logbook"
    logbook_response = session.get(url_logbook)
    
    if logbook_response.status_code == 200:
        logbook_entries = logbook_response.json().get("data", [])
        print(f"\n--- Logbuch Einträge ({len(logbook_entries)} gesamt) ---")
        for entry in logbook_entries[:10]:
            val = entry.get("Value") or entry.get("GlucoseMeasurement", {}).get("Value")
            ts = entry.get("Timestamp")
            if val:
                print(f"{ts}: {val} mg/dL")
    else:
        print(f"\nFehler beim Abrufen des Logbuchs: {logbook_response.status_code}")
    print("-" * 30)

if __name__ == "__main__":
    get_libre_data()
