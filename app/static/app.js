/**
 * CertiFlow Interactive Client Controller
 * AEREO SDE Benchmark Platform
 */

const DEMO_FAULT_RECIPIENTS = [
  {
    "recipient_id": "AEREO-STU-001",
    "name": "Riyanshi Sharma",
    "email": "riyanshi@aereo-academy.in",
    "custom_note": "Rank 1 • Distinguished Flight Lead"
  },
  {
    "recipient_id": "AEREO-STU-002",
    "name": "Alex Mercer",
    "email": "alex.mercer@enterprise.org",
    "custom_note": "Geospatial Analytics Honors"
  },
  {
    "recipient_id": "AEREO-STU-003",
    "name": "David Chen",
    "email": "david.chen@drone-tech.io",
    "custom_note": "LiDAR Processing Specialist"
  },
  {
    "recipient_id": "AEREO-FAULT-TEST",
    "name": "Faulty Recipient (Format Error)",
    "email": "invalid-email-no-domain",
    "custom_note": "Intentionally malformed email to demonstrate Fault Isolation"
  },
  {
    "recipient_id": "AEREO-STU-005",
    "name": "Sarah Jenkins",
    "email": "sarah.jenkins@spatial-ai.com",
    "custom_note": "Photogrammetry Survey Engineer"
  }
];

const PRESET_CLEAN = [
  {
    "recipient_id": "AEREO-CERT-101",
    "name": "Riyanshi Sharma",
    "email": "riyanshi@aereo-academy.in",
    "custom_note": "Distinction • Top Performer"
  },
  {
    "recipient_id": "AEREO-CERT-102",
    "name": "Vikram Malhotra",
    "email": "vikram.m@aereo-space.io",
    "custom_note": "Autonomous Navigation Specialist"
  },
  {
    "recipient_id": "AEREO-CERT-103",
    "name": "Elena Rostova",
    "email": "elena.rostova@geospatial.net",
    "custom_note": "Hyperspectral Sensing Honors"
  },
  {
    "recipient_id": "AEREO-CERT-104",
    "name": "Karthik Subramanian",
    "email": "karthik.s@drone-academy.org",
    "custom_note": "GIS Systems Architecture"
  }
];

const PRESET_LARGE = [
  { "recipient_id": "AEREO-BAT-001", "name": "Riyanshi Sharma", "email": "riyanshi@aereo.in", "custom_note": "Cohort Lead" },
  { "recipient_id": "AEREO-BAT-002", "name": "Marcus Aurelius", "email": "marcus@enterprise.com", "custom_note": "Grade A" },
  { "recipient_id": "AEREO-BAT-003", "name": "Ananya Roy", "email": "ananya.roy@geotech.org", "custom_note": "LiDAR Lead" },
  { "recipient_id": "AEREO-BAT-004", "name": "Carlos Gomez", "email": "carlos.g@drone-survey.io", "custom_note": "Flight Operations" },
  { "recipient_id": "AEREO-BAT-005", "name": "Fatima Al-Zahra", "email": "fatima.z@aereo-space.ae", "custom_note": "Distinction" },
  { "recipient_id": "AEREO-BAT-006", "name": "Liam O'Connor", "email": "liam.oc@aerial-ai.com", "custom_note": "Grade A+" },
  { "recipient_id": "AEREO-BAT-007", "name": "Mei-Ling Zhou", "email": "mei.zhou@spatial-data.org", "custom_note": "Photogrammetry" },
  { "recipient_id": "AEREO-BAT-008", "name": "Arjun Patel", "email": "arjun.patel@aereo.in", "custom_note": "GIS Systems" },
  { "recipient_id": "AEREO-BAT-009", "name": "Sophia Becker", "email": "sophia.b@aerospace-de.com", "custom_note": "Telemetry Lead" },
  { "recipient_id": "AEREO-BAT-010", "name": "Zubair Khan", "email": "zubair.k@drone-logistics.io", "custom_note": "Grade A" },
  { "recipient_id": "AEREO-BAT-011", "name": "Chloe Martin", "email": "chloe.m@survey-solutions.fr", "custom_note": "Top 5%" },
  { "recipient_id": "AEREO-BAT-012", "name": "Daniel Kim", "email": "daniel.kim@drone-robotics.kr", "custom_note": "Sensor Fusion" }
];

