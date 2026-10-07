// CertiFlow Interactive Client Controller

const DEMO_RECIPIENTS = [
  {
    "name": "Riyanshi Sharma",
    "email": "riyanshi@aereo-academy.in",
    "custom_note": "Rank 1 • Distinguished Flight Lead"
  },
  {
    "name": "Alex Mercer",
    "email": "alex.mercer@enterprise.org",
    "custom_note": "Geospatial Analytics Honors"
  },
  {
    "name": "David Chen",
    "email": "david.chen@drone-tech.io",
    "custom_note": "LiDAR Processing Specialist"
  },
  {
    "name": "Faulty Recipient (Simulated Error)",
    "email": "test.__fail__@invalid-domain.com",
    "custom_note": "Intentionally triggered fault to prove error isolation"
  },
  {
    "name": "Sarah Jenkins",
    "email": "sarah.jenkins@spatial-ai.com",
    "custom_note": "Photogrammetry Survey Engineer"
  }
];

let pollingInterval = null;
let currentJobId = null;
let pollStartTime = null;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initViewRouting();
  initTabs();
  initDemoData();
  initDropzone();
  initEventListeners();
});

// Theme Management (Light / Dark Toggle)
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
      showNotification(`Switched to ${nextTheme.charAt(0).toUpperCase() + nextTheme.slice(1)} Mode`);
    });
  }
}

