import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  UploadCloud, 
  Plus, 
  Trash2, 
  FileSpreadsheet, 
  Code, 
  Users, 
  Sparkles, 
  Send, 
  AlertTriangle,
  CheckCircle,
  FileText
} from 'lucide-react';
import confetti from 'canvas-confetti';
import CertificatePreview3D from './CertificatePreview3D';

// High-impact enterprise presets tailored for AEREO
const PRESETS = [
  {
    id: 'aereo_drones',
    title: '🚁 AEREO DGCA Drone Fleet Pilot Certification',
    badge: 'AEREO Flagship',
    courseTitle: 'DGCA Certified Commercial Drone Pilot (Multi-Rotor & BVLOS)',
    issuer: 'AEREO Directorate of Flight Operations & Aerial Systems',
    signatory: 'Dr. Vipul Sharma',
    signatoryTitle: 'Chief Flight Standards Examiner',
    recipients: [
      { name: 'Capt. Sarah Jenkins', email: 'sarah.jenkins@aereo.ai', recipient_id: 'AER-PILOT-101' },
      { name: 'Rajesh Menon', email: 'rajesh.menon@geospatial.aereo.in', recipient_id: 'AER-PILOT-102' },
      { name: 'Ananya Deshmukh', email: 'ananya.d@aerial-survey.com', recipient_id: 'AER-PILOT-103' },
      { name: 'Lt. Marcus Vance', email: 'marcus.vance@defense-flight.org', recipient_id: 'AER-PILOT-104' },
      { name: 'Priya Sundaram', email: 'priya.sundaram@aereo.ai', recipient_id: 'AER-PILOT-105' },
      { name: 'David K. O’Connor', email: 'david.oconnor@skydocs.io', recipient_id: 'AER-PILOT-106' },
    ],
  },
  {
    id: 'geospatial_lidar',
    title: '🛰️ Advanced LiDAR & Photogrammetry Specialist',
    badge: 'Geospatial',
    courseTitle: 'High-Resolution LiDAR Point Cloud Processing & Orthomosaic Synthesis',
    issuer: 'AEREO Center for Geospatial Intelligence',
    signatory: 'Prof. Neha Kulkarni',
    signatoryTitle: 'Head of Remote Sensing & AI',
    recipients: [
      { name: 'Vikramaditya Roy', email: 'vikram.roy@geolabs.net', recipient_id: 'GEO-LIDAR-201' },
      { name: 'Elena Rostova', email: 'elena.rostova@sat-intelligence.org', recipient_id: 'GEO-LIDAR-202' },
      { name: 'Karthik Balakrishnan', email: 'karthik.b@spatial-aereo.in', recipient_id: 'GEO-LIDAR-203' },
      { name: 'Amina Al-Mansoor', email: 'amina.m@remote-sensing.ae', recipient_id: 'GEO-LIDAR-204' },
    ],
  },
  {
    id: 'fault_isolation',
    title: '🛡️ Zero-Drop Fault Isolation Benchmark (Dirty Batch)',
    badge: 'Defense Test',
    courseTitle: 'Industrial Aerial Inspection & Structural Telemetry',
    issuer: 'AEREO Quality & Safety Commission',
    signatory: 'Vikram Malhotra',
    signatoryTitle: 'Lead Verification Architect',
    recipients: [
      { name: 'Arjun Verma', email: 'arjun.verma@valid-firm.com', recipient_id: 'ISO-001' },
      { name: '', email: 'missing-name@test.com', recipient_id: 'ISO-002' }, // Invalid: missing name
      { name: 'Sneha Patel', email: 'sneha.patel@aerotech.io', recipient_id: 'ISO-003' },
      { name: 'Corrupt Recipient', email: 'corrupt-email-without-at-sign', recipient_id: 'ISO-004' }, // Invalid: bad email
      { name: 'Kabir Singhania', email: 'kabir.s@valid-inspection.org', recipient_id: 'ISO-005' },
      { name: 'Broken Row User', email: '', recipient_id: 'ISO-006' }, // Invalid: empty email
      { name: 'Dr. Rohini Iyer', email: 'rohini.iyer@aereo.ai', recipient_id: 'ISO-007' },
    ],
  },
];

