document.addEventListener('DOMContentLoaded', () => {
    // --- Supabase Setup ---
    // BITTE HIER IHRE SUPABASE DATEN EINTRAGEN:
    const SUPABASE_URL = 'https://kanfloefkfezsbadtlcu.supabase.co';
    const SUPABASE_ANON_KEY = 'sb_publishable_4fgeYxrBBxSJYe0qDm4uxw_GEnCvrqD';
    const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

    // --- App Zugriffsschutz ---
    const APP_PASSWORD = 'ResearchProject2026';

    // --- Configuration ---
    // List of PDFs
    // BEGIN_PATIENT_FILES
    const pdfFiles = [
        'data/real/Adriana_Boucsein_e364c18a.pdf',
        'data/real/Andrei_Roht_cd8ea021.pdf',
        'data/real/Anna-Lena_Hendriks_b7417d93.pdf',
        'data/real/Anne-Katrin_Hahn_0bbb7cec.pdf',
        'data/real/Ariane_Klemt_f38f0483.pdf',
        'data/real/Beate_Bruder_82341893.pdf',
        'data/real/Brit_Pechel_d12c0b37.pdf',
        'data/real/Christian_Flantz_7c21aabe.pdf',
        'data/real/Cordula_Dehmel_2bbb5f6c.pdf',
        'data/real/Cordula_Reising_f8c400d7.pdf',
        'data/real/Curt_Grein Groth_dd5a3352.pdf',
        'data/real/Daniela_Staude_178179e8.pdf',
        'data/real/Doris_Gute_038c2232.pdf',
        'data/real/Eleni_Mülichen_ed6b0701.pdf',
        'data/real/Elisabeth_Beyer_9203a958.pdf',
        'data/real/Elli_Kramer_48dff458.pdf',
        'data/real/Fedor_Birnbaum_7ff793c1.pdf',
        'data/real/Hansjürgen_Neureuther_996c4500.pdf',
        'data/real/Holger_Margraf_1c5431a0.pdf',
        'data/real/Ignatz_Albers_5318cf9c.pdf',
        'data/real/Josef_Hermann_c434b7d7.pdf',
        'data/real/Kathy_Hamann_d690ca47.pdf',
        'data/real/Kristine_Gumprich_3897e451.pdf',
        'data/real/Laszlo_auch Schlauchin_65edbd62.pdf',
        'data/real/Mandy_Dowerg_2780e7bf.pdf',
        'data/real/Marzena_Wirth_65dbaa63.pdf',
        'data/real/Meinrad_Stiebitz_11eaea15.pdf',
        'data/real/Melissa_Bohnbach_aecac158.pdf',
        'data/real/Nicolai_Hübel_824fcd1c.pdf',
        'data/real/Niko_Stoll_a01d15a3.pdf',
        'data/real/Peer_Mülichen_6dee6508.pdf',
        'data/real/Reinhart_Siering_2eda6bfb.pdf',
        'data/real/Sami_Niemeier_a2801c2b.pdf',
        'data/real/Sandy_Christoph_aa81bbf0.pdf',
        'data/real/Sigrun_Gotthard_b1cfcd58.pdf',
        'data/real/Sönke_Schomber_280cd2b1.pdf',
        'data/real/Valentina_Spieß_9480c9e4.pdf',
        'data/real/Walter_Baum_97cc27a9.pdf',
        'data/real/Wolfram_Hahn_674b8f82.pdf',
        'data/real/Zlatko_Scholl_d25ad9ef.pdf',
        'data/synthea/Anke_Peters_630dc962.pdf',
        'data/synthea/Barbara_Lang_d8cb2b5c.pdf',
        'data/synthea/Clara_Haas_82758bb9.pdf',
        'data/synthea/Daniela_Braun_da478352.pdf',
        'data/synthea/Daniela_Koch_6ee0ce72.pdf',
        'data/synthea/Dieter_Wagner_b034fd9f.pdf',
        'data/synthea/Dirk_Schmitt_0d410091.pdf',
        'data/synthea/Elke_Haas_fe15482d.pdf',
        'data/synthea/Elke_Hartmann_e09461fc.pdf',
        'data/synthea/Emil_Werner_5f5d0f40.pdf',
        'data/synthea/Gerhard_Fischer_02b9e1bc.pdf',
        'data/synthea/Hans_Winter_87899c90.pdf',
        'data/synthea/Helmut_Maier_2bcf177b.pdf',
        'data/synthea/Hermann_Hartmann_0b96a232.pdf',
        'data/synthea/Ida_Roth_ab613a8e.pdf',
        'data/synthea/Jonas_Weiß_f7e8239a.pdf',
        'data/synthea/Julian_Jung_6e7e0898.pdf',
        'data/synthea/Jürgen_Baumann_33a1f41a.pdf',
        'data/synthea/Karin_Krämer_d0ba9874.pdf',
        'data/synthea/Katharina_Fuchs_29225702.pdf',
        'data/synthea/Klaus_Klein_81ba987f.pdf',
        'data/synthea/Maria_Möller_fbb9f4a6.pdf',
        'data/synthea/Martha_Schulz_e3c366a8.pdf',
        'data/synthea/Mathilda_Wolf_c197f39f.pdf',
        'data/synthea/Maximilian_Neumann_f301a572.pdf',
        'data/synthea/Mila_Seiler_679c662b.pdf',
        'data/synthea/Patrick_Becker_335fdc18.pdf',
        'data/synthea/Paul_Jäger_27bc3e57.pdf',
        'data/synthea/Peter_Herrmann_2aac3d4b.pdf',
        'data/synthea/Peter_Krämer_7f0cd5db.pdf',
        'data/synthea/Petra_Koch_46caba0e.pdf',
        'data/synthea/Renate_Seidel_4c6961af.pdf',
        'data/synthea/Sandra_Meier_736b3c5c.pdf',
        'data/synthea/Sonja_Herrmann_6186127a.pdf',
        'data/synthea/Susanne_Fischer_8692f143.pdf',
        'data/synthea/Susanne_Möller_3beb9c4b.pdf',
        'data/synthea/Thomas_Schneider_b4069712.pdf',
        'data/synthea/Thorsten_Huber_4e7aab62.pdf',
        'data/synthea/Tim_Jäger_23569092.pdf',
        'data/synthea/Yvonne_Martin_2a675760.pdf',
        'data/llm/Alexander_Müller_eaaab7fc.pdf',
        'data/llm/Anna_Müller_eb9ad221.pdf',
        'data/llm/Felix_Hoffmann_91bb8f53.pdf',
        'data/llm/Felix_Müller_23d0b483.pdf',
        'data/llm/Johanna_Bauer_73a8883f.pdf',
        'data/llm/Johanna_Klein_f0728ff8.pdf',
        'data/llm/Johanna_Meyer_58912a39.pdf',
        'data/llm/Johanna_Wolf_76caf881.pdf',
        'data/llm/Jonas_Wagner_0c826f1d.pdf',
        'data/llm/Jonas_Wolf_c17419c6.pdf',
        'data/llm/Julia_Schulz_da33635d.pdf',
        'data/llm/Lea_Koch_e3e4e233.pdf',
        'data/llm/Lea_Weber_23b87261.pdf',
        'data/llm/Lena_Fischer_dfcc698a.pdf',
        'data/llm/Lena_Hoffmann_0f112a3d.pdf',
        'data/llm/Lena_Meyer_587cc6bb.pdf',
        'data/llm/Lena_Wagner_b0528e59.pdf',
        'data/llm/Leon_Becker_a8691325.pdf',
        'data/llm/Leon_Wagner_8e22dd18.pdf',
        'data/llm/Lisa_Richter_0d231a25.pdf',
        'data/llm/Lisa_Richter_72336208.pdf',
        'data/llm/Lisa_Schmidt_411f1d89.pdf',
        'data/llm/Lisa_Schneider_cb5fb015.pdf',
        'data/llm/Lukas_Fischer_a299776f.pdf',
        'data/llm/Lukas_Wagner_c04da995.pdf',
        'data/llm/Maria_Becker_c277f224.pdf',
        'data/llm/Maria_Weber_94db9e46.pdf',
        'data/llm/Marie_Müller_ca2d0495.pdf',
        'data/llm/Marie_Richter_3deb4dd0.pdf',
        'data/llm/Marie_Weber_95699e64.pdf',
        'data/llm/Max_Schneider_f7a257d3.pdf',
        'data/llm/Max_Wolf_f1625f53.pdf',
        'data/llm/Michael_Hoffmann_f7664f83.pdf',
        'data/llm/Michael_Schulz_d390cc9f.pdf',
        'data/llm/Paul_Becker_63cb13e6.pdf',
        'data/llm/Paul_Koch_50eed607.pdf',
        'data/llm/Paul_Weber_61e9e42a.pdf',
        'data/llm/Sarah_Wagner_8efa48c0.pdf',
        'data/llm/Stefan_Müller_8e4e1ca0.pdf',
        'data/llm/Tobias_Fischer_8b0d95e6.pdf'
    ];
    // END_PATIENT_FILES

    // Prototype Evaluation Criteria (Likert 1-5)
    const criteria = [
        {
            id: 'c1',
            title: '1. Klinische Plausibilität',
            description: 'Bewertet, ob Symptome, Diagnosen und Behandlungen medizinisch logisch zusammenpassen und der Verlauf klinisch plausibel ist.',
            minLabel: 'Sehr unplausibel',
            maxLabel: 'Sehr plausibel'
        },
        {
            id: 'c2',
            title: '2. Longitudinale Konsistenz',
            description: 'Prüft, ob die Patientengeschichte über die Zeit hinweg konsistent dokumentiert ist (keine plötzlichen unlogischen Sprünge).',
            minLabel: 'Sehr inkonsistent',
            maxLabel: 'Sehr konsistent'
        },
        {
            id: 'c3',
            title: '3. Zeitlich logische Abfolge',
            description: 'Bewertet die chronologische Reihenfolge der Ereignisse (z. B. Diagnostik vor Therapie, logische Abstände der Kontrollen).',
            minLabel: 'Sehr unlogisch',
            maxLabel: 'Sehr logisch'
        },
        {
            id: 'c4',
            title: '4. Gesamteindruck',
            description: 'Ihre globale Einschätzung der Qualität und des Realismus dieser Patientenakte.',
            minLabel: 'Schlecht',
            maxLabel: 'Hervorragend'
        }
    ];

    // --- State ---
    let state = {
        doctorName: '',
        remainingPdfs: [],
        totalPdfs: pdfFiles.length
    };

    // --- DOM Elements ---
    const screens = {
        password: document.getElementById('password-screen'),
        start: document.getElementById('start-screen'),
        eval: document.getElementById('eval-screen'),
        end: document.getElementById('end-screen')
    };

    const passwordForm = document.getElementById('password-form');
    const appPasswordInput = document.getElementById('app-password');
    const passwordError = document.getElementById('password-error');

    const startForm = document.getElementById('start-form');
    const doctorNameInput = document.getElementById('doctor-name'); // This is now a <select>

    const pdfViewer = document.getElementById('pdf-viewer');
    const progressIndicator = document.getElementById('progress-indicator');
    const progressBar = document.getElementById('progress-bar');

    const evalForm = document.getElementById('evaluation-form');
    const criteriaContainer = document.getElementById('criteria-container');
    const btnPrev = document.getElementById('btn-prev');
    const btnRestart = document.getElementById('btn-restart');

    // Wir verstecken/entfernen den CSV Download Button, da der Forscher die Daten direkt aus Supabase exportiert.
    const btnDownloadCsv = document.getElementById('btn-download-csv');
    if (btnDownloadCsv) btnDownloadCsv.style.display = 'none';

    // --- Initialization ---
    initApp();

    function initApp() {
        renderCriteriaForm();
        showScreen('password');
    }

    function renderCriteriaForm() {
        criteriaContainer.innerHTML = '';
        criteria.forEach(c => {
            const group = document.createElement('div');
            group.className = 'criterion-group';

            let radiosHtml = '';
            for (let i = 1; i <= 5; i++) {
                radiosHtml += `
                    <div class="likert-item">
                        <input type="radio" name="${c.id}" id="${c.id}-${i}" value="${i}" required>
                        <label class="likert-label" for="${c.id}-${i}">${i}</label>
                    </div>
                `;
            }

            group.innerHTML = `
                <div class="criterion-header">
                    <div class="criterion-title">${c.title}</div>
                    <div class="header-actions">
                        <div class="tooltip-container">
                            <span class="info-icon" title="">i</span>
                            <div class="tooltip-text">${c.description}</div>
                        </div>
                    </div>
                </div>
                <div class="likert-scale">
                    ${radiosHtml}
                </div>
                <div class="likert-legend">
                    <span>${c.minLabel}</span>
                    <span>${c.maxLabel}</span>
                </div>
                <div class="comment-container">
                    <textarea name="${c.id}_comment" class="comment-textarea" placeholder="Kommentar hinzufügen (optional)..."></textarea>
                </div>
            `;
            criteriaContainer.appendChild(group);
        });
    }

    // --- Navigation & UI ---
    function showScreen(screenName) {
        Object.values(screens).forEach(s => s.classList.remove('active'));
        screens[screenName].classList.add('active');
    }

    function loadCurrentPatient() {
        const currentPdf = state.remainingPdfs[0];

        // Update UI
        pdfViewer.src = currentPdf + '#toolbar=0&navpanes=0';

        const evaluatedCount = state.totalPdfs - state.remainingPdfs.length;
        const currentPatientNum = evaluatedCount + 1;
        progressIndicator.textContent = `Patient ${currentPatientNum} von ${state.totalPdfs}`;
        progressBar.style.width = `${(currentPatientNum / state.totalPdfs) * 100}%`;

        evalForm.reset();

        // Hide prev button as we don't allow going back to already saved ones in cloud mode
        btnPrev.style.display = 'none';
    }

    // --- Event Listeners ---
    passwordForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const enteredPassword = appPasswordInput.value;
        if (enteredPassword === APP_PASSWORD) {
            passwordError.style.display = 'none';
            showScreen('start');
        } else {
            passwordError.style.display = 'block';
            appPasswordInput.value = '';
            appPasswordInput.focus();
        }
    });

    startForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = doctorNameInput.value.trim();
        if (!name) return;

        const btnSubmit = startForm.querySelector('button[type="submit"]');
        const originalText = btnSubmit.textContent;
        btnSubmit.textContent = 'Lade Fortschritt...';
        btnSubmit.disabled = true;

        try {
            // Fetch evaluated PDFs for this doctor
            const { data, error } = await supabase
                .from('evaluations')
                .select('pdf_filename')
                .eq('doctor_name', name);

            if (error) throw error;

            const evaluatedFilenames = data.map(row => row.pdf_filename);

            // Filter pdfFiles to get remaining ones
            let remaining = pdfFiles.filter(pdfPath => {
                const filename = pdfPath.split('/').pop();
                return !evaluatedFilenames.includes(filename);
            });

            // Randomize the order (Fisher-Yates Shuffle)
            for (let i = remaining.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [remaining[i], remaining[j]] = [remaining[j], remaining[i]];
            }

            state.remainingPdfs = remaining;

            state.doctorName = name;

            if (state.remainingPdfs.length === 0) {
                showScreen('end');
            } else {
                showScreen('eval');
                loadCurrentPatient();
            }
        } catch (err) {
            console.error("Fehler beim Laden:", err);
            alert("Fehler beim Laden des Fortschritts aus der Cloud.");
        } finally {
            btnSubmit.textContent = originalText;
            btnSubmit.disabled = false;
        }
    });

    evalForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btnNext = document.getElementById('btn-next');
        const originalText = btnNext.textContent;
        btnNext.textContent = 'Speichert...';
        btnNext.disabled = true;

        // Gather responses
        const formData = new FormData(evalForm);
        const responses = {};
        criteria.forEach(c => {
            responses[c.id] = formData.get(c.id);
            const comment = formData.get(`${c.id}_comment`);
            responses[`${c.id}_comment`] = comment && comment.trim() !== '' ? comment.trim() : null;
        });

        const currentPdfPath = state.remainingPdfs[0];
        const pdfName = currentPdfPath.split('/').pop();
        const timestamp = new Date().toISOString();

        try {
            const { error } = await supabase
                .from('evaluations')
                .insert([
                    {
                        doctor_name: state.doctorName,
                        pdf_filename: pdfName,
                        c1: parseInt(responses.c1),
                        c1_comment: responses.c1_comment,
                        c2: parseInt(responses.c2),
                        c2_comment: responses.c2_comment,
                        c3: parseInt(responses.c3),
                        c3_comment: responses.c3_comment,
                        c4: parseInt(responses.c4),
                        c4_comment: responses.c4_comment,
                        created_at: timestamp
                    }
                ]);

            if (error) throw error;

            // Erfolgreich gespeichert, entferne PDF aus verbleibender Liste
            state.remainingPdfs.shift();

            if (state.remainingPdfs.length === 0) {
                showScreen('end');
            } else {
                loadCurrentPatient();
            }
        } catch (err) {
            console.error("Supabase Error:", err);
            alert("Fehler beim Speichern in der Cloud. Bitte prüfen Sie Ihre Verbindung.");
        } finally {
            btnNext.textContent = originalText;
            btnNext.disabled = false;
        }
    });

    btnRestart.addEventListener('click', () => {
        state = { doctorName: '', remainingPdfs: [], totalPdfs: pdfFiles.length };
        doctorNameInput.value = '';
        showScreen('start');
    });
});
