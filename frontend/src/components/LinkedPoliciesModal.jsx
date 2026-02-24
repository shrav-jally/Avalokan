import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { X, AlertCircle } from 'lucide-react';
import './LinkedPoliciesModal.css';

const LinkedPoliciesModal = ({ policyId, onClose }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const handleEsc = (event) => {
            if (event.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    useEffect(() => {
        const fetchLinked = async () => {
            try {
                setLoading(true);
                const res = await axios.get(`http://localhost:5000/api/analytics/compare-linked/${policyId}`);
                setData(res.data.chain || []);
                setError(null);
            } catch (e) {
                console.error("Failed to fetch linked policies", e);
                setError("Failed to load related policy data.");
                setData([]);
            } finally {
                setLoading(false);
            }
        };
        if (policyId) fetchLinked();
    }, [policyId]);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="lpm-tooltip-container">
                    <p className="lpm-tooltip-label">Policy: <strong>{label}</strong></p>
                    <div className="lpm-tooltip-content">
                        {payload.map((entry, index) => (
                            <p key={index} style={{ color: entry.color, margin: 0, fontSize: '0.875rem' }}>
                                {entry.name}: {entry.value} exact comments
                            </p>
                        ))}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="lpm-overlay" onClick={onClose}>
            <div className="lpm-modal" onClick={(e) => e.stopPropagation()}>
                <div className="lpm-header">
                    <div>
                        <h3>Sentiment Trend Comparison</h3>
                        <p className="lpm-subtitle">Historical sentiment analysis for linked policies related to {policyId}</p>
                    </div>
                    <button className="lpm-close-btn" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                <div className="lpm-body">
                    {loading ? (
                        <div className="lpm-empty-state">
                            <div className="lpm-loader"></div>
                            <p>Analyzing historical iterations...</p>
                        </div>
                    ) : error ? (
                        <div className="lpm-empty-state lpm-error">
                            <AlertCircle size={40} color="#e03131" />
                            <p>{error}</p>
                        </div>
                    ) : data.length < 2 ? (
                        <div className="lpm-empty-state">
                            <AlertCircle size={40} color="#adb5bd" />
                            <h4>No Ancestor Links Found</h4>
                            <p>This appears to be the first iteration of this policy. There is no historical data to chart.</p>
                        </div>
                    ) : (
                        <div className="lpm-chart-container">
                            <ResponsiveContainer width="100%" height={400}>
                                <LineChart
                                    data={data}
                                    margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9ecef" />
                                    <XAxis
                                        dataKey="id"
                                        tick={{ fontSize: 12, fill: '#495057' }}
                                        axisLine={{ stroke: '#dee2e6' }}
                                        tickLine={false}
                                        dy={10}
                                    />
                                    <YAxis
                                        tick={{ fontSize: 12, fill: '#495057' }}
                                        axisLine={{ stroke: '#dee2e6' }}
                                        tickLine={false}
                                        dx={-10}
                                    />
                                    <RechartsTooltip content={<CustomTooltip />} />
                                    <Legend
                                        verticalAlign="top"
                                        height={36}
                                        iconType="circle"
                                        wrapperStyle={{ fontSize: '14px', paddingTop: '10px' }}
                                    />

                                    <Line
                                        type="monotone"
                                        dataKey="positive"
                                        name="Positive Comments"
                                        stroke="#0ca678"
                                        strokeWidth={3}
                                        dot={{ r: 6, fill: "#0ca678", strokeWidth: 2, stroke: "#fff" }}
                                        activeDot={{ r: 8 }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="neutral"
                                        name="Neutral Comments"
                                        stroke="#868e96"
                                        strokeWidth={3}
                                        dot={{ r: 6, fill: "#868e96", strokeWidth: 2, stroke: "#fff" }}
                                        activeDot={{ r: 8 }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="negative"
                                        name="Negative Comments"
                                        stroke="#e03131"
                                        strokeWidth={3}
                                        dot={{ r: 6, fill: "#e03131", strokeWidth: 2, stroke: "#fff" }}
                                        activeDot={{ r: 8 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                            <div className="lpm-chart-footer">
                                <p>Click on legend items to toggle their visibility. Showing chronological iterations from left to right.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LinkedPoliciesModal;