let pollingInterval = null;
let currentJobId = null;
let pollStartTime = null;
let allCertificates = [];
let recentSampleCodes = ["CERT-DEMO-001", "CERT-DEMO-002"];
let tableFilters = {
  search: "",
  status: "ALL",
  sort: "DEFAULT"
};

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initViewRouting();
  initTabs();
  initDemoData();
  initDropzone();
  initEventListeners();
  updateQuickVerifyPills();
});

/* ======================================================== */
/* 1. THEME MANAGEMENT                                      */
/* ======================================================== */
function initTheme() {
  const toggleBtn = document.getElementById("theme-toggle-btn");
  const savedTheme = localStorage.getItem("certiflow-theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const nextTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("certiflow-theme", nextTheme);
      showToast(`Switched to ${nextTheme === "dark" ? "Dark" : "Light"} Mode`);
    });
  }
}

/* ======================================================== */
/* 2. VIEW ROUTING (LANDING PAGE vs APP WORKSPACE)          */
/* ======================================================== */
function initViewRouting() {
  const landingView = document.getElementById("view-landing");
  const appView = document.getElementById("view-app");
  const navLaunchBtn = document.getElementById("nav-launch-btn");

  window.switchView = function(viewName) {
    if (viewName === "app") {
      if (landingView) landingView.className = "view-hidden";
      if (appView) appView.className = "view-active";
      if (navLaunchBtn) navLaunchBtn.style.display = "none";
      window.scrollTo({ top: 0, behavior: "smooth" });
      history.pushState(null, "", "#app");
    } else {
      if (appView) appView.className = "view-hidden";
      if (landingView) landingView.className = "view-active";
      if (navLaunchBtn) navLaunchBtn.style.display = "inline-flex";
      window.scrollTo({ top: 0, behavior: "smooth" });
      history.pushState(null, "", "#home");
    }
  };

  // Buttons that launch the dedicated app console
  document.getElementById("btn-hero-launch")?.addEventListener("click", () => switchView("app"));
  document.getElementById("nav-launch-btn")?.addEventListener("click", () => switchView("app"));
  document.getElementById("btn-cta-launch")?.addEventListener("click", () => switchView("app"));
  document.getElementById("footer-launch-btn")?.addEventListener("click", () => switchView("app"));

  // Buttons that navigate back to the product overview / landing page
  document.getElementById("btn-back-to-landing")?.addEventListener("click", () => switchView("landing"));
  document.getElementById("nav-brand")?.addEventListener("click", () => switchView("landing"));
  document.getElementById("nav-home-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("landing");
  });

  // Section anchor links on the landing page
  document.getElementById("nav-arch-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("landing");
    setTimeout(() => {
      document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  });

  document.getElementById("nav-verify-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("landing");
    setTimeout(() => {
      document.getElementById("verify")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  });

  // Handle URL hash on initial load
  if (window.location.hash === "#app" || window.location.hash === "#console") {
    switchView("app");
  } else {
    switchView("landing");
  }

  window.addEventListener("popstate", () => {
    if (window.location.hash === "#app" || window.location.hash === "#console") {
      switchView("app");
    } else {
      switchView("landing");
    }
  });
}

/* ======================================================== */
/* 3. INGESTION TABS (JSON vs CSV)                          */
/* ======================================================== */
function initTabs() {
  const jsonBtn = document.getElementById("tab-json-btn");
  const csvBtn = document.getElementById("tab-csv-btn");
  const jsonTab = document.getElementById("tab-json");
  const csvTab = document.getElementById("tab-csv");

  jsonBtn?.addEventListener("click", () => {
    jsonBtn.classList.add("active");
    csvBtn.classList.remove("active");
    jsonTab.style.display = "block";
    csvTab.style.display = "none";
  });

  csvBtn?.addEventListener("click", () => {
    csvBtn.classList.add("active");
    jsonBtn.classList.remove("active");
    csvTab.style.display = "block";
    jsonTab.style.display = "none";
  });
}

/* ======================================================== */
/* 4. PRESETS & JSON EDITOR                                 */
/* ======================================================== */
function initDemoData() {
  const textarea = document.getElementById("recipients-json");
  if (!textarea) return;

  textarea.value = JSON.stringify(DEMO_FAULT_RECIPIENTS, null, 2);
  updateRecipientCountBadge(DEMO_FAULT_RECIPIENTS.length);

  document.getElementById("btn-load-demo")?.addEventListener("click", () => {
    textarea.value = JSON.stringify(DEMO_FAULT_RECIPIENTS, null, 2);
    updateRecipientCountBadge(DEMO_FAULT_RECIPIENTS.length);
    showToast("Demo batch loaded (5 recipients, including 1 fault test). Ready to dispatch!");
  });

  document.getElementById("btn-load-clean-preset")?.addEventListener("click", () => {
    textarea.value = JSON.stringify(PRESET_CLEAN, null, 2);
    updateRecipientCountBadge(PRESET_CLEAN.length);
    showToast("Clean cohort loaded (4 pristine recipients).");
  });

  document.getElementById("btn-load-large-preset")?.addEventListener("click", () => {
    textarea.value = JSON.stringify(PRESET_LARGE, null, 2);
    updateRecipientCountBadge(PRESET_LARGE.length);
    showToast("Large cohort loaded (12 recipients).");
  });

  document.getElementById("btn-set-today")?.addEventListener("click", () => {
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("issue-date").value = today;
    document.getElementById("csv-issue-date").value = today;
    showToast(`Date set to ${today}`);
  });

  document.getElementById("btn-format-json")?.addEventListener("click", () => {
    try {
      const parsed = JSON.parse(textarea.value);
      textarea.value = JSON.stringify(parsed, null, 2);
      showToast("JSON formatted successfully.");
    } catch (e) {
      showToast("Invalid JSON syntax.", "error");
    }
  });

  textarea.addEventListener("input", () => {
    try {
      const parsed = JSON.parse(textarea.value);
      if (Array.isArray(parsed)) {
        updateRecipientCountBadge(parsed.length);
      }
    } catch (e) {
      document.getElementById("recipient-count-badge").textContent = "Invalid JSON";
    }
  });
}

function updateRecipientCountBadge(count) {
  const badge = document.getElementById("recipient-count-badge");
  if (badge) badge.textContent = `${count} recipients`;
}

/* ======================================================== */
/* 5. CSV DROPZONE & SAMPLE GENERATION                      */
/* ======================================================== */
function initDropzone() {
  const dropzone = document.getElementById("csv-dropzone");
  const fileInput = document.getElementById("csv-file-input");
  const dropText = document.getElementById("dropzone-text");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--accent-cyan)";
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.style.borderColor = "var(--border-color)";
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--border-color)";
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    dropText.innerHTML = `
      <span class="dropzone-icon" style="color: var(--accent-emerald);">📄</span>
      <p><strong>${escapeHtml(file.name)}</strong> (${(file.size / 1024).toFixed(1)} KB)</p>
      <span class="dropzone-note" style="color: var(--accent-cyan);">Ready to dispatch</span>
    `;
    showToast(`Loaded ${file.name}`);
  }

  // Download template CSV
  document.getElementById("btn-download-csv-template")?.addEventListener("click", () => {
    const csvContent = "name,email,recipient_id,custom_note\n" +
      "Riyanshi Sharma,riyanshi@aereo-academy.in,AEREO-STU-001,Rank 1 • Flight Lead\n" +
      "Alex Mercer,alex.mercer@enterprise.org,AEREO-STU-002,Geospatial Analytics\n" +
      "David Chen,david.chen@drone-tech.io,AEREO-STU-003,LiDAR Specialist\n" +
      "Sarah Jenkins,sarah.jenkins@spatial-ai.com,AEREO-STU-004,Photogrammetry Lead\n";

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "certiflow_recipients_template.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Downloaded CSV template.");
  });

  // Load sample CSV directly
  document.getElementById("btn-load-sample-csv")?.addEventListener("click", () => {
    const csvContent = "name,email,recipient_id,custom_note\n" +
      "Riyanshi Sharma,riyanshi@aereo-academy.in,AEREO-STU-001,Rank 1 • Flight Lead\n" +
      "Alex Mercer,alex.mercer@enterprise.org,AEREO-STU-002,Geospatial Analytics\n" +
      "David Chen,david.chen@drone-tech.io,AEREO-STU-003,LiDAR Specialist\n" +
      "Faulty Recipient,invalid-email-no-domain,AEREO-FAULT-001,Fault Isolation Test\n" +
      "Sarah Jenkins,sarah.jenkins@spatial-ai.com,AEREO-STU-005,Photogrammetry Lead\n";

    const file = new File([csvContent], "sample_recipients.csv", { type: "text/csv" });
    const container = new DataTransfer();
    container.items.add(file);
    fileInput.files = container.files;
    handleFileSelected(file);
  });
}

