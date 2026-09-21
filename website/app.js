/* ==========================================================================
   GoodNotes OCR & AI Summaries - Frontend Application Logic
   ========================================================================== */

let supabaseClient = null;
let allNotes = [];
let allSubjects = [];
let activeSchool = 'all';
let activeYear = 'all';
let activeSubjectId = 'all';
let searchQuery = '';
let expandedSchools = {};
let expandedYears = {};

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    initLucideIcons();
    initTheme();
    initSupabase();
    setupEventListeners();
    loadData();
});

function initLucideIcons() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.className = savedTheme;
    updateThemeIcon(savedTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById("theme-icon");
    if (icon) {
        icon.setAttribute("data-lucide", theme === "light" ? "moon" : "sun");
        initLucideIcons();
    }
}

function initSupabase() {
    const url = window.ENV?.SUPABASE_URL;
    const key = window.ENV?.SUPABASE_ANON_KEY;

    if (url && key && !url.includes("your-project")) {
        try {
            supabaseClient = supabase.createClient(url, key);
            console.log("[Supabase] Client initialized successfully.");
        } catch (e) {
            console.warn("[Supabase] Failed to initialize client:", e);
        }
    } else {
        console.log("[Supabase] Using demo local mode.");
    }
}

function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById("search-input");
    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderCourses();
    });

    // Keyboard shortcut '/' for search
    document.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
        if (e.key === "Escape") {
            closeModal();
        }
    });

    // Theme toggle
    document.getElementById("theme-toggle-btn").addEventListener("click", () => {
        const isDark = document.documentElement.classList.contains("dark");
        const newTheme = isDark ? "light" : "dark";
        document.documentElement.className = newTheme;
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme);
    });

    // Mobile sidebar toggle
    document.getElementById("mobile-sidebar-toggle").addEventListener("click", () => {
        document.getElementById("sidebar").classList.toggle("open");
    });

    // Modal tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");
            switchTab(tabName);
        });
    });

    // Modal close
    document.getElementById("modal-close-btn").addEventListener("click", closeModal);
    document.getElementById("course-modal").addEventListener("click", (e) => {
        if (e.target.id === "course-modal") closeModal();
    });

    // Move note modal listeners
    const schoolSelect = document.getElementById("move-school-select");
    const schoolCustom = document.getElementById("move-school-custom");
    if (schoolSelect) {
        schoolSelect.addEventListener("change", () => {
            if (schoolSelect.value === "__NEW__") {
                schoolCustom.classList.remove("hidden");
                schoolCustom.focus();
            } else {
                schoolCustom.classList.add("hidden");
            }
        });
    }

    const yearSelect = document.getElementById("move-year-select");
    const yearCustom = document.getElementById("move-year-custom");
    if (yearSelect) {
        yearSelect.addEventListener("change", () => {
            if (yearSelect.value === "__NEW__") {
                yearCustom.classList.remove("hidden");
                yearCustom.focus();
            } else {
                yearCustom.classList.add("hidden");
            }
        });
    }

    const saveMoveBtn = document.getElementById("save-move-note-btn");
    if (saveMoveBtn) {
        saveMoveBtn.addEventListener("click", saveMoveNote);
    }
}

function parseNoteMeta(note) {
    let school = (note.school_name || "").trim();
    let year = (note.year_name || "").trim();
    let subject = (note.subject_name || "").trim();
    const title = (note.title || "").trim();

    // Check encoded format: [School / Year] Subject or [School] Subject
    if (subject.startsWith("[")) {
        const fullMatch = subject.match(/^\[(.*?)\s*\/\s*(.*?)\]\s*(.*)$/);
        if (fullMatch) {
            school = fullMatch[1].trim();
            year = fullMatch[2].trim();
            subject = fullMatch[3].trim();
        } else {
            const match = subject.match(/^\[(.*?)\]\s*(.*)$/);
            if (match) {
                const tag = match[1].trim();
                subject = match[2].trim();
                if (tag.includes("BME")) school = "Master BME";
                else if (tag.includes("TSP")) school = "TSP";
            }
        }
    }

    // Infer school if missing or "Général"
    if (!school || school === "Général") {
        if (subject.includes("BME") || title.includes("BME") || subject.includes("Master")) {
            school = "Master BME";
        } else {
            school = "TSP";
        }
    }

    // Normalize school names
    if (school.toUpperCase().includes("TSP") || school.toLowerCase().includes("telecom") || school.toLowerCase().includes("sudparis")) {
        school = "TSP";
    } else if (school.toUpperCase().includes("BME") || school.toLowerCase().includes("biomedical")) {
        school = "Master BME";
    }

    // Infer year if missing or "Général"
    if (!year || year === "Général") {
        const textToSearch = `${subject} ${title}`;
        
        // 1. Check for 4-digit codes (e.g., 3101, 4101, 5101)
        const codeMatch = textToSearch.match(/\b([345])\d{3}\b/);
        if (codeMatch) {
            const digit = codeMatch[1];
            if (digit === "3") year = "1A";
            else if (digit === "4") year = "2A";
            else if (digit === "5") year = "3A";
        } 
        // 2. Check explicit keywords
        else if (/\b1A\b/i.test(textToSearch)) {
            year = "1A";
        } else if (/\b2A\b/i.test(textToSearch)) {
            year = "2A";
        } else if (/\b3A\b/i.test(textToSearch) || /\bVAP\b/i.test(textToSearch) || /\bparcours\b/i.test(textToSearch)) {
            year = "3A";
        } else if (/\bM1\b/i.test(textToSearch) || /Master\s*1/i.test(textToSearch)) {
            year = "Master 1";
        } else if (/\bM2\b/i.test(textToSearch) || /Master\s*2/i.test(textToSearch)) {
            year = "Master 2";
        } else {
            if (school === "TSP") {
                year = "2A";
            } else if (school === "Master BME") {
                year = "Master 1";
            } else {
                year = "2A";
            }
        }
    }

    if (!subject) subject = "Général";

    return { school, year, subject };
}

