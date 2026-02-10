import React from 'react';

const SentimentTrendChart = ({ drafts }) => {
    if (!drafts || drafts.length === 0) return null;

    // X-axis: Drafts (newest to oldest - backend already sends them in some order, 
    // assume newest is first so we just use the array)
    // Max comments for scaling Y
    const maxVal = Math.max(
        ...drafts.map(d => Math.max(d.sentiment.pos, d.sentiment.neu, d.sentiment.neg))
    );

    const padding = 40;
    const widthPerDraft = 120;
    const chartHeight = 250;
    const chartWidth = drafts.length * widthPerDraft;

    const getY = (val) => chartHeight - (val / maxVal) * (chartHeight - padding) - padding;
    const getX = (index) => index * widthPerDraft + padding;

    const points = (type) => drafts.map((d, i) => `${getX(i)},${getY(d.sentiment[type])}`).join(' ');

    return (
        <div className="trend-section">
            <h3 className="section-title">Draft-wise Sentiment Trends</h3>

            <div className="chart-legend standalone">
                <div className="legend-item"><span className="dot line pos"></span> Positive</div>
                <div className="legend-item"><span className="dot line neu"></span> Neutral</div>
                <div className="legend-item"><span className="dot line neg"></span> Negative</div>
            </div>

            <div className="horizontal-scroll-container">
                <svg width={chartWidth} height={chartHeight} className="trend-line-chart">
                    {/* Grid lines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
                        <line
                            key={i}
                            x1={padding}
                            y1={getY(maxVal * p)}
                            x2={chartWidth}
                            y2={getY(maxVal * p)}
                            stroke="#eee"
                        />
                    ))}

                    {/* Positive Line */}
                    <polyline
                        fill="none"
                        stroke="var(--sentiment-pos)"
                        strokeWidth="2"
                        points={points('pos')}
                    />
                    {/* Neutral Line */}
                    <polyline
                        fill="none"
                        stroke="var(--sentiment-neu)"
                        strokeWidth="2"
                        points={points('neu')}
                    />
                    {/* Negative Line */}
                    <polyline
                        fill="none"
                        stroke="var(--sentiment-neg)"
                        strokeWidth="2"
                        points={points('neg')}
                    />

                    {/* Points and Labels */}
                    {drafts.map((draft, i) => (
                        <g key={draft.id}>
                            <text
                                x={getX(i)}
                                y={chartHeight - 5}
                                fontSize="10"
                                textAnchor="middle"
                                fill="#6c757d"
                            >
                                {draft.id}
                            </text>
                            {/* Data points */}
                            <circle cx={getX(i)} cy={getY(draft.sentiment.pos)} r="3" fill="var(--sentiment-pos)" />
                            <circle cx={getX(i)} cy={getY(draft.sentiment.neu)} r="3" fill="var(--sentiment-neu)" />
                            <circle cx={getX(i)} cy={getY(draft.sentiment.neg)} r="3" fill="var(--sentiment-neg)" />
                        </g>
                    ))}
                </svg>
            </div>

            <div className="interpretive-caption">
                <p><strong>Interpretive Analysis:</strong> This visualization tracks the evolution of public sentiment across successive versions of policy drafts. Fluctuations in line positions indicate significant shifts in public response, often correlating with major amendments or policy updates. Newer drafts (left-most) are prioritized for immediate administrative monitoring.</p>
            </div>
        </div>
    );
};

export default SentimentTrendChart;
