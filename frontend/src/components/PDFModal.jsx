import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Download, ExternalLink, ShieldCheck } from 'lucide-react';

export default function PDFModal({ pdfUrl, onClose }) {
  if (!pdfUrl) return null;

  return (
    <AnimatePresence>
      <div className="modal-backdrop" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="glass-panel modal-card"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <div className="modal-title-group">
              <ShieldCheck size={20} className="text-cyan" />
              <span className="modal-title font-display">Vector PDF Credential Viewer</span>
              <span className="modal-spec-tag">ReportLab 300 DPI</span>
            </div>
            <div className="modal-actions">
              <a
                href={pdfUrl}
                download
                className="btn btn-secondary btn-sm"
                title="Download PDF"
              >
                <Download size={14} />
                <span>Save PDF</span>
              </a>
              <button onClick={onClose} className="icon-btn" title="Close Viewer">
                <X size={18} />
              </button>
            </div>
          </div>

          <div className="modal-iframe-container">
            <iframe
              src={pdfUrl}
              title="Certificate PDF Preview"
              className="pdf-iframe"
            />
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
