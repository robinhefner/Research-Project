import json
import csv
import os
import glob

def process_fhir_folder(input_dir='fhir_patienten', output_dir='output_csvs'):
    # Erstelle Ausgabeordner, falls nicht vorhanden
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Suche alle JSON-Dateien im Eingabeordner
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    
    if not json_files:
        print(f"Fehler: Keine .json Dateien im Ordner '{input_dir}' gefunden.")
        print("Bitte stelle sicher, dass der Ordner existiert und JSON-Dateien enthält.")
        return

    print(f"Starte Verarbeitung von {len(json_files)} FHIR-Patientendateien...")

    # Zentrale Listen für alle ausgelesenen Daten (über alle Dateien hinweg)
    patients_data = []
    encounters_data = []
    conditions_data = []
    medications_data = []
    observations_data = []

    # Iteriere durch jede gefundene JSON-Datei
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
        except Exception as e:
            print(f"Überspringe Datei {os.path.basename(file_path)} aufgrund eines Fehlers: {e}")
            continue # Mache mit der nächsten Datei weiter

        # Iteriere durch alle Ressourcen im aktuellen Bundle
        for entry in bundle.get('entry', []):
            resource = entry.get('resource', {})
            res_type = resource.get('resourceType')

            # ---------------- PATIENTS ----------------
            if res_type == 'Patient':
                patient_id = resource.get('id', '')
                
                name_list = resource.get('name', [{}])
                first_name = name_list[0].get('given', [''])[0] if name_list[0].get('given') else ''
                last_name = name_list[0].get('family', '')
                
                address_list = resource.get('address', [{}])
                address_line = address_list[0].get('line', [''])[0] if address_list[0].get('line') else ''
                city = address_list[0].get('city', '')
                zip_code = address_list[0].get('postalCode', '')
                
                patients_data.append({
                    'Id': patient_id, 'BIRTHDATE': resource.get('birthDate', ''),
                    'FIRST': first_name, 'LAST': last_name,
                    'GENDER': 'F' if resource.get('gender') == 'female' else ('M' if resource.get('gender') == 'male' else ''),
                    'ADDRESS': address_line, 'CITY': city, 'ZIP': zip_code,
                    'DEATHDATE': '', 'SSN': '', 'DRIVERS': '', 'PASSPORT': '', 'PREFIX': '', 
                    'MIDDLE': '', 'SUFFIX': '', 'MAIDEN': '', 'MARITAL': '', 'RACE': '', 
                    'ETHNICITY': '', 'BIRTHPLACE': '', 'STATE': '', 'COUNTY': '', 'FIPS': '', 
                    'LAT': '', 'LON': '', 'HEALTHCARE_EXPENSES': '', 'HEALTHCARE_COVERAGE': '', 'INCOME': ''
                })

            # ---------------- ENCOUNTERS ----------------
            elif res_type == 'Encounter':
                encounters_data.append({
                    'Id': resource.get('id', ''),
                    'START': resource.get('period', {}).get('start', ''),
                    'STOP': resource.get('period', {}).get('end', ''),
                    'PATIENT': resource.get('subject', {}).get('reference', '').replace('urn:uuid:', ''),
                    'ENCOUNTERCLASS': resource.get('class', {}).get('code', ''),
                    'CODE': '', 'DESCRIPTION': '', 'ORGANIZATION': '', 'PROVIDER': '', 'PAYER': '',
                    'BASE_ENCOUNTER_COST': '', 'TOTAL_CLAIM_COST': '', 'PAYER_COVERAGE': '', 
                    'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- CONDITIONS ----------------
            elif res_type == 'Condition':
                coding = resource.get('code', {}).get('coding', [{}])[0]
                conditions_data.append({
                    'START': '', 'STOP': '', 
                    'PATIENT': resource.get('subject', {}).get('reference', '').replace('urn:uuid:', ''),
                    'ENCOUNTER': resource.get('encounter', {}).get('reference', '').replace('urn:uuid:', ''),
                    'SYSTEM': coding.get('system', ''),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': coding.get('display', '')
                })

            # ---------------- MEDICATIONS ----------------
            elif res_type == 'MedicationRequest':
                coding = resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0]
                medications_data.append({
                    'START': '', 'STOP': '',
                    'PATIENT': resource.get('subject', {}).get('reference', '').replace('urn:uuid:', ''),
                    'ENCOUNTER': resource.get('encounter', {}).get('reference', '').replace('urn:uuid:', ''),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': coding.get('display', ''),
                    'PAYER': '', 'BASE_COST': '', 'PAYER_COVERAGE': '', 'DISPENSES': '', 
                    'TOTALCOST': '', 'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- OBSERVATIONS ----------------
            elif res_type == 'Observation':
                patient_ref = resource.get('subject', {}).get('reference', '').replace('urn:uuid:', '')
                encounter_ref = resource.get('encounter', {}).get('reference', '').replace('urn:uuid:', '')
                date = resource.get('effectiveDateTime', '')
                components = resource.get('component')
                
                if components: # Panel (z.B. Blutdruck)
                    for comp in components:
                        comp_coding = comp.get('code', {}).get('coding', [{}])[0]
                        vq = comp.get('valueQuantity', {})
                        observations_data.append({
                            'DATE': date, 'PATIENT': patient_ref, 'ENCOUNTER': encounter_ref,
                            'CATEGORY': '', 'CODE': comp_coding.get('code', ''),
                            'DESCRIPTION': comp_coding.get('display', ''),
                            'VALUE': vq.get('value', ''), 'UNITS': vq.get('unit', ''), 'TYPE': 'numeric'
                        })
                else: # Einzelwert
                    main_coding = resource.get('code', {}).get('coding', [{}])[0]
                    vq = resource.get('valueQuantity', {})
                    observations_data.append({
                        'DATE': date, 'PATIENT': patient_ref, 'ENCOUNTER': encounter_ref,
                        'CATEGORY': '', 'CODE': main_coding.get('code', ''),
                        'DESCRIPTION': main_coding.get('display', ''),
                        'VALUE': vq.get('value', ''), 'UNITS': vq.get('unit', ''), 'TYPE': 'numeric'
                    })

    # --- GESAMMELTE CSVs SCHREIBEN ---
    def write_csv(filename, data_list, columns):
        if not data_list:
            print(f"Überspringe {filename} (Keine Daten über alle Dateien hinweg gefunden).")
            return
            
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for row in data_list:
                writer.writerow(row)
        print(f"Erstellt: {filepath} (Gesamt: {len(data_list)} Einträge)")

    cols_patients = ['Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 'PREFIX', 'FIRST', 'MIDDLE', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL', 'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS', 'CITY', 'STATE', 'COUNTY', 'FIPS', 'ZIP', 'LAT', 'LON', 'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE', 'INCOME']
    cols_encounters = ['Id', 'START', 'STOP', 'PATIENT', 'ORGANIZATION', 'PROVIDER', 'PAYER', 'ENCOUNTERCLASS', 'CODE', 'DESCRIPTION', 'BASE_ENCOUNTER_COST', 'TOTAL_CLAIM_COST', 'PAYER_COVERAGE', 'REASONCODE', 'REASONDESCRIPTION']
    cols_conditions = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'SYSTEM', 'CODE', 'DESCRIPTION']
    cols_medications = ['START', 'STOP', 'PATIENT', 'PAYER', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'BASE_COST', 'PAYER_COVERAGE', 'DISPENSES', 'TOTALCOST', 'REASONCODE', 'REASONDESCRIPTION']
    cols_observations = ['DATE', 'PATIENT', 'ENCOUNTER', 'CATEGORY', 'CODE', 'DESCRIPTION', 'VALUE', 'UNITS', 'TYPE']

    print("\nSchreibe kombinierte CSV Dateien...")
    write_csv('patients.csv', patients_data, cols_patients)
    write_csv('encounters.csv', encounters_data, cols_encounters)
    write_csv('conditions.csv', conditions_data, cols_conditions)
    write_csv('medications.csv', medications_data, cols_medications)
    write_csv('observations.csv', observations_data, cols_observations)
    print("\nBatch-Konvertierung erfolgreich abgeschlossen!")

if __name__ == '__main__':
    process_fhir_folder(input_dir='llm_json', output_dir='synthea_csv_export_from_llm_json')