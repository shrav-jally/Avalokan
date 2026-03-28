import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { 
    FileText, Link, ChevronLeft, ChevronRight, X, Search, AlertTriangle, Download, Cpu, RefreshCw, 
    TrendingUp, TrendingDown, ArrowUpRight, ChevronDown, Check, FileSpreadsheet, Loader2
} from 'lucide-react';
import './PolicyDetail.css';
import SentimentWordCloud from './SentimentWordCloud';
import SentimentTrendLineChart from './SentimentTrendLineChart';
import LinkedPoliciesModal from './LinkedPoliciesModal';

// Chart colors

const COLORS = ['#0ca678', '#495057', '#e03131'];

const PolicyDetail = ({ policy, userRole, onBack }) => {
    // Search & Filter state
    const [comments, setComments] = useState([]);
    const [loadingComments, setLoadingComments] = useState(false);
    const [searchKeyword, setSearchKeyword] = useState('');
    const [filterSentiment, setFilterSentiment] = useState('');
    const [filterHighRisk, setFilterHighRisk] = useState(false);
    const [filterStakeholder, setFilterStakeholder] = useState('');
    const [analytics, setAnalytics] = useState(null);
    const [analyticsError, setAnalyticsError] = useState(false);
    const [searchAnalytics, setSearchAnalytics] = useState(null);
    const [wordCloudData, setWordCloudData] = useState([]);
    const [trendHistory, setTrendHistory] = useState([]);
    const [isRegenerating, setIsRegenerating] = useState(false);
    
    const [currentPage, setCurrentPage] = useState(1);
    const commentsPerPage = 10;

    const [isPreviewOpen, setIsPreviewOpen] = useState(false);
    const [isLinkedPoliciesOpen, setIsLinkedPoliciesOpen] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [isExportDropdownOpen, setIsExportDropdownOpen] = useState(false);
    
    const explorerRef = useRef(null);
    const wordCloudContainerRef = useRef(null);
    const [wordCloudWidth, setWordCloudWidth] = useState(0);

    useEffect(() => {
        if (!wordCloudContainerRef.current) return;
        
        // Ensure container dimensions exist before passing to any graphing library
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                if (entry.contentRect.width > 0) {
                    setWordCloudWidth(entry.contentRect.width);
                }
            }
        });
        
        resizeObserver.observe(wordCloudContainerRef.current);
        return () => resizeObserver.disconnect();
    }, [policy]);

    const fetchAnalytics = async () => {
        try {
            setAnalyticsError(false);
            const res = await axios.get(`http://localhost:5000/api/analytics/draft/${policy.id}`);
            if (res.data) {
                setAnalytics(res.data);
                setWordCloudData(res.data.wordCloud || []);
            } else {
                setAnalyticsError(true);
            }
        } catch (err) {
            console.error("Failed to fetch analytics", err);
            setAnalyticsError(true);
        }
        // WordCloud data is now populated via the consolidated draft endpoint

        try {
            const trendRes = await axios.get(`http://localhost:5000/api/analytics/policy-trend/${policy.id}`);
            setTrendHistory(trendRes.data || []);
        } catch (err) {
            console.error("Failed to fetch trend history", err);
        }
    };

    useEffect(() => {
        if (!policy) return;
        fetchAnalytics();
    }, [policy]);

    useEffect(() => {
        if (!policy) return;
        
        const fetchComments = async () => {
            setLoadingComments(true);
            try {
                const params = { 
                    policy_id: policy.id, 
                    limit: 1000,
                    skip: 0
                };
                if (searchKeyword.trim()) params.keyword = searchKeyword.trim();
                
                if (filterHighRisk) {
                    params.high_risk = 'true';
                } else {
                    if (filterSentiment) params.sentiment = filterSentiment;
                    if (filterStakeholder) params.stakeholder_type = filterStakeholder;
                }

                const res = await axios.get('http://localhost:5000/api/comments/search', { params });
                setComments(res.data.results || []);
                setSearchAnalytics(res.data.sentimentDistribution || null);
                setCurrentPage(1); 
            } catch (err) {
                console.error("Failed to fetch comments", err);
            } finally {
                setLoadingComments(false);
            }
        };

        // 500ms Debounce
        const timer = setTimeout(fetchComments, 500);
        return () => clearTimeout(timer);
    }, [policy, searchKeyword, filterSentiment, filterHighRisk, filterStakeholder]);

    const handleResetFilters = () => {
        setSearchKeyword('');
        setFilterSentiment('');
        setFilterHighRisk(false);
        setFilterStakeholder('');
    };

    const handleRegenerateSummary = async () => {
        setIsRegenerating(true);
        try {
            // Trigger meta-summarization
            await axios.post(`http://localhost:5000/api/analysis/summarize-draft/${analytics?.draft_id || policy.id}`);
            // Refresh local analytics state after regeneration
            await fetchAnalytics();
        } catch (err) {
            console.error("Regeneration failed", err);
            alert(err.response?.data?.message || "Failed to regenerate executive summary.");
        } finally {
            setIsRegenerating(false);
        }
    };

    // Improvement Delta Calculation
    const improvementDelta = React.useMemo(() => {
        if (trendHistory.length < 2) return null;
        
        const latest = trendHistory[trendHistory.length - 1];
        const previous = trendHistory[trendHistory.length - 2];
        
        const diff = latest.negative - previous.negative;
        return {
            val: Math.abs(diff),
            isImproved: diff < 0,
            previousVersion: previous.version
        };
    }, [trendHistory]);

    if (!policy) return null;

    const totalPages = Math.ceil(comments.length / commentsPerPage);
    const startIndex = (currentPage - 1) * commentsPerPage;
    const currentComments = comments.slice(startIndex, startIndex + commentsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const handleDownload = async (format) => {
        setIsExporting(true);
        setIsExportDropdownOpen(false);
        try {
            const endpoint = format === 'pdf' ? 'pdf' : 'excel';
            const response = await axios.get(`http://localhost:5000/api/reports/${endpoint}/${policy.id}`, {
                responseType: 'blob'
            });
            
            // Create a blob link to trigger download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            const ext = format === 'pdf' ? 'pdf' : 'xlsx';
            link.setAttribute('download', `Consultation_Report_${policy.id}.${ext}`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (err) {
            console.error("Download failed", err);
            alert("Export failed. Please try again.");
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="policy-detail-layout" onClick={() => isExportDropdownOpen && setIsExportDropdownOpen(false)}>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '2rem' }}>
                    <div style={{ flex: 1 }}>
                        <p className="pd-summary" style={{ fontSize: '1.05rem', lineHeight: '1.6', color: '#495057' }}>
                            {analytics?.combinedSummary || policy.summary}
                        </p>
                        {analytics?.last_updated && (
                            <div style={{ fontSize: '0.75rem', color: '#adb5bd', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span>• Meta-Analysis Last Updated: {new Date(analytics.last_updated).toLocaleString()}</span>
                                {analytics.is_meta_summary && <span style={{ color: '#0ca678', fontWeight: 'bold' }}>(Verified AI Consensus)</span>}
                            </div>
                        )}
                    </div>
                    
                    {userRole === 'admin' && (
                        <button 
                            className="pd-btn-secondary" 
                            onClick={handleRegenerateSummary}
                            disabled={isRegenerating}
                            style={{ whiteSpace: 'nowrap', marginTop: '4px', border: '1px solid var(--accent-primary)', color: 'var(--accent-primary)' }}
                        >
                            {isRegenerating ? (
                                <RefreshCw size={16} className="spin-animation" />
                            ) : (
                                <RefreshCw size={16} />
                            )}
                            {isRegenerating ? ' Analyzing Feedback...' : ' Regenerate Summary'}
                        </button>
                    )}
                </div>

                <div className="pd-actions">
                    <div className="pd-export-dropdown-container">
                        <button 
                            className="pd-btn-secondary" 
                            style={{ background: 'var(--accent-primary)', color: 'white', border: 'none' }}
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsExportDropdownOpen(!isExportDropdownOpen);
                            }}
                            disabled={isExporting}
                        >
                            {isExporting ? <Loader2 size={16} className="spin-animation" /> : <Download size={16} />}
                            {isExporting ? ' Generating Report...' : ' Export Report'}
                            {!isExporting && <ChevronDown size={14} style={{ marginLeft: '4px' }} />}
                        </button>

                        {isExportDropdownOpen && (
                            <div className="pd-export-menu">
                                <button className="pd-export-item" onClick={() => handleDownload('pdf')}>
                                    <FileText size={16} style={{ color: '#2980b9' }} />
                                    <div>
                                        <div style={{ fontWeight: '600' }}>Download PDF Summary</div>
                                        <div style={{ fontSize: '0.7rem', color: '#868e96' }}>Formatted executive overview</div>
                                    </div>
                                </button>
                                <button className="pd-export-item" onClick={() => handleDownload('excel')}>
                                    <FileSpreadsheet size={16} style={{ color: '#099268' }} />
                                    <div>
                                        <div style={{ fontWeight: '600' }}>Download Full Excel Data</div>
                                        <div style={{ fontSize: '0.7rem', color: '#868e96' }}>Raw comments & keyword audit</div>
                                    </div>
                                </button>
                            </div>
                        )}
                    </div>

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
                        {analyticsError ? (
                            <div className="p-4 text-center" style={{ padding: '4rem', color: '#e03131', textAlign: 'center' }}>Analytics currently unavailable</div>
                        ) : (searchAnalytics || analytics?.sentiment || []).length > 0 ? (
                            <ResponsiveContainer width="100%" height={300} minWidth={0}>
                                <PieChart>
                                    <Pie
                                        data={searchAnalytics || analytics?.sentiment || []}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    >
                                        {(searchAnalytics || analytics?.sentiment || []).map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                    <Legend verticalAlign="bottom" height={36} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="p-4 text-center" style={{ padding: '4rem', color: '#adb5bd', textAlign: 'center' }}>Loading Analytics Data...</div>
                        )}
                    </div>
                </div>

                {/* Right Column: Word Cloud Engine */}
                <div className="pd-card">
                    <h3 className="pd-card-title">Keyword Extraction</h3>
                    <div style={{ fontSize: '0.8rem', color: '#adb5bd', marginBottom: '8px', textAlign: 'center' }}>
                        Click a keyword to search related feedback.
                    </div>
                    <div className="pd-word-cloud-box" ref={wordCloudContainerRef} style={{ width: '100%', height: '350px', minHeight: '350px', position: 'relative' }}>
                        {wordCloudWidth > 0 ? (
                            wordCloudData && wordCloudData.length > 0 ? (
                                <SentimentWordCloud 
                                    words={wordCloudData.map(word => ({ ...word, value: word.value || Math.floor(Math.random() * 50) + 10 }))} 
                                    onWordClick={(word) => {
                                        setSearchKeyword(word);
                                        if (explorerRef.current) {
                                            explorerRef.current.scrollIntoView({ behavior: 'smooth' });
                                        }
                                    }} 
                                />
                            ) : (
                                <SentimentWordCloud 
                                    words={[
                                        {text: 'Processing', value: 20, sentiment: 'neutral'}, 
                                        {text: 'Keywords', value: 15, sentiment: 'neutral'}, 
                                        {text: 'For', value: 10, sentiment: 'neutral'},
                                        {text: 'Analysis...', value: 10, sentiment: 'neutral'}
                                    ]} 
                                    onWordClick={() => {}} 
                                />
                            )
                        ) : (
                            <div className="loading-placeholder" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#adb5bd' }}>Processing layout dimensions...</div>
                        )}
                    </div>
                </div>
            </div>

            {/* 2.5 Historical Trend Section */}
            {trendHistory.length >= 2 && (
                <div className="pd-card" style={{ marginTop: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                        <div>
                            <h3 className="pd-card-title" style={{ marginBottom: '8px' }}>Version-wise Progress</h3>
                            <p style={{ fontSize: '0.85rem', color: '#868e96', margin: 0 }}>Stakeholder sentiment evolution across official iterations.</p>
                        </div>
                        
                        {improvementDelta && (
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '12px', 
                                padding: '10px 16px', 
                                borderRadius: '8px', 
                                background: improvementDelta.isImproved ? '#e6fcf5' : '#fff5f5',
                                border: `1px solid ${improvementDelta.isImproved ? '#0ca678' : '#e03131'}`
                            }}>
                                <div style={{ 
                                    width: '32px', 
                                    height: '32px', 
                                    borderRadius: '50%', 
                                    background: '#fff', 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    color: improvementDelta.isImproved ? '#0ca678' : '#e03131'
                                }}>
                                    {improvementDelta.isImproved ? <TrendingDown size={18} /> : <AlertTriangle size={18} />}
                                </div>
                                <div>
                                    <div style={{ 
                                        fontWeight: 'bold', 
                                        fontSize: '0.9rem', 
                                        color: improvementDelta.isImproved ? '#099268' : '#c92a2a',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px'
                                    }}>
                                        {improvementDelta.isImproved ? 'Moving in Right Direction' : 'Requires Review'}
                                        {improvementDelta.isImproved && <ArrowUpRight size={14} />}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: improvementDelta.isImproved ? '#0ca678' : '#e03131' }}>
                                        Negative feedback {improvementDelta.isImproved ? 'decreased' : 'increased'} by {improvementDelta.val}% since {improvementDelta.previousVersion}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    
                    <SentimentTrendLineChart data={trendHistory} policyId={policy.id} />
                </div>
            )}
            <div className="pd-comments-container" style={{ marginTop: '20px' }}>
                <div className="pd-comments-header">
                    <h3>Clause-wise Feedback Synthesis</h3>
                    <span className="pd-pagination-info">{analytics?.clauseSummaries?.length || 0} Clauses Analyzed</span>
                </div>
                
                <div className="pd-comments-body">
                    {!analytics ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: '#adb5bd' }}>
                            <RefreshCw size={24} className="spin-animation" style={{ marginBottom: '10px' }} />
                            <div>Loading clause-wise synthesis...</div>
                        </div>
                    ) : !analytics?.clauseSummaries?.length ? (
                        <div style={{ textAlign: 'center', padding: '3rem 1rem', background: '#f8f9fa', borderRadius: '8px', border: '1px dashed #dee2e6' }}>
                            <Cpu size={32} color="#adb5bd" style={{ marginBottom: '16px' }} />
                            <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>No Automated Clause Analysis Found</h4>
                            <p style={{ color: '#868e96', fontSize: '0.9rem', marginBottom: '20px', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                                The localized AI models have not yet grouped feedback for specific legal clauses within this draft. 
                            </p>
                            {userRole === 'admin' && (
                                <button 
                                    className="pd-btn-primary" 
                                    onClick={handleRegenerateSummary}
                                    disabled={isRegenerating}
                                >
                                    {isRegenerating ? <RefreshCw size={16} className="spin-animation" /> : <Cpu size={16} />}
                                    {isRegenerating ? ' Synthesizing...' : ' Trigger AI Analysis Engine'}
                                </button>
                            )}
                        </div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Clause Name</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Consensus</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>AI Synthesis</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem', textAlign: 'center' }}>Volume</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {analytics.clauseSummaries.map((item, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                                            <td style={{ padding: '12px', fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--accent-primary)', minWidth: '120px' }}>
                                                {item.clause}
                                            </td>
                                            <td style={{ padding: '12px' }}>
                                                <span className={`pd-comment-sentiment ${item.sentiment}`} style={{ fontSize: '0.7rem' }}>
                                                    {item.sentiment.toUpperCase()}
                                                </span>
                                            </td>
                                            <td style={{ padding: '12px', maxWidth: '500px' }}>
                                                <div style={{ fontSize: '0.88rem', color: '#495057', fontStyle: 'italic', lineHeight: '1.4' }}>
                                                    "{item.summary}"
                                                </div>
                                            </td>
                                            <td style={{ padding: '12px', textAlign: 'center' }}>
                                                <span style={{ fontSize: '0.8rem', color: '#6c757d', background: '#f1f3f5', padding: '2px 8px', borderRadius: '12px' }}>
                                                    {item.count}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* 3. Searchable Comment Explorer */}
            <div className="pd-comments-container" ref={explorerRef}>
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
                            setFilterHighRisk(false);
                        }}
                        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                    >
                        <option value="">All Sentiments</option>
                        <option value="POSITIVE">Positive</option>
                        <option value="NEUTRAL">Neutral</option>
                        <option value="NEGATIVE">Negative</option>
                    </select>

                    <select 
                        className="pd-select" 
                        value={filterStakeholder}
                        onChange={(e) => setFilterStakeholder(e.target.value)}
                        style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                    >
                        <option value="">All Stakeholders</option>
                        <option value="CA">Chartered Accountants (CA)</option>
                        <option value="Company">Companies / Directors</option>
                        <option value="Citizen">General Citizens</option>
                    </select>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#495057' }}>Safety Filter:</span>
                        <select 
                            className="pd-select"
                            value={filterHighRisk ? 'HIGH_RISK' : 'ALL'}
                            onChange={(e) => {
                                const val = e.target.value;
                                if (val === 'HIGH_RISK') {
                                    setFilterHighRisk(true);
                                    setFilterSentiment('');
                                    setFilterStakeholder('');
                                } else {
                                    setFilterHighRisk(false);
                                }
                            }}
                            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                        >
                            <option value="ALL">All Comments</option>
                            <option value="HIGH_RISK">High Risk (Toxic & Negative)</option>
                        </select>
                    </div>

                    <button 
                        onClick={handleResetFilters}
                        style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '8px 12px', background: '#fff', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem', color: '#495057' }}
                    >
                        <X size={14} /> Reset
                    </button>
                </div>

                <div className="pd-comments-body">
                    {loadingComments ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>Loading comments...</div>
                    ) : currentComments.length === 0 ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>No comments match your search criteria.</div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Status</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Stakeholder</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Comment Text</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Clause</th>
                                        <th style={{ padding: '12px', fontSize: '0.85rem' }}>Sentiment</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentComments.map(comment => (
                                        <tr key={comment.comment_id} style={{ borderBottom: '1px solid #dee2e6', background: comment.is_toxic ? '#fff5f5' : '#fff' }}>
                                            <td style={{ padding: '12px', textAlign: 'center' }}>
                                                {comment.is_toxic ? <AlertTriangle size={18} color="#e03131" /> : (comment.sentiment === 'POSITIVE' ? <div style={{width: 18, height: 18, background: '#e6fcf5', borderRadius: '50%', border: '2px solid #0ca678'}} /> : <div style={{width: 18}} />)}
                                            </td>
                                            <td style={{ padding: '12px', fontSize: '0.85rem', fontWeight: '500' }}>
                                                {comment.stakeholder_type || 'General'}
                                            </td>
                                            <td style={{ padding: '12px', maxWidth: '400px' }}>
                                                <div style={{ fontSize: '0.9rem', color: '#212529', marginBottom: '4px' }}>"{comment.text}"</div>
                                                {comment.summary && comment.summary !== comment.text && (
                                                    <div style={{ fontSize: '0.8rem', color: '#868e96', fontStyle: 'italic' }}>
                                                        Summary: {comment.summary}
                                                    </div>
                                                )}
                                            </td>
                                            <td style={{ padding: '12px', fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 'bold' }}>
                                                {comment.clause_ref || 'N/A'}
                                            </td>
                                            <td style={{ padding: '12px' }}>
                                                <span className={`pd-comment-sentiment ${comment.sentiment.toLowerCase()}`}>
                                                    {comment.sentiment}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
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

            {/* 4. AI Insights & Transparency */}
            <div className="pd-ai-insights-section" style={{ marginTop: '2rem', padding: '1.5rem', border: '1px solid #e9ecef', borderRadius: '8px', background: '#f8f9fa' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                    <Cpu size={20} color="var(--accent-primary)" />
                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#343a40' }}>AI Insight Diagnostics</h3>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                    <div className="insight-stat">
                        <span style={{ fontSize: '0.8rem', color: '#868e96', display: 'block', marginBottom: '4px' }}>Sentiment Engine</span>
                        <code style={{ fontSize: '0.9rem', color: 'var(--accent-secondary)', fontWeight: 'bold' }}>distilbert-base-uncased</code>
                    </div>
                    
                    <div className="insight-stat">
                        <span style={{ fontSize: '0.8rem', color: '#868e96', display: 'block', marginBottom: '4px' }}>Avg. Confidence Score</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ height: '8px', width: '100px', background: '#e9ecef', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${Math.round((comments.reduce((acc, c) => acc + (c.sentiment_score || 0), 0) / (comments.length || 1)) * 100)}%`, background: 'var(--accent-primary)' }} />
                            </div>
                            <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>
                                {Math.round((comments.reduce((acc, c) => acc + (c.sentiment_score || 0), 0) / (comments.length || 1)) * 100)}%
                            </span>
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', padding: '10px', borderLeft: '4px solid #adb5bd', fontSize: '0.85rem', color: '#6c757d', background: '#fff' }}>
                    <strong>Note:</strong> Toxicity detected using <em>Unitary Toxic-BERT</em>; results may require human verification as part of the semi-autonomous auditing process.
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
