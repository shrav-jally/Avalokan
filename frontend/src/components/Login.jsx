import React from 'react';

const Login = () => {
    const handleLogin = () => {
        window.location.href = 'http://localhost:5000/login';
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="gov-seal-large">
                    <span className="gov-text">G</span>
                </div>
                <h1>Avalokan</h1>
                <p className="login-subtitle">Government Sentiment Analytics Portal</p>
                <div className="login-divider"></div>
                <button className="login-btn-primary" onClick={handleLogin}>
                    Sign in with Organization Account
                </button>
                <p className="legal-text">
                    Authorized personnel only. Access is monitored and logged.
                </p>
            </div>
        </div>
    );
};

export default Login;
