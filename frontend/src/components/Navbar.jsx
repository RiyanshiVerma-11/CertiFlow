import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Award, 
  Activity, 
  ShieldCheck, 
  Gauge, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle,
  Home 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, activeJobId, isJobRunning }) {
  const [backendHealth, setBackendHealth] = useState({ status: 'checking', service: '' });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          setBackendHealth({ status: 'healthy', service: data.service });
        } else {
          setBackendHealth({ status: 'unhealthy' });
        }
      } catch (err) {
        setBackendHealth({ status: 'offline' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'studio', label: 'Batch Studio', icon: Award },
    { 
      id: 'telemetry', 
      label: 'Live Telemetry', 
      icon: Activity,
      badge: isJobRunning ? 'Processing' : activeJobId ? 'Ready' : null 
    },
    { id: 'verifier', label: 'Public Verifier', icon: ShieldCheck },
    { id: 'benchmark', label: 'Systems Benchmark', icon: Gauge, tag: 'AEREO Test' },
  ];

  return (
    <header className="navbar-wrapper">
      <div className="nav-container">
        {/* Brand */}
        <div className="nav-brand" onClick={() => setActiveTab('overview')}>
          <div className="brand-icon-wrapper">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Award className="brand-icon" size={24} />
            </motion.div>
            <div className="brand-glow" />
          </div>
          <div className="brand-info">
            <div className="brand-title">
              CertiFlow
              <span className="brand-badge">AEREO SDE</span>
            </div>
            <span className="brand-subtitle">Asynchronous Synthesis Engine</span>
          </div>
        </div>

        {/* Tab Navigation with Spring Layout Animation */}
        <nav className="nav-tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTabHighlight"
                    className="nav-tab-pill-highlight"
                    transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                  />
                )}
                <span className="tab-btn-content">
                  <Icon size={16} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className={`tab-badge ${isJobRunning ? 'pulse' : ''}`}>
                      {tab.badge}
                    </span>
                  )}
                  {tab.tag && <span className="tab-tag">{tab.tag}</span>}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Action strip & Health */}
        <div className="nav-actions">
          <div className="health-indicator" title={`FastAPI Backend: ${backendHealth.status}`}>
            <span
              className={`health-dot ${
                backendHealth.status === 'healthy' ? 'healthy' : 'offline'
              }`}
            />
            <span className="health-label">
              {backendHealth.status === 'healthy' ? 'FastAPI 202 Live' : 'Backend Offline'}
            </span>
          </div>

          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary btn-sm nav-doc-link"
          >
            <span>Swagger</span>
            <ExternalLink size={13} />
          </a>
        </div>
      </div>
    </header>
  );
}