const DEMO_NOTES = [
    {
        id: "demo-1",
        title: "Introduction aux Réseaux & Commutation (NET 3001)",
        school_name: "TSP",
        year_name: "1A",
        subject_name: "NET 3001 - Réseaux",
        created_at: new Date().toISOString(),
        summary: "### Synthèse du Cours (1A)\n- **Notions clés** : Modèle OSI, routage IP, paquets TCP/UDP.\n- **Formules de débit** : \\$R = \\frac{B}{\\Delta t}\\$ et capacité de Shannon \\$C = B \\log_2(1 + SNR)\\$.\n- **Points d'attention** : Contrôle de congestion et fenêtre glissante.",
        full_transcription: "# Introduction aux Réseaux (NET 3001)\n\n## 1. Modèle OSI & Layering\nLe modèle OSI comporte 7 couches distinctes de l'application à la couche physique.\n\n$$\nC = B \\log_2 \\left(1 + \\frac{S}{N}\\right)\n$$\n\n## 2. Protocoles de Transport\nTCP assure la fiabilité par accusé de réception (ACK)."
    },
    {
        id: "demo-2",
        title: "Calcul Matriciel & Traitement du Signal (SIC 4101)",
        school_name: "TSP",
        year_name: "2A",
        subject_name: "SIC 4101 - Traitement du Signal",
        created_at: new Date().toISOString(),
        summary: "### Résumé Exécutif (2A)\n- **Transformée de Fourier** : Passage domaine temporel vers fréquentiel.\n- **Formule de Parseval** : conservation de l'énergie \\$\\int |f(t)|^2 dt = \\int |F(\\nu)|^2 d\\nu\\$.",
        full_transcription: "# Traitement du Signal (SIC 4101)\n\n$$\nF(\\nu) = \\int_{-\\infty}^{+\\infty} f(t) e^{-i 2 \\pi \\nu t} dt\n$$"
    },
    {
        id: "demo-3",
        title: "Biomécanique & Imagerie Médicale",
        school_name: "Master BME",
        year_name: "Master 1",
        subject_name: "Biomécanique",
        created_at: new Date().toISOString(),
        summary: "### Principes Biomécaniques\n- Analyse des contraintes mécaniques sur le tissu osseux.\n- Modélisation de l'élasticité avec la loi de Hooke 3D.",
        full_transcription: "# Biomécanique\n\nContraintes élastiques tensorielles :"
    }
];

async function fetchWithTimeout(promise, ms = 2000) {
    let timeout = new Promise((resolve) => setTimeout(() => resolve({ timeout: true }), ms));
    return Promise.race([promise, timeout]);
}

async function loadData() {
    // 1. Instantly render demo notes so page is NEVER blank or empty
    allNotes = DEMO_NOTES;
    const statusEl = document.querySelector(".profile-status");
    if (statusEl) {
        statusEl.textContent = "Mode Local / Démo";
        statusEl.style.color = "#f59e0b";
    }

    try {
        renderAccordionSidebar();
        renderCourses();
    } catch (renderErr) {
        console.error("[Render Error]:", renderErr);
    }

    // 2. Safely attempt fetching real Supabase data with timeout
    if (supabaseClient) {
        try {
            const subPromise = Promise.resolve(supabaseClient.from("subjects").select("*"));
            const notesPromise = Promise.resolve(supabaseClient.from("notes").select("*").order("created_at", { ascending: false }));

            const res = await fetchWithTimeout(Promise.all([subPromise, notesPromise]), 1500);

            if (res && !res.timeout) {
                const [subRes, notesRes] = res;
                if (!notesRes?.error && notesRes?.data && notesRes.data.length > 0) {
                    allSubjects = subRes?.data || [];
                    allNotes = notesRes.data;
                    if (statusEl) {
                        statusEl.textContent = "Supabase Connecté";
                        statusEl.style.color = "#059669";
                    }
                    renderAccordionSidebar();
                    renderCourses();
                }
            }
        } catch (err) {
            console.warn("[Supabase] Offline or fetch error:", err);
        }
    }
}

