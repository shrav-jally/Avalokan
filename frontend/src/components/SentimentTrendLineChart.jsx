import React, { useState, useEffect } from 'react';
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
    const [fetchedData, setFetchedData] = useState([]);
    const [localLoading, setLocalLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!policyId) return;
        const fetchData = async () => {
            try {
                setLocalLoading(true);
                const res = await axios.get(`http://localhost:5000/api/analytics/trend/${policyId}`);
                setFetchedData(res.data.chain || []);
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

    const activeData = policyId ? fetchedData : initialData;
    const isLoading = policyId ? localLoading : externalLoading;

    if (isLoading) return <div className="chart-loading-placeholder"><p>Loading Sentiment Trends...</p></div>;
    if (error) return <div className="error-banner">{error}</div>;
    if (!activeData || activeData.length === 0) return null;

    // Adapt the X-axis mapping depending on data structure
    // If global, we use sorted data and 'draft_title'. If policy-specific, we use chronological 'version'.
    const isGlobal = !policyId;
    let chartData = [];

    if (isGlobal) {
        const sortedData = [...activeData].sort((a, b) => b.release_order - a.release_order);
        chartData = sortedData.map(d => ({
            name: d.draft_title,
            positive: d.positive_count,
            negative: d.negative_count,
            neutral: d.neutral_count,
        }));
    } else {
        chartData = activeData.map(d => ({
            name: d.version,
            positive: d.positive,
            negative: d.negative,
            neutral: d.neutral,
        }));
    }

    const chartMinWidth = Math.max(800, chartData.length * 150);

    return (
        <div className="trend-line-container">
            <h3 className="section-title">{isGlobal ? "Draft-wise Sentiment Trends (Newest to Oldest)" : "Sentiment Trend Across Versions"}</h3>
            <div className="horizontal-scroll-wrapper">
                <div style={{ minWidth: `${chartMinWidth}px`, height: '300px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                            data={chartData}
                            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                            <XAxis
                                dataKey="name"
                                tick={{ fontSize: 10, fill: '#6c757d' }}
                                axisLine={{ stroke: '#dee2e6' }}
                            />
                            <YAxis
                                tick={{ fontSize: 10, fill: '#6c757d' }}
                                axisLine={{ stroke: '#dee2e6' }}
                            />
                            <Tooltip
                                contentStyle={{
                                    borderRadius: '0px',
                                    border: '1px solid #dee2e6',
                                    fontSize: '12px',
                                    boxShadow: 'none'
                                }}
                            />
                            <Legend
                                verticalAlign="top"
                                height={36}
                                iconType="plainline"
                                wrapperStyle={{ fontSize: '12px' }}
                            />
                            <Line
                                type="monotone"
                                dataKey="positive"
                                stroke="var(--sentiment-pos)"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="negative"
                                stroke="var(--sentiment-neg)"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="neutral"
                                stroke="var(--sentiment-neu)"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default SentimentTrendLineChart;
