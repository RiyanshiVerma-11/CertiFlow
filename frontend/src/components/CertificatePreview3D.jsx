import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'motion/react';
import { Sparkles, QrCode, Shield, Check, ZoomIn, RotateCcw } from 'lucide-react';

export default function CertificatePreview3D({
  title = "DGCA Certified Commercial Drone Pilot (Multi-Rotor & BVLOS)",
  recipientName = "Rajesh Menon",
  recipientEmail = "rajesh.menon@geospatial.aereo.in",
  recipientId = "AER-PILOT-102",
  issuerName = "AEREO Directorate of Flight Operations & Aerial Systems",
  issueDate = new Date().toISOString().split('T')[0],
  signatory = "Dr. Vipul Sharma",
  signatoryTitle = "Authorized Signatory",
}) {
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  // Motion physics for 3D tilt
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 20, stiffness: 200 };
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [8, -8]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-8, 8]), springConfig);

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
          <span>Real-Time 1:1 Vector Preview</span>
          <span className="live-tag">Exact PDF Replica</span>
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
          {/* Faithful 1:1 Replica of ReportLab Vector Canvas */}
          <div className="cert-canvas cert-canvas-executive">
            {/* Outer Navy Border (4.5px) */}
            <div className="cert-border-outer">
              {/* Inner Gold Border (1.5px) */}
              <div className="cert-border-inner">
                {/* 4 Corner Geometric Gold Brackets */}
                <div className="corner-bracket corner-tl" />
                <div className="corner-bracket corner-tr" />
                <div className="corner-bracket corner-bl" />
                <div className="corner-bracket corner-br" />

                {/* 1. Header Section */}
                <div className="cert-header">
                  <div className="cert-badge-strip font-mono">
                    OFFICIAL CREDENTIAL • VERIFIED RECORD
                  </div>
                  <h1 className="cert-main-title font-display">
                    CERTIFICATE OF ACHIEVEMENT
                  </h1>
                  <p className="cert-subtitle">
                    THIS CERTIFICATE IS PROUDLY PRESENTED TO
                  </p>
                </div>

                {/* 2. Recipient Section */}
                <div className="cert-recipient-block">
                  <div className="cert-recipient-name">
                    {recipientName || "Recipient Full Name"}
                  </div>
                  <div className="cert-recipient-underline" />
                  <p className="cert-conferral">
                    for successfully completing the curriculum and demonstrating proficiency in
                  </p>
                  <h2 className="cert-course-title">
                    {title || "Specialized Certification Course"}
                  </h2>
                </div>

                {/* Subtle Horizontal Divider */}
                <div className="cert-canvas-divider" />

                {/* 3. Bottom 3-Column Footer matching ReportLab */}
                <div className="cert-footer-replica">
                  {/* Left Column: QR Code */}
                  <div className="cert-qr-replica">
                    <div className="qr-box-frame">
                      <QrCode size={52} className="qr-canvas-svg" />
                    </div>
                    <span className="qr-scan-text">
                      Scan to Verify Authenticity
                    </span>
                  </div>

                  {/* Center Column: Credential Identifier */}
                  <div className="cert-center-meta">
                    <span className="meta-kicker">CREDENTIAL IDENTIFIER</span>
                    <span className="meta-code font-mono">
                      CERT-D8D4C57C {recipientId ? ` • ID: ${recipientId}` : ''}
                    </span>
                    <span className="meta-date">
                      Issued Date: {issueDate || "2026-10-11"}
                    </span>
                    <span className="meta-registry">
                      Digitally signed and archived in the CertiFlow registry
                    </span>
                  </div>

                  {/* Right Column: Signature & Safely Wrapped Issuer Name */}
                  <div className="cert-signature-replica">
                    <div className="sig-flourish font-signature">
                      {signatory || "Dr. Vipul Sharma"}
                    </div>
                    <div className="sig-rule-line" />
                    <div className="sig-issuer-wrapped font-bold">
                      {(() => {
                        const raw = (issuerName || "AEREO Directorate of Flight Operations & Aerial Systems").trim();
                        if (raw.includes(" & ")) {
                          const parts = raw.split(" & ");
                          return (
                            <>
                              <div className="sig-issuer-line">{parts[0].trim()}</div>
                              <div className="sig-issuer-line">&amp; {parts[1].trim()}</div>
                            </>
                          );
                        }
                        const words = raw.split(/\s+/);
                        if (words.length <= 3) return <div className="sig-issuer-line">{raw}</div>;
                        const mid = Math.ceil(words.length / 2);
                        return (
                          <>
                            <div className="sig-issuer-line">{words.slice(0, mid).join(" ")}</div>
                            <div className="sig-issuer-line">{words.slice(mid).join(" ")}</div>
                          </>
                        );
                      })()}
                    </div>
                    <span className="sig-title-text">
                      {signatoryTitle || "Authorized Signatory"}
                    </span>
                  </div>
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
                }% ${(mouseY.get() + 0.5) * 100}%, rgba(255,255,255,0.4) 0%, transparent 60%)`,
              }}
            />
          )}
        </motion.div>
      </div>

      <div className="preview-caption">
        <span>💡 1:1 Live Vector Preview matching the exact ReportLab PDF render specifications.</span>
      </div>
    </div>
  );
}
