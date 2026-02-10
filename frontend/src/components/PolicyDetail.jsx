import React from 'react';

const PolicyDetail = ({ policy, onBack }) => {
    if (!policy) return null;

    return (
        <div className="policy-detail-container">
            <button className="back-btn" onClick={onBack}>&larr; Back to Policy List</button>

            <div className="panel-white detail-header-panel">
                <div className="detail-meta">
                    <span className="policy-id-large">{policy.id}</span>
                    <span className="policy-badge">Open for Consultation</span>
                </div>
                <h1 className="detail-title">{policy.title}</h1>
                <p className="detail-summary">{policy.summary}</p>
            </div>

            <div className="panel-white pdf-viewer-placeholder">
                <div className="placeholder-content">
                    <div className="pdf-icon">📄</div>
                    <h3>Document Preview Unavailable</h3>
                    <p>The PDF document for <strong>{policy.title}</strong> is being retrieved from the secure archive (MongoDB/S3).</p>
                    <div className="loading-bar-shim"></div>
                    <p className="small-text">Feature coming soon in v1.3</p>
                </div>
            </div>
        </div>
    );
};

export default PolicyDetail;
