import React, { useState } from 'react';
import axios from 'axios';
import './LandingPage.css';

axios.defaults.withCredentials = true;

const STAKEHOLDER_OPTIONS = [
    { value: '', label: 'Select stakeholder type...' },
    { value: 'Citizen / NGO', label: 'Citizen / NGO' },
    { value: 'Company / Industry', label: 'Company / Industry' },
    { value: 'CA / Legal Expert', label: 'CA / Legal Expert' },
];

const GoogleIcon = () => (
    <svg width="18" height="18" viewBox="0 0 48 48">
        <path fill="#EA4335" d="M24 9.5c3.5 0 6.5 1.2 8.9 3.5l6.7-6.7C35.1 2.7 29.9 0 24 0 14.7 0 6.7 5.6 2.9 13.6l7.8 6.1C12.7 13.1 17.9 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.9 7.2l7.6 5.9c4.5-4.1 7.1-10.2 7.1-17.1z"/>
        <path fill="#FBBC05" d="M10.7 28.3c-.7-2-1-4.1-1-6.3s.4-4.3 1-6.3l-7.8-6.1C1 13 0 17.4 0 22s1 9 2.9 13.1l7.8-5.8z"/>
        <path fill="#34A853" d="M24 44c5.9 0 10.9-2 14.5-5.3l-7.6-5.9c-2 1.3-4.5 2.1-6.9 2.1-6.1 0-11.3-4-13.2-9.5l-7.8 5.9C6.7 38.5 14.7 44 24 44z"/>
    </svg>
);

