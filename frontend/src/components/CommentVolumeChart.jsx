import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

const CommentVolumeChart = ({ data, loading }) => {
    if (loading) return null;
    if (!data || data.length === 0) return null;

    // Sorting: Most engagement (total_comments) at the top
    const sortedData = [...data].sort((a, b) => b.total_comments - a.total_comments);

    const CustomYAxisTick = ({ x, y, payload }) => {
        return (
            <g transform={`translate(${x},${y})`}>
                <text
                    x={-10}
                    y={0}
                    dy={4}
                    textAnchor="end"
                    fill="#6c757d"
                    fontSize={11}
                    fontWeight={500}
                >
                    {payload.value}
                </text>
            </g>
        );
    };

    return (
        <div className="global-engagement-volume-only">
            <h3 className="section-title">Draft Engagement Volume (Sorted by Influence)</h3>
            <div className="recharts-wrapper-custom">
                <ResponsiveContainer width="100%" height={sortedData.length * 50 + 40}>
                    <BarChart
                        layout="vertical"
                        data={sortedData}
                        margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
                        barSize={20}
                    >
                        <XAxis
                            type="number"
                            tick={{ fontSize: 10, fill: '#adb5bd' }}
                            axisLine={{ stroke: '#dee2e6' }}
                            tickLine={false}
                        />
                        <YAxis
                            type="category"
                            dataKey="draft_id"
                            tick={<CustomYAxisTick />}
                            axisLine={false}
                            tickLine={false}
                            width={100}
                        />
                        <Tooltip
                            cursor={{ fill: '#f8f9fa' }}
                            contentStyle={{
                                borderRadius: '0px',
                                border: '1px solid #dee2e6',
                                fontSize: '12px',
                                boxShadow: 'none'
                            }}
                        />
                        <Bar dataKey="total_comments" fill="var(--chart-bar-bg)">
                            {sortedData.map((entry, index) => (
                                <Cell key={`cell-${index}`} radius={[0, 2, 2, 0]} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default CommentVolumeChart;