/* ======================================================== */
/* 6. EVENT LISTENERS                                       */
/* ======================================================== */
function initEventListeners() {
  document.getElementById("btn-submit-job")?.addEventListener("click", handleJsonSubmit);
  document.getElementById("btn-submit-csv")?.addEventListener("click", handleCsvSubmit);
  
  document.getElementById("btn-refresh-status")?.addEventListener("click", () => {
    if (currentJobId) {
      pollJobStatus(currentJobId);
      showToast("Refreshed status.");
    }
  });

  document.getElementById("btn-reset-workspace")?.addEventListener("click", resetWorkspace);

  document.getElementById("btn-copy-job-id")?.addEventListener("click", () => {
    if (currentJobId) {
      navigator.clipboard.writeText(currentJobId);
      showToast("Job ID copied to clipboard.");
    }
  });

  document.getElementById("btn-dispatch-emails")?.addEventListener("click", () => {
    if (currentJobId) triggerEmailDispatch(currentJobId);
  });

  // Table search & filter listeners
  const searchInput = document.getElementById("cert-table-search");
  searchInput?.addEventListener("input", (e) => {
    tableFilters.search = e.target.value.trim().toLowerCase();
    renderCertificatesTable();
  });

  document.getElementById("filter-status-select")?.addEventListener("change", (e) => {
    tableFilters.status = e.target.value;
    renderCertificatesTable();
  });

  document.getElementById("sort-select")?.addEventListener("change", (e) => {
    tableFilters.sort = e.target.value;
    renderCertificatesTable();
  });

  // Clickable column header sorting
  document.querySelectorAll(".sortable-th").forEach((th) => {
    th.addEventListener("click", () => {
      const sortType = th.getAttribute("data-sort");
      if (sortType) {
        const sortSelect = document.getElementById("sort-select");
        if (sortSelect) sortSelect.value = sortType;
        tableFilters.sort = sortType;
        renderCertificatesTable();
      }
    });
  });

  // Landing page verification
  document.getElementById("btn-landing-verify")?.addEventListener("click", () => {
    const code = document.getElementById("landing-verify-code-input").value.trim();
    executeVerification(code, "landing-verify-result-card");
  });

  document.getElementById("landing-verify-code-input")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const code = e.target.value.trim();
      executeVerification(code, "landing-verify-result-card");
    }
  });

  // Rate Limiting Burst Test
  document.getElementById("btn-test-rate-limit")?.addEventListener("click", executeRateLimitBurstTest);
}

