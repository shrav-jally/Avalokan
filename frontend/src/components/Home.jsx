import React from 'react';

const Home = () => {
    return (
        <div className="view-home">
            <div className="page-header">
                <div className="header-text">
                    <h2>Welcome to Avalokan</h2>
                    <p>Your centralized dashboard for government e-consultation analytics and sentiment tracking.</p>
                </div>
            </div>

            <div className="home-dashboard-grid">
                <div className="panel-white notification-panel">
                    <h3>Recent Notifications</h3>
                    <ul className="notification-list">
                        <li className="notification-item">
                            <span className="dot dot-new"></span>
                            <div className="notif-content">
                                <strong>New Draft Released</strong>
                                <p>The 'National Cyber Security Protocol v2' is now open for public consultation.</p>
                                <span className="timestamp">2 hours ago</span>
                            </div>
                        </li>
                        <li className="notification-item">
                            <span className="dot dot-urgent"></span>
                            <div className="notif-content">
                                <strong>Urgent: Feedback Deadline</strong>
                                <p>Public comments for 'Green Energy Initiative' close in 24 hours.</p>
                                <span className="timestamp">Yesterday</span>
                            </div>
                        </li>
                        <li className="notification-item">
                            <span className="dot dot-normal"></span>
                            <div className="notif-content">
                                <strong>System Update</strong>
                                <p>Sentiment analysis engine updated to v4.5 with improved vernacular support.</p>
                                <span className="timestamp">3 days ago</span>
                            </div>
                        </li>
                    </ul>
                </div>

                <div className="panel-white stats-highlight-panel">
                    <h3>Popular Draft Statistics</h3>
                    <div className="popular-draft">
                        <div className="draft-header">
                            <h4>Digital Personal Data Protection Bill</h4>
                            <span className="trending-tag">🔥 Trending</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Total Comments</span>
                            <span className="stat-val">12,450</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Engagement Rate</span>
                            <span className="stat-val">High (85%)</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Dominant Sentiment</span>
                            <span className="stat-val text-pos">Positive</span>
                        </div>
                    </div>

                    <div className="popular-draft">
                        <div className="draft-header">
                            <h4>Urban Mobility Reform</h4>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Total Comments</span>
                            <span className="stat-val">8,200</span>
                        </div>
                        <div className="stat-row">
                            <span className="stat-label">Dominant Sentiment</span>
                            <span className="stat-val text-neg">Negative</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
