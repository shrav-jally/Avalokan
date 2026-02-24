import React, { useState, useMemo, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { FileText, Link, ChevronLeft, ChevronRight, X } from 'lucide-react';
import './PolicyDetail.css';
import SentimentWordCloud from './SentimentWordCloud';
import LinkedPoliciesModal from './LinkedPoliciesModal';

// Mock Data Generators
const wordCloudData = {
    positive: [
        { text: "support", value: 32 },
        { text: "efficient", value: 28 },
        { text: "improvement", value: 24 },
        { text: "clear", value: 20 },
        { text: "helpful", value: 18 },
        { text: "comprehensive", value: 16 },
        { text: "forward-thinking", value: 14 }
    ],
    neutral: [
        { text: "timeline", value: 30 },
        { text: "cost", value: 25 },
        { text: "process", value: 22 },
        { text: "implementation", value: 20 },
        { text: "details", value: 18 },
        { text: "scope", value: 15 },
        { text: "framework", value: 12 }
    ],
    negative: [
        { text: "restrictive", value: 35 },
        { text: "confusing", value: 30 },
        { text: "delays", value: 25 },
        { text: "unclear", value: 20 },
        { text: "burden", value: 18 },
        { text: "costly", value: 15 },
        { text: "bureaucratic", value: 12 }
    ]
};

const generateComments = () => {
    const sentiments = ['positive', 'neutral', 'negative'];
    const textSamples = {
        positive: [
            "Great initiative. I fully support these changes.",
            "Very clear guidelines. Will help standardize our workflow.",
            "Significant improvement over the previous iteration."
        ],
        neutral: [
            "Need more details on section 4 implementation details.",
            "When is the exact rollout date anticipated?",
            "How will this policy affect small-to-medium businesses?"
        ],
        negative: [
            "Too restrictive. This limits operational flexibility.",
            "This will undoubtedly cause administrative delays.",
            "I strongly disagree with the reporting burden this imposes."
        ]
    };

    return Array.from({ length: 28 }, (_, i) => {
        const s = sentiments[i % 3];
        return {
            id: `C-2026-${1000 + i}`,
            user: `Stakeholder_${Math.floor(Math.random() * 9000) + 1000}`,
            sentiment: s,
            text: textSamples[s][Math.floor(Math.random() * textSamples[s].length)],
            date: `2026-02-${String((i % 28) + 1).padStart(2, '0')}`
        };
    });
};

const MOCK_COMMENTS = generateComments();

const sentimentDistribution = [
    { name: 'Positive', value: 45 },
    { name: 'Neutral', value: 35 },
    { name: 'Negative', value: 20 }
];
const COLORS = ['#0ca678', '#495057', '#e03131'];

const PolicyDetail = ({ policy, onBack }) => {
    const [activeTab, setActiveTab] = useState('positive');
    const [currentPage, setCurrentPage] = useState(1);
    const commentsPerPage = 10;

    const [isPreviewOpen, setIsPreviewOpen] = useState(false);
    const [isLinkedPoliciesOpen, setIsLinkedPoliciesOpen] = useState(false);

    if (!policy) return null;

    // Pagination Logic
    const totalPages = Math.ceil(MOCK_COMMENTS.length / commentsPerPage);
    const startIndex = (currentPage - 1) * commentsPerPage;
    const currentComments = MOCK_COMMENTS.slice(startIndex, startIndex + commentsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const currentWords = wordCloudData[activeTab];

    return (
        <div className="policy-detail-layout">
            {/* Back Button */}
            <button className="pd-back-btn" onClick={onBack}>
                <ChevronLeft size={16} /> Back to Policies
            </button>

            {/* 1. Header & Quick Actions */}
            <div className="pd-header-card">
                <div className="pd-meta">
                    <span className="pd-id-badge">{policy.id}</span>
                    <span className="pd-status-badge">Analytics View</span>
                </div>
                <h1 className="pd-title">{policy.title}</h1>
                <p className="pd-summary">{policy.summary}</p>

                <div className="pd-actions">
                    <button className="pd-btn-secondary" onClick={() => setIsPreviewOpen(true)}>
                        <FileText size={16} /> Preview Document
                    </button>
                    <button className="pd-btn-secondary" onClick={() => setIsLinkedPoliciesOpen(true)}>
                        <Link size={16} /> Linked Policies
                    </button>
                </div>
            </div>

            {/* 2. Analytics Core (Two-Column Grid) */}
            <div className="pd-analytics-grid">
                {/* Left Column: Sentiment Chart */}
                <div className="pd-card">
                    <h3 className="pd-card-title">Sentiment Distribution</h3>
                    <div className="pd-pie-container" style={{ minHeight: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={sentimentDistribution}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                >
                                    {sentimentDistribution.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend verticalAlign="bottom" height={36} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Right Column: Word Cloud Engine */}
                <div className="pd-card">
                    <h3 className="pd-card-title">Keyword Extraction</h3>
                    <div className="pd-tabs">
                        <button
                            className={`pd-tab ${activeTab === 'positive' ? 'active-pos' : ''}`}
                            onClick={() => setActiveTab('positive')}
                        >
                            Positive
                        </button>
                        <button
                            className={`pd-tab ${activeTab === 'neutral' ? 'active-neu' : ''}`}
                            onClick={() => setActiveTab('neutral')}
                        >
                            Neutral
                        </button>
                        <button
                            className={`pd-tab ${activeTab === 'negative' ? 'active-neg' : ''}`}
                            onClick={() => setActiveTab('negative')}
                        >
                            Negative
                        </button>
                    </div>

                    <div className="pd-word-cloud-box">
                        <SentimentWordCloud words={currentWords} sentiment={activeTab} />
                    </div>
                </div>
            </div>

            {/* 3. Internal Comment Pagination */}
            <div className="pd-comments-container">
                <div className="pd-comments-header">
                    <h3>Stakeholder Comments</h3>
                    <span className="pd-pagination-info">Total: {MOCK_COMMENTS.length}</span>
                </div>

                <div className="pd-comments-body">
                    {currentComments.map(comment => (
                        <div key={comment.id} className="pd-comment-card">
                            <div className="pd-comment-meta">
                                <div className="pd-comment-user">
                                    <span className="pd-comment-id">{comment.id}</span>
                                    {comment.user}
                                </div>
                                <span className={`pd-comment-sentiment ${comment.sentiment}`}>
                                    {comment.sentiment}
                                </span>
                            </div>
                            <div className="pd-comment-text">
                                "{comment.text}"
                            </div>
                        </div>
                    ))}
                </div>

                <div className="pd-comments-footer">
                    <span className="pd-pagination-info">
                        Showing {startIndex + 1} - {Math.min(startIndex + commentsPerPage, MOCK_COMMENTS.length)} of {MOCK_COMMENTS.length}
                    </span>
                    <div className="pd-pagination-controls">
                        <button
                            className="pd-page-btn"
                            disabled={currentPage === 1}
                            onClick={handlePrevPage}
                        >
                            Previous
                        </button>
                        <button
                            className="pd-page-btn"
                            disabled={currentPage === totalPages}
                            onClick={handleNextPage}
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {/* Modals */}
            {isPreviewOpen && (
                <div className="pd-modal-overlay">
                    <div className="pd-modal">
                        <h3>Document Preview</h3>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            The actual PDF document viewer would be embedded here via an iframe or a react-pdf renderer.
                        </p>
                        <div style={{ padding: '3rem', textAlign: 'center', background: '#f8f9fa', border: '1px dashed #ccc', marginTop: '1rem' }}>
                            <FileText size={48} color="#adb5bd" style={{ marginBottom: '1rem' }} />
                            <h4>{policy.title}.pdf</h4>
                        </div>
                        <button className="pd-modal-close" onClick={() => setIsPreviewOpen(false)}>Close</button>
                    </div>
                </div>
            )}

            {isLinkedPoliciesOpen && (
                <LinkedPoliciesModal
                    policyId={policy.id}
                    onClose={() => setIsLinkedPoliciesOpen(false)}
                />
            )}

        </div>
    );
};

export default PolicyDetail;
