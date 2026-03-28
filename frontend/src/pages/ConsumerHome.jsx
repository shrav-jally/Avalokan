import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ConsumerHome = ({ onLogout }) => {
    const [policies, setPolicies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPolicy, setSelectedPolicy] = useState(null);
    const [commentText, setCommentText] = useState('');
    const [clauseRef, setClauseRef] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        axios.get('http://localhost:5000/api/public/policies')
            .then(res => setPolicies(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const submitComment = async () => {
        if (!commentText) return;
        setSubmitting(true);
        const draftId = selectedPolicy.latest_draft_id || selectedPolicy.id || selectedPolicy.policy_id;
        try {
            await axios.post('http://localhost:5000/api/consumer/submit-comment', {
                draft_id: String(draftId),
                text: commentText,
                comment_text: commentText,
                clause_ref: clauseRef
            });
            setSuccess(true);
            setCommentText('');
            setClauseRef('');
        } catch(e) {
            console.error(e.response?.data || e);
        } finally {
            setSubmitting(false);
        }
    };

    const handleBack = () => {
        setSelectedPolicy(null);
        setSuccess(false);
    };

    return (
        <div className="app-container">
            <header className="top-header">
                <div className="header-brand">
                    <span className="gov-seal">G</span>
                    <h1>Avalokan Public Consultation Portal</h1>
                </div>
                <div className="admin-profile">
                    <span className="profile-role">Citizen Portal</span>
                    <button className="back-button" onClick={onLogout}>Logout</button>
                </div>
            </header>

            <div className="main-layout" style={{ backgroundColor: 'var(--bg-color)', overflowY: 'auto' }}>
                <div className="main-content" style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
                    {loading ? (
                        <div className="skeleton-container">Loading Active Consultations...</div>
                    ) : !selectedPolicy ? (
                        <>
                            <div className="page-header">
                                <div className="header-text">
                                    <h2>Available Public Consultations</h2>
                                    <p>Select a policy to read the draft document and submit public feedback.</p>
                                </div>
                            </div>
                            
                            <div className="policies-list policy-list-container">
                                {(!policies || policies.length === 0) ? (
                                    <div className="panel-white" style={{ textAlign: 'center' }}>No active policies available right now.</div>
                                ) : (
                                    policies?.map((draft, index) => (
                                        <div key={draft._id || index} className="policy-item" onClick={() => setSelectedPolicy(draft)}>
                                            <div className="policy-content">
                                                <div className="policy-header" style={{ marginBottom: '0.25rem' }}>
                                                    <span className="policy-status">ACTIVE</span>
                                                    <span>{draft.created_at ? new Date(draft.created_at).toLocaleDateString() : 'N/A'}</span>
                                                </div>
                                                <h3 className="policy-title">{draft.title}</h3>
                                                <p className="policy-summary">{draft.summary || draft.description || 'No description available.'}</p>
                                            </div>
                                            <div className="policy-arrow">→</div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="detail-header-actions" style={{ marginBottom: '1.5rem' }}>
                                <button className="back-button" onClick={handleBack}>← Back to Consultations</button>
                            </div>
                            
                            <div className="panel-white" style={{ marginBottom: '2rem' }}>
                                <div className="detail-meta">
                                    <span className="policy-badge">Active Consultation</span>
                                    <span className="policy-id-large">{selectedPolicy.latest_draft_id || selectedPolicy.id || selectedPolicy.policy_id}</span>
                                </div>
                                <h1 className="detail-title">{selectedPolicy.title}</h1>
                                <p className="detail-summary" style={{ marginTop: '1rem', whiteSpace: 'pre-wrap' }}>
                                    {selectedPolicy.summary || selectedPolicy.description || 'Detailed policy description goes here.'}
                                </p>
                                
                                {selectedPolicy.document_url && (
                                    <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)'}}>
                                        <a href={selectedPolicy.document_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-blue)', fontWeight: 600 }}>
                                            📄 View Official Document
                                        </a>
                                    </div>
                                )}
                            </div>

                            <div className="panel-white">
                                <h2>Submit Public Comment</h2>
                                <div className="login-divider" style={{ margin: '1rem 0' }}></div>
                                
                                {success ? (
                                    <div className="error-banner" style={{ backgroundColor: '#d4edda', color: '#155724', borderColor: '#c3e6cb' }}>
                                        Your comment was successfully submitted to the consultation portal securely.
                                        <br/><br/>
                                        <button className="login-btn-primary" style={{ width: 'auto' }} onClick={() => setSuccess(false)}>Submit Another Comment</button>
                                    </div>
                                ) : (
                                    <div>
                                        <p className="login-subtitle" style={{marginBottom: '1.5rem'}}>
                                            Your stakeholder category is automatically attached to this submission.
                                        </p>
                                        
                                        <div style={{ marginBottom: '1rem' }}>
                                            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                                                Clause Reference (Optional)
                                            </label>
                                            <input 
                                                type="text"
                                                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '4px', outline: 'none' }}
                                                placeholder="e.g. Section 135"
                                                value={clauseRef}
                                                onChange={e => setClauseRef(e.target.value)}
                                            />
                                        </div>

                                        <div style={{ marginBottom: '1rem' }}>
                                            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                                                Detailed Feedback *
                                            </label>
                                            <textarea 
                                                style={{ 
                                                    width: '100%', minHeight: '150px', padding: '0.75rem', 
                                                    border: '1px solid var(--border-color)', borderRadius: '4px', 
                                                    fontFamily: 'var(--font-family)', fontSize: '0.95rem',
                                                    color: 'var(--text-primary)', outline: 'none', resize: 'vertical'
                                                }}
                                                placeholder="Type your official feedback here..."
                                                value={commentText}
                                                onChange={(e) => setCommentText(e.target.value)}
                                            />
                                        </div>
                                        
                                        <button 
                                            className="login-btn-primary" 
                                            style={{ width: 'auto', opacity: (!commentText || submitting) ? 0.7 : 1 }} 
                                            onClick={submitComment} 
                                            disabled={!commentText || submitting}
                                        >
                                            {submitting ? 'Submitting...' : 'Submit Comment'}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ConsumerHome;
