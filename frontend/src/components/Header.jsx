import React from 'react';

const Header = ({ onLogout }) => {
    return (
        <header className="top-header">
            <div className="header-brand">
                <span className="gov-seal">G</span>
                <h1>Avalokan - Sentiment Analytics</h1>
            </div>
            <div className="admin-profile" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                    <span className="profile-role">Senior Administrator</span>
                    {onLogout && <button onClick={onLogout} style={{ fontSize: '0.8rem', background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer', padding: 0 }}>Logout</button>}
                </div>
                <div className="profile-avatar">AD</div>
            </div>
        </header>
    );
};

export default Header;
