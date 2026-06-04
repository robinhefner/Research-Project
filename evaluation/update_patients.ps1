# PowerShell-Skript zur automatischen Aktualisierung der Patienten-PDF-Liste in app.js
# Dieses Skript scannt die Ordner data/real, data/synthea und data/llm nach .pdf Dateien.
# Führen Sie dieses Skript aus, wenn Sie neue PDFs hinzufügen oder entfernen.

$ErrorActionPreference = "Stop"
$UTF8NoBOM = New-Object System.Text.UTF8Encoding($false)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Patienten-Liste Aktualisierungswerkzeug" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Pfade definieren
$scriptPath = $PSScriptRoot
if (-not $scriptPath) { $scriptPath = Get-Location }
$appJsPath = Join-Path $scriptPath "app.js"
$dataDir = Join-Path $scriptPath "data"

if (-not (Test-Path $appJsPath)) {
    Write-Error "Fehler: app.js konnte im Verzeichnis '$scriptPath' nicht gefunden werden."
    exit 1
}

if (-not (Test-Path $dataDir)) {
    Write-Error "Fehler: Der Ordner 'data' existiert nicht in '$scriptPath'."
    exit 1
}

# 2. Ordner durchsuchen
$folders = @("real", "synthea", "llm")
$pdfFiles = @()
$csvItems = @()
$patientCounts = @{}

foreach ($folderName in $folders) {
    $folderPath = Join-Path $dataDir $folderName
    $patientCounts[$folderName] = 0
    
    if (Test-Path $folderPath) {
        Write-Host "Scanne Ordner: data/$folderName..." -ForegroundColor Gray
        $files = Get-ChildItem -Path $folderPath -Filter "*.pdf" | Sort-Object Name
        foreach ($file in $files) {
            # Web-Pfade mit Forward Slashes zusammenbauen
            $relativeUrl = "data/$folderName/$($file.Name)"
            $pdfFiles += "        '$relativeUrl'"
            $patientCounts[$folderName]++
            
            # Für CSV-Export
            $csvItems += [PSCustomObject]@{
                "filename" = $file.Name
                "group"    = $folderName
            }
        }
        Write-Host "  -> ${folderName}: $($patientCounts[$folderName]) Patienten gefunden." -ForegroundColor Green
    } else {
        Write-Host "Hinweis: Ordner data/$folderName existiert nicht. Überspringe..." -ForegroundColor Yellow
    }
}

$totalPatients = $pdfFiles.Count
Write-Host ""
Write-Host "Gesamtzahl gefundener Patienten-PDFs: $totalPatients" -ForegroundColor Cyan

# 3. app.js einlesen (UTF-8)
Write-Host "Lese app.js ein..." -ForegroundColor Gray
$content = [System.IO.File]::ReadAllText($appJsPath, [System.Text.Encoding]::UTF8)

# 4. Ersetzung vorbereiten
$markerStart = "// BEGIN_PATIENT_FILES"
$markerEnd = "// END_PATIENT_FILES"

# Regex-Pattern für den Bereich zwischen den Markern
$pattern = "(?s)//\s*BEGIN_PATIENT_FILES.*?//\s*END_PATIENT_FILES"

# Formatiere das neue Array für app.js
$arrayItems = $pdfFiles -join ",`r`n"
$replacement = "$markerStart`r`n    const pdfFiles = [`r`n$arrayItems`r`n    ];`r`n    $markerEnd"

# Ersetzung durchführen
if ($content -match $pattern) {
    Write-Host "Aktualisiere die Liste in app.js..." -ForegroundColor Gray
    $newContent = $content -replace $pattern, $replacement
    
    # app.js wieder als UTF-8 ohne BOM (oder Standard-UTF8) speichern
    [System.IO.File]::WriteAllText($appJsPath, $newContent, $UTF8NoBOM)
    
    Write-Host "ERFOLG: app.js wurde erfolgreich aktualisiert!" -ForegroundColor Green
    Write-Host "Die Fortschrittsanzeige wird beim nächsten Start $totalPatients Patienten anzeigen." -ForegroundColor Green
} else {
    Write-Error "Fehler: Die Marker '$markerStart' und '$markerEnd' wurden in app.js nicht gefunden."
}

# 5. CSV Lookup Table generieren
Write-Host ""
Write-Host "Generiere CSV-Lookup-Tabelle..." -ForegroundColor Gray
$csvPath = Join-Path $scriptPath "patient_lookup.csv"

try {
    # UTF-8 CSV Datei erzeugen (mit BOM, damit Excel Umlaute korrekt liest)
    $csvItems | Export-Csv -Path $csvPath -NoTypeInformation -Delimiter "," -Encoding UTF8
    Write-Host "ERFOLG: CSV-Lookup-Tabelle unter '$csvPath' gespeichert!" -ForegroundColor Green
} catch {
    Write-Error "Fehler beim Generieren der CSV-Datei: $_"
}

Write-Host "=============================================" -ForegroundColor Cyan