function renderAccordionSidebar() {
    const navEl = document.getElementById("sidebar-nav");
    if (!navEl) return;

    // Build hierarchy tree: School -> Year -> Subject -> count
    const tree = {};

    allNotes.forEach(note => {
        const { school, year, subject } = parseNoteMeta(note);

        if (!tree[school]) {
            tree[school] = { count: 0, years: {} };
        }
        tree[school].count++;

        if (!tree[school].years[year]) {
            tree[school].years[year] = { count: 0, subjects: {} };
        }
        tree[school].years[year].count++;

        tree[school].years[year].subjects[subject] = (tree[school].years[year].subjects[subject] || 0) + 1;
    });

    let html = `
        <div class="nav-section-label" style="margin-bottom: 8px;">Écoles & Formations</div>
        <ul class="accordion-tree">
            <li class="accordion-item ${activeSchool === 'all' ? 'active' : ''}" id="btn-all-courses">
                <i data-lucide="graduation-cap" style="width: 16px; height: 16px;"></i>
                <span class="tree-label">Toutes les écoles</span>
                <span class="tree-count">${allNotes.length}</span>
            </li>
    `;

    const schoolNames = Object.keys(tree).sort();

    schoolNames.forEach(schName => {
        const schoolObj = tree[schName];
        const isSchActive = activeSchool === schName;
        const isSchExpanded = expandedSchools[schName] !== undefined ? expandedSchools[schName] : (isSchActive || schoolNames.length <= 3);

        html += `
            <li class="tree-node-school">
                <div class="accordion-item ${isSchActive && activeYear === 'all' ? 'active' : ''}" data-school="${escapeHTML(schName)}">
                    <i data-lucide="chevron-right" class="tree-chevron ${isSchExpanded ? 'open' : ''}"></i>
                    <i data-lucide="building-2" style="width: 16px; height: 16px;"></i>
                    <span class="tree-label">${escapeHTML(schName)}</span>
                    <span class="tree-count">${schoolObj.count}</span>
                </div>
        `;

        if (isSchExpanded) {
            html += `<ul class="years-subtree">`;
            const yearNames = Object.keys(schoolObj.years).sort();

            yearNames.forEach(yrName => {
                const yearObj = schoolObj.years[yrName];
                const yrKey = `${schName}_${yrName}`;
                const isYrActive = activeSchool === schName && activeYear === yrName;
                const isYrExpanded = expandedYears[yrKey] !== undefined ? expandedYears[yrKey] : (isYrActive || yearNames.length <= 2);

                html += `
                    <li class="tree-node-year">
                        <div class="year-tree-item ${isYrActive && activeSubjectId === 'all' ? 'active' : ''}" data-school="${escapeHTML(schName)}" data-year="${escapeHTML(yrName)}">
                            <i data-lucide="chevron-right" class="tree-chevron ${isYrExpanded ? 'open' : ''}"></i>
                            <i data-lucide="folder-git-2" style="width: 14px; height: 14px;"></i>
                            <span class="tree-label">${escapeHTML(yrName)}</span>
                            <span class="tree-count">${yearObj.count}</span>
                        </div>
                `;

                if (isYrExpanded) {
                    html += `<ul class="subjects-subtree">`;
                    const subNames = Object.keys(yearObj.subjects).sort();

                    subNames.forEach(subName => {
                        const subCount = yearObj.subjects[subName];
                        const isSubActive = activeSchool === schName && activeYear === yrName && activeSubjectId === subName;

                        html += `
                            <li class="subject-tree-item ${isSubActive ? 'active' : ''}" data-school="${escapeHTML(schName)}" data-year="${escapeHTML(yrName)}" data-subject="${escapeHTML(subName)}">
                                <span class="subject-dot" style="width: 8px; height: 8px; border-radius: 50%; background-color: #3b82f6;"></span>
                                <span class="tree-label">${escapeHTML(subName)}</span>
                                <span class="tree-count">${subCount}</span>
                            </li>
                        `;
                    });
                    html += `</ul>`;
                }

                html += `</li>`;
            });
            html += `</ul>`;
        }

        html += `</li>`;
    });

    html += `</ul>`;
    navEl.innerHTML = html;

    // Attach Event Listeners
    // 1. All courses
    const allBtn = document.getElementById("btn-all-courses");
    if (allBtn) {
        allBtn.addEventListener("click", () => {
            activeSchool = 'all';
            activeYear = 'all';
            activeSubjectId = 'all';
            document.getElementById("active-subject-title").textContent = "Tous les cours";
            renderAccordionSidebar();
            renderCourses();
        });
    }

    // 2. School headers
    navEl.querySelectorAll(".accordion-item[data-school]").forEach(el => {
        el.addEventListener("click", (e) => {
            const schName = el.getAttribute("data-school");
            expandedSchools[schName] = !expandedSchools[schName];
            activeSchool = schName;
            activeYear = 'all';
            activeSubjectId = 'all';
            document.getElementById("active-subject-title").textContent = `Cours - ${schName}`;
            renderAccordionSidebar();
            renderCourses();
        });
    });

    // 3. Year headers
    navEl.querySelectorAll(".year-tree-item[data-year]").forEach(el => {
        el.addEventListener("click", (e) => {
            e.stopPropagation();
            const schName = el.getAttribute("data-school");
            const yrName = el.getAttribute("data-year");
            const yrKey = `${schName}_${yrName}`;

            expandedYears[yrKey] = !expandedYears[yrKey];
            activeSchool = schName;
            activeYear = yrName;
            activeSubjectId = 'all';
            document.getElementById("active-subject-title").textContent = `Cours - ${schName} (${yrName})`;
            renderAccordionSidebar();
            renderCourses();
        });
    });

    // 4. Subject leaves
    navEl.querySelectorAll(".subject-tree-item[data-subject]").forEach(el => {
        el.addEventListener("click", (e) => {
            e.stopPropagation();
            const schName = el.getAttribute("data-school");
            const yrName = el.getAttribute("data-year");
            const subName = el.getAttribute("data-subject");

            activeSchool = schName;
            activeYear = yrName;
            activeSubjectId = subName;
            document.getElementById("active-subject-title").textContent = `${subName} (${schName} ${yrName})`;
            renderAccordionSidebar();
            renderCourses();
        });
    });

    initLucideIcons();
}

function renderCourses() {
    const grid = document.getElementById("courses-grid");
    const emptyState = document.getElementById("empty-state");
    const totalCountEl = document.getElementById("notes-total-count");

    // Filter notes
    const filtered = allNotes.filter(note => {
        const { school, year, subject } = parseNoteMeta(note);

        const matchSchool = activeSchool === "all" || school === activeSchool;
        const matchYear = activeYear === "all" || year === activeYear;
        const matchSubject = activeSubjectId === "all" || subject === activeSubjectId;

        const matchQuery = !searchQuery || 
                           note.title.toLowerCase().includes(searchQuery) || 
                           (note.summary && note.summary.toLowerCase().includes(searchQuery)) ||
                           (note.full_transcription && note.full_transcription.toLowerCase().includes(searchQuery));

        return matchSchool && matchYear && matchSubject && matchQuery;
    });

    totalCountEl.textContent = filtered.length;

    if (filtered.length === 0) {
        grid.innerHTML = "";
        emptyState.classList.remove("hidden");
        return;
    }

    emptyState.classList.add("hidden");
    grid.innerHTML = filtered.map(note => createCourseCardHTML(note)).join("");

    // Attach click listeners to cards for opening modal
    grid.querySelectorAll(".course-card").forEach(card => {
        card.addEventListener("click", (e) => {
            if (e.target.closest(".card-delete-btn")) return;
            const noteId = card.getAttribute("data-note-id");
            const targetNote = allNotes.find(n => n.id === noteId);
            if (targetNote) {
                openCourseModal(targetNote);
            }
        });
    });

    initLucideIcons();
}