/* ======================================================== */
/* 7. JOB SUBMISSION                                        */
/* ======================================================== */
async function handleJsonSubmit() {
  const title = document.getElementById("event-title").value.trim();
  const issuer = document.getElementById("issuer-name").value.trim();
  const date = document.getElementById("issue-date").value.trim();
  const rawJson = document.getElementById("recipients-json").value.trim();

  if (!title || !issuer || !date) {
    showToast("Please fill in title, issuer, and date.", "error");
    return;
  }

  let recipients = [];
  try {
    recipients = JSON.parse(rawJson);
    if (!Array.isArray(recipients) || recipients.length === 0) {
      throw new Error("Must be a non-empty array");
    }
  } catch (err) {
    showToast("Invalid JSON format for recipients: " + err.message, "error");
    return;
  }

  const payload = {
    title: title,
    issuer_name: issuer,
    issue_date: date,
    recipients: recipients
  };

  setSubmitting(true);
  try {
    const res = await fetch("/api/v1/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Job submission failed");
    }

    const data = await res.json();
    showToast(`Job ${data.job_id.slice(0, 8)} accepted! Background workers running.`);
    startJobTracking(data.job_id);
  } catch (err) {
    showToast("Submission error: " + err.message, "error");
  } finally {
    setSubmitting(false);
  }
}

