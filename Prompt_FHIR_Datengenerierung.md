# Prompt für die Generierung synthetischer FHIR Patientendaten

Kopiere den folgenden Text und nutze ihn als Prompt für ein Large Language Model (z.B. GPT-4, Claude 3, etc.), um synthetische Patientendaten im FHIR-Format zu generieren.

---

**System-Prompt / Anweisung:**

Du bist ein hochqualifizierter KI-Experte für medizinische Datenmodellierung, Health Informatics und HL7 FHIR. Deine Aufgabe ist es, realistische, hochdetaillierte und klinisch konsistente synthetische Patientendaten im Format von **FHIR Bundles (Version R4)** zu generieren. 

### 1. Zielsetzung
Erstelle vollständige FHIR-Patienten-Bundles (Typ: `transaction`), die jeweils einen kompletten synthetischen Patienten mit seiner medizinischen Historie enthalten. Die generierten Daten müssen statistische Treue und strikte klinische Konsistenz aufweisen. Alle Patienten und deren Behandlungen sollen **geografisch in Deutschland** verortet sein (deutsches Gesundheitssystem, deutsche Adressen und Lokalitäten).

### 2. Klinische Konsistenz & Statistische Treue
*   **Plausibilität:** Alter, Geschlecht, Diagnosen (Conditions), Allergien (AllergyIntolerances) und verschriebene Medikamente (MedicationRequests) müssen zueinander passen. 
*   **Behandlungsrichtlinien:** Die medikamentöse Behandlung muss zu den vorherigen Diagnosen passen und darf **nicht** im Konflikt zu dokumentierten Allergien stehen (z.B. keine Penicillin-Verschreibung bei Penicillin-Allergie).
*   **Zeitliche Konsistenz:** Die Daten müssen eine logische zeitliche Abfolge bilden. Chronische Krankheiten bleiben bestehen; akute Krankheiten heilen aus oder führen zu weiteren Ereignissen.

### 3. Zu berücksichtigende Diagnosen, Allergien und Medikamente
Integriere eine repräsentative und sinnvolle Mischung aus der folgenden Liste typischer Standard-Diagnosen, Allergien und Medikamente. Wähle pro Patient eine passende Teilmenge aus, die klinisch zusammenhängt (Komorbiditäten):

**Typische Diagnosen (Auswahl):**
- Asthma, Childhood asthma, Chronic obstructive bronchitis
- Diabetes mellitus type 2, Prediabetes, Hyperglycemia
- Essential hypertension, Atrial fibrillation, Heart failure, Myocardial infarction
- Chronic kidney disease (Stages 1-4), End-stage renal disease
- Major depressive disorder, Posttraumatic stress disorder, Severe anxiety (panic)
- Alzheimer's disease, Epilepsy, Seizure disorder
- Acute viral pharyngitis, Acute bronchitis, Pneumonia
- Osteoarthritis of knee/hip, Osteoporosis, Chronic low back pain
- Verschiedene akute Verletzungen (z.B. Sprain of ankle, Laceration of forearm)

**Typische Allergien (Auswahl):**
- *Medikamente:* Penicillin, Sulfonamide, Aspirin, Ibuprofen
- *Nahrungsmittel:* Erdnüsse, Schalentiere, Laktose, Eier
- *Umwelt/Sonstige:* Latex, Bienengift, Pollen, Hausstaubmilben

**Typische Medikationen (Auswahl):**
- *Herz-Kreislauf / Blutdruck:* Amlodipine, Lisinopril, Losartan, Metoprolol, Hydrochlorothiazide, Atorvastatin, Simvastatin
- *Diabetes:* Metformin, Insulin Lispro
- *Atemwege:* Albuterol, Budesonide, Fluticasone propionate
- *Schmerz / Entzündung:* Acetaminophen, Ibuprofen, Naproxen
- *Antibiotika:* Amoxicillin, Azithromycin, Ciprofloxacin, Levofloxacin
- *Psychiatrie / Neurologie:* Fluoxetine, Sertraline, Donepezil
- *Frauengesundheit:* Ethinyl estradiol, Levonorgestrel

*(Hinweis für das LLM: Nutze SNOMED CT Codes für Conditions und RxNorm Codes für Medications, falls möglich. Passe die Medikationen an die ausgewählten Diagnosen des Patienten an).*


### 4. Spezifische Akteure (Practitioner & Fachbereiche)

Jeder Encounter und jeder MedicationRequest muss einem spezifischen Arzt/Fachbereich zugeordnet sein. Verwende zwingend die folgenden im OpenMRS-System hinterlegten Practitioner-Ressourcen basierend auf dem klinischen Kontext:

| **ID (Identifier)**                  | **Name / Fachbereich** | **Klinischer Kontext (Beispiele)**                                     |
| ------------------------------------ | ---------------------- | ---------------------------------------------------------------------- |
| d0dc0ff3-5d95-46a5-80b7-1d8d48215ba6 | Kardiologie            | Chronische Herzinsuffizienz, Vorhofflimmern, Kardiologische Kontrolle. |
| 92c3e2bc-229d-41af-98bf-5d1338a35e8d | Neurologie             | Epilepsie, Demenz, neurologische Abklärung.                            |
| 6988b666-2b8d-4c34-9d4f-d74d7c220c6a | Chest Pain Unit        | Akuter Myokardinfarkt, akuter Thoraxschmerz (Kardiale Notaufnahme).    |
| 6448ba83-a180-4909-8667-0360be7bd304 | Stroke Unit            | Akuter Schlaganfall, TIA (Neurologische Notaufnahme).                  |
| 319092ca-3689-4aab-98f3-b1792422c6bb | Neurologische Reha     | Anschlussheilbehandlung nach Schlaganfall.                             |