function createCourseCardHTML(note) {
    const dateStr = new Date(note.created_at).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });

    const meta = parseNoteMeta(note);
    const badgeText = meta.school !== "Général" && meta.school !== meta.subject ? `[${meta.school}] ${meta.subject}` : meta.subject;
    
    // Clean summary preview
    const rawSummary = note.summary || "Résumé non disponible.";
    const cleanPreview = rawSummary.replace(/[#*`$]/g, "").substring(0, 160) + "...";
    const escapedTitle = escapeHTML(note.title).replace(/'/g, "\\'");

    return `
        <div class="course-card" data-note-id="${note.id}">
            <div class="card-top">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <span class="card-badge" style="background-color: rgba(59, 130, 246, 0.15); color: #2563eb;">
                        ${badgeText}
                    </span>
                    <div class="card-actions-group">
                        <button class="card-move-btn" title="Déplacer / Classer cette fiche" onclick="event.stopPropagation(); event.preventDefault(); openMoveModal(allNotes.find(n => n.id === '${note.id}'));">
                            <i data-lucide="folder-output"></i>
                        </button>
                        <button class="card-delete-btn" title="Supprimer ce cours" onclick="event.stopPropagation(); event.preventDefault(); deleteNote('${note.id}', '${escapedTitle}');">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </div>
                <h3 class="card-title">${escapeHTML(note.title)}</h3>
                <p class="card-summary">${escapeHTML(cleanPreview)}</p>
            </div>
            <div class="card-footer">
                <div class="card-date">
                    <i data-lucide="calendar"></i> ${dateStr}
                </div>
                <div class="card-action">
                    Consulter <i data-lucide="chevron-right"></i>
                </div>
            </div>
        </div>
    `;
}

let activeModalNoteId = null;

function openCourseModal(note) {
    activeModalNoteId = note.id;
    const modal = document.getElementById("course-modal");
    document.getElementById("modal-title").textContent = note.title;
    
    // Reset re-analyze button state
    const reanalyzeBtn = document.getElementById("modal-reanalyze-btn");
    const reanalyzeIcon = document.getElementById("modal-reanalyze-icon");
    const reanalyzeText = document.getElementById("modal-reanalyze-text");
    if (reanalyzeBtn) reanalyzeBtn.disabled = false;
    if (reanalyzeIcon) reanalyzeIcon.classList.remove("spin");
    if (reanalyzeText) reanalyzeText.textContent = "Ré-analyser par IA";

    const subjectTag = document.getElementById("modal-subject-tag");
    const subjectTagText = document.getElementById("modal-subject-tag-text");
    if (subjectTagText) {
        subjectTagText.textContent = note.subject_name || "Général";
    } else if (subjectTag) {
        subjectTag.textContent = note.subject_name || "Général";
    }

    const editSubjectHandler = (e) => {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        changeSubject(note.id, note.subject_name || "Général");
    };

    subjectTag.onclick = editSubjectHandler;
    const editBtn = document.getElementById("modal-edit-subject-btn");
    if (editBtn) editBtn.onclick = editSubjectHandler;

    const deleteBtn = document.getElementById("modal-delete-btn");
    if (deleteBtn) {
        deleteBtn.onclick = (e) => {
            if (e) {
                e.stopPropagation();
                e.preventDefault();
            }
            deleteNote(note.id, note.title);
        };
    }
    
    const dateStr = new Date(note.created_at).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric"
    });
    document.getElementById("modal-date").innerHTML = `<i data-lucide="calendar"></i> ${dateStr}`;

    // Helper to render Markdown while preserving SVG/HTML blocks without code-block escaping
    function renderMarkdownWithHTML(text) {
        if (!text) return "";
        const cleaned = text.replace(/(<svg[\s\S]*?<\/svg>)/gi, (match) => {
            return match.split('\n').map(line => line.trim()).join('\n');
        });
        return marked.parse(cleaned);
    }

    // Render Tab 1: AI Summary
    const summaryContainer = document.getElementById("summary-content");
    summaryContainer.innerHTML = renderMarkdownWithHTML(note.summary || "*Aucun résumé disponible.*");

    // Render Tab 2: Full Transcription & LaTeX
    const transcriptionContainer = document.getElementById("transcription-content");
    transcriptionContainer.innerHTML = renderMarkdownWithHTML(note.full_transcription || "*Aucune retranscription disponible.*");

    // Render Tab 3: Formulaire du cours
    renderFormulasTab(note);

    // Render Tab 4: QCM Quiz ONLY for 3A (VAP) and Master BME notes!
    const meta = parseNoteMeta(note);
    const quizBtn = document.getElementById("tab-btn-quiz");
    const isEligibleForQuiz = (meta.year === "3A" || meta.school === "Master BME" || meta.year.includes("Master") || meta.year.includes("3A"));

    if (quizBtn) {
        if (isEligibleForQuiz) {
            quizBtn.classList.remove("hidden");
            renderQuizTab(note);
        } else {
            quizBtn.classList.add("hidden");
        }
    }

    // Render LaTeX Math with KaTeX
    renderKaTeX(summaryContainer);
    renderKaTeX(transcriptionContainer);

    switchTab("summary");
    modal.classList.remove("hidden");
    initLucideIcons();
}

function renderKaTeX(element) {
    if (window.renderMathInElement) {
        renderMathInElement(element, {
            delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "$", right: "$", display: false }
            ],
            throwOnError: false
        });
    }
}

function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        if (btn.getAttribute("data-tab") === tabName) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    document.querySelectorAll(".tab-content").forEach(content => {
        if (content.id === `tab-${tabName}`) {
            content.classList.remove("hidden");
        } else {
            content.classList.add("hidden");
        }
    });
}

function closeModal() {
    document.getElementById("course-modal").classList.add("hidden");
}

async function deleteNote(noteId, title) {
    if (!confirm(`Voulez-vous vraiment supprimer la fiche "${title}" ?`)) {
        return;
    }

    try {
        if (supabaseClient) {
            await supabaseClient.from("notes").delete().eq("id", noteId);
        }
        allNotes = allNotes.filter(n => n.id !== noteId);
        renderAccordionSidebar();
        renderCourses();
        closeModal();
    } catch (e) {
        alert("Erreur lors de la suppression : " + e.message);
    }
}

async function changeSubject(noteId, currentSubject) {
    const note = allNotes.find(n => n.id === noteId);
    const meta = note ? parseNoteMeta(note) : { school: "TSP", year: "2A", subject: currentSubject };

    const newSubject = prompt(`Changer la matière pour ce cours (actuellement : "${meta.subject}") :`, meta.subject);
    
    if (!newSubject || newSubject.trim() === "" || newSubject.trim() === meta.subject) {
        return;
    }

    const cleanSubject = newSubject.trim();
    const encodedSubjectName = `[${meta.school} / ${meta.year}] ${cleanSubject}`;

    try {
        if (supabaseClient) {
            await supabaseClient.from("notes").update({ subject_name: encodedSubjectName }).eq("id", noteId);
        }

        if (note) {
            note.subject_name = encodedSubjectName;
        }

        // Refresh UI
        document.getElementById("modal-subject-tag").textContent = cleanSubject;
        renderAccordionSidebar();
        renderCourses();
    } catch (e) {
        alert("Erreur lors de la modification de la matière : " + e.message);
    }
}

let movingNoteId = null;