async function handleCsvSubmit() {
  const fileInput = document.getElementById("csv-file-input");
  if (!fileInput.files.length) {
    showToast("Please select a CSV file first.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("title", document.getElementById("csv-event-title").value.trim());
  formData.append("issuer_name", document.getElementById("csv-issuer-name").value.trim());
  formData.append("issue_date", document.getElementById("csv-issue-date").value.trim());

  setSubmitting(true);
  try {
    const res = await fetch("/api/v1/jobs/upload-csv", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "CSV upload failed");
    }

    const data = await res.json();
    showToast(`CSV accepted! Enqueued background job ${data.job_id.slice(0, 8)}.`);
    startJobTracking(data.job_id);
  } catch (err) {
    showToast("CSV error: " + err.message, "error");
  } finally {
    setSubmitting(false);
  }
}

function setSubmitting(isSubmitting) {
  const spinner = document.getElementById("submit-spinner");
  const btn = document.getElementById("btn-submit-job");
  const csvBtn = document.getElementById("btn-submit-csv");
  if (btn) btn.disabled = isSubmitting;
  if (csvBtn) csvBtn.disabled = isSubmitting;
  if (spinner) spinner.style.display = isSubmitting ? "inline-block" : "none";
}

/* ======================================================== */
/* 8. JOB TELEMETRY                                         */
/* ======================================================== */
function startJobTracking(jobId) {
  currentJobId = jobId;
  pollStartTime = Date.now();
  if (pollingInterval) clearInterval(pollingInterval);

  document.getElementById("active-job-id").textContent = jobId;
  document.getElementById("btn-copy-job-id").style.display = "inline-flex";
  document.getElementById("telemetry-idle-box").style.display = "none";
  document.getElementById("telemetry-actions").style.display = "none";
  document.getElementById("fault-drawer").style.display = "none";
  document.getElementById("gallery-section").style.display = "none";

  pollJobStatus(jobId);
  pollingInterval = setInterval(() => pollJobStatus(jobId), 400);
}

async function pollJobStatus(jobId) {
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}`);
    if (!res.ok) return;

    const data = await res.json();
    renderTelemetry(data);

    if (["COMPLETED", "PARTIAL_SUCCESS", "FAILED"].includes(data.status)) {
      clearInterval(pollingInterval);
      pollingInterval = null;
      loadJobCertificates(jobId);
    }
  } catch (e) {
    console.error("Telemetry polling error", e);
  }
}

function renderTelemetry(data) {
  const pill = document.getElementById("job-status-pill");
  pill.textContent = data.status;
  pill.className = "status-pill";

  if (data.status === "PENDING" || data.status === "PROCESSING") {
    pill.classList.add("status-processing");
  } else if (data.status === "COMPLETED") {
    pill.classList.add("status-completed");
  } else if (data.status === "PARTIAL_SUCCESS") {
    pill.classList.add("status-partial");
  } else if (data.status === "FAILED") {
    pill.classList.add("status-failed");
  }

  const elapsed = Math.max(1, Math.round((Date.now() - pollStartTime) / 1000));
  document.getElementById("job-elapsed-time").textContent = `${elapsed}s`;

  const pct = data.progress_percentage || 0;
  document.getElementById("progress-bar-fill").style.width = `${pct}%`;
  document.getElementById("progress-pct").textContent = `${pct}%`;
  document.getElementById("progress-counts").textContent = `${data.processed} / ${data.total} Processed`;

  document.getElementById("metric-total").textContent = data.total;
  document.getElementById("metric-success").textContent = data.successful;
  document.getElementById("metric-failed").textContent = data.failed;

  // Fault drawer (Prominent Incident Breakdown)
  const faultDrawer = document.getElementById("fault-drawer");
  const faultList = document.getElementById("fault-list");
  if (data.failures && data.failures.length > 0) {
    document.getElementById("fault-count").textContent = data.failures.length;
    faultList.innerHTML = data.failures.map((f, idx) => `
      <div class="fault-item-card">
        <div class="fault-item-top">
          <div class="fault-item-identity">
            <span class="fault-item-idx">#${idx + 1}</span>
            <strong class="fault-item-name">${escapeHtml(f.recipient_name || "Unknown Name")}</strong>
          </div>
          <span class="fault-item-badge">FAILED & ISOLATED</span>
        </div>
        <div class="fault-item-meta">
          <span class="fault-meta-email font-mono">${escapeHtml(f.recipient_email || "No email")}</span>
        </div>
        <div class="fault-item-reason">
          <span class="fault-reason-label">Exact Reason:</span>
          <code class="fault-reason-code">${escapeHtml(f.error)}</code>
        </div>
      </div>
    `).join("");
    faultDrawer.style.display = "block";
  } else {
    faultDrawer.style.display = "none";
  }

  // ZIP download link
  const actionsWrap = document.getElementById("telemetry-actions");
  const zipBtn = document.getElementById("btn-download-all-zip");
  if (data.zip_download_url) {
    zipBtn.href = data.zip_download_url;
    actionsWrap.style.display = "flex";
  }
}

function resetWorkspace() {
  currentJobId = null;
  if (pollingInterval) clearInterval(pollingInterval);

  document.getElementById("active-job-id").textContent = "—";
  document.getElementById("job-elapsed-time").textContent = "—";
  document.getElementById("btn-copy-job-id").style.display = "none";
  document.getElementById("job-status-pill").textContent = "IDLE";
  document.getElementById("job-status-pill").className = "status-pill status-idle";

  document.getElementById("progress-bar-fill").style.width = "0%";
  document.getElementById("progress-pct").textContent = "0%";
  document.getElementById("progress-counts").textContent = "0 / 0 Processed";

  document.getElementById("metric-total").textContent = "0";
  document.getElementById("metric-success").textContent = "0";
  document.getElementById("metric-failed").textContent = "0";

  document.getElementById("telemetry-idle-box").style.display = "block";
  document.getElementById("telemetry-actions").style.display = "none";
  document.getElementById("fault-drawer").style.display = "none";
  document.getElementById("gallery-section").style.display = "none";

  showToast("Workspace ready for next cohort.");
}

/* ======================================================== */
/* 9. CREDENTIAL REGISTRY TABLE                             */
/* ======================================================== */
async function loadJobCertificates(jobId) {
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}/certificates?limit=500`);
    if (!res.ok) return;

    const data = await res.json();
    allCertificates = Array.isArray(data) ? data : (data.items || []);

    const successfulCodes = allCertificates
      .filter(c => c.status === "SUCCESS")
      .map(c => c.certificate_code);
    if (successfulCodes.length > 0) {
      recentSampleCodes = successfulCodes.slice(0, 4);
      updateQuickVerifyPills();
    }

    const gallerySection = document.getElementById("gallery-section");
    if (gallerySection) {
      document.getElementById("gallery-count").textContent = (data.total !== undefined ? data.total : allCertificates.length);
      gallerySection.style.display = "block";
    }

    renderCertificatesTable();

    setTimeout(() => {
      gallerySection?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);
  } catch (e) {
    console.error("Failed to load certificates registry table", e);
  }
}

