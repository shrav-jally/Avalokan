import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PolicyList = ({ onSelectPolicy }) => {
    const [policies, setPolicies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPolicies = async () => {
            try {
                setLoading(true);
                const response = await axios.get('http://localhost:5000/api/policies');
                setPolicies(response.data);
                setError(null);
            } catch (err) {
                console.error('Error fetching policies:', err);
                setError('Failed to load policies. Please ensure backend is running.');
            } finally {
                setLoading(false);
            }
        };

        fetchPolicies();
    }, []);

    if (loading) {
        return (
            <div className="policy-loading">
                <p>Loading Policy Directory...</p>
            </div>
        );
    }

    if (error) {
        return <div className="error-banner">{error}</div>;
    }

    return (
        <div className="policy-list-container">
            {policies.map((policy) => (
                <div
                    key={policy.id}
                    className="policy-item panel-white"
                    onClick={() => onSelectPolicy(policy)}
                >
                    <div className="policy-header">
                        <span className="policy-id">{policy.id}</span>
                        <span className="policy-status">Active Draft</span>
                    </div>
                    <h3 className="policy-title">{policy.title}</h3>
                    <p className="policy-summary">{policy.summary}</p>
                    <div className="policy-footer">
                        <button className="view-details-btn">View Document & Details &rarr;</button>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default PolicyList;