// View Navigation & Router (Landing Page vs Dedicated App Workspace)
function initViewRouting() {
  const landingView = document.getElementById("view-landing");
  const appView = document.getElementById("view-app");
  const navLaunchBtn = document.getElementById("nav-launch-btn");

  window.switchView = function(viewName) {
    if (viewName === "app") {
      landingView.className = "view-hidden";
      appView.className = "view-active";
      if (navLaunchBtn) navLaunchBtn.style.display = "none";
      window.scrollTo({ top: 0, behavior: "smooth" });
      history.pushState(null, "", "#app");
    } else {
      appView.className = "view-hidden";
      landingView.className = "view-active";
      if (navLaunchBtn) navLaunchBtn.style.display = "inline-flex";
      window.scrollTo({ top: 0, behavior: "smooth" });
      history.pushState(null, "", "#home");
    }
  };

  // Launch buttons
  document.getElementById("btn-hero-launch")?.addEventListener("click", () => switchView("app"));
  document.getElementById("nav-launch-btn")?.addEventListener("click", () => switchView("app"));
  document.getElementById("btn-cta-launch")?.addEventListener("click", () => switchView("app"));
  document.getElementById("footer-launch-btn")?.addEventListener("click", () => switchView("app"));

  // Back to landing buttons
  document.getElementById("btn-back-to-landing")?.addEventListener("click", () => switchView("landing"));
  document.getElementById("nav-brand")?.addEventListener("click", () => switchView("landing"));
  document.getElementById("nav-home-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("landing");
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

function initTabs() {
  const jsonBtn = document.getElementById("tab-json-btn");
  const csvBtn = document.getElementById("tab-csv-btn");
  const jsonTab = document.getElementById("tab-json");
  const csvTab = document.getElementById("tab-csv");

  jsonBtn.addEventListener("click", () => {
    jsonBtn.classList.add("active");
    csvBtn.classList.remove("active");
    jsonTab.style.display = "block";
    csvTab.style.display = "none";
  });

  csvBtn.addEventListener("click", () => {
    csvBtn.classList.add("active");
    jsonBtn.classList.remove("active");
    csvTab.style.display = "block";
    jsonTab.style.display = "none";
  });
}

function initDemoData() {
  const textarea = document.getElementById("recipients-json");
  textarea.value = JSON.stringify(DEMO_RECIPIENTS, null, 2);
  updateRecipientCountBadge(DEMO_RECIPIENTS.length);

  document.getElementById("btn-load-demo").addEventListener("click", () => {
    textarea.value = JSON.stringify(DEMO_RECIPIENTS, null, 2);
    updateRecipientCountBadge(DEMO_RECIPIENTS.length);
    showNotification("Demo batch loaded (5 recipients, including 1 fault test). Ready to dispatch!");
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
  document.getElementById("recipient-count-badge").textContent = `${count} recipients`;
}

function initDropzone() {
  const dropzone = document.getElementById("csv-dropzone");
  const fileInput = document.getElementById("csv-file-input");
  const dropText = document.getElementById("dropzone-text");

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
      <p><strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)</p>
      <span class="dropzone-note" style="color: var(--accent-cyan);">Ready to dispatch</span>
    `;
  }
}

function initEventListeners() {
  document.getElementById("btn-submit-job").addEventListener("click", handleJsonSubmit);
  document.getElementById("btn-submit-csv").addEventListener("click", handleCsvSubmit);
  document.getElementById("btn-refresh-status").addEventListener("click", () => {
    if (currentJobId) pollJobStatus(currentJobId);
  });

  // Landing page verification
  document.getElementById("btn-landing-verify")?.addEventListener("click", () => {
    const code = document.getElementById("landing-verify-code-input").value.trim();
    executeVerification(code, "landing-verify-result-card");
  });
  document.getElementById("landing-verify-code-input")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const code = document.getElementById("landing-verify-code-input").value.trim();
      executeVerification(code, "landing-verify-result-card");
    }
  });
}

async function handleJsonSubmit() {
  const title = document.getElementById("event-title").value.trim();
  const issuer = document.getElementById("issuer-name").value.trim();
  const date = document.getElementById("issue-date").value.trim();
  const rawJson = document.getElementById("recipients-json").value.trim();

  if (!title || !issuer || !date) {
    alert("Please fill in the title, issuer name, and issue date.");
    return;
  }

  let recipients = [];
  try {
    recipients = JSON.parse(rawJson);
    if (!Array.isArray(recipients) || recipients.length === 0) {
      throw new Error("Must be a non-empty array");
    }
  } catch (err) {
    alert("Invalid JSON format for recipients: " + err.message);
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
    startJobTracking(data.job_id);
  } catch (err) {
    alert("Submission error: " + err.message);
  } finally {
    setSubmitting(false);
  }
}

async function handleCsvSubmit() {
  const fileInput = document.getElementById("csv-file-input");
  if (!fileInput.files.length) {
    alert("Please select a CSV file first.");
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
    startJobTracking(data.job_id);
  } catch (err) {
    alert("CSV error: " + err.message);
  } finally {
    setSubmitting(false);
  }
}

function setSubmitting(isSubmitting) {
  const spinner = document.getElementById("submit-spinner");
  const btn = document.getElementById("btn-submit-job");
  if (isSubmitting) {
    btn.disabled = true;
    spinner.style.display = "inline-block";
  } else {
    btn.disabled = false;
    spinner.style.display = "none";
  }
}

function startJobTracking(jobId) {
  currentJobId = jobId;
  pollStartTime = Date.now();
  if (pollingInterval) clearInterval(pollingInterval);

  document.getElementById("active-job-id").textContent = jobId;
  document.getElementById("telemetry-actions").style.display = "none";
  document.getElementById("fault-drawer").style.display = "none";
  document.getElementById("gallery-section").style.display = "none";

  // Initial poll
  pollJobStatus(jobId);
  pollingInterval = setInterval(() => pollJobStatus(jobId), 600);
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
  // Status pill
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

  // Elapsed time
  const elapsed = Math.round((Date.now() - pollStartTime) / 1000);
  document.getElementById("job-elapsed-time").textContent = `${elapsed}s`;

  // Progress Bar
  document.getElementById("progress-bar-fill").style.width = `${data.progress_percentage}%`;
  document.getElementById("progress-pct").textContent = `${data.progress_percentage}%`;
  document.getElementById("progress-counts").textContent = `${data.processed} / ${data.total} Processed`;

  // Metric numbers
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
            <strong class="fault-item-name">${f.recipient_name}</strong>
          </div>
          <span class="fault-item-badge">FAILED & ISOLATED</span>
        </div>
        <div class="fault-item-meta">
          <span class="fault-meta-label">Recipient Email:</span>
          <span class="fault-meta-email font-mono">${f.recipient_email}</span>
        </div>
        <div class="fault-item-reason">
          <span class="fault-reason-label">Exact Failure Reason:</span>
          <code class="fault-reason-code">${f.error}</code>
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

async function loadJobCertificates(jobId) {
  try {
    const res = await fetch(`/api/v1/jobs/${jobId}/certificates`);
    if (!res.ok) return;

    const certs = await res.json();
    const gallerySection = document.getElementById("gallery-section");
    const grid = document.getElementById("certs-grid");
    document.getElementById("gallery-count").textContent = certs.length;

    grid.innerHTML = certs.map(c => {
      const isSuccess = c.status === "SUCCESS";
      return `
        <div class="cert-card ${isSuccess ? 'cert-card-success' : 'cert-card-failed'}">
          <div>
            <div class="cert-card-badges">
              <span class="cert-code">${c.certificate_code}</span>
              ${!isSuccess ? `<span class="badge-failed">❌ FAILED</span>` : `<span class="badge-success">✓ ISSUED</span>`}
            </div>
            <div class="cert-recipient">${c.recipient_name}</div>
            <div class="cert-email font-mono">${c.recipient_email}</div>
            ${c.custom_note ? `<div class="cert-note">★ ${c.custom_note}</div>` : ''}
            ${!isSuccess ? `
              <div class="cert-failure-callout">
                <span class="failure-callout-title">Failure Reason:</span>
                <span class="failure-callout-msg">${c.error_message || 'Simulated fault boundary'}</span>
                <span class="failure-callout-note">Safely skipped to protect batch execution</span>
              </div>
            ` : ''}
          </div>
          <div class="cert-actions">
            ${isSuccess ? `
              <a href="${c.download_url}" target="_blank" class="cert-btn-dl">
                View PDF ↗
              </a>
              <button onclick="quickVerify('${c.certificate_code}')" class="cert-btn-verify">
                Verify
              </button>
            ` : `
              <span class="cert-failed-label">Excluded From ZIP Archive</span>
            `}
          </div>
        </div>
      `;
    }).join("");

    gallerySection.style.display = "block";
  } catch (e) {
    console.error("Failed to load certificates gallery", e);
  }
}

window.quickVerify = function(code) {
  switchView("landing");
  const input = document.getElementById("landing-verify-code-input");
  input.value = code;
  document.getElementById("verify").scrollIntoView({ behavior: "smooth" });
  executeVerification(code, "landing-verify-result-card");
};

async function executeVerification(code, cardElementId) {
  const card = document.getElementById(cardElementId);
  if (!code) {
    alert("Please enter a credential code to verify.");
    return;
  }

  card.style.display = "block";
  card.innerHTML = `<p style="color:var(--text-muted);">Verifying credential with CertiFlow registry...</p>`;

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (data.is_valid) {
      card.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
          <span style="background:rgba(16,185,129,0.2); color:#34d399; padding:4px 10px; border-radius:999px; font-weight:700; font-size:0.8rem; border:1px solid #059669;">
            ✓ OFFICIAL CREDENTIAL VERIFIED
          </span>
          <span class="font-mono" style="color:var(--accent-cyan); font-weight:600;">${data.certificate_code}</span>
        </div>
        <h3 style="font-size:1.2rem; margin-bottom:6px;">${data.recipient_name}</h3>
        <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:8px;">${data.title}</p>
        <div style="font-size:0.8rem; color:var(--text-dim); display:flex; gap:16px;">
          <span>Issued By: <strong>${data.issuer_name}</strong></span>
          <span>Date: <strong>${data.issue_date}</strong></span>
        </div>
      `;
    } else {
      card.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
          <span style="background:rgba(244,63,94,0.2); color:#fb7185; padding:4px 10px; border-radius:999px; font-weight:700; font-size:0.8rem; border:1px solid #e11d48;">
            ✕ INVALID OR REVOKED CREDENTIAL
          </span>
        </div>
        <p style="color:var(--text-muted); font-size:0.85rem;">${data.message}</p>
      `;
    }
  } catch (err) {
    card.innerHTML = `<p style="color:var(--accent-rose);">Verification network error: ${err.message}</p>`;
  }
}

function showNotification(msg) {
  const notif = document.createElement("div");
  notif.style.position = "fixed";
  notif.style.bottom = "24px";
  notif.style.right = "24px";
  notif.style.background = "#0b1329";
  notif.style.border = "1px solid var(--accent-cyan)";
  notif.style.color = "#fff";
  notif.style.padding = "12px 20px";
  notif.style.borderRadius = "8px";
  notif.style.boxShadow = "0 8px 24px rgba(0,0,0,0.5)";
  notif.style.zIndex = "999";
  notif.style.fontSize = "0.9rem";
  notif.textContent = msg;
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 4000);
}
