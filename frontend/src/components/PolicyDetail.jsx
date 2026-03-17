import React, { useState, useMemo, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { FileText, Link, ChevronLeft, ChevronRight, X, Search, AlertTriangle, Download } from 'lucide-react';
import './PolicyDetail.css';
import SentimentWordCloud from './SentimentWordCloud';
import LinkedPoliciesModal from './LinkedPoliciesModal';

// Mock Data Generators for WordCloud/Charts
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

const COLORS = ['#0ca678', '#495057', '#e03131'];

const PolicyDetail = ({ policy, onBack }) => {
    const [activeTab, setActiveTab] = useState('positive');
    
    // Search & Filter state
    const [comments, setComments] = useState([]);
    const [loadingComments, setLoadingComments] = useState(false);
    const [searchKeyword, setSearchKeyword] = useState('');
    const [filterSentiment, setFilterSentiment] = useState('');
    const [filterHighRisk, setFilterHighRisk] = useState(false);
    
    const [currentPage, setCurrentPage] = useState(1);
    const commentsPerPage = 10;

    const [isPreviewOpen, setIsPreviewOpen] = useState(false);
    const [isLinkedPoliciesOpen, setIsLinkedPoliciesOpen] = useState(false);

    useEffect(() => {
        if (!policy) return;
        const fetchComments = async () => {
            setLoadingComments(true);
            try {
                const params = { policy_id: policy.id, limit: 1000 };
                if (searchKeyword.trim()) params.keyword = searchKeyword.trim();
                
                if (filterHighRisk) {
                    params.sentiment = 'NEGATIVE';
                    params.is_toxic = 'true';
                } else if (filterSentiment) {
                    params.sentiment = filterSentiment;
                }

                const res = await axios.get('http://localhost:5000/api/comments/search', { params });
                setComments(res.data.results || []);
                setCurrentPage(1); // reset to first page on new search
            } catch (err) {
                console.error("Failed to fetch comments", err);
            } finally {
                setLoadingComments(false);
            }
        };

        // debounce the search slightly
        const timer = setTimeout(() => {
            fetchComments();
        }, 300);
        return () => clearTimeout(timer);
    }, [policy, searchKeyword, filterSentiment, filterHighRisk]);

    if (!policy) return null;

    // Pagination Logic
    const derivedSentimentDistribution = useMemo(() => {
        const counts = { POSITIVE: 0, NEUTRAL: 0, NEGATIVE: 0 };
        comments.forEach(c => {
            const s = c.sentiment?.toUpperCase();
            if (counts[s] !== undefined) counts[s]++;
        });
        const total = comments.length;
        if (total === 0) return [
            { name: 'Positive', value: 0 },
            { name: 'Neutral', value: 0 },
            { name: 'Negative', value: 0 }
        ];
        return [
            { name: 'Positive', value: Math.round((counts.POSITIVE / total) * 100) },
            { name: 'Neutral', value: Math.round((counts.NEUTRAL / total) * 100) },
            { name: 'Negative', value: Math.round((counts.NEGATIVE / total) * 100) }
        ];
    }, [comments]);

    const totalPages = Math.ceil(comments.length / commentsPerPage);
    const startIndex = (currentPage - 1) * commentsPerPage;
    const currentComments = comments.slice(startIndex, startIndex + commentsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const currentWords = wordCloudData[activeTab];

    const handleExportPdf = () => {
        // Trigger download of generated PDF
        window.open(`http://localhost:5000/api/reports/generate/${policy.id}`, '_blank');
    };

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
                    <button className="pd-btn-secondary" onClick={handleExportPdf}>
                        <Download size={16} /> Export PDF Report
                    </button>
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
                                    data={derivedSentimentDistribution}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                >
                                    {derivedSentimentDistribution.map((entry, index) => (
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

            {/* 3. Searchable Comment Explorer */}
            <div className="pd-comments-container">
                <div className="pd-comments-header">
                    <h3>Searchable Comment Explorer</h3>
                    <span className="pd-pagination-info">Returns: {comments.length}</span>
                </div>
                
                {/* Filters Row */}
                <div className="pd-filters-bar" style={{ display: 'flex', gap: '1rem', padding: '1rem', borderBottom: '1px solid #dee2e6', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div className="pd-search-box" style={{ flex: '1', display: 'flex', alignItems: 'center', background: '#fff', border: '1px solid #ccc', borderRadius: '4px', padding: '4px 8px' }}>
                        <Search size={16} color="#adb5bd" style={{ marginRight: '8px' }} />
                        <input 
                            type="text" 
                            placeholder="Enter keyword or phrase to search..." 
                            style={{ border: 'none', outline: 'none', width: '100%', padding: '4px' }}
                            value={searchKeyword}
                            onChange={(e) => setSearchKeyword(e.target.value)}
                        />
                    </div>
                    
                    <select 
                        className="pd-select" 
                        value={filterSentiment}
                        onChange={(e) => {
                            setFilterSentiment(e.target.value);
                            setFilterHighRisk(false); // Reset high risk if changing sentiment manually
                        }}
                        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                    >
                        <option value="">All Sentiments</option>
                        <option value="POSITIVE">Positive</option>
                        <option value="NEUTRAL">Neutral</option>
                        <option value="NEGATIVE">Negative</option>
                    </select>

                    <button 
                        className={`pd-btn-high-risk ${filterHighRisk ? 'active' : ''}`}
                        onClick={() => {
                            setFilterHighRisk(!filterHighRisk);
                            if (!filterHighRisk) setFilterSentiment('');
                        }}
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', border: filterHighRisk ? '1px solid #e03131' : '1px solid #ccc', background: filterHighRisk ? '#fff5f5' : '#fff', color: filterHighRisk ? '#e03131' : '#495057', borderRadius: '4px', cursor: 'pointer', fontWeight: '500' }}
                    >
                        <AlertTriangle size={16} /> High Risk (Toxic/Negative)
                    </button>
                </div>

                <div className="pd-comments-body">
                    {loadingComments ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>Loading comments...</div>
                    ) : currentComments.length === 0 ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>No comments match your search criteria.</div>
                    ) : (
                        currentComments.map(comment => (
                            <div key={comment.comment_id} className="pd-comment-card" style={{ borderLeft: comment.is_toxic ? '4px solid #e03131' : '4px solid transparent' }}>
                                <div className="pd-comment-meta">
                                    <div className="pd-comment-user">
                                        <span className="pd-comment-id">{comment.comment_id.substring(0, 8)}...</span>
                                        {/* Fallback to draft_id or arbitrary text if mock user not available */}
                                        <span style={{color: '#868e96', fontSize: '0.8rem', marginLeft: '8px'}}>(Draft: {comment.draft_id})</span>
                                        {comment.is_toxic && <span style={{ color: '#e03131', fontSize: '0.75rem', fontWeight: 'bold', marginLeft: '8px' }}>[FLAGGED TOXIC]</span>}
                                    </div>
                                    <span className={`pd-comment-sentiment ${comment.sentiment.toLowerCase()}`}>
                                        {comment.sentiment}
                                    </span>
                                </div>
                                <div className="pd-comment-text">
                                    "{comment.text}"
                                </div>
                                {comment.summary && comment.summary !== comment.text && (
                                    <div className="pd-comment-summary" style={{ marginTop: '8px', padding: '8px', background: '#f8f9fa', borderRadius: '4px', fontSize: '0.85rem', color: '#495057', fontStyle: 'italic' }}>
                                        <strong>AI Summary:</strong> {comment.summary}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                <div className="pd-comments-footer">
                    <span className="pd-pagination-info">
                        Showing {startIndex + (currentComments.length > 0 ? 1 : 0)} - {startIndex + currentComments.length} of {comments.length}
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
                            disabled={currentPage === totalPages || totalPages === 0}
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