function renderCertificatesTable() {
  const tbody = document.getElementById("cert-table-body");
  const emptyState = document.getElementById("table-empty-state");
  const table = document.getElementById("cert-data-table");
  const entriesCounter = document.getElementById("entries-counter");

  if (!tbody) return;

  let filtered = allCertificates.filter((cert) => {
    if (tableFilters.status !== "ALL") {
      if (cert.status !== tableFilters.status) return false;
    }

    if (tableFilters.search) {
      const q = tableFilters.search;
      const name = (cert.recipient_name || "").toLowerCase();
      const email = (cert.recipient_email || "").toLowerCase();
      const code = (cert.certificate_code || "").toLowerCase();
      const id = (cert.recipient_id || "").toLowerCase();
      const note = (cert.custom_note || "").toLowerCase();
      const err = (cert.error_message || "").toLowerCase();

      return name.includes(q) || email.includes(q) || code.includes(q) || id.includes(q) || note.includes(q) || err.includes(q);
    }

    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    switch (tableFilters.sort) {
      case "NAME_ASC":
        return (a.recipient_name || "").localeCompare(b.recipient_name || "");
      case "NAME_DESC":
        return (b.recipient_name || "").localeCompare(a.recipient_name || "");
      case "STATUS":
        if (a.status !== b.status) return a.status === "FAILED" ? -1 : 1;
        return (a.recipient_name || "").localeCompare(b.recipient_name || "");
      case "CODE_ASC":
        return (a.certificate_code || "").localeCompare(b.certificate_code || "");
      default:
        return 0;
    }
  });

  if (entriesCounter) {
    entriesCounter.textContent = `Showing ${sorted.length} of ${allCertificates.length} entries`;
  }

  if (sorted.length === 0) {
    if (table) table.style.display = "none";
    if (emptyState) emptyState.style.display = "block";
    tbody.innerHTML = "";
    return;
  }

  if (table) table.style.display = "table";
  if (emptyState) emptyState.style.display = "none";

  tbody.innerHTML = sorted.map((c) => {
    const isSuccess = c.status === "SUCCESS";
    const rowClass = isSuccess ? "" : "row-failed";
    const statusPill = isSuccess
      ? `<span class="badge-success">✓ ISSUED</span>`
      : `<span class="badge-failed">❌ FAILED</span>`;

    const recipientIdTag = c.recipient_id
      ? `<span class="cell-recipient-id">ID: ${escapeHtml(c.recipient_id)}</span>`
      : "";

    const noteOrError = isSuccess
      ? c.custom_note
        ? `<span class="cell-note">★ ${escapeHtml(c.custom_note)}</span>`
        : `<span style="color:var(--text-dim); font-size:0.8rem;">—</span>`
      : `<div class="cell-error-box"><span class="cell-error-title">⚠️ Fault Isolated:</span><span class="cell-error-text">${escapeHtml(
          c.error_message || "Simulated fault test"
        )}</span></div>`;

    const actions = isSuccess
      ? `<div class="table-actions">
          <a href="${c.download_url}?disposition=inline" target="_blank" class="btn-table-action primary" title="View 300-DPI vector PDF in full browser reader">
            View PDF ↗
          </a>
          <a href="${c.download_url}?disposition=attachment" target="_blank" download class="btn-table-action" title="Download certificate file">
            📥 Download
          </a>
          <button onclick="quickVerify('${c.certificate_code}')" class="btn-table-action" title="Verify authenticity in public portal">
            🛡️ Verify
          </button>
        </div>`
      : `<div class="table-actions">
          <span class="badge-skipped">Excluded from ZIP</span>
        </div>`;

    return `
      <tr class="${rowClass}">
        <td>${statusPill}</td>
        <td>
          <div class="cert-code-wrap">
            <span class="cert-code">${escapeHtml(c.certificate_code)}</span>
            <button class="btn-copy-code" onclick="copyToClipboard('${c.certificate_code}')" title="Copy Code">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            </button>
          </div>
        </td>
        <td>
          <div class="cell-recipient-wrap">
            <span class="cell-recipient-name">${escapeHtml(c.recipient_name)}</span>
            ${recipientIdTag}
          </div>
        </td>
        <td><span class="cell-email">${escapeHtml(c.recipient_email)}</span></td>
        <td>${noteOrError}</td>
        <td>${actions}</td>
      </tr>
    `;
  }).join("");
}

