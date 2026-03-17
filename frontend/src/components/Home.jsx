import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Home = () => {
    const [notifications, setNotifications] = useState([]);
    const [popularStats, setPopularStats] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [notifRes, statsRes] = await Promise.all([
                    axios.get('http://localhost:5000/api/home/notifications'),
                    axios.get('http://localhost:5000/api/dashboard/detailed-metrics')
                ]);
                setNotifications(notifRes.data);
                setPopularStats(statsRes.data);
            } catch (err) {
                console.error('Error fetching home data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

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
                    {loading ? <p>Loading activity...</p> : (
                        <ul className="notification-list">
                            {notifications.length === 0 ? <li className="notification-item">No recent activity.</li> : (
                                notifications.map((notif, idx) => (
                                    <li key={idx} className="notification-item">
                                        <span className={`dot ${notif.class}`}></span>
                                        <div className="notif-content">
                                            <strong>{notif.title}</strong>
                                            <p>{notif.message}</p>
                                            <span className="timestamp">{notif.timestamp}</span>
                                        </div>
                                    </li>
                                ))
                            )}
                        </ul>
                    )}
                </div>

                <div className="panel-white stats-highlight-panel">
                    <h3>Popular Draft Statistics</h3>
                    {loading ? <p>Loading popular drafts...</p> : (
                        popularStats.length === 0 ? <p>No popular draft stats available.</p> : (
                            popularStats.map((stat, idx) => (
                                <div key={idx} className="popular-draft">
                                    <div className="draft-header">
                                        <h4>{stat.title}</h4>
                                        {idx === 0 && <span className="trending-tag">🔥 Trending</span>}
                                    </div>
                                    <div className="stat-row">
                                        <span className="stat-label">Total Comments</span>
                                        <span className="stat-val">{stat.comments.toLocaleString()}</span>
                                    </div>
                                    <div className="stat-row">
                                        <span className="stat-label">Sentiment Breakdown</span>
                                        <span className="stat-val" style={{fontSize: '0.75rem'}}>
                                            <span className="text-pos">Pos: {stat.sentiment.pos}</span> | 
                                            <span className="text-neu"> Neu: {stat.sentiment.neu}</span> | 
                                            <span className="text-neg"> Neg: {stat.sentiment.neg}</span>
                                        </span>
                                    </div>
                                </div>
                            ))
                        )
                    )}
                </div>
            </div>
        </div>
    );
};

export default Home;
