import React, { useState } from 'react';
import axios from 'axios';

const OnboardingForm = ({ onComplete }) => {
    const [stakeholder, setStakeholder] = useState('');
    const [loading, setLoading] = useState(false);
    
    const OPTIONS = [
        "Individual / Citizen",
        "Company / Corporate",
        "Legal Professional / CA",
        "NGO / Think Tank",
        "Academic / Researcher"
    ];

    const handleSubmit = async () => {
        if (!stakeholder) return;
        setLoading(true);
        try {
            await axios.post('http://localhost:5000/api/auth/onboard', { stakeholder_type: stakeholder });
            onComplete(stakeholder);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            <header className="top-header">
                <div className="header-brand">
                    <span className="gov-seal">G</span>
                    <h1>Avalokan Onboarding</h1>
                </div>
            </header>
            <div className="login-container">
                <div className="login-card">
                    <h2>Complete Your Profile</h2>
                    <p className="login-subtitle" style={{marginTop: '0.5rem'}}>Select Stakeholder Category</p>
                    <div className="login-divider"></div>
                    
                    <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                            Category *
                        </label>
                        <select 
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', outline: 'none' }}
                            value={stakeholder}
                            onChange={e => setStakeholder(e.target.value)}
                        >
                            <option value="" disabled>-- Select Option --</option>
                            {OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                        </select>
                    </div>
                    
                    <button 
                    className="login-btn-primary" 
                    onClick={handleSubmit} 
                    disabled={!stakeholder || loading}
                    style={{ opacity: (!stakeholder || loading) ? 0.7 : 1 }}
                    >
                        {loading ? 'Saving...' : 'Continue'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default OnboardingForm;
