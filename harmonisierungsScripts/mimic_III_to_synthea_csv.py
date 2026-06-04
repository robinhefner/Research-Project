import psycopg2
from psycopg2 import Error
import csv
import os
import uuid
from datetime import datetime, timedelta
from faker import Faker

# --- KONFIGURATION ---
HOST = "lehre.mi.uni-heidelberg.de"
PORT = "55432"
USER = "pgread"
PASSWORD = "Wu5Hkc7UbP"
DATABASE = "mimic"
SCHEMA = "mimiciii"
OUTPUT_DIR = "synthea_csv_export_from_mimic_III"

# LIMITIERUNG DER PATIENTEN
PATIENT_LIMIT = 40

# --- FAKER INITIALISIERUNG ---
fake = Faker('de_DE')
# Seed setzen, damit bei jedem Durchlauf dieselben Namen generiert werden (optional, aber hilfreich zum Testen)
Faker.seed(42) 

patient_mapping = {}

def get_fake_patient_data(original_id, gender=None):
    """
    Sucht nach der alten ID im Mapping. Wenn sie neu ist, wird ein 
    komplett neues, konsistentes Fake-Profil generiert. Das Geschlecht 
    bestimmt den Vornamen.
    """
    clean_id = str(original_id).replace('urn:uuid:', '').replace('Patient/', '')
    
    if clean_id not in patient_mapping:
        # Geschlechtsspezifischer Vorname
        if gender == 'M':
            first_name = fake.first_name_male()
        elif gender == 'F':
            first_name = fake.first_name_female()
        else:
            first_name = fake.first_name() # Fallback

        patient_mapping[clean_id] = {
            'new_id': str(uuid.uuid4()),  # Neue UUID für Synthea
            'first_name': first_name,
            'last_name': fake.last_name(),
            'address': f"{fake.street_name()} {fake.building_number()}",
            'city': fake.city(),
            'zip': fake.postcode(),
            'state': fake.state() # in de_DE sind das Bundesländer
        }
    return patient_mapping[clean_id]