function openMoveModal(note) {
    if (!note) return;
    movingNoteId = note.id;
    const meta = parseNoteMeta(note);
    const modal = document.getElementById("move-note-modal");
    const subtitle = document.getElementById("move-modal-subtitle");
    if (subtitle) {
        subtitle.textContent = `Fiche : "${note.title}"`;
    }

    const schoolSelect = document.getElementById("move-school-select");
    const schoolCustom = document.getElementById("move-school-custom");
    const yearSelect = document.getElementById("move-year-select");
    const yearCustom = document.getElementById("move-year-custom");
    const subjectInput = document.getElementById("move-subject-input");

    // Pre-fill school
    if (["TSP", "Master BME"].includes(meta.school)) {
        schoolSelect.value = meta.school;
        schoolCustom.classList.add("hidden");
    } else {
        schoolSelect.value = "__NEW__";
        schoolCustom.value = meta.school;
        schoolCustom.classList.remove("hidden");
    }

    // Pre-fill year
    if (["1A", "2A", "3A", "Tronc Commun (1A/2A)", "Master 1", "Master 2"].includes(meta.year)) {
        yearSelect.value = meta.year;
        yearCustom.classList.add("hidden");
    } else {
        yearSelect.value = "__NEW__";
        yearCustom.value = meta.year;
        yearCustom.classList.remove("hidden");
    }

    // Pre-fill subject
    subjectInput.value = meta.subject;

    modal.classList.remove("hidden");
    initLucideIcons();
}

function closeMoveModal() {
    const modal = document.getElementById("move-note-modal");
    if (modal) modal.classList.add("hidden");
    movingNoteId = null;
}

async function saveMoveNote() {
    if (!movingNoteId) return;

    const note = allNotes.find(n => n.id === movingNoteId);
    if (!note) return;

    const schoolSelect = document.getElementById("move-school-select");
    const schoolCustom = document.getElementById("move-school-custom");
    const yearSelect = document.getElementById("move-year-select");
    const yearCustom = document.getElementById("move-year-custom");
    const subjectInput = document.getElementById("move-subject-input");

    const newSchool = schoolSelect.value === "__NEW__" ? schoolCustom.value.trim() : schoolSelect.value;
    const newYear = yearSelect.value === "__NEW__" ? yearCustom.value.trim() : yearSelect.value;
    const newSubject = subjectInput.value.trim() || "Général";

    if (!newSchool || !newYear) {
        alert("Veuillez spécifier l'école et l'année.");
        return;
    }

    const encodedSubjectName = `[${newSchool} / ${newYear}] ${newSubject}`;

    try {
        if (supabaseClient) {
            const { data, error } = await supabaseClient.from("notes").update({
                subject_name: encodedSubjectName
            }).eq("id", movingNoteId).select();

            if (error) {
                console.error("[Supabase Error] Failed to move note:", error);
                alert("Erreur Supabase : " + error.message);
                return;
            }
            console.log("[Supabase] Note moved and saved successfully to DB:", data);
        }

        // Update local object
        note.school_name = newSchool;
        note.year_name = newYear;
        note.subject_name = encodedSubjectName;

        closeMoveModal();
        renderAccordionSidebar();
        renderCourses();

        // Update modal tag if open
        const subjectTag = document.getElementById("modal-subject-tag");
        if (subjectTag && activeModalNoteId === movingNoteId) {
            subjectTag.textContent = newSubject;
        }
    } catch (err) {
        alert("Erreur lors du déplacement de la fiche : " + err.message);
    }
}

const CANONICAL_FORMULARIES = {
    signal: [
        {
            name: "Transformée de Fourier (TF)",
            formula: "F(\\nu) = \\mathcal{F}\\{f(t)\\} = \\int_{-\\infty}^{+\\infty} f(t) e^{-i 2\\pi \\nu t} dt",
            desc: "Passage du domaine temporel au domaine fréquentiel pour les signaux continus."
        },
        {
            name: "Transformée de Fourier Inverse",
            formula: "f(t) = \\mathcal{F}^{-1}\\{F(\\nu)\\} = \\int_{-\\infty}^{+\\infty} F(\\nu) e^{+i 2\\pi \\nu t} d\\nu",
            desc: "Reconstitution du signal temporel à partir de son spectre fréquentiel."
        },
        {
            name: "Produit de Convolution",
            formula: "(f * g)(t) = \\int_{-\\infty}^{+\\infty} f(\\tau) g(t - \\tau) d\\tau \\quad \\Longleftrightarrow \\quad \\mathcal{F}\\{(f * g)(t)\\} = F(\\nu) \\cdot G(\\nu)",
            desc: "Réponse d'un système LTI à un signal d'entrée. En fréquence, la convolution devient une simple multiplication."
        },
        {
            name: "Théorème de Parseval-Plancherel (Conservation d'Énergie)",
            formula: "E_f = \\int_{-\\infty}^{+\\infty} |f(t)|^2 dt = \\int_{-\\infty}^{+\\infty} |F(\\nu)|^2 d\\nu",
            desc: "L'énergie totale du signal est rigoureusement identique dans le domaine temporel et le domaine fréquentiel."
        },
        {
            name: "Théorème d'Échantillonnage de Nyquist-Shannon",
            formula: "f_s \\ge 2 f_{\\max} \\quad \\implies \\quad x(t) = \\sum_{n=-\\infty}^{+\\infty} x(n T_s) \\cdot \\mathrm{sinc}\\left(\\frac{t - n T_s}{T_s}\\right)",
            desc: "Condition exacte d'échantillonnage sans repliement spectral (aliasing) et formule de reconstruction Sinc."
        },
        {
            name: "Densité Spectrale de Puissance (DSP) & Autocorrélation",
            formula: "R_{xx}(\\tau) = \\int_{-\\infty}^{+\\infty} x(t) x(t - \\tau) dt \\quad \\Longleftrightarrow \\quad S_{xx}(\\nu) = \\mathcal{F}\\{R_{xx}(\\tau)\\} = |X(\\nu)|^2",
            desc: "Théorème de Wiener-Khintchine : la DSP est la transformée de Fourier de la fonction d'autocorrélation."
        },
        {
            name: "Transformée en Z (Signaux Discrets)",
            formula: "X(z) = \\mathcal{Z}\\{x[n]\\} = \\sum_{n=-\\infty}^{+\\infty} x[n] z^{-n}",
            desc: "Analyse fréquentielle des filtres numériques RIF/RII et des systèmes discrets LTI."
        }
    ],
    networks: [
        {
            name: "Capacité Théorique de Shannon-Hartley",
            formula: "C = B \\log_2 \\left(1 + \\frac{S}{N}\\right)",
            desc: "Débit binaire maximal théorique d'un canal de transmission avec bruit blanc Gaussien (AWGN)."
        },
        {
            name: "Formule de Nyquist (Canal Idéal Sans Bruit)",
            formula: "C_{\\max} = 2 B \\log_2(M)",
            desc: "Débit maximal sur un canal M-aire sans bruit de largeur de bande B."
        },
        {
            name: "Temps de Transmission & Délais de Propagation",
            formula: "T_{\\text{total}} = T_{\\text{trans}} + T_{\\text{prop}} = \\frac{L}{R} + \\frac{D}{V}",
            desc: "Calcul du délai de transfert bout-en-bout (L: taille paquet, R: débit, D: distance, V: vitesse)."
        }
    ],
    bme: [
        {
            name: "Loi de Hooke Tridimensionnelle (Biomécanique)",
            formula: "\\sigma_{ij} = C_{ijkl} \\varepsilon_{kl} \\quad \\implies \\quad \\sigma = E \\cdot \\varepsilon",
            desc: "Relation contrainte-déformation pour les tissus musculaires et structures osseuses anisotropes."
        },
        {
            name: "Fréquence de Larmor (Imagerie IRM)",
            formula: "\\omega_0 = \\gamma B_0",
            desc: "Fréquence de précession des spins nucléaires (protons H+) sous l'action du champ magnétique B0."
        },
        {
            name: "Loi d'Atténuation des Rayons X (Beer-Lambert)",
            formula: "I(x) = I_0 \\cdot e^{-\\mu x}",
            desc: "Absorption du faisceau X en tomodensitométrie (CT-Scan) à travers un tissu de coefficient mu."
        }
    ],
    math: [
        {
            name: "Série de Fourier",
            formula: "f(t) = a_0 + \\sum_{n=1}^{+\\infty} \\left( a_n \\cos(n \\omega t) + b_n \\sin(n \\omega t) \\right)",
            desc: "Décomposition d'un signal périodique en somme d'harmoniques sinusoïdales."
        },
        {
            name: "Transformée de Laplace",
            formula: "X(s) = \\mathcal{L}\\{x(t)\\} = \\int_{0}^{+\\infty} x(t) e^{-s t} dt",
            desc: "Analyse des systèmes différentiels et fonctions de transfert continus."
        }
    ]
};