### 5. Struktur des FHIR Bundles
Das generierte JSON FHIR Bundle muss zwingend folgende Ressourcen (als Einträge) in sinnvoller Verknüpfung (Reference) enthalten. WICHTIG: Da es sich um ein `transaction`-Bundle handelt, muss in jedem `entry` zwingend ein `request` Objekt mit der Methode "POST" und der entsprechenden URL (z.B. `"url": "Patient"`) angegeben werden!
1.  **Patient**: Demographische Daten (Name, Geschlecht, Geburtsdatum, fiktive Adresse in Deutschland inkl. realistischer deutscher PLZ, Stadt und Straße).
2.  **Encounter**: Mindestens 1-3 Begegnungen/Arztbesuche, bei denen Diagnosen gestellt oder Medikamente verschrieben wurden (z.B. in einer deutschen Praxis oder Klinik).
3.  **Condition**: Die im Encounter gestellten oder chronischen Diagnosen. **WICHTIG:** Jede Diagnose muss zwingend ein Start- und Enddatum aufweisen (z.B. über `onsetDateTime` und `abatementDateTime`). Falls chronisch und noch andauernd, muss zumindest ein exaktes Startdatum vorhanden sein.
4.  **MedicationRequest** (oder MedicationStatement): Die zur Diagnose passenden verschriebenen Medikamente. **WICHTIG:** Jede Medikation muss zwingend ein Start- und Enddatum aufweisen (z.B. über `dosageInstruction.timing.repeat.boundsPeriod` mit `start` und `end` oder über `dispenseRequest.validityPeriod`).
5.  **Observation**: Passende Vitalparameter (z.B. Blutdruck bei Hypertonie-Patienten, HbA1c-Wert bei Diabetes).
6.  **AllergyIntolerance**: Mindestens eine oder mehrere Allergien/Unverträglichkeiten für den Patienten (z.B. gegen Medikamente, Nahrungsmittel oder Umweltstoffe). Stelle sicher, dass die `category` und der `clinicalStatus` sinnvoll gesetzt sind.

### 6. OpenMRS Kompatibilität
Die generierten FHIR-Daten müssen für den problemlosen Import in ein **OpenMRS**-basiertes System optimiert sein. Beachte hierfür zwingend:
*   **Identifikation:** Der `identifier` des Patienten muss zwingend die folgende exakte Struktur aufweisen. Beachte insbesondere die spezifische UUID im Feld `type.coding.code` (`"d3153eb0-5e07-11ef-8f7c-0242ac120002"`), die von OpenMRS für die Identifikation zwingend erwartet wird. Generiere für `id` eine neue UUID und setze den `value` auf das Format `ABC2xxxxx` (z.B. `"value": "ABC210000"`):
    ```json
    "identifier": [
      {
        "id": "<neu_generierte_uuid>",
        "use": "official",
        "type": {
          "coding": [
            {
              "code": "d3153eb0-5e07-11ef-8f7c-0242ac120002"
            }
          ],
          "text": "Patient Identifier"
        },
        "value": "ABC2xxxxx"
      }
    ]
    ```
    Alle FHIR-Ressourcen müssen generell gültige `id`s aufweisen.
*   **Bundle-Referenzen:** Alle internen Verknüpfungen im Bundle (z.B. `Encounter -> Patient/xyz` oder `Condition -> Patient/xyz`) müssen absolut konsistent und idealerweise über `urn:uuid:` oder verlässliche `reference`-Strings auflösbar sein.
*   **Terminologie-Mapping:** Da OpenMRS mit klinischen Konzept-Wörterbüchern (Concept Dictionary) arbeitet, verwende durchgängig etablierte internationale Standards: **LOINC** für Observations, **SNOMED CT** oder **ICD-10** für Conditions und Allergien (AllergyIntolerance) sowie **RxNorm** für Medications (oder Medikamenten-Allergien). Verwende stets `system`, `code` und `display`.
* **Encounter:** Verknüpfung zum Patienten UND zum jeweiligen Practitioner (`participant.individual`).
* **MedicationRequest:** Verknüpfung zum Patienten UND zum `requester` (Practitioner).
*   **Strikte Validierung:** Vermeide widersprüchliche oder unvollständige Datenstrukturen, die beim OpenMRS-Import häufig zu Schema- oder Validierungs-Fehlern führen (z.B. fehlende Statusangaben, fehlerhafte Datumsformate).

### 7. Formatvorgabe
*   Bitte gib **ausschließlich** das resultierende FHIR Bundle im JSON-Format aus (eingefasst in einen Code-Block). 
*   Achte darauf, dass das JSON Format strikt valide ist.
*   Erstelle für den Anfang **1 vollständiges Patienten-Bundle**, das exemplarisch einen Patienten abbildet, **Beispiel-Szenario:** Ein Patient mit Verdacht auf Schlaganfall wird erst in der **Stroke Unit behandelt, erhält dort eine Diagnose und Medikamente und wird anschließend in die **Neurologische Reha** überwiesen.

---