def export_synthea_csvs():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    connection = None
    try:
        print("Stelle Verbindung zur Datenbank her...")
        connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            dbname=DATABASE,
            options=f'-c search_path={SCHEMA}'
        )
        cursor = connection.cursor()

        # ---------------------------------------------------------
        # ZEITVERSCHIEBUNG BERECHNEN
        # ---------------------------------------------------------
        subset_query = f"(SELECT subject_id FROM patients ORDER BY subject_id LIMIT {PATIENT_LIMIT})"
        
        print("\nBerechne Zeitverschiebung pro Patient...")
        offset_query = f"""
            SELECT p.subject_id, 
                   MAX(p.dod) as max_dod, 
                   MAX(a.dischtime) as max_disch
            FROM patients p
            LEFT JOIN admissions a ON p.subject_id = a.subject_id
            WHERE p.subject_id IN {subset_query}
            GROUP BY p.subject_id;
        """
        cursor.execute(offset_query)
        
        patient_offsets = {}
        now = datetime.now()
        
        for row in cursor:
            subject_id = row[0]
            dates = [d for d in (row[1], row[2]) if d is not None]
            if dates:
                latest_date = max(dates)
                offset = latest_date - now
                patient_offsets[subject_id] = offset
            else:
                patient_offsets[subject_id] = timedelta(0)

        def format_shifted_date(dt_obj, subject_id, fmt='%Y-%m-%d'):
            if not dt_obj:
                return ''
            offset = patient_offsets.get(subject_id, timedelta(0))
            shifted_dt = dt_obj - offset
            return shifted_dt.strftime(fmt)

        # ---------------------------------------------------------
        # CSV GENERIERUNG
        # ---------------------------------------------------------
        def write_csv_from_query(filename, query, headers, row_mapper=None):
            filepath = os.path.join(OUTPUT_DIR, filename)
            print(f"Generiere {filename}...")
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                if query:
                    cursor.execute(query)
                    count = 0
                    for row in cursor:
                        if row_mapper:
                            mapped_row = row_mapper(row)
                            writer.writerow(mapped_row)
                        else:
                            writer.writerow(row)
                        count += 1
                    print(f" -> {count} Zeilen in {filename} geschrieben.")
                else:
                    print(f" -> Leere Datei (nur Header) erstellt.")


        # ==========================================
        # 1. PATIENTS.csv
        # ==========================================
        cols_patients = ['Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 'PREFIX', 'FIRST', 'MIDDLE', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL', 'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS', 'CITY', 'STATE', 'COUNTY', 'FIPS', 'ZIP', 'LAT', 'LON', 'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE', 'INCOME']
        
        query_patients = f"""
            SELECT subject_id, dob, dod, gender
            FROM patients
            WHERE subject_id IN {subset_query}
            ORDER BY subject_id;
        """
        def map_patients(row):
            subject_id = row[0]
            gender_db = row[3]
            gender_synthea = 'M' if gender_db == 'M' else ('F' if gender_db == 'F' else '')
            
            # Hole Fake-Daten passend zum Geschlecht
            fake_data = get_fake_patient_data(subject_id, gender_db)
            
            dob = format_shifted_date(row[1], subject_id, '%Y-%m-%d')
            dod = format_shifted_date(row[2], subject_id, '%Y-%m-%d')
            
            return [
                fake_data['new_id'],  # UUID statt MIMIC ID
                dob, dod, '', '', '', '', 
                fake_data['first_name'], '', fake_data['last_name'], '', '', '', '', '', 
                gender_synthea, '', fake_data['address'], fake_data['city'], fake_data['state'], '', '', fake_data['zip'], '', '', '', '', ''
            ]

        # WICHTIG: patients.csv MUSS zuerst generiert werden, damit get_fake_patient_data mit dem Geschlecht initialisiert wird!
        write_csv_from_query('patients.csv', query_patients, cols_patients, map_patients)


        # ==========================================
        # 2. ENCOUNTERS.csv
        # ==========================================
        cols_encounters = ['Id', 'START', 'STOP', 'PATIENT', 'ORGANIZATION', 'PROVIDER', 'PAYER', 'ENCOUNTERCLASS', 'CODE', 'DESCRIPTION', 'BASE_ENCOUNTER_COST', 'TOTAL_CLAIM_COST', 'PAYER_COVERAGE', 'REASONCODE', 'REASONDESCRIPTION']
        
        query_encounters = f"""
            SELECT hadm_id, admittime, dischtime, subject_id, admission_type
            FROM admissions
            WHERE subject_id IN {subset_query};
        """
        def map_encounters(row):
            subject_id = row[3]
            fake_data = get_fake_patient_data(subject_id) # Holt das bestehende Mapping inkl. UUID
            
            start = format_shifted_date(row[1], subject_id, '%Y-%m-%dT%H:%M:%SZ')
            stop = format_shifted_date(row[2], subject_id, '%Y-%m-%dT%H:%M:%SZ')
            return [row[0], start, stop, fake_data['new_id'], '', '', '', row[4], '', 'Hospital Admission', '', '', '', '', '']

        write_csv_from_query('encounters.csv', query_encounters, cols_encounters, map_encounters)


        # ==========================================
        # 3. CONDITIONS.csv
        # ==========================================
        cols_conditions = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'SYSTEM', 'CODE', 'DESCRIPTION']
        
        query_conditions = f"""
            SELECT a.admittime, a.dischtime, d.subject_id, d.hadm_id, d.icd9_code, dict.short_title
            FROM diagnoses_icd d
            JOIN admissions a ON d.hadm_id = a.hadm_id
            LEFT JOIN d_icd_diagnoses dict ON d.icd9_code = dict.icd9_code
            WHERE d.subject_id IN {subset_query};
        """
        def map_conditions(row):
            subject_id = row[2]
            fake_data = get_fake_patient_data(subject_id)
            
            start = format_shifted_date(row[0], subject_id, '%Y-%m-%d')
            stop = format_shifted_date(row[1], subject_id, '%Y-%m-%d')
            return [start, stop, fake_data['new_id'], row[3], 'ICD9', row[4], row[5]]

        write_csv_from_query('conditions.csv', query_conditions, cols_conditions, map_conditions)


        # ==========================================
        # 4. MEDICATIONS.csv
        # ==========================================
        cols_medications = ['START', 'STOP', 'PATIENT', 'PAYER', 'ENCOUNTER', 'CODE', 'DESCRIPTION', 'BASE_COST', 'PAYER_COVERAGE', 'DISPENSES', 'TOTALCOST', 'REASONCODE', 'REASONDESCRIPTION']
        
        query_medications = f"""
            SELECT startdate, enddate, subject_id, hadm_id, ndc, drug
            FROM prescriptions
            WHERE subject_id IN {subset_query};
        """
        def map_medications(row):
            subject_id = row[2]
            fake_data = get_fake_patient_data(subject_id)
            
            start = format_shifted_date(row[0], subject_id, '%Y-%m-%dT%H:%M:%SZ')
            stop = format_shifted_date(row[1], subject_id, '%Y-%m-%dT%H:%M:%SZ')
            return [start, stop, fake_data['new_id'], '', row[3], row[4], row[5], '', '', '', '', '', '']

        write_csv_from_query('medications.csv', query_medications, cols_medications, map_medications)


        # ==========================================
        # 5. OBSERVATIONS.csv
        # ==========================================
        cols_observations = ['DATE', 'PATIENT', 'ENCOUNTER', 'CATEGORY', 'CODE', 'DESCRIPTION', 'VALUE', 'UNITS', 'TYPE']
        
        query_observations = f"""
            SELECT l.charttime, l.subject_id, l.hadm_id, d.category, d.loinc_code, d.label, l.value, l.valueuom
            FROM labevents l
            JOIN d_labitems d ON l.itemid = d.itemid
            WHERE l.value IS NOT NULL 
              AND l.subject_id IN {subset_query};
        """
        def map_observations(row):
            subject_id = row[1]
            fake_data = get_fake_patient_data(subject_id)
            
            date = format_shifted_date(row[0], subject_id, '%Y-%m-%dT%H:%M:%SZ')
            code = row[4] if row[4] else 'MIMIC-INTERNAL'
            return [date, fake_data['new_id'], row[2], row[3], code, row[5], row[6], row[7], 'numeric']

        write_csv_from_query('observations.csv', query_observations, cols_observations, map_observations)


        # ==========================================
        # 6. ALLERGIES.csv
        # ==========================================
        cols_allergies = ['START', 'STOP', 'PATIENT', 'ENCOUNTER', 'CODE', 'SYSTEM', 'DESCRIPTION', 'TYPE', 'CATEGORY', 'REACTION1', 'DESCRIPTION1', 'SEVERITY1', 'REACTION2', 'DESCRIPTION2', 'SEVERITY2']
        
        write_csv_from_query('allergies.csv', None, cols_allergies)


    except Error as e:
        print(f"\n❌ Fehler bei der Verbindung oder Abfrage: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()
            print("\n" + "="*50)
            print("🔒 Die PostgreSQL-Verbindung wurde sicher geschlossen.")

if __name__ == "__main__":
    # Faker Modul muss via 'pip install faker' installiert sein
    export_synthea_csvs()