import requests
import json
import glob
import csv
import os
from deep_translator import GoogleTranslator

import uuid
from faker import Faker

# Initialisiere Faker (de_DE sorgt für deutsche Namen, Straßen und Städte)
fake = Faker('de_DE')

# Zentrales Mapping: Speichert zu jeder alten Patienten-ID die neuen Fake-Daten
patient_mapping = {}

def get_fake_patient_data(original_id):
    """
    Sucht nach der alten ID im Mapping. Wenn sie neu ist, wird ein 
    komplett neues, konsistentes Fake-Profil generiert.
    """
    clean_id = original_id.replace('urn:uuid:', '').replace('Patient/', '')
    
    if clean_id not in patient_mapping:
        patient_mapping[clean_id] = {
            'new_id': str(uuid.uuid4()),  # Generiert eine UUID wie 8ab00aef-fa9f...
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'address': f"{fake.street_name()} {fake.building_number()}", # Straße + Hausnummer
            'city': fake.city(),
            'zip': fake.postcode(),
            'state': fake.state()
        }
    return patient_mapping[clean_id]

CACHE_FILE = 'fhir_display_cache.json'

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warnung: Cache-Datei konnte nicht geladen werden ({e}).")
    return {}

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(DISPLAY_CACHE, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Warnung: Konnte Cache nicht speichern ({e}).")

DISPLAY_CACHE = load_cache()
# Initialisiere den Übersetzer (von automatisch erkannter Sprache nach Englisch)
translator = GoogleTranslator(source='auto', target='en')

def translate_to_english(text):
    """Hilfsfunktion für die automatische Übersetzung."""
    if not text:
        return ""
    try:
        # Übersetzt den Text und gibt ihn zurück
        english_text = translator.translate(text)
        return english_text
    except Exception as e:
        print(f"Warnung: Übersetzung fehlgeschlagen für '{text}' ({e})")
        return text # Fallback: Gib den Originaltext zurück

def fetch_and_translate(system, code, existing_display=""):
    """
    Holt den Namen (oder nutzt den vorhandenen), übersetzt ihn und speichert ihn.
    """
    if not system or not code:
        return ""

    cache_key = f"{system}|{code}"
    
    # 1. Lokalen Cache prüfen (ist es schon auf Englisch gespeichert?)
    if cache_key in DISPLAY_CACHE:
        return DISPLAY_CACHE[cache_key]

    # 2. Den zu übersetzenden Text ermitteln
    text_to_translate = existing_display

    # Wenn wir keinen Text aus dem JSON haben, fragen wir den Server
    if not text_to_translate:
        fhir_terminology_server = "http://hapi.fhir.org/baseR4/CodeSystem/$lookup"
        params = {"system": system, "code": code}
        
        try:
            response = requests.get(fhir_terminology_server, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for param in data.get("parameter", []):
                    if param.get("name") == "display":
                        text_to_translate = param.get("valueString", "")
                        break
        except requests.exceptions.RequestException:
            pass # Ignoriere Netzwerkfehler leise, Text bleibt leer

    # 3. Text übersetzen und cachen
    if text_to_translate:
        english_name = translate_to_english(text_to_translate)
        DISPLAY_CACHE[cache_key] = english_name
        save_cache()
        print(f"Gelernt & Übersetzt: {code} -> {english_name}")
        return english_name

    # 4. Unbekannter Code
    DISPLAY_CACHE[cache_key] = ""
    save_cache()
    return ""

def get_display(coding_dict):
    """
    Hauptfunktion, die in deinem Daten-Mapping aufgerufen wird.
    """
    if not coding_dict:
        return ""
        
    code = coding_dict.get('code')
    system = coding_dict.get('system')
    display = coding_dict.get('display', '')
    
    return fetch_and_translate(system, code, display)

def process_fhir_folder(input_dir='fhir_patienten', output_dir='output_csvs'):
    # Erstelle Ausgabeordner, falls nicht vorhanden
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Suche alle JSON-Dateien im Eingabeordner
    json_files = glob.glob(os.path.join(input_dir, '*.json'))
    
    if not json_files:
        print(f"Fehler: Keine .json Dateien im Ordner '{input_dir}' gefunden.")
        return

    print(f"Starte Verarbeitung von {len(json_files)} FHIR-Patientendateien...")

    # Zentrale Listen für alle ausgelesenen Daten
    patients_data = []
    encounters_data = []
    conditions_data = []
    medications_data = []
    observations_data = []
    allergies_data = []
    careplans_data = []
    claims_data = []
    claims_transactions_data = []
    devices_data = []
    imaging_studies_data = []
    immunizations_data = []
    organizations_data = []
    payers_data = []
    payer_transitions_data = []
    procedures_data = []
    providers_data = []
    supplies_data = []

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
        except Exception as e:
            print(f"Überspringe Datei {os.path.basename(file_path)} aufgrund eines Fehlers: {e}")
            continue

        for entry in bundle.get('entry', []):
            resource = entry.get('resource', {})
            res_type = resource.get('resourceType')

            def get_ref(field_name):
                ref = resource.get(field_name, {}).get('reference', '')
                clean_ref = ref.replace('urn:uuid:', '').replace('Patient/', '').replace('Encounter/', '')
                
                if not clean_ref:
                    return ''

                # Wenn die Referenz auf einen Patienten zeigt, gib die NEUE UUID zurück
                if ref.startswith('Patient/') or field_name in ['subject', 'patient']:
                    return get_fake_patient_data(clean_ref)['new_id']
                
                return clean_ref
            # ---------------- PATIENTS ----------------
            if res_type == 'Patient':
                original_id = resource.get('id', '')
                
                # Generiere oder lade das Fake-Profil für diese ID
                fake_profile = get_fake_patient_data(original_id)
                
                patients_data.append({
                    'Id': fake_profile['new_id'], 
                    'BIRTHDATE': resource.get('birthDate', ''),
                    'FIRST': fake_profile['first_name'], 
                    'LAST': fake_profile['last_name'],
                    'GENDER': 'F' if resource.get('gender') == 'female' else ('M' if resource.get('gender') == 'male' else ''),
                    'ADDRESS': fake_profile['address'], 
                    'CITY': fake_profile['city'], 
                    'STATE': fake_profile['state'], 
                    'ZIP': fake_profile['zip'],
                    'DEATHDATE': '', 'SSN': '', 'DRIVERS': '', 'PASSPORT': '', 'PREFIX': '', 
                    'MIDDLE': '', 'SUFFIX': '', 'MAIDEN': '', 'MARITAL': '', 'RACE': '', 
                    'ETHNICITY': '', 'BIRTHPLACE': '', 'COUNTY': '', 'FIPS': '', 
                    'LAT': '', 'LON': '', 'HEALTHCARE_EXPENSES': '', 'HEALTHCARE_COVERAGE': '', 'INCOME': ''
                })

            # ---------------- ENCOUNTERS ----------------
            elif res_type == 'Encounter':
                encounters_data.append({
                    'Id': resource.get('id', ''),
                    'START': resource.get('period', {}).get('start', ''),
                    'STOP': resource.get('period', {}).get('end', ''),
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTERCLASS': resource.get('class', {}).get('code', ''),
                    'CODE': '', 'DESCRIPTION': '', 'ORGANIZATION': '', 'PROVIDER': '', 'PAYER': '',
                    'BASE_ENCOUNTER_COST': '', 'TOTAL_CLAIM_COST': '', 'PAYER_COVERAGE': '', 
                    'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- CONDITIONS ----------------
            elif res_type == 'Condition':
                coding = resource.get('code', {}).get('coding', [{}])[0]
                conditions_data.append({
                    'START': resource.get('onsetDateTime', ''), 'STOP': resource.get('abatementDateTime', ''), 
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'SYSTEM': coding.get('system', ''),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding) # <--- ANGEPASST
                })

            # ---------------- MEDICATIONS ----------------
            elif res_type == 'MedicationRequest':
                coding = resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0]
                start = ''
                stop = ''
                dosage = resource.get('dosageInstruction', [{}])[0]
                bounds = dosage.get('timing', {}).get('repeat', {}).get('boundsPeriod', {})
                if bounds:
                    start = bounds.get('start', '')
                    stop = bounds.get('end', '')

                medications_data.append({
                    'START': start, 'STOP': stop,
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'PAYER': '', 'BASE_COST': '', 'PAYER_COVERAGE': '', 'DISPENSES': '', 
                    'TOTALCOST': '', 'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- OBSERVATIONS ----------------
            elif res_type == 'Observation':
                patient_ref = get_ref('subject')
                encounter_ref = get_ref('encounter')
                date = resource.get('effectiveDateTime', '')
                
                # Check ob category existiert
                category_list = resource.get('category', [{}])
                category = category_list[0].get('coding', [{}])[0].get('code', '') if category_list else ''
                
                components = resource.get('component')
                
                if components: # Panel (z.B. Blutdruck)
                    for comp in components:
                        comp_coding = comp.get('code', {}).get('coding', [{}])[0]
                        vq = comp.get('valueQuantity', {})
                        observations_data.append({
                            'DATE': date, 'PATIENT': patient_ref, 'ENCOUNTER': encounter_ref,
                            'CATEGORY': category, 'CODE': comp_coding.get('code', ''),
                            'DESCRIPTION': get_display(comp_coding), # <--- ANGEPASST
                            'VALUE': vq.get('value', ''), 'UNITS': vq.get('unit', ''), 'TYPE': 'numeric'
                        })
                else: # Einzelwert
                    main_coding = resource.get('code', {}).get('coding', [{}])[0]
                    vq = resource.get('valueQuantity', {})
                    observations_data.append({
                        'DATE': date, 'PATIENT': patient_ref, 'ENCOUNTER': encounter_ref,
                        'CATEGORY': category, 'CODE': main_coding.get('code', ''),
                        'DESCRIPTION': get_display(main_coding), # <--- ANGEPASST
                        'VALUE': vq.get('value', ''), 'UNITS': vq.get('unit', ''), 'TYPE': 'numeric'
                    })

            # ---------------- ALLERGIES ----------------
            elif res_type == 'AllergyIntolerance':
                coding = resource.get('code', {}).get('coding', [{}])[0]
                reaction = resource.get('reaction', [{}])[0] if resource.get('reaction') else {}
                manifestation = reaction.get('manifestation', [{}])[0].get('coding', [{}])[0] if reaction.get('manifestation') else {}
                categories = resource.get('category', [''])
                
                allergies_data.append({
                    'START': resource.get('onsetDateTime', resource.get('recordedDate', '')),
                    'STOP': resource.get('abatementDateTime', ''),
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'SYSTEM': coding.get('system', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'TYPE': resource.get('type', ''),
                    'CATEGORY': categories[0] if categories else '',
                    'REACTION1': manifestation.get('code', ''),
                    'DESCRIPTION1': get_display(manifestation), # <--- ANGEPASST
                    'SEVERITY1': reaction.get('severity', ''),
                    'REACTION2': '', 'DESCRIPTION2': '', 'SEVERITY2': ''
                })

            # ---------------- CAREPLANS ----------------
            elif res_type == 'CarePlan':
                coding = resource.get('category', [{}])[0].get('coding', [{}])[0] if resource.get('category') else {}
                careplans_data.append({
                    'Id': resource.get('id', ''),
                    'START': resource.get('period', {}).get('start', ''),
                    'STOP': resource.get('period', {}).get('end', ''),
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- PROCEDURES ----------------
            elif res_type == 'Procedure':
                coding = resource.get('code', {}).get('coding', [{}])[0]
                start_date = resource.get('performedDateTime', '')
                if not start_date and 'performedPeriod' in resource:
                    start_date = resource['performedPeriod'].get('start', '')
                stop_date = resource.get('performedPeriod', {}).get('end', '')

                procedures_data.append({
                    'START': start_date, 'STOP': stop_date,
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'SYSTEM': coding.get('system', ''),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'BASE_COST': '', 'REASONCODE': '', 'REASONDESCRIPTION': ''
                })

            # ---------------- IMMUNIZATIONS ----------------
            elif res_type == 'Immunization':
                coding = resource.get('vaccineCode', {}).get('coding', [{}])[0]
                immunizations_data.append({
                    'DATE': resource.get('occurrenceDateTime', ''),
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'BASE_COST': ''
                })

            # ---------------- DEVICES ----------------
            elif res_type in ['Device', 'DeviceRequest']:
                coding = resource.get('code', {}).get('coding', [{}])[0] if res_type == 'DeviceRequest' else resource.get('type', {}).get('coding', [{}])[0]
                devices_data.append({
                    'START': resource.get('authoredOn', ''), 'STOP': '',
                    'PATIENT': get_ref('subject') if res_type == 'DeviceRequest' else resource.get('patient', {}).get('reference', '').replace('urn:uuid:', ''),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'UDI': ''
                })

            # ---------------- IMAGING STUDIES ----------------
            elif res_type == 'ImagingStudy':
                series = resource.get('series', [{}])[0]
                modality = series.get('modality', {})
                body_site = series.get('bodySite', {})
                imaging_studies_data.append({
                    'Id': resource.get('id', ''),
                    'DATE': resource.get('started', ''),
                    'PATIENT': get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'SERIES_UID': series.get('uid', ''),
                    'BODYSITE_CODE': body_site.get('code', ''),
                    'BODYSITE_DESCRIPTION': get_display(body_site), # <--- ANGEPASST
                    'MODALITY_CODE': modality.get('code', ''),
                    'MODALITY_DESCRIPTION': get_display(modality), # <--- ANGEPASST
                    'INSTANCE_UID': '', 'SOP_CODE': '', 'SOP_DESCRIPTION': '', 'PROCEDURE_CODE': ''
                })

            # ---------------- SUPPLIES ----------------
            elif res_type in ['SupplyDelivery', 'SupplyRequest']:
                coding = resource.get('itemCodeableConcept', {}).get('coding', [{}])[0] if resource.get('itemCodeableConcept') else {}
                supplies_data.append({
                    'DATE': resource.get('authoredOn', resource.get('occurrenceDateTime', '')),
                    'PATIENT': resource.get('patient', {}).get('reference', '').replace('urn:uuid:', '') if res_type == 'SupplyDelivery' else get_ref('subject'),
                    'ENCOUNTER': get_ref('encounter'),
                    'CODE': coding.get('code', ''),
                    'DESCRIPTION': get_display(coding), # <--- ANGEPASST
                    'QUANTITY': resource.get('quantity', {}).get('value', '')
                })

    # --- GESAMMELTE CSVs SCHREIBEN (MIT DEDUPLIZIERUNG) ---
    def write_csv(filename, data_list, columns):
        if not data_list:
            print(f"Überspringe {filename} (Keine Daten gefunden).")
            return
            
        # --- DEDUPLIZIERUNG START ---
        unique_data = []
        seen = set()
        for row in data_list:
            # Konvertiere das Dictionary in ein Tuple aus Items, da Dictionaries nicht hashbar sind
            # Wir sortieren die Items, um sicherzugehen, dass die Reihenfolge im Dict egal ist
            row_tuple = tuple(sorted(row.items()))
            if row_tuple not in seen:
                seen.add(row_tuple)
                unique_data.append(row)
        # --- DEDUPLIZIERUNG ENDE ---
            
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for row in unique_data:
                writer.writerow(row)
        
        duplicates_removed = len(data_list) - len(unique_data)
        if duplicates_removed > 0:
            print(f"Erstellt: {filepath} ({len(unique_data)} Einträge, {duplicates_removed} Duplikate entfernt)")
        else:
            print(f"Erstellt: {filepath} ({len(unique_data)} Einträge)")

    cols_allergies = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'CODE', 'SYSTEM', 'DESCRIPTION', 'TYPE', 'CATEGORY', 'REACTION1', 'DESCRIPTION1', 'SEVERITY1', 'REACTION2', 'DESCRIPTION2', 'SEVERITY2']
    cols_careplans = ['Id', 'START', 'STOP', 'PATIENT', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'REASONCODE', 'REASONDESCRIPTION']
    cols_claims = ['Id', 'PATIENTID', 'PROVIDERID', 'PRIMARYPATIENTINSURANCEID', 'SECONDARYPATIENTINSURANCEID', 'DEPARTMENTID', 'PATIENTDEPARTMENTID', 'DIAGNOSIS1', 'DIAGNOSIS2', 'DIAGNOSIS3', 'DIAGNOSIS4', 'DIAGNOSIS5', 'DIAGNOSIS6', 'DIAGNOSIS7', 'DIAGNOSIS8', 'REFERRINGPROVIDERID', 'APPOINTMENTID', 'CURRENTILLNESSDATE', 'SERVICEDATE', 'SUPERVISINGPROVIDERID', 'STATUS1', 'STATUS2', 'STATUSP', 'OUTSTANDING1', 'OUTSTANDING2', 'OUTSTANDINGP', 'LASTBILLEDDATE1', 'LASTBILLEDDATE2', 'LASTBILLEDDATEP', 'HEALTHCARECLAIMTYPEID1', 'HEALTHCARECLAIMTYPEID2']
    cols_claims_transactions = ['ID', 'CLAIMID', 'CHARGEID', 'PATIENTID', 'TYPE', 'AMOUNT', 'METHOD', 'FROMDATE', 'TODATE', 'PLACEOFSERVICE', 'PROCEDURECODE', 'MODIFIER1', 'MODIFIER2', 'DIAGNOSISREF1', 'DIAGNOSISREF2', 'DIAGNOSISREF3', 'DIAGNOSISREF4', 'UNITS', 'DEPARTMENTID', 'NOTES', 'UNITAMOUNT', 'TRANSFEROUTID', 'TRANSFERTYPE', 'PAYMENTS', 'ADJUSTMENTS', 'TRANSFERS', 'OUTSTANDING', 'APPOINTMENTID', 'LINENOTE', 'PATIENTINSURANCEID', 'FEESCHEDULEID', 'PROVIDERID', 'SUPERVISINGPROVIDERID']
    cols_conditions = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'SYSTEM', 'CODE', 'DESCRIPTION']
    cols_devices = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'UDI']
    cols_encounters = ['Id', 'START', 'STOP', 'PATIENT', 'ORGANIZATION', 'PROVIDER', 'PAYER', 'ENCOUNTERCLASS', 'CODE', 'DESCRIPTION', 'BASE_ENCOUNTER_COST', 'TOTAL_CLAIM_COST', 'PAYER_COVERAGE', 'REASONCODE', 'REASONDESCRIPTION']
    cols_imaging_studies = ['Id', 'DATE', 'PATIENT', 'ENCOUNTER', 'SERIES_UID', 'BODYSITE_CODE', 'BODYSITE_DESCRIPTION', 'MODALITY_CODE', 'MODALITY_DESCRIPTION', 'INSTANCE_UID', 'SOP_CODE', 'SOP_DESCRIPTION', 'PROCEDURE_CODE']
    cols_immunizations = ['DATE', 'PATIENT', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'BASE_COST']
    cols_medications = ['START', 'STOP', 'PATIENT', 'PAYER', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'BASE_COST', 'PAYER_COVERAGE', 'DISPENSES', 'TOTALCOST', 'REASONCODE', 'REASONDESCRIPTION']
    cols_observations = ['DATE', 'PATIENT', 'ENCOUNTER', 'CATEGORY', 'CODE', 'DESCRIPTION', 'VALUE', 'UNITS', 'TYPE']
    cols_organizations = ['Id', 'NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP', 'LAT', 'LON', 'PHONE', 'REVENUE', 'UTILIZATION']
    cols_patients = ['Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 'PREFIX', 'FIRST', 'MIDDLE', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL', 'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS', 'CITY', 'STATE', 'COUNTY', 'FIPS', 'ZIP', 'LAT', 'LON', 'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE', 'INCOME']
    cols_payers = ['Id', 'NAME', 'OWNERSHIP', 'ADDRESS', 'CITY', 'STATE_HEADQUARTERED', 'ZIP', 'PHONE', 'AMOUNT_COVERED', 'AMOUNT_UNCOVERED', 'REVENUE', 'COVERED_ENCOUNTERS', 'UNCOVERED_ENCOUNTERS', 'COVERED_MEDICATIONS', 'UNCOVERED_MEDICATIONS', 'COVERED_PROCEDURES', 'UNCOVERED_PROCEDURES', 'COVERED_IMMUNIZATIONS', 'UNCOVERED_IMMUNIZATIONS', 'UNIQUE_CUSTOMERS', 'QOLS_AVG', 'MEMBER_MONTHS']
    cols_payer_transitions = ['PATIENT', 'MEMBERID', 'START_DATE', 'END_DATE', 'PAYER', 'SECONDARY_PAYER', 'PLAN_OWNERSHIP', 'OWNER_NAME']
    cols_procedures = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'SYSTEM', 'CODE', 'DESCRIPTION', 'BASE_COST', 'REASONCODE', 'REASONDESCRIPTION']    
    cols_providers = ['Id', 'ORGANIZATION', 'NAME', 'GENDER', 'SPECIALITY', 'ADDRESS', 'CITY', 'STATE', 'ZIP', 'LAT', 'LON', 'ENCOUNTERS', 'PROCEDURES']
    cols_supplies = ['DATE', 'PATIENT', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'QUANTITY']

    print("\nSchreibe kombinierte CSV Dateien...")
    write_csv('patients.csv', patients_data, cols_patients)
    write_csv('allergies.csv', allergies_data, cols_allergies)
    write_csv('careplans.csv', careplans_data, cols_careplans)
    write_csv('claims.csv', claims_data, cols_claims)
    write_csv('claims_transactions.csv', claims_transactions_data, cols_claims_transactions)
    write_csv('conditions.csv', conditions_data, cols_conditions)
    write_csv('devices.csv', devices_data, cols_devices)
    write_csv('encounters.csv', encounters_data, cols_encounters)
    write_csv('imaging_studies.csv', imaging_studies_data, cols_imaging_studies)
    write_csv('immunizations.csv', immunizations_data, cols_immunizations)
    write_csv('medications.csv', medications_data, cols_medications)
    write_csv('observations.csv', observations_data, cols_observations)
    write_csv('organizations.csv', organizations_data, cols_organizations)
    write_csv('payers.csv', payers_data, cols_payers)
    write_csv('payer_transitions.csv', payer_transitions_data, cols_payer_transitions)
    write_csv('procedures.csv', procedures_data, cols_procedures)
    write_csv('providers.csv', providers_data, cols_providers)
    write_csv('supplies.csv', supplies_data, cols_supplies)
    
    print("\nBatch-Konvertierung erfolgreich abgeschlossen!")

if __name__ == '__main__':
    process_fhir_folder(input_dir='musterspende_echte_patienten', output_dir='synthea_csv_export_from_musterdaten')