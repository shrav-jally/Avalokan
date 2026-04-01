import React, { useState } from 'react';
import Auth from './Auth';
import './LandingPage.css';

const LandingPage = () => {
    // null = landing, 'admin' = admin auth, 'consumer' = consumer auth
    const [authMode, setAuthMode] = useState(null);

    if (authMode) {
        return <Auth mode={authMode} onBack={() => setAuthMode(null)} />;
    }

    return (
        <div className="lp-root">
            {/* Header */}
            <header className="lp-header">
                <div className="lp-brand">
                    <div className="lp-brand-seal">A</div>
                    <span className="lp-brand-name">Avalokan</span>
                </div>
                <span className="lp-tagline">India's AI-Powered Policy Consultation Platform</span>
            </header>

            {/* Hero */}
            <main className="lp-main">
                <div className="lp-hero">
                    <div className="lp-hero-badge">Government of India · Unified Portal</div>
                    <h1 className="lp-hero-title">
                        Shaping Policy Through<br />
                        <span className="lp-hero-accent">Public Intelligence</span>
                    </h1>
                    <p className="lp-hero-subtitle">
                        Avalokan enables citizens to participate in active policy consultations
                        while providing government officials with real-time AI sentiment analytics.
                    </p>
                </div>

                {/* Role Cards */}
                <div className="lp-cards">
                    {/* Consumer Card */}
                    <button
                        className="lp-card lp-card--consumer"
                        onClick={() => setAuthMode('consumer')}
                        id="btn-public-consultation"
                    >
                        <div className="lp-card-icon lp-card-icon--consumer">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                                <circle cx="9" cy="7" r="4" />
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                            </svg>
                        </div>
                        <div className="lp-card-body">
                            <h2 className="lp-card-title">Public Consultation</h2>
                            <p className="lp-card-desc">
                                Review active policy drafts, share your feedback as a citizen,
                                company, or expert, and track how public sentiment shapes government decisions.
                            </p>
                            <div className="lp-card-pills">
                                <span className="lp-pill">Open to all citizens</span>
                                <span className="lp-pill">Free registration</span>
                            </div>
                        </div>
                        <div className="lp-card-arrow">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </div>
                    </button>

                    {/* Admin Card */}
                    <button
                        className="lp-card lp-card--admin"
                        onClick={() => setAuthMode('admin')}
                        id="btn-government-portal"
                    >
                        <div className="lp-card-icon lp-card-icon--admin">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                            </svg>
                        </div>
                        <div className="lp-card-body">
                            <h2 className="lp-card-title">Government Portal</h2>
                            <p className="lp-card-desc">
                                Secure access for Ministry Administrators to manage policy drafts,
                                analyse AI sentiment trends, toxicity heatmaps, and generate consultation reports.
                            </p>
                            <div className="lp-card-pills">
                                <span className="lp-pill lp-pill--secure">Restricted Access</span>
                                <span className="lp-pill lp-pill--secure">AI Analytics</span>
                            </div>
                        </div>
                        <div className="lp-card-arrow">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </div>
                    </button>
                </div>

                {/* Stats Strip */}
                <div className="lp-stats">
                    <div className="lp-stat">
                        <span className="lp-stat-num">142+</span>
                        <span className="lp-stat-label">Active Policy Drafts</span>
                    </div>
                    <div className="lp-stat-sep" />
                    <div className="lp-stat">
                        <span className="lp-stat-num">8,540</span>
                        <span className="lp-stat-label">Public Submissions</span>
                    </div>
                    <div className="lp-stat-sep" />
                    <div className="lp-stat">
                        <span className="lp-stat-num">24</span>
                        <span className="lp-stat-label">Open Consultations</span>
                    </div>
                    <div className="lp-stat-sep" />
                    <div className="lp-stat">
                        <span className="lp-stat-num">AI</span>
                        <span className="lp-stat-label">Sentiment Analysis</span>
                    </div>
                </div>
            </main>

            <footer className="lp-footer">
                <p>© 2026 Avalokan · Government of India · All rights reserved</p>
                <p>This portal is governed by the IT Act, 2000 and applicable data protection regulations.</p>
            </footer>
        </div>
    );
};

export default LandingPage;
