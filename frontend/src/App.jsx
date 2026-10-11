import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import BatchStudio from './components/BatchStudio';
import JobTelemetry from './components/JobTelemetry';
import PublicVerifier from './components/PublicVerifier';
import BenchmarkSuite from './components/BenchmarkSuite';
import PDFModal from './components/PDFModal';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'studio' | 'telemetry' | 'verifier' | 'benchmark'
  const [activeJobId, setActiveJobId] = useState(null);
  const [isJobRunning, setIsJobRunning] = useState(false);
  const [verifyCode, setVerifyCode] = useState('');
  const [previewPdfUrl, setPreviewPdfUrl] = useState(null);

  // Triggered when a new job is dispatched from BatchStudio
  const handleJobCreated = (jobId) => {
    setActiveJobId(jobId);
    setIsJobRunning(true);
    setActiveTab('telemetry');
  };

  // Triggered from JobTelemetry when clicking 'Verify' on a certificate
  const handleSelectVerifyCode = (code) => {
    setVerifyCode(code);
    setActiveTab('verifier');
  };

  // Triggered when Benchmark dispatches a load test
  const handleBenchmarkJobCreated = (jobId) => {
    setActiveJobId(jobId);
  };

  return (
    <div className="app-root">
      {/* Dynamic Aurora Ambient Atmosphere */}
      <div className="app-atmosphere">
        <div className="aurora-glow-1" />
        <div className="aurora-glow-2" />
        <div className="ambient-grid" />
      </div>

      {/* Modern Floating Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeJobId={activeJobId}
        isJobRunning={isJobRunning}
      />

      {/* Main Dynamic Viewport */}
      <main className="app-main-content">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="tab-view-container"
            >
              <LandingPage onNavigateTab={(tab) => setActiveTab(tab)} />
            </motion.div>
          )}

          {activeTab === 'studio' && (
            <motion.div
              key="studio"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="tab-view-container"
            >
              <BatchStudio onJobCreated={handleJobCreated} />
            </motion.div>
          )}

          {activeTab === 'telemetry' && (
            <motion.div
              key="telemetry"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="tab-view-container"
            >
              <JobTelemetry
                jobId={activeJobId}
                onSelectVerifyCode={handleSelectVerifyCode}
                onPreviewPdf={(url) => setPreviewPdfUrl(url)}
              />
            </motion.div>
          )}

          {activeTab === 'verifier' && (
            <motion.div
              key="verifier"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="tab-view-container"
            >
              <PublicVerifier
                initialCode={verifyCode}
                onPreviewPdf={(url) => setPreviewPdfUrl(url)}
              />
            </motion.div>
          )}

          {activeTab === 'benchmark' && (
            <motion.div
              key="benchmark"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="tab-view-container"
            >
              <BenchmarkSuite onBenchmarkJobCreated={handleBenchmarkJobCreated} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* PDF Modal Viewer */}
      <PDFModal
        pdfUrl={previewPdfUrl}
        onClose={() => setPreviewPdfUrl(null)}
      />

      {/* Global Bottom Status Bar */}
      <footer className="app-footer">
        <div className="footer-container">
          <div className="footer-left">
            <span className="footer-tag">CertiFlow v3.2 Enterprise</span>
            <span className="footer-divider">•</span>
            <span>AEREO SDE Task Submission (Bangalore)</span>
          </div>
          <div className="footer-right">
            <span className="footer-badge badge-green">34/34 Pytest Tests Passing</span>
            <span className="footer-badge badge-blue">FastAPI 202 Async Worker</span>
            <span className="footer-badge badge-gold">ReportLab 300-DPI Vector</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