export default function BatchStudio({ onJobCreated }) {
  const [activePreset, setActivePreset] = useState(PRESETS[0]);
  const [title, setTitle] = useState(PRESETS[0].courseTitle);
  const [issuerName, setIssuerName] = useState(PRESETS[0].issuer);
  const [issueDate, setIssueDate] = useState(new Date().toISOString().split('T')[0]);
  const [signatory, setSignatory] = useState(PRESETS[0].signatory);
  const [signatoryTitle, setSignatoryTitle] = useState(PRESETS[0].signatoryTitle);

  const [inputMode, setInputMode] = useState('table'); // 'table' | 'csv' | 'json'
  const [recipients, setRecipients] = useState(PRESETS[0].recipients);
  const [csvFile, setCsvFile] = useState(null);
  const [csvPreviewRows, setCsvPreviewRows] = useState([]);
  const [jsonText, setJsonText] = useState('');
  const [selectedRecipientIndex, setSelectedRecipientIndex] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Apply a preset
  const handleSelectPreset = (preset) => {
    setActivePreset(preset);
    setTitle(preset.courseTitle);
    setIssuerName(preset.issuer);
    setSignatory(preset.signatory);
    setSignatoryTitle(preset.signatoryTitle);
    setRecipients(preset.recipients);
    setSelectedRecipientIndex(0);
    setSubmitError(null);
  };

  // Recipient manipulation
  const handleAddRecipient = () => {
    const newRecipient = {
      name: '',
      email: '',
      recipient_id: `REC-${Date.now().toString().slice(-4)}`,
    };
    setRecipients([...recipients, newRecipient]);
    setSelectedRecipientIndex(recipients.length);
  };

  const handleUpdateRecipient = (index, field, value) => {
    const updated = [...recipients];
    updated[index][field] = value;
    setRecipients(updated);
  };

  const handleRemoveRecipient = (index) => {
    if (recipients.length <= 1) return;
    const updated = recipients.filter((_, i) => i !== index);
    setRecipients(updated);
    if (selectedRecipientIndex >= updated.length) {
      setSelectedRecipientIndex(updated.length - 1);
    }
  };

  // Handle CSV Selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setCsvFile(file);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const lines = text.split('\n').filter((l) => l.trim().length > 0);
      const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
      const preview = lines.slice(1, 6).map((line) => {
        const parts = line.split(',').map((p) => p.trim());
        return {
          name: parts[headers.indexOf('name')] || parts[0] || '',
          email: parts[headers.indexOf('email')] || parts[1] || '',
        };
      });
      setCsvPreviewRows(preview);
    };
    reader.readAsText(file);
  };

  // Submit Job to FastAPI Backend
  const handleSubmitBatch = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      let res;
      let data;

      if (inputMode === 'csv') {
        if (!csvFile) {
          throw new Error('Please select a valid CSV file to upload.');
        }
        const formData = new FormData();
        formData.append('file', csvFile);
        formData.append('title', title);
        formData.append('issuer_name', issuerName);
        formData.append('issue_date', issueDate);

        res = await fetch('/api/v1/jobs/upload-csv', {
          method: 'POST',
          body: formData,
        });
      } else {
        // Table or JSON Mode
        let payloadRecipients = recipients;
        if (inputMode === 'json') {
          try {
            payloadRecipients = JSON.parse(jsonText);
          } catch (err) {
            throw new Error('Invalid JSON format. Please verify the recipients array structure.');
          }
        }

        const payload = {
          title,
          issuer_name: issuerName,
          issue_date: issueDate,
          recipients: payloadRecipients,
        };

        res = await fetch('/api/v1/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to dispatch generation job.');
      }

      // 202 Accepted Confetti Celebration
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#00F2FE', '#38BDF8', '#10B981', '#FBBF24'],
      });

      // Switch to Telemetry tab with new Job ID
      if (onJobCreated) {
        onJobCreated(data.job_id);
      }
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const previewRecipient = recipients[selectedRecipientIndex] || {
    name: 'Capt. Sarah Jenkins',
    email: 'sarah.jenkins@aereo.ai',
    recipient_id: 'AER-PILOT-101',
  };

  return (
    <div className="studio-layout">
      {/* Left Column: Form & Cohort Config */}
      <div className="studio-config-column">
        {/* Preset Strip */}
        <div className="glass-panel preset-panel">
          <div className="preset-header">
            <Sparkles size={16} className="text-cyan" />
            <span className="preset-title">Select AEREO Industry Scenario Preset:</span>
          </div>
          <div className="preset-grid">
            {PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => handleSelectPreset(p)}
                className={`preset-card ${activePreset.id === p.id ? 'active' : ''}`}
              >
                <div className="preset-card-top">
                  <span className="preset-badge">{p.badge}</span>
                  <span className="preset-count">{p.recipients.length} Cohort</span>
                </div>
                <div className="preset-name">{p.title}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Global Metadata Card */}
        <div className="glass-panel studio-card">
          <h3 className="card-section-title">
            <FileText size={18} className="text-cyan" />
            Credential Schema & Metadata
          </h3>
          <div className="form-grid-2">
            <div className="form-group">
              <label className="input-label">Certificate Title / Event</label>
              <input
                type="text"
                className="input-field"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. DGCA Commercial Drone Pilot"
              />
            </div>
            <div className="form-group">
              <label className="input-label">Issuing Body / Organization</label>
              <input
                type="text"
                className="input-field"
                value={issuerName}
                onChange={(e) => setIssuerName(e.target.value)}
                placeholder="e.g. AEREO Academy"
              />
            </div>
            <div className="form-group">
              <label className="input-label">Date of Issuance</label>
              <input
                type="date"
                className="input-field font-mono"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="input-label">Authorized Signatory</label>
              <input
                type="text"
                className="input-field"
                value={signatory}
                onChange={(e) => setSignatory(e.target.value)}
                placeholder="e.g. Dr. Vipul Sharma"
              />
            </div>
          </div>
        </div>

        {/* Recipient Ingestion Modes */}
        <div className="glass-panel studio-card">
          <div className="card-header-tabs">
            <h3 className="card-section-title">
              <Users size={18} className="text-cyan" />
              Recipient Ingestion ({recipients.length} Candidates)
            </h3>
            <div className="mode-toggle-group">
              <button
                onClick={() => setInputMode('table')}
                className={`mode-btn ${inputMode === 'table' ? 'active' : ''}`}
              >
                <Users size={14} />
                <span>Visual Grid</span>
              </button>
              <button
                onClick={() => setInputMode('csv')}
                className={`mode-btn ${inputMode === 'csv' ? 'active' : ''}`}
              >
                <FileSpreadsheet size={14} />
                <span>CSV Upload</span>
              </button>
              <button
                onClick={() => {
                  setInputMode('json');
                  setJsonText(JSON.stringify(recipients, null, 2));
                }}
                className={`mode-btn ${inputMode === 'json' ? 'active' : ''}`}
              >
                <Code size={14} />
                <span>JSON</span>
              </button>
            </div>
          </div>

          {/* Mode 1: Visual Cohort Table */}
          {inputMode === 'table' && (
            <div className="table-mode-container">
              <div className="recipients-table-wrapper">
                <table className="recipients-table">
                  <thead>
                    <tr>
                      <th style={{ width: '40px' }}>#</th>
                      <th>Candidate Full Name</th>
                      <th>Email Address</th>
                      <th>ID Code</th>
                      <th style={{ width: '50px' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recipients.map((rec, index) => {
                      const isSelected = selectedRecipientIndex === index;
                      const isEmailValid = rec.email && rec.email.includes('@');
                      return (
                        <tr
                          key={index}
                          onClick={() => setSelectedRecipientIndex(index)}
                          className={isSelected ? 'row-selected' : ''}
                        >
                          <td className="row-num font-mono">{index + 1}</td>
                          <td>
                            <input
                              type="text"
                              value={rec.name}
                              onChange={(e) =>
                                handleUpdateRecipient(index, 'name', e.target.value)
                              }
                              placeholder="Full Name"
                              className="table-input"
                            />
                          </td>
                          <td>
                            <div className="table-email-cell">
                              <input
                                type="text"
                                value={rec.email}
                                onChange={(e) =>
                                  handleUpdateRecipient(index, 'email', e.target.value)
                                }
                                placeholder="name@domain.com"
                                className="table-input"
                              />
                              {rec.email && (
                                <span
                                  className={`validation-dot ${
                                    isEmailValid ? 'dot-valid' : 'dot-invalid'
                                  }`}
                                  title={
                                    isEmailValid
                                      ? 'Valid Email'
                                      : 'Will trigger fault isolation'
                                  }
                                />
                              )}
                            </div>
                          </td>
                          <td>
                            <input
                              type="text"
                              value={rec.recipient_id || ''}
                              onChange={(e) =>
                                handleUpdateRecipient(index, 'recipient_id', e.target.value)
                              }
                              placeholder="Optional ID"
                              className="table-input font-mono"
                            />
                          </td>
                          <td className="text-center">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemoveRecipient(index);
                              }}
                              className="icon-btn-danger"
                              title="Delete Recipient"
                            >
                              <Trash2 size={13} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="table-footer-actions">
                <button onClick={handleAddRecipient} className="btn btn-secondary btn-sm">
                  <Plus size={14} />
                  <span>Add Candidate</span>
                </button>
                <span className="caption-text">
                  Click any row to bind its values live to the 3D Certificate Preview.
                </span>
              </div>
            </div>
          )}

          {/* Mode 2: CSV Upload */}
          {inputMode === 'csv' && (
            <div className="csv-mode-container">
              <label className="csv-dropzone">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <div className="dropzone-content">
                  <UploadCloud size={36} className="text-cyan dropzone-icon" />
                  <span className="dropzone-main-text">
                    {csvFile ? csvFile.name : 'Click or drop .CSV recipient cohort file here'}
                  </span>
                  <span className="dropzone-sub-text">
                    Expects headers: <code>name</code>, <code>email</code>, optional <code>recipient_id</code>
                  </span>
                </div>
              </label>

              {csvPreviewRows.length > 0 && (
                <div className="csv-preview-block">
                  <span className="csv-preview-title">Detected CSV Sample:</span>
                  <div className="csv-pills">
                    {csvPreviewRows.map((row, i) => (
                      <div key={i} className="csv-pill">
                        <strong>{row.name || 'Anonymous'}</strong> ({row.email})
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Mode 3: Raw JSON */}
          {inputMode === 'json' && (
            <div className="json-mode-container">
              <textarea
                className="json-textarea font-mono"
                rows={10}
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                placeholder="[ { 'name': 'John Doe', 'email': 'john@example.com' } ]"
              />
            </div>
          )}
        </div>

        {/* Submit Action Box */}
        {submitError && (
          <div className="error-alert">
            <AlertTriangle size={18} />
            <span>{submitError}</span>
          </div>
        )}

        <div className="dispatch-action-bar">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSubmitBatch}
            disabled={isSubmitting}
            className="btn btn-primary btn-lg dispatch-btn"
          >
            {isSubmitting ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                  <Send size={18} />
                </motion.div>
                <span>Dispatching Asynchronous Job (202 Accepted)...</span>
              </>
            ) : (
              <>
                <Send size={18} />
                <span>
                  Synthesize Bulk Credentials ({inputMode === 'csv' ? (csvFile ? csvFile.name : 'CSV') : `${recipients.length} Cohort`}) →
                </span>
              </>
            )}
          </motion.button>
          <div className="dispatch-telemetry-note">
            <span>⚡ Returns immediate <code>202 Accepted</code> with non-blocking FastAPI worker execution.</span>
          </div>
        </div>
      </div>

      {/* Right Column: Interactive 3D Vector Preview */}
      <div className="studio-preview-column">
        <div className="preview-sticky-wrapper">
          <CertificatePreview3D
            title={title}
            recipientName={previewRecipient.name}
            recipientEmail={previewRecipient.email}
            recipientId={previewRecipient.recipient_id}
            issuerName={issuerName}
            issueDate={issueDate}
            signatory={signatory}
            signatoryTitle={signatoryTitle}
          />
        </div>
      </div>
    </div>
  );
}