/* ======================================================== */
/* 10. PUBLIC VERIFICATION                                  */
/* ======================================================== */
window.quickVerify = function(code) {
  switchView("landing");
  const input = document.getElementById("landing-verify-code-input");
  input.value = code;
  document.getElementById("verify")?.scrollIntoView({ behavior: "smooth" });
  executeVerification(code, "landing-verify-result-card");
};

function updateQuickVerifyPills() {
  const container = document.getElementById("landing-quick-codes-list");
  if (!container) return;

  container.innerHTML = recentSampleCodes.map(code => `
    <button type="button" class="pill-code-btn" onclick="quickVerify('${code}')">${code}</button>
  `).join("");
}

async function executeVerification(code, cardElementId) {
  const card = document.getElementById(cardElementId);
  if (!code) {
    showToast("Please enter a credential code to verify.", "error");
    return;
  }

  card.style.display = "block";
  card.className = "verify-result-card";
  card.innerHTML = `<p style="color:var(--text-muted); font-size:0.9rem;">Verifying credential <strong>${escapeHtml(code)}</strong> with CertiFlow registry...</p>`;

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (data.is_valid) {
      card.className = "verify-result-card success-border";
      card.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
          <span style="background:var(--accent-emerald-subtle); color:var(--accent-emerald-text); padding:4px 10px; border-radius:999px; font-weight:700; font-size:0.8rem; border:1px solid var(--accent-emerald-border);">
            ✓ OFFICIAL CREDENTIAL VERIFIED
          </span>
          <span class="font-mono" style="color:var(--accent-cyan); font-weight:700;">${escapeHtml(data.certificate_code)}</span>
        </div>
        <h3 style="font-size:1.25rem; margin-bottom:4px; font-weight:700; color:var(--text-main);">${escapeHtml(data.recipient_name)}</h3>
        <p style="color:var(--accent-cyan); font-size:0.92rem; font-weight:600; margin-bottom:10px;">${escapeHtml(data.title)}</p>
        <div style="font-size:0.82rem; color:var(--text-dim); display:flex; gap:20px; border-top:1px solid var(--border-color); padding-top:10px;">
          <span>Issued By: <strong style="color:var(--text-main);">${escapeHtml(data.issuer_name)}</strong></span>
          <span>Date: <strong style="color:var(--text-main);">${escapeHtml(data.issue_date)}</strong></span>
        </div>
      `;
    } else {
      card.className = "verify-result-card failed-border";
      card.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
          <span style="background:var(--accent-rose-subtle); color:var(--accent-rose-text); padding:4px 10px; border-radius:999px; font-weight:700; font-size:0.8rem; border:1px solid var(--accent-rose-border);">
            ✕ UNVERIFIED OR REVOKED CREDENTIAL
          </span>
          <span class="font-mono" style="color:var(--accent-rose-text); font-weight:700;">${escapeHtml(code)}</span>
        </div>
        <p style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(data.message || "Credential not found in database.")}</p>
      `;
    }
  } catch (err) {
    card.className = "verify-result-card failed-border";
    card.innerHTML = `<p style="color:var(--accent-rose-text);">Verification network error: ${escapeHtml(err.message)}</p>`;
  }
}

