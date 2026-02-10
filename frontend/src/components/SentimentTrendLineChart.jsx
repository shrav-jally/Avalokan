import React from 'react';
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

const SentimentTrendLineChart = ({ data, loading }) => {
    if (loading) return <div className="chart-loading-placeholder"><p>Loading Sentiment Trends...</p></div>;
    if (!data || data.length === 0) return null;

    // Sorting: Newest released (highest release_order) leftmost, oldest right
    const sortedData = [...data].sort((a, b) => b.release_order - a.release_order);

    // Each draft point will have positive, negative, and neutral counts
    const chartData = sortedData.map(d => ({
        name: d.draft_title,
        Positive: d.positive_count,
        Negative: d.negative_count,
        Neutral: d.neutral_count,
    }));

    const chartMinWidth = Math.max(1200, chartData.length * 150);

    return (
        <div className="trend-line-container">
            <h3 className="section-title">Draft-wise Sentiment Trends (Newest to Oldest)</h3>
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
                                dataKey="Positive"
                                stroke="var(--sentiment-pos)"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="Negative"
                                stroke="var(--sentiment-neg)"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="Neutral"
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
