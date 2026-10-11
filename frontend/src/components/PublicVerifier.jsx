import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Search, 
  CheckCircle, 
  Lock, 
  Download, 
  QrCode,
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function PublicVerifier({ initialCode = '', onPreviewPdf }) {
  const [code, setCode] = useState(initialCode);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [hasQueried, setHasQueried] = useState(false);

  // Automatically authenticate when initialCode is provided (from QR code scan or deep link)
  React.useEffect(() => {
    if (initialCode && initialCode.trim()) {
      const clean = initialCode.trim().toUpperCase();
      setCode(clean);
      handleVerify(clean);
    }
  }, [initialCode]);

  const handleVerify = async (targetCode = code) => {
    if (!targetCode || !targetCode.trim()) return;
    setIsVerifying(true);
    setHasQueried(true);
    try {
      const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(targetCode.trim())}`);
      const data = await res.json();
      setVerifyResult(data);
    } catch (err) {
      setVerifyResult({
        is_valid: false,
        message: 'Network verification timed out or server unreachable.',
      });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="verifier-layout">
      <div className="glass-panel verifier-hero-card">
        <div className="verifier-header-content">
          <div className="verifier-icon-badge">
            <Lock size={24} className="text-cyan" />
          </div>
          <h2>Public Cryptographic Credential Verifier</h2>
          <p>
            Verify the authenticity, tamper status, and issuance authority of any AEREO credential.
            Each certificate contains an immutable cryptographic signature and verification code.
          </p>
        </div>

        {/* Search Bar */}
        <div className="verifier-search-bar">
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="verifier-input font-mono"
              placeholder="Enter Certificate Code (e.g. CERT-A8B9C1) or UUID"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleVerify()}
            />
          </div>
          <button
            onClick={() => handleVerify()}
            disabled={isVerifying || !code.trim()}
            className="btn btn-primary"
          >
            {isVerifying ? 'Authenticating...' : 'Verify Authenticity'}
            <ArrowRight size={16} />
          </button>
        </div>

        {/* Quick Sample Code for Instant Recruiter Evaluation */}
        <div className="verifier-quick-sample">
          <span className="sample-label">⚡ Recruiter Quick Test:</span>
          <button
            type="button"
            className="sample-code-pill font-mono"
            onClick={() => {
              setCode('CERT-AEREO-DEMO-001');
              handleVerify('CERT-AEREO-DEMO-001');
            }}
          >
            CERT-AEREO-DEMO-001
          </button>
        </div>
      </div>

      {/* Verification Result Card */}
      {hasQueried && verifyResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="verifier-result-wrapper"
        >
          {verifyResult.is_valid ? (
            <div className="glass-panel verification-success-card">
              <div className="result-status-header">
                <div className="verified-shield-icon">
                  <ShieldCheck size={36} className="text-emerald" />
                  <div className="shield-glow" />
                </div>
                <div>
                  <div className="status-tag tag-verified">
                    <CheckCircle size={14} />
                    <span>CRYPTOGRAPHICALLY AUTHENTICATED</span>
                  </div>
                  <h3>Verified Genuine Credential</h3>
                </div>
              </div>

              <div className="result-details-grid">
                <div className="result-field">
                  <span className="field-label">CREDENTIAL HOLDER</span>
                  <span className="field-value font-display text-white">
                    {verifyResult.recipient_name}
                  </span>
                </div>
                <div className="result-field">
                  <span className="field-label">CERTIFICATION TITLE</span>
                  <span className="field-value">{verifyResult.title}</span>
                </div>
                <div className="result-field">
                  <span className="field-label">ISSUING ENTITY</span>
                  <span className="field-value">{verifyResult.issuer_name || 'AEREO Academy'}</span>
                </div>
                <div className="result-field">
                  <span className="field-label">OFFICIAL ISSUE DATE</span>
                  <span className="field-value font-mono">{verifyResult.issue_date}</span>
                </div>
                <div className="result-field">
                  <span className="field-label">UNIQUE CODE</span>
                  <span className="field-value font-mono text-cyan">
                    {verifyResult.certificate_code}
                  </span>
                </div>
                <div className="result-field">
                  <span className="field-label">AUTHENTICITY SPEC</span>
                  <span className="field-value font-mono text-muted">
                    SHA-256 Vector QR Embed
                  </span>
                </div>
              </div>

              {verifyResult.download_url && (
                <div className="result-action-strip">
                  <button
                    onClick={() => onPreviewPdf(verifyResult.download_url)}
                    className="btn btn-emerald"
                  >
                    <Download size={16} />
                    <span>Inspect Authentic Vector PDF</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel verification-failed-card">
              <div className="result-status-header">
                <ShieldAlert size={36} className="text-rose" />
                <div>
                  <div className="status-tag tag-failed">
                    <span>INVALID OR UNISSUED CREDENTIAL</span>
                  </div>
                  <h3>Verification Unsuccessful</h3>
                  <p className="text-muted">
                    {verifyResult.message || 'No credential was found matching this code.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
