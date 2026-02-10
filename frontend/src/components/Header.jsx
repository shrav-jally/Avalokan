import React from 'react';

const Header = () => {
    return (
        <header className="top-header">
            <div className="header-brand">
                <span className="gov-seal">G</span>
                <h1>Avalokan - Sentiment Analytics</h1>
            </div>
            <div className="admin-profile">
                <span className="profile-role">Senior Administrator</span>
                <div className="profile-avatar">AD</div>
            </div>
        </header>
    );
};

export default Header;