function renderFormulasTab(note) {
    const container = document.getElementById("formulas-content");
    if (!container) return;

    const meta = parseNoteMeta(note);
    const subjectText = `${meta.subject} ${note.title}`.toLowerCase();
    
    // Select canonical cheatsheet category
    let categoryKey = "generalMath";
    if (subjectText.includes("signal") || subjectText.includes("sic") || subjectText.includes("traitement") || subjectText.includes("fourier")) {
        categoryKey = "signal";
    } else if (subjectText.includes("réseau") || subjectText.includes("net") || subjectText.includes("shannon") || subjectText.includes("commutation")) {
        categoryKey = "networks";
    } else if (subjectText.includes("bme") || subjectText.includes("biomécanique") || subjectText.includes("imagerie") || subjectText.includes("médical")) {
        categoryKey = "bme";
    } else if (subjectText.includes("mat") || subjectText.includes("math")) {
        categoryKey = "math";
    } else {
        categoryKey = "signal"; // Default to signal processing if engineering course
    }

    const formulasList = CANONICAL_FORMULARIES[categoryKey] || CANONICAL_FORMULARIES.signal;

    let html = `
        <div style="padding: 10px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 14px;">
                <div>
                    <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;">
                        📐 Formulaire Canonique — ${escapeHTML(meta.subject)}
                    </h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
                        Formules de référence du cours, théorèmes et définitions fondamentales
                    </p>
                </div>
                <span class="card-badge" style="background: rgba(59, 130, 246, 0.15); color: #2563eb;">
                    ${formulasList.length} équations de référence
                </span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 16px;">
    `;

    formulasList.forEach((item, idx) => {
        html += `
            <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="font-size: 1rem; font-weight: 700; color: var(--text-primary); margin: 0;">
                        ${idx + 1}. ${escapeHTML(item.name)}
                    </h4>
                </div>
                <div class="formula-box" style="font-size: 1.15rem; text-align: center; overflow-x: auto; padding: 12px 16px; background: var(--bg-modal); border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 10px;">
                    $$\n${item.formula}\n$$
                </div>
                <p style="font-size: 0.88rem; color: var(--text-secondary); margin: 0; line-height: 1.4;">
                    ℹ️ ${escapeHTML(item.desc)}
                </p>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    container.innerHTML = html;
    renderKaTeX(container);
}

const SAMPLE_QUIZZES = {
    bme: [
        {
            question: "1. Quel modèle est principalement utilisé pour analyser l'élasticité 3D des tissus biologiques ?",
            options: [
                "Loi de Hooke isotrope / anisotrope",
                "Modèle de Navier-Stokes pour fluides",
                "Équation de Maxwell-Boltzmann",
                "Théorème de Nyquist"
            ],
            correct: 0,
            explanation: "La loi de Hooke 3D relie le tenseur des contraintes au tenseur des déformations pour les tissus osseux et musculaires."
        },
        {
            question: "2. Quelle modalité d'imagerie médicale est non-ionisante et basée sur le spin des protons d'hydrogène ?",
            options: [
                "Scanner X (CT-Scan)",
                "IRM (Imagerie par Résonance Magnétique)",
                "Scintigraphie osseuse",
                "Radiographie conventionnelle"
            ],
            correct: 1,
            explanation: "L'IRM utilise un champ magnétique intense et des ondes RF pour exciter les spins des noyaux d'hydrogène sans radiation ionisante."
        },
        {
            question: "3. Quelle est l'unité principale de mesure du module d'Young en biomécanique osseuse ?",
            options: [
                "Pascal (Pa) ou GigaPascal (GPa)",
                "Joules (J)",
                "Watts (W)",
                "Hertz (Hz)"
            ],
            correct: 0,
            explanation: "Le module d'Young exprime la rigidité d'un matériau et se mesure en Pa ou GPa (l'os cortical a un module d'environ 15-20 GPa)."
        }
    ],
    vap3a: [
        {
            question: "1. Dans les réseaux avancés de 3A VAP, quel protocole garantit la qualité de service (QoS) en réservant la bande passante ?",
            options: [
                "RSVP (Resource Reservation Protocol)",
                "UDP (User Datagram Protocol)",
                "ICMP Echo Request",
                "ARP (Address Resolution Protocol)"
            ],
            correct: 0,
            explanation: "RSVP permet d'établir des réservations de ressources à travers un réseau pour prendre en charge des flux multimédias exigeants."
        },
        {
            question: "2. Quel est l'objectif principal d'un algorithme de consensus Proof of Stake (PoS) ?",
            options: [
                "Valider des blocs selon la quantité de jetons séquestrés au lieu de la puissance de calcul",
                "Accroître la consommation d'électricité des serveurs",
                "Remplacer les adresses IP v6 par du NAT 444",
                "Crypter les paquets HTTP en SSL v2"
            ],
            correct: 0,
            explanation: "Le PoS sélectionne les valideurs en fonction de leur participation financière (stake), économisant ainsi l'énergie par rapport au PoW."
        },
        {
            question: "3. Quelle formule régit le calcul du débit maximal sans erreur sur un canal bruité ?",
            options: [
                "Capacité de Shannon C = B * log2(1 + SNR)",
                "Formule de Taylor-Young",
                "Équation de Schrödinger",
                "Loi d'Ohm R = U / I"
            ],
            correct: 0,
            explanation: "La capacité de Shannon définit la limite théorique maximale de débit binaire pour un canal avec une largeur de bande B et un rapport signal/bruit SNR."
        }
    ]
};

function renderQuizTab(note) {
    const container = document.getElementById("quiz-content");
    if (!container) return;

    const meta = parseNoteMeta(note);
    const quizList = meta.school === "Master BME" ? SAMPLE_QUIZZES.bme : SAMPLE_QUIZZES.vap3a;

    let html = `
        <div style="background: var(--bg-modal); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 14px;">
                <div>
                    <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin: 0;">
                        🎯 QCM d'Évaluation (Réservé 3A VAP & Master BME)
                    </h3>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
                        Vérification des notions clés pour la séance "${escapeHTML(note.title)}"
                    </p>
                </div>
                <div id="quiz-score-badge" style="background: #2563eb; color: #fff; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
                    Score : 0 / ${quizList.length}
                </div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 20px;">
    `;

    quizList.forEach((q, qIdx) => {
        html += `
            <div class="quiz-question-card" data-q-idx="${qIdx}" style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 18px;">
                <h4 style="font-size: 0.98rem; font-weight: 600; color: var(--text-primary); margin-bottom: 14px;">
                    ${escapeHTML(q.question)}
                </h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">
        `;

        q.options.forEach((opt, optIdx) => {
            const isCorrect = optIdx === q.correct;
            const escapedExp = escapeHTML(q.explanation).replace(/'/g, "\\'");
            html += `
                <button type="button" class="quiz-option-btn" 
                        onclick="handleQuizOptionClick(this, ${qIdx}, ${isCorrect}, '${escapedExp}', ${quizList.length})"
                        style="text-align: left; padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-modal); color: var(--text-primary); font-size: 0.9rem; cursor: pointer; transition: all 0.2s ease;">
                    ${escapeHTML(opt)}
                </button>
            `;
        });

        html += `
                </div>
                <div class="quiz-feedback hidden" style="margin-top: 14px; padding: 12px; border-radius: 8px; font-size: 0.88rem; line-height: 1.4;"></div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    container.innerHTML = html;
    window.quizScores = { answered: 0, correct: 0 };
}

function handleQuizOptionClick(btn, qIdx, isCorrect, explanation, totalQuestions) {
    const parentCard = btn.closest(".quiz-question-card");
    if (!parentCard || parentCard.classList.contains("answered")) return;

    parentCard.classList.add("answered");
    const feedbackEl = parentCard.querySelector(".quiz-feedback");
    
    // Disable all options in this question
    parentCard.querySelectorAll(".quiz-option-btn").forEach(b => {
        b.disabled = true;
        b.style.cursor = "default";
        b.style.opacity = "0.7";
    });

    if (!window.quizScores) window.quizScores = { answered: 0, correct: 0 };
    window.quizScores.answered++;

    if (isCorrect) {
        window.quizScores.correct++;
        btn.style.background = "#dcfce7";
        btn.style.borderColor = "#22c55e";
        btn.style.color = "#15803d";
        btn.style.fontWeight = "600";
        btn.style.opacity = "1";
        
        if (feedbackEl) {
            feedbackEl.classList.remove("hidden");
            feedbackEl.style.background = "rgba(34, 197, 94, 0.1)";
            feedbackEl.style.border = "1px solid rgba(34, 197, 94, 0.3)";
            feedbackEl.style.color = "#15803d";
            feedbackEl.innerHTML = `<strong>Correct !</strong> ${explanation}`;
        }
    } else {
        btn.style.background = "#fee2e2";
        btn.style.borderColor = "#ef4444";
        btn.style.color = "#b91c1c";
        btn.style.fontWeight = "600";
        btn.style.opacity = "1";

        if (feedbackEl) {
            feedbackEl.classList.remove("hidden");
            feedbackEl.style.background = "rgba(239, 68, 68, 0.1)";
            feedbackEl.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            feedbackEl.style.color = "#b91c1c";
            feedbackEl.innerHTML = `<strong>Incorrect.</strong> ${explanation}`;
        }
    }

    const badge = document.getElementById("quiz-score-badge");
    if (badge) {
        badge.textContent = `Score : ${window.quizScores.correct} / ${totalQuestions}`;
    }
}

window.deleteNote = deleteNote;
window.changeSubject = changeSubject;
window.openMoveModal = openMoveModal;
window.closeMoveModal = closeMoveModal;
window.handleQuizOptionClick = handleQuizOptionClick;

function openCorrectionEditor() {
    if (!activeModalNoteId) return;
    const note = allNotes.find(n => n.id === activeModalNoteId);
    if (!note) return;

    const modal = document.getElementById("correction-editor-modal");
    const textarea = document.getElementById("correction-textarea");
    const statusMsg = document.getElementById("correction-status-msg");
    const subtitle = document.getElementById("correction-subtitle");

    if (subtitle) subtitle.textContent = `Correction du cours : "${note.title}"`;
    if (textarea) textarea.value = note.full_transcription || "";
    if (statusMsg) statusMsg.textContent = "";

    if (modal) modal.classList.remove("hidden");
    if (window.lucide) window.lucide.createIcons();
}

function closeCorrectionModal() {
    const modal = document.getElementById("correction-editor-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveCorrection() {
    if (!activeModalNoteId) return;
    const note = allNotes.find(n => n.id === activeModalNoteId);
    if (!note) return;

    const textarea = document.getElementById("correction-textarea");
    const statusMsg = document.getElementById("correction-status-msg");
    const saveBtn = document.getElementById("save-correction-btn");
    
    if (!textarea) return;

    const newTranscription = textarea.value;
    if (saveBtn) saveBtn.disabled = true;
    if (statusMsg) {
        statusMsg.style.color = "#2563eb";
        statusMsg.textContent = "Sauvegarde dans Supabase...";
    }

    try {
        if (supabaseClient) {
            const { data, error } = await supabaseClient
                .from("notes")
                .update({ full_transcription: newTranscription })
                .eq("id", note.id);

            if (error) {
                console.error("[Supabase Correction Error]:", error);
                alert("Erreur lors de la sauvegarde dans Supabase : " + error.message);
                if (statusMsg) {
                    statusMsg.style.color = "#ef4444";
                    statusMsg.textContent = "Erreur de sauvegarde.";
                }
                if (saveBtn) saveBtn.disabled = false;
                return;
            }
        }

        // Update local state
        note.full_transcription = newTranscription;

        // Re-render Tab 2: Transcription & KaTeX
        const transcriptionContainer = document.getElementById("transcription-content");
        if (transcriptionContainer) {
            transcriptionContainer.innerHTML = marked.parse(newTranscription);
            renderKaTeX(transcriptionContainer);
        }

        if (statusMsg) {
            statusMsg.style.color = "#10b981";
            statusMsg.textContent = "✅ Modifié & Enregistré dans Supabase !";
        }

        setTimeout(() => {
            closeCorrectionModal();
            if (saveBtn) saveBtn.disabled = false;
        }, 600);

    } catch (err) {
        console.error("[Save Correction Error]:", err);
        alert("Erreur : " + err.message);
        if (saveBtn) saveBtn.disabled = false;
    }
}

window.openCorrectionEditor = openCorrectionEditor;
window.closeCorrectionModal = closeCorrectionModal;
window.saveCorrection = saveCorrection;

window.onDeleteCurrentNote = function() {
    if (activeModalNoteId) {
        const note = allNotes.find(n => n.id === activeModalNoteId);
        if (note) deleteNote(note.id, note.title);
    }
};

window.onMoveCurrentNote = function() {
    if (activeModalNoteId) {
        const note = allNotes.find(n => n.id === activeModalNoteId);
        if (note) openMoveModal(note);
    }
};

window.onEditSubject = function() {
    if (activeModalNoteId) {
        const note = allNotes.find(n => n.id === activeModalNoteId);
        if (note) changeSubject(note.id, note.subject_name || "Général");
    }
};

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 10);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function triggerWebScan() {
    const btn = document.getElementById("trigger-scan-btn");
    const icon = document.getElementById("scan-btn-icon");
    const text = document.getElementById("scan-btn-text");

    if (btn) btn.disabled = true;
    if (icon) icon.classList.add("spin");
    if (text) text.textContent = "Scan en cours...";

    showToast("🔄 Démarrage du scan Google Drive en arrière-plan...", "info");

    try {
        const response = await fetch("/api/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();

        if (response.ok) {
            showToast("🚀 " + (data.message || "Scan Google Drive lancé avec succès !"), "success");
            setTimeout(() => {
                loadData();
            }, 3000);
        } else {
            showToast("❌ Erreur de scan : " + (data.error || "Échec"), "error");
        }
    } catch (err) {
        console.error("Scan error:", err);
        showToast("⚠️ Impossible de contacter le serveur backend /api/scan", "error");
    } finally {
        setTimeout(() => {
            if (btn) btn.disabled = false;
            if (icon) icon.classList.remove("spin");
            if (text) text.textContent = "Resynchroniser Drive";
        }, 2500);
    }
}

window.triggerWebScan = triggerWebScan;
window.showToast = showToast;

async function triggerReanalyzeNote(noteId) {
    if (!noteId) return;
    const note = allNotes.find(n => n.id === noteId);
    const title = note ? note.title : "le document";

    if (!confirm(`Refaire une analyse IA (Gemini Vision) complète sur le document d'origine Google Drive pour "${title}" ?`)) {
        return;
    }

    const btn = document.getElementById("modal-reanalyze-btn");
    const icon = document.getElementById("modal-reanalyze-icon");
    const text = document.getElementById("modal-reanalyze-text");

    if (btn) btn.disabled = true;
    if (icon) icon.classList.add("spin");
    if (text) text.textContent = "Analyse IA...";

    showToast(`⚡ Lancement de l'analyse IA sur "${title}"...`, "info");

    try {
        const response = await fetch("/api/reanalyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ note_id: noteId })
        });

        const data = await response.json();

        if (response.ok) {
            showToast("✨ " + (data.message || "Analyse IA relancée !"), "success");
            setTimeout(() => {
                loadData();
            }, 4000);
        } else {
            showToast("❌ Erreur : " + (data.error || "Échec"), "error");
        }
    } catch (err) {
        console.error("Reanalyze error:", err);
        showToast("⚠️ Impossible de contacter le serveur backend /api/reanalyze", "error");
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove("spin");
        if (text) text.textContent = "Ré-analyser par IA";
    }
}

async function triggerReanalyzeAll() {
    if (!confirm("Voulez-vous forcer une nouvelle analyse Gemini IA sur TOUS les documents PDF dans Google Drive ? (Cela peut prendre plusieurs minutes)")) {
        return;
    }

    const btn = document.getElementById("trigger-reanalyze-all-btn");
    const icon = document.getElementById("reanalyze-all-btn-icon");
    const text = document.getElementById("reanalyze-all-btn-text");

    if (btn) btn.disabled = true;
    if (icon) icon.classList.add("spin");
    if (text) text.textContent = "Analyse en cours...";

    showToast("⚡ Lancement de la ré-analyse IA globale en arrière-plan...", "info");

    try {
        const response = await fetch("/api/reanalyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ all: true })
        });

        const data = await response.json();

        if (response.ok) {
            showToast("🚀 " + (data.message || "Ré-analyse IA globale démarrée !"), "success");
            setTimeout(() => {
                loadData();
            }, 5000);
        } else {
            showToast("❌ Erreur : " + (data.error || "Échec"), "error");
        }
    } catch (err) {
        console.error("Reanalyze all error:", err);
        showToast("⚠️ Impossible de contacter le serveur backend /api/reanalyze", "error");
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove("spin");
        if (text) text.textContent = "Ré-analyser tout par IA";
    }
}

window.onReanalyzeCurrentNote = function() {
    if (activeModalNoteId) {
        triggerReanalyzeNote(activeModalNoteId);
    }
};

window.triggerReanalyzeAll = triggerReanalyzeAll;
window.triggerReanalyzeNote = triggerReanalyzeNote;


