import React from 'react';

const PoliciesList = ({ onSelectPolicy }) => {
    const policies = [
        {
            id: 'p1',
            title: 'Digital Personal Data Protection Bill 2026',
            summary: 'Framework for processing digital personal data, recognizing the rights of individuals and duties of data fiduciaries.',
        },
        {
            id: 'p2',
            title: 'National AI Safety Regulation Framework',
            summary: 'Guidelines for ethical AI development, focusing on transparency, accountability, and risk mitigation in public sector usage.',
        },
        {
            id: 'p3',
            title: 'Green Energy Transition Policy Draft',
            summary: 'Strategic roadmap to achieve 50% renewable energy capacity by 2030, including incentives for solar and wind adoption.',
        },
        {
            id: 'p4',
            title: 'Urban Mobility & Public Transport Reform',
            summary: 'Comprehensive plan to overhaul metropolitan transit systems, emphasizing electric buses and last-mile connectivity.',
        }
    ];

    return (
        <div className="policies-view">
            <div className="page-header">
                <div className="header-text">
                    <h2>Policy Consultations</h2>
                    <p>Review active drafts and their corresponding public feedback summaries.</p>
                </div>
            </div>

            <div className="policies-list">
                {policies.map((policy) => (
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
