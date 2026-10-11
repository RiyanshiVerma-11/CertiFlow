import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'motion/react';
import { Sparkles, QrCode, Shield, Check, ZoomIn, RotateCcw } from 'lucide-react';

export default function CertificatePreview3D({
  title = "Commercial Drone Pilot Certification",
  recipientName = "Capt. Sarah Jenkins",
  recipientEmail = "sarah.jenkins@aereo.ai",
  recipientId = "AER-UAV-8842",
  issuerName = "AEREO Academy of Geospatial Technology",
  issueDate = new Date().toISOString().split('T')[0],
  signatory = "Dr. Vipul Sharma",
  signatoryTitle = "Director of Aerial Standards",
}) {
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  // Motion physics for 3D tilt
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 20, stiffness: 200 };
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [10, -10]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-10, 10]), springConfig);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    mouseX.set(0);
    mouseY.set(0);
  };

  const resetTilt = () => {
    mouseX.set(0);
    mouseY.set(0);
    setZoomLevel(1);
  };

  return (
    <div className="preview-container">
      <div className="preview-header">
        <div className="preview-title-bar">
          <Sparkles size={16} className="text-cyan" />
          <span>Real-Time Vector Preview</span>
          <span className="live-tag">Live Dynamic Binding</span>
        </div>
        <div className="preview-controls">
          <button
            onClick={() => setZoomLevel((z) => (z === 1 ? 1.08 : 1))}
            className="icon-btn"
            title="Toggle Inspection Zoom"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={resetTilt}
            className="icon-btn"
            title="Reset Perspective"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      <div
        className="perspective-stage"
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
      >
        <motion.div
          ref={cardRef}
          className="certificate-3d-card"
          style={{
            rotateX: rotateX,
            rotateY: rotateY,
            scale: zoomLevel,
            transformStyle: 'preserve-3d',
          }}
          transition={{ type: 'spring', damping: 15 }}
        >
          {/* Photorealistic Dynamic Certificate Canvas */}
          <div className="cert-canvas">
            {/* Holographic Border Pattern */}
            <div className="cert-border-outer">
              <div className="cert-border-inner">
                {/* Subtle Geometric Background Watermark */}
                <div className="cert-watermark">
                  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="0.5" strokeDasharray="2 2" />
                    <polygon points="50,15 80,75 20,75" stroke="currentColor" strokeWidth="0.5" />
                    <circle cx="50" cy="50" r="28" stroke="currentColor" strokeWidth="0.8" />
                  </svg>
                </div>

                {/* Header Section */}
                <div className="cert-header">
                  <div className="cert-badge-strip">
                    <Shield size={16} className="cert-icon" />
                    <span>AUTHENTICATED CREDENTIAL • AEREO AUTONOMY PROTOCOL</span>
                  </div>
                  <h1 className="cert-main-title">
                    CERTIFICATE OF ACHIEVEMENT
                  </h1>
                  <p className="cert-subtitle">THIS DOCUMENT OFFICIALLY ACCREDITS THAT</p>
                </div>

                {/* Recipient Section */}
                <div className="cert-recipient-block">
                  <div className="cert-recipient-name">
                    {recipientName || "Recipient Full Name"}
                  </div>
                  <div className="cert-recipient-underline" />
                  <p className="cert-conferral">
                    Has successfully satisfied all rigorous operational criteria and examinations for:
                  </p>
                  <h2 className="cert-course-title">
                    {title || "Specialized Certification Course"}
                  </h2>
                </div>

                {/* Credentials & Details Strip */}
                <div className="cert-meta-strip">
                  <div className="cert-meta-col">
                    <span className="cert-meta-label">RECIPIENT ID</span>
                    <span className="cert-meta-value font-mono">
                      {recipientId || "AER-USR-001"}
                    </span>
                  </div>
                  <div className="cert-meta-col">
                    <span className="cert-meta-label">DATE OF ISSUANCE</span>
                    <span className="cert-meta-value font-mono">
                      {issueDate || "2026-10-11"}
                    </span>
                  </div>
                  <div className="cert-meta-col">
                    <span className="cert-meta-label">VERIFICATION HASH</span>
                    <span className="cert-meta-value font-mono">
                      SHA256:7a4c9b...
                    </span>
                  </div>
                </div>

                {/* Signatures & Seal Footer */}
                <div className="cert-footer">
                  <div className="cert-sig-block">
                    <div className="cert-sig-script font-signature">
                      {signatory || "Dr. Vipul Sharma"}
                    </div>
                    <div className="cert-sig-line" />
                    <span className="cert-sig-name">{signatory}</span>
                    <span className="cert-sig-role">{signatoryTitle}</span>
                  </div>

                  {/* Gold Foil Holographic Seal */}
                  <div className="cert-gold-seal">
                    <div className="seal-outer-ring">
                      <div className="seal-inner-star">
                        <Sparkles size={20} className="seal-sparkle" />
                      </div>
                    </div>
                    <div className="seal-ribbon ribbon-left" />
                    <div className="seal-ribbon ribbon-right" />
                  </div>

                  {/* Cryptographic QR Seal */}
                  <div className="cert-qr-block">
                    <div className="cert-qr-frame">
                      <QrCode size={48} className="qr-svg" />
                    </div>
                    <span className="cert-qr-label font-mono">
                      SCAN TO VERIFY
                    </span>
                  </div>
                </div>

                <div className="cert-legal-footer">
                  <span>Issued under the auspices of {issuerName} • 300-DPI Vector Specification</span>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Light Reflection Shine on Hover */}
          {isHovered && (
            <motion.div
              className="card-shine-glare"
              style={{
                background: `radial-gradient(circle at ${
                  (mouseX.get() + 0.5) * 100
                }% ${(mouseY.get() + 0.5) * 100}%, rgba(255,255,255,0.18) 0%, transparent 60%)`,
              }}
            />
          )}
        </motion.div>
      </div>

      <div className="preview-caption">
        <span>💡 Move cursor over certificate for 3D vector inspection. Rendered via ReportLab vector backend.</span>
      </div>
    </div>
  );
}
