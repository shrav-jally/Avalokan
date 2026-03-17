import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PoliciesList = ({ onSelectPolicy }) => {
    const [policies, setPolicies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPolicies = async () => {
            try {
                setLoading(true);
                const res = await axios.get('http://localhost:5000/api/policies');
                setPolicies(res.data);
                setError(null);
            } catch (err) {
                console.error('Error fetching policies:', err);
                setError('Failed to load policies. Please try again later.');
            } finally {
                setLoading(false);
            }
        };

        fetchPolicies();
    }, []);

    return (
        <div className="policies-view">
            <div className="page-header">
                <div className="header-text">
                    <h2>Policy Consultations</h2>
                    <p>Review active drafts and their corresponding public feedback summaries.</p>
                </div>
            </div>

            <div className="policies-list">
                {loading && <div className="loading-state">Loading policies...</div>}
                {error && <div className="error-banner">{error}</div>}
                {!loading && !error && policies.length === 0 && (
                    <div className="empty-state">No policies found.</div>
                )}
                {!loading && !error && policies.map((policy) => (
                    <div
                        key={policy.id}
                        className="policy-item"
                        onClick={() => onSelectPolicy(policy)}
                    >
                        <div className="policy-content">
                            <h3 className="policy-title">{policy.title}</h3>
                            <p className="policy-summary">{policy.summary}</p>
                        </div>
                        <div className="policy-arrow">
                            →
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PoliciesList;