// ─── Admin Login Form ───────────────────────────────────────────
const AdminLoginForm = ({ onAuthSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLocalLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await axios.post('http://localhost:5000/api/auth/login', { email, password, role: 'admin' });
            if (res.data.status === 'success') {
                onAuthSuccess();
            } else {
                setError(res.data.error || 'Login failed. Please check your credentials.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        window.location.href = 'http://localhost:5000/auth/google/admin';
    };

    return (
        <form className="auth-form" onSubmit={handleLocalLogin}>
            {error && <div className="auth-error">{error}</div>}
            <div className="auth-field">
                <label className="auth-label">Ministry Email</label>
                <input
                    id="admin-email"
                    className="auth-input"
                    type="email"
                    placeholder="admin@ministry.gov.in"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                />
            </div>
            <div className="auth-field">
                <label className="auth-label">Password</label>
                <input
                    id="admin-password"
                    className="auth-input"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />
            </div>
            <button
                id="admin-login-submit"
                className="auth-btn-primary auth-btn-primary--admin"
                type="submit"
                disabled={loading}
            >
                {loading ? 'Verifying Access...' : 'Sign In to Dashboard'}
            </button>
            <div className="auth-divider">or</div>
            <button
                id="admin-google-login"
                className="auth-btn-google"
                type="button"
                onClick={handleGoogleLogin}
            >
                <GoogleIcon />
                Continue with Google (Admin Verification)
            </button>
            <p className="auth-legal">
                Access is restricted to authorised Ministry personnel only.<br />
                Unauthorised access attempts are logged.
            </p>
        </form>
    );
};

// ─── Consumer Login Form ────────────────────────────────────────
const ConsumerLoginForm = ({ onAuthSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLocalLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await axios.post('http://localhost:5000/api/auth/login', { email, password, role: 'consumer' });
            if (res.data.status === 'success') {
                onAuthSuccess();
            } else {
                setError(res.data.error || 'Invalid email or password.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Invalid email or password.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        window.location.href = 'http://localhost:5000/auth/google/consumer';
    };

    return (
        <form className="auth-form" onSubmit={handleLocalLogin}>
            {error && <div className="auth-error">{error}</div>}
            <div className="auth-field">
                <label className="auth-label">Email Address</label>
                <input
                    id="consumer-login-email"
                    className="auth-input"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                />
            </div>
            <div className="auth-field">
                <label className="auth-label">Password</label>
                <input
                    id="consumer-login-password"
                    className="auth-input"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />
            </div>
            <button
                id="consumer-login-submit"
                className="auth-btn-primary auth-btn-primary--consumer"
                type="submit"
                disabled={loading}
            >
                {loading ? 'Signing In...' : 'Sign In'}
            </button>
            <div className="auth-divider">or</div>
            <button
                id="consumer-google-login"
                className="auth-btn-google"
                type="button"
                onClick={handleGoogleLogin}
            >
                <GoogleIcon />
                Continue with Google
            </button>
        </form>
    );
};

// ─── Consumer Signup Form ───────────────────────────────────────
const ConsumerSignupForm = ({ onAuthSuccess }) => {
    const [form, setForm] = useState({ name: '', email: '', password: '', stakeholder_type: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

    const handleSignup = async (e) => {
        e.preventDefault();
        if (!form.stakeholder_type) {
            setError('Please select your stakeholder type.');
            return;
        }
        setLoading(true);
        setError('');
        try {
            const res = await axios.post('http://localhost:5000/api/auth/signup', form);
            if (res.data.status === 'success') {
                onAuthSuccess();
            } else {
                setError(res.data.error || 'Signup failed. Please try again.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Signup failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="auth-form" onSubmit={handleSignup}>
            {error && <div className="auth-error">{error}</div>}
            <div className="auth-field">
                <label className="auth-label">Full Name</label>
                <input
                    id="signup-name"
                    className="auth-input"
                    type="text"
                    name="name"
                    placeholder="Arjun Verma"
                    value={form.name}
                    onChange={handleChange}
                    required
                />
            </div>
            <div className="auth-field">
                <label className="auth-label">Email Address</label>
                <input
                    id="signup-email"
                    className="auth-input"
                    type="email"
                    name="email"
                    placeholder="you@example.com"
                    value={form.email}
                    onChange={handleChange}
                    required
                />
            </div>
            <div className="auth-field">
                <label className="auth-label">Password</label>
                <input
                    id="signup-password"
                    className="auth-input"
                    type="password"
                    name="password"
                    placeholder="Minimum 6 characters"
                    value={form.password}
                    onChange={handleChange}
                    minLength={6}
                    required
                />
            </div>
            <div className="auth-field">
                <label className="auth-label">I am a...</label>
                <select
                    id="signup-stakeholder"
                    className="auth-select"
                    name="stakeholder_type"
                    value={form.stakeholder_type}
                    onChange={handleChange}
                    required
                >
                    {STAKEHOLDER_OPTIONS.map(o => (
                        <option key={o.value} value={o.value} disabled={o.value === ''}>{o.label}</option>
                    ))}
                </select>
            </div>
            <button
                id="signup-submit"
                className="auth-btn-primary auth-btn-primary--consumer"
                type="submit"
                disabled={loading}
            >
                {loading ? 'Creating Account...' : 'Create Account & Continue'}
            </button>
            <p className="auth-legal">
                By creating an account you agree to Avalokan's Terms of Service and Privacy Policy.
            </p>
        </form>
    );
};

// ─── Main Auth Component ────────────────────────────────────────
const Auth = ({ mode, onBack }) => {
    // Consumer has two sub-tabs: login | signup
    const [consumerTab, setConsumerTab] = useState('login');

    // Called when any auth method succeeds — reload to trigger App.jsx /api/auth/status check
    const handleAuthSuccess = () => {
        window.location.reload();
    };

    return (
        <div className="auth-root">
            <div className="auth-card">
                <button className="auth-back-btn" onClick={onBack} id="auth-back-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="15 18 9 12 15 6" />
                    </svg>
                    Back to Home
                </button>

                {mode === 'admin' ? (
                    <>
                        <span className="auth-mode-badge auth-mode-badge--admin">🔒 Government Portal</span>
                        <h1 className="auth-title">Admin Sign In</h1>
                        <p className="auth-subtitle">Access the Avalokan analytics and policy management dashboard.</p>
                        <AdminLoginForm onAuthSuccess={handleAuthSuccess} />
                    </>
                ) : (
                    <>
                        <span className="auth-mode-badge auth-mode-badge--consumer">🌏 Public Consultation</span>
                        <h1 className="auth-title">
                            {consumerTab === 'login' ? 'Welcome Back' : 'Create Your Account'}
                        </h1>
                        <p className="auth-subtitle">
                            {consumerTab === 'login'
                                ? 'Sign in to access active policy consultations and submit your feedback.'
                                : 'Register to participate in public consultations and shape national policy.'}
                        </p>

                        {/* Tabs */}
                        <div className="auth-tabs">
                            <button
                                id="tab-login"
                                className={`auth-tab ${consumerTab === 'login' ? 'active active--consumer' : ''}`}
                                onClick={() => setConsumerTab('login')}
                                type="button"
                            >
                                Sign In
                            </button>
                            <button
                                id="tab-signup"
                                className={`auth-tab ${consumerTab === 'signup' ? 'active active--consumer' : ''}`}
                                onClick={() => setConsumerTab('signup')}
                                type="button"
                            >
                                Register
                            </button>
                        </div>

                        {consumerTab === 'login'
                            ? <ConsumerLoginForm onAuthSuccess={handleAuthSuccess} />
                            : <ConsumerSignupForm onAuthSuccess={handleAuthSuccess} />
                        }
                    </>
                )}
            </div>
        </div>
    );
};

export default Auth;