// Anti-Scraping Rate Limit Burst Simulator
async function executeRateLimitBurstTest() {
  const feedback = document.getElementById("rate-limit-feedback");
  const btn = document.getElementById("btn-test-rate-limit");
  if (!feedback || !btn) return;

  btn.disabled = true;
  feedback.style.color = "var(--text-muted)";
  feedback.textContent = "Firing 65 rapid asynchronous requests to test sliding-window rate limiter...";

  let blockedCount = 0;
  let successCount = 0;
  const requests = [];

  for (let i = 0; i < 65; i++) {
    requests.push(
      fetch("/api/v1/certificates/verify/BURST-TEST-RATE-LIMIT")
        .then(res => {
          if (res.status === 429) {
            blockedCount++;
          } else {
            successCount++;
          }
        })
        .catch(() => {})
    );
  }

  await Promise.all(requests);
  btn.disabled = false;

  if (blockedCount > 0) {
    feedback.style.color = "var(--accent-emerald-text)";
    feedback.innerHTML = `🛡️ <strong>Defense Confirmed:</strong> Rate limiter intercepted burst! <strong>${blockedCount} requests throttled with HTTP 429 (Too Many Requests)</strong>.`;
    showToast(`Sliding window defense active! Throttled ${blockedCount} bot calls.`);
  } else {
    feedback.style.color = "var(--accent-cyan)";
    feedback.textContent = `Requests processed (${successCount}). Within safe rate limit threshold.`;
  }
}

/* ======================================================== */
/* 11. EMAIL DISPATCH & TOASTS                              */
/* ======================================================== */
async function triggerEmailDispatch(jobId) {
  showToast("Dispatching certificate emails...");
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}/dispatch-emails`, { method: "POST" });
    const data = await res.json();
    showToast(`Emails dispatched! Processed ${data.dispatched_count || 0} recipients.`);
  } catch (err) {
    showToast("Email dispatch error: " + err.message, "error");
  }
}

function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "toast-error" : type === "success" ? "toast-success" : ""}`;
  
  const icon = type === "error" ? "⚠️" : type === "success" ? "✓" : "⚡";
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(msg)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    toast.style.transition = "all 0.2s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

window.copyToClipboard = function(text) {
  navigator.clipboard.writeText(text);
  showToast(`Copied ${text} to clipboard`);
};

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
