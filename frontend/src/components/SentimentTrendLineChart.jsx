import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';

const SentimentTrendLineChart = ({ data: initialData, policyId, loading: externalLoading }) => {
    const navigate = useNavigate();
    const [fetchedData, setFetchedData] = useState([]);
    const [localLoading, setLocalLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!policyId) return;
        const fetchData = async () => {
            try {
                setLocalLoading(true);
                const res = await axios.get(`http://localhost:5000/api/analytics/policy-trend/${policyId}`);
                setFetchedData(res.data || []);
                setError(null);
            } catch (err) {
                console.error("Error fetching trend data", err);
                setError("Failed to load trend data.");
            } finally {
                setLocalLoading(false);
            }
        };
        fetchData();
    }, [policyId]);

    const activeData = (initialData && initialData.length > 0) ? initialData : fetchedData;
    const isLoading = (initialData && initialData.length > 0) ? false : (policyId ? localLoading : externalLoading);

    if (isLoading) return <div className="chart-loading-placeholder"><p>Loading Sentiment Trends...</p></div>;
    if (error) return <div className="error-banner" style={{ padding: '1rem', color: '#EF4444', background: '#fef2f2', borderRadius: '4px' }}>{error}</div>;
    
    if (!Array.isArray(activeData)) return <div>No chart data available</div>;
    if (!activeData || activeData.length === 0) {
        return <div style={{ padding: '2rem', textAlign: 'center', color: '#6B7280', background: '#f9fafb', borderRadius: '8px' }}>No analysis data available for this policy.</div>;
    }

    if (activeData.length < 2) {
        return (
            <div style={{ padding: '3rem 1rem', textAlign: 'center', background: '#f9fafb', borderRadius: '8px', border: '1px dashed #E5E7EB' }}>
                <p style={{ color: '#4B5563', fontWeight: '500', marginBottom: '8px' }}>Insufficient version data for trend analysis</p>
                <p style={{ color: '#9CA3AF', fontSize: '0.85rem' }}>Trends require at least two draft versions to compare sentiment shifts.</p>
            </div>
        );
    }

    const chartData = activeData.map(d => ({
        name: d.version,
        positive: d.positive,
        negative: d.negative,
        neutral: d.neutral,
        draft_id: d.draft_id // Ensure ID exists for navigation
    }));

    const handlePointClick = (state) => {
        if (state && state.activePayload && state.activePayload.length > 0) {
            const dataPoint = state.activePayload[0].payload;
            if (dataPoint.draft_id) {
                // Navigate to the specific historical draft's analysis page
                navigate(`/policy/${dataPoint.draft_id}`);
            }
        }
    };

    return (
        <div className="trend-line-container" style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #E5E7EB' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827', marginBottom: '1.5rem' }}>Sentiment Evolution Trend</h3>
            <div style={{ width: '100%', height: '350px' }}>
                <ResponsiveContainer width="100%" height={350} minHeight={300}>
                    <LineChart
                        data={chartData}
                        margin={{ top: 10, right: 30, left: 0, bottom: 20 }}
                        onClick={handlePointClick}
                        style={{ cursor: 'pointer' }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 11, fill: '#6B7280' }}
                            axisLine={{ stroke: '#E5E7EB' }}
                            padding={{ left: 20, right: 20 }}
                        />
                        <YAxis
                            tick={{ fontSize: 11, fill: '#6B7280' }}
                            axisLine={{ stroke: '#E5E7EB' }}
                            unit="%"
                        />
                        <Tooltip
                            contentStyle={{
                                borderRadius: '8px',
                                border: '1px solid #E5E7EB',
                                fontSize: '12px',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                            }}
                        />
                        <Legend
                            verticalAlign="bottom"
                            height={36}
                            iconType="circle"
                            wrapperStyle={{ fontSize: '13px', paddingTop: '20px' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="positive"
                            name="Positive"
                            stroke="#10B981"
                            strokeWidth={3}
                            dot={{ r: 5, fill: '#10B981', strokeWidth: 2, stroke: '#fff' }}
                            activeDot={{ r: 8 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="negative"
                            name="Negative"
                            stroke="#EF4444"
                            strokeWidth={3}
                            dot={{ r: 5, fill: '#EF4444', strokeWidth: 2, stroke: '#fff' }}
                            activeDot={{ r: 8 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="neutral"
                            name="Neutral"
                            stroke="#6B7280"
                            strokeWidth={3}
                            dot={{ r: 5, fill: '#6B7280', strokeWidth: 2, stroke: '#fff' }}
                            activeDot={{ r: 8 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default SentimentTrendLineChart;
