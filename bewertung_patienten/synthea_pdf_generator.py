import pandas as pd
from weasyprint import HTML
import os

def generate_full_patient_pdfs(data_dir='.', output_dir='patienten_pdfs_komplett'):
    # Erstelle Ausgabeordner, falls nicht vorhanden
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Lade alle Synthea CSV-Daten (Dies kann einen Moment dauern)...")
    
    # Hilfsfunktion zum sicheren Laden von CSV-Dateien
    def load_csv(filename):
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            # dtype=str verhindert Probleme mit führenden Nullen (z.B. bei PLZ)
            return pd.read_csv(path, dtype=str).fillna('')
        else:
            print(f"Warnung: {filename} wurde nicht gefunden und wird übersprungen.")
            return pd.DataFrame()

    # Alle relevanten Tabellen laden
    patients = load_csv('patients.csv')
    allergies = load_csv('allergies.csv')
    careplans = load_csv('careplans.csv')
    claims = load_csv('claims.csv')
    claims_transactions = load_csv('claims_transactions.csv')
    conditions = load_csv('conditions.csv')
    devices = load_csv('devices.csv')
    encounters = load_csv('encounters.csv')
    imaging_studies = load_csv('imaging_studies.csv')
    immunizations = load_csv('immunizations.csv')
    medications = load_csv('medications.csv')
    observations = load_csv('observations.csv')
    payer_transitions = load_csv('payer_transitions.csv')
    procedures = load_csv('procedures.csv')
    supplies = load_csv('supplies.csv')

    if patients.empty:
        print("Fehler: patients.csv konnte nicht geladen werden. Abbruch.")
        return

    # HTML Template für die Hülle des Dokuments
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 15mm;
                background-color: #fdfbf7;
                @bottom-right {{
                    content: "Seite " counter(page) " von " counter(pages);
                    font-size: 8pt;
                    font-family: sans-serif;
                    color: #7f8c8d;
                }}
            }}
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #2c3e50;
                margin: 0; padding: 0;
            }}
            .header {{
                background-color: #2c3e50; color: white;
                padding: 15px; margin: -15mm -15mm 20px -15mm;
            }}
            .header h1 {{ margin: 0; font-size: 20pt; }}
            h2 {{
                color: #2980b9; border-bottom: 2px solid #2980b9;
                padding-bottom: 3px; font-size: 13pt; margin-top: 30px;
                page-break-after: avoid;
            }}
            table {{
                width: 100%; border-collapse: collapse;
                margin-top: 10px; font-size: 9pt;
                background-color: white; 
                /* page-break-inside: avoid; wurde hier entfernt! */
            }}
            thead {{
                display: table-header-group; /* Wiederholt die Spaltentitel auf der nächsten Seite */
            }}
            tr {{
                page-break-inside: avoid; /* Verhindert, dass Text innerhalb einer Zelle auf zwei Seiten zerrissen wird */
                page-break-after: auto;
            }}
            th, td {{ border: 1px solid #bdc3c7; padding: 6px; text-align: left; }}
            th {{ background-color: #ecf0f1; font-weight: bold; }}
            .info-item span {{ display: block; color: #7f8c8d; font-size: 8pt; text-transform: uppercase; }}
            .info-item strong {{ font-size: 11pt; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Klinische Patientenakte</h1>
        </div>

        <div class="info-grid">
            <div class="info-item"><span>Name</span><strong>{first} {last}</strong></div>
            <div class="info-item"><span>Patienten-ID</span><strong>{pat_id}</strong></div>
            <div class="info-item"><span>Geburtsdatum</span><strong>{dob}</strong></div>
            <div class="info-item"><span>Geschlecht</span><strong>{gender}</strong></div>
            <div class="info-item"><span>Adresse</span><strong>{address}, {city}, {state} {zip_code}</strong></div>
        </div>

        {content_html}
    </body>
    </html>
    '''

    # Dynamische Hilfsfunktion zur Generierung der HTML-Tabellen
    def build_html_table(df, title, columns_map, max_rows=100):
        if df.empty:
            return f"<h2>{title}</h2><p>Keine Einträge vorhanden.</p>"
        
        # Prüfe, welche Spalten tatsächlich im DataFrame existieren
        valid_cols = {k: v for k, v in columns_map.items() if k in df.columns}
        if not valid_cols:
            return ""

        html = f"<h2>{title}</h2><table><thead><tr>"
        for col_name in valid_cols.values():
            html += f"<th>{col_name}</th>"
        html += "</tr></thead><tbody>"
        
        # Um endlose PDFs zu vermeiden (z.B. bei Observations), limitieren wir die Zeilen optional
        df_subset = df.head(max_rows) 
        
        for _, row in df_subset.iterrows():
            html += "<tr>"
            for col_key in valid_cols.keys():
                val = str(row[col_key]) if pd.notna(row[col_key]) and str(row[col_key]).strip() != '' else '-'
                html += f"<td>{val}</td>"
            html += "</tr>"
        
        html += "</tbody></table>"
        if len(df) > max_rows:
            html += f"<p style='font-size: 8pt; color: #7f8c8d;'><i>... und {len(df)-max_rows} weitere Einträge (Ansicht auf {max_rows} limitiert)</i></p>"
            
        return html

    print(f"Starte PDF-Generierung für {len(patients)} Patienten...")
    
    # Optional: Limitiere hier für einen ersten Test auf die ersten 5 Patienten
    # for index, patient in patients.head(5).iterrows():
    for index, patient in patients.iterrows():
        pat_id = patient.get('Id', '')
        if not pat_id: continue

        content_html = ""
        
        # 1. Allergies
        pat_df = allergies[allergies['PATIENT'] == pat_id] if not allergies.empty and 'PATIENT' in allergies.columns else pd.DataFrame()
        content_html += build_html_table(pat_df, "Allergien", {'START': 'Start', 'STOP': 'Stop', 'DESCRIPTION': 'Allergie', 'DESCRIPTION1': 'Reaktion', 'SEVERITY1': 'Schweregrad'})

        # 2. Conditions (Diagnosen)
        pat_df = conditions[conditions['PATIENT'] == pat_id] if not conditions.empty and 'PATIENT' in conditions.columns else pd.DataFrame()
        content_html += build_html_table(pat_df, "Diagnosen (Conditions)", {'START': 'Start', 'STOP': 'Stop', 'DESCRIPTION': 'Beschreibung', 'CODE': 'Code'})

        # 3. Medications
        pat_df = medications[medications['PATIENT'] == pat_id] if not medications.empty and 'PATIENT' in medications.columns else pd.DataFrame()
        content_html += build_html_table(pat_df, "Medikamente", {'START': 'Start', 'STOP': 'Stop', 'DESCRIPTION': 'Medikament', 'REASONDESCRIPTION': 'Grund'})

        # # 4. Careplans
        # pat_df = careplans[careplans['PATIENT'] == pat_id] if not careplans.empty and 'PATIENT' in careplans.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Pflegepläne", {'START': 'Start', 'STOP': 'Stop', 'DESCRIPTION': 'Plan', 'REASONDESCRIPTION': 'Grund'})

        # 5. Encounters
        pat_df = encounters[encounters['PATIENT'] == pat_id] if not encounters.empty and 'PATIENT' in encounters.columns else pd.DataFrame()
        pat_df = pat_df.sort_values(by='START', ascending=False) if not pat_df.empty and 'START' in pat_df.columns else pat_df
        content_html += build_html_table(pat_df, "Behandlungen (Encounters)", {'START': 'Datum', 'ENCOUNTERCLASS': 'Klasse', 'DESCRIPTION': 'Beschreibung', 'REASONDESCRIPTION': 'Grund'})

        # # 6. Procedures (Eingriffe)
        # pat_df = procedures[procedures['PATIENT'] == pat_id] if not procedures.empty and 'PATIENT' in procedures.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Eingriffe (Procedures)", {'START': 'Datum', 'DESCRIPTION': 'Eingriff', 'REASONDESCRIPTION': 'Grund'})

        # # 7. Immunizations (Impfungen)
        # pat_df = immunizations[immunizations['PATIENT'] == pat_id] if not immunizations.empty and 'PATIENT' in immunizations.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Impfungen", {'DATE': 'Datum', 'DESCRIPTION': 'Impfstoff'})

        # # 8. Imaging Studies (Bildgebung)
        # pat_df = imaging_studies[imaging_studies['PATIENT'] == pat_id] if not imaging_studies.empty and 'PATIENT' in imaging_studies.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Bildgebung", {'DATE': 'Datum', 'MODALITY_DESCRIPTION': 'Methode', 'BODYSITE_DESCRIPTION': 'Körperregion', 'SOP_DESCRIPTION': 'Details'})

        # 9. Observations (Laborwerte/Vitalzeichen) - hier limitieren wir strenger, da extrem viele Daten!
        pat_df = observations[observations['PATIENT'] == pat_id] if not observations.empty and 'PATIENT' in observations.columns else pd.DataFrame()
        pat_df = pat_df.sort_values(by='DATE', ascending=False) if not pat_df.empty and 'DATE' in pat_df.columns else pat_df
        content_html += build_html_table(pat_df, "Labor & Vitalwerte (Observations)", {'DATE': 'Datum', 'DESCRIPTION': 'Parameter', 'VALUE': 'Wert', 'UNITS': 'Einheit'})

        # # 10. Devices (Geräte/Implantate)
        # pat_df = devices[devices['PATIENT'] == pat_id] if not devices.empty and 'PATIENT' in devices.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Geräte & Implantate", {'START': 'Start', 'STOP': 'Stop', 'DESCRIPTION': 'Gerät', 'UDI': 'UDI'})

        # # 11. Supplies (Verbrauchsmaterial)
        # pat_df = supplies[supplies['PATIENT'] == pat_id] if not supplies.empty and 'PATIENT' in supplies.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Materialien (Supplies)", {'DATE': 'Datum', 'DESCRIPTION': 'Material', 'QUANTITY': 'Menge'})

        # 12. Payer Transitions (Versicherungshistorie)
        # pat_df = payer_transitions[payer_transitions['PATIENT'] == pat_id] if not payer_transitions.empty and 'PATIENT' in payer_transitions.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Versicherungshistorie", {'START_DATE': 'Von', 'END_DATE': 'Bis', 'OWNER_NAME': 'Versicherer'})

        # # 13. Claims (Abrechnungen - ACHTUNG: Nutzt PATIENTID statt PATIENT)
        # pat_df = claims[claims['PATIENTID'] == pat_id] if not claims.empty and 'PATIENTID' in claims.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Abrechnungen (Claims)", {'SERVICEDATE': 'Datum', 'STATUS1': 'Status', 'DIAGNOSIS1': 'Diagnose-Code'})

        # # 14. Claims Transactions (Transaktionen - ACHTUNG: Nutzt PATIENTID statt PATIENT)
        # pat_df = claims_transactions[claims_transactions['PATIENTID'] == pat_id] if not claims_transactions.empty and 'PATIENTID' in claims_transactions.columns else pd.DataFrame()
        # content_html += build_html_table(pat_df, "Abrechnungspositionen", {'FROMDATE': 'Datum', 'TYPE': 'Typ', 'AMOUNT': 'Betrag', 'NOTES': 'Notiz'})

        # Sicheres Extrahieren für den Header
        def safe_get(val): return str(val) if pd.notna(val) else ""

        final_html = html_template.format(
            first=safe_get(patient.get('FIRST', '')),
            last=safe_get(patient.get('LAST', '')),
            pat_id=safe_get(pat_id),
            dob=safe_get(patient.get('BIRTHDATE', '')),
            gender=safe_get(patient.get('GENDER', '')),
            address=safe_get(patient.get('ADDRESS', '')),
            city=safe_get(patient.get('CITY', '')),
            state=safe_get(patient.get('STATE', '')),
            zip_code=safe_get(patient.get('ZIP', '')),
            content_html=content_html
        )

        safe_first = safe_get(patient.get('FIRST', 'Unbekannt'))
        safe_last = safe_get(patient.get('LAST', 'Unbekannt'))
        filename = f"{safe_first}_{safe_last}_{str(pat_id)[:8]}.pdf"
        output_file = os.path.join(output_dir, filename)
        
        try:
            HTML(string=final_html).write_pdf(output_file)
            print(f"Erstellt: {filename}")
        except Exception as e:
            print(f"Fehler bei {filename}: {e}")

if __name__ == '__main__':
    # generate_full_patient_pdfs("synthea_csv_export_from_llm_json", "patienten_pdfs_komplett_from_llm_json")
    generate_full_patient_pdfs("synthea_csv", "patienten_pdfs_komplett")