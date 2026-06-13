import pandas as pd
from weasyprint import HTML
import os
import re  # NEU: Modul für reguläre Ausdrücke importieren

def format_to_german_date(val):
        if not val or val == '-':
            return val
        try:
            # Konvertiert ISO (z.B. 2022-07-20T11:18:00+02:00) in datetime Objekt
            dt = pd.to_datetime(val)
            # Wenn ein 'T' enthalten ist, gehen wir von einem Zeitstempel aus
            if 'T' in str(val):
                return dt.strftime('%d.%m.%Y %H:%M')
            # Ansonsten nur das Datum
            return dt.strftime('%d.%m.%Y')
        except:
            return val

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
            }}
            thead {{
                display: table-header-group;
            }}
            tr {{
                page-break-inside: avoid;
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
            <div class="info-item"><span>Adresse</span><strong>{address}, {city}, {zip_code}</strong></div>
        </div>

        {content_html}
    </body>
    </html>
    '''

    # Dynamische Hilfsfunktion zur Generierung der HTML-Tabellen
    def build_html_table(df, title, columns_map, max_rows=100):
        if df.empty:
            return f"<h2>{title}</h2><p>Keine Einträge vorhanden.</p>"
        
        valid_cols = {k: v for k, v in columns_map.items() if k in df.columns}
        if not valid_cols:
            return ""

        html = f"<h2>{title}</h2><table><thead><tr>"
        html += "<th>ID</th>"
        for col_name in valid_cols.values():
            html += f"<th>{col_name}</th>"
        html += "</tr></thead><tbody>"
        
        df_subset = df.head(max_rows) 
        
        for idx, (_, row) in enumerate(df_subset.iterrows(), 1):
            html += "<tr>"
            html += f"<td>{idx}</td>"
            for col_key in valid_cols.keys():
                val = str(row[col_key]) if pd.notna(row[col_key]) and str(row[col_key]).strip() != '' else '-'
                
                date_fields = ['START', 'STOP', 'DATE', 'BIRTHDATE', 'SERVICEDATE', 'FROMDATE']
                if col_key in date_fields:
                    val = format_to_german_date(val)

                if col_key in ['DESCRIPTION', 'DESCRIPTION1', 'REASONDESCRIPTION'] and val != '-':
                    val = re.sub(r'\s*\([^)]*\)', '', val).strip()

                html += f"<td>{val}</td>"
            html += "</tr>"
        
        html += "</tbody></table>"
        # if len(df) > max_rows:
        #     html += f"<p style='font-size: 8pt; color: #7f8c8d;'><i>... und {len(df)-max_rows} weitere Einträge (Ansicht auf {max_rows} limitiert)</i></p>"
            
        return html

    print(f"Starte PDF-Generierung für {len(patients)} Patienten...")
    
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

        # 5. Encounters
        pat_df = encounters[encounters['PATIENT'] == pat_id] if not encounters.empty and 'PATIENT' in encounters.columns else pd.DataFrame()
        pat_df = pat_df.sort_values(by='START', ascending=False) if not pat_df.empty and 'START' in pat_df.columns else pat_df
        content_html += build_html_table(pat_df, "Behandlungen (Encounters)", {'START': 'Datum', 'ENCOUNTERCLASS': 'Klasse', 'DESCRIPTION': 'Beschreibung', 'REASONDESCRIPTION': 'Grund'})

        # 9. Observations (Laborwerte/Vitalzeichen)
        pat_df = observations[observations['PATIENT'] == pat_id] if not observations.empty and 'PATIENT' in observations.columns else pd.DataFrame()
        
        # Logik zum Filtern demographischer Daten (Code 56799-0)
        if not pat_df.empty and 'CODE' in pat_df.columns and 'DATE' in pat_df.columns:
            exclusion_dates = pat_df[pat_df['CODE'] == '56799-0']['DATE'].unique()
            pat_df = pat_df[~pat_df['DATE'].isin(exclusion_dates)]
            
        pat_df = pat_df.sort_values(by='DATE', ascending=False) if not pat_df.empty and 'DATE' in pat_df.columns else pat_df
        content_html += build_html_table(pat_df, "Labor & Vitalwerte (Observations)", {'DATE': 'Datum', 'DESCRIPTION': 'Parameter', 'VALUE': 'Wert', 'UNITS': 'Einheit'})


        # Sicheres Extrahieren für den Header
        def safe_get(val): return str(val) if pd.notna(val) else ""

        final_html = html_template.format(
            first=safe_get(patient.get('FIRST', '')),
            last=safe_get(patient.get('LAST', '')),
            pat_id=safe_get(pat_id),
            dob=format_to_german_date(patient.get('BIRTHDATE', '')),
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
    generate_full_patient_pdfs("synthea_csv_export_from_llm_json", "patienten_pdfs_komplett_from_llm_json")
    # generate_full_patient_pdfs("synthea_csv_export_from_mimic_III", "patienten_pdfs_komplett_from_mimic_III")
    generate_full_patient_pdfs("synthea_csv", "patienten_pdfs_komplett")