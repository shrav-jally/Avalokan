import React from 'react';

const LandingPage = () => {
    const handleLogin = () => {
        window.location.href = 'http://localhost:5000/login';
    };

    return (
        <div className="app-container">
            <header className="top-header">
                <div className="header-brand">
                    <span className="gov-seal">G</span>
                    <h1>Avalokan - Sentiment Analytics</h1>
                </div>
            </header>
            
            <div className="login-container" style={{ flex: 1, flexDirection: 'column', gap: '2rem' }}>
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                    <div className="gov-seal-large">
                        <span className="gov-text">G</span>
                    </div>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Avalokan Unified Portal</h1>
                    <p className="login-subtitle">AI-driven public policy consultation and sentiment analytics</p>
                </div>
                
                <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <div className="login-card" style={{ maxWidth: '350px' }}>
                        <h2>Public Participation</h2>
                        <div className="login-divider" style={{ margin: '1rem 0' }}></div>
                        <p className="login-subtitle" style={{marginBottom: '2rem'}}>
                            Review active policies, share your feedback, and track how public sentiment shapes decisions.
                        </p>
                        <button className="login-btn-primary" onClick={handleLogin}>
                            Public Login
                        </button>
                    </div>

                    <div className="login-card" style={{ maxWidth: '350px' }}>
                        <h2>Admin Portal</h2>
                        <div className="login-divider" style={{ margin: '1rem 0' }}></div>
                        <p className="login-subtitle" style={{marginBottom: '2rem'}}>
                            Secure access for Ministry Administrators to analyze sentiment trends and toxicity.
                        </p>
                        <button className="login-btn-primary" onClick={handleLogin}>
                            Admin Dashboard Login
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LandingPage;
