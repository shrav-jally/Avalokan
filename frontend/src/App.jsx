import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MetricCard from './components/MetricCard';
import CommentVolumeChart from './components/CommentVolumeChart';
import SentimentTrendLineChart from './components/SentimentTrendLineChart';

import PoliciesList from './components/PoliciesList';
import PolicyDetail from './components/PolicyDetail';
import Home from './components/Home';
import Login from './components/Login';

// Configure Axios to always send credentials
axios.defaults.withCredentials = true;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  const [activeTab, setActiveTab] = useState('home');
  const [metrics, setMetrics] = useState(null);
  const [globalData, setGlobalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPolicy, setSelectedPolicy] = useState(null);

  useEffect(() => {
    // Check Authentication Status
    const checkAuth = async () => {
      try {
        const res = await axios.get('http://localhost:5000/api/auth/status');
        if (res.data.isAuthenticated) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } catch (err) {
        setIsAuthenticated(false);
      } finally {
        setIsAuthChecking(false);
      }
    };
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const [metricsRes, globalRes] = await Promise.all([
          axios.get('http://localhost:5000/api/dashboard/metrics'),
          axios.get('http://localhost:5000/api/global/draft-comment-volume')
        ]);
        setMetrics(metricsRes.data);
        setGlobalData(globalRes.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching metrics:', err);
        // Fallback to mock data
        const MOCK_METRICS = {
          totalDrafts: 142,
          totalComments: 8540,
          activeConsultations: 24,
          sentimentDistribution: {
            positive: 45,
            neutral: 35,
            negative: 20
          }
        };

        const MOCK_GLOBAL_DATA = [
          { draft_id: "D-2026-012", draft_title: "Coastal Protection Regulation", total_comments: 4200, positive_count: 1512, neutral_count: 714, negative_count: 2016, release_order: 12 },
          { draft_id: "D-2026-011", draft_title: "Electronic ID Standards", total_comments: 1200, positive_count: 804, neutral_count: 300, negative_count: 96, release_order: 11 },
          { draft_id: "D-2026-010", draft_title: "Public Health Bill v1.2", total_comments: 2450, positive_count: 1200, neutral_count: 857, negative_count: 392, release_order: 10 },
          { draft_id: "D-2026-009", draft_title: "Urban Transport Policy", total_comments: 1820, positive_count: 600, neutral_count: 928, negative_count: 291, release_order: 9 },
          { draft_id: "D-2026-008", draft_title: "Data Privacy Framework", total_comments: 3100, positive_count: 1085, neutral_count: 713, negative_count: 1302, release_order: 8 }
        ];

        setMetrics(MOCK_METRICS);
        setGlobalData(MOCK_GLOBAL_DATA);
        setError('Backend unavailable. Showing demo data.');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  if (isAuthChecking) {
    return <div className="skeleton-container">Verifying Access...</div>;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  if (loading && !metrics) {
    return (
      <div className="skeleton-container">
        <p>Loading Government Analytics Dashboard...</p>
      </div>
    );
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedPolicy(null);
  };

  return (
    <div className="app-container">
      <Header />
      <div className="main-layout">
        <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />

        <main className="main-content">
          {activeTab === 'home' && <Home />}

          {activeTab === 'dashboard' && (
            <div className="view-dashboard">
              <div className="page-header">
                <div className="header-text">
                  <h2>Analytics Overview</h2>
                  <p>Summary of public consultation metrics for the current fiscal period.</p>
                </div>
                <div className="header-actions">
                  <span className="last-updated">Last synchronized: {new Date().toLocaleTimeString()}</span>
                </div>
              </div>

              {error && <div className="error-banner">{error}</div>}

              <div className="dashboard-grid">
                <MetricCard
                  label="Total Drafts"
                  value={metrics?.totalDrafts || 0}
                  subtext="Policies currently being drafted"
                />
                <MetricCard
                  label="Comments Received"
                  value={metrics?.totalComments?.toLocaleString() || 0}
                  subtext="Total unique public submissions"
                />
                <MetricCard
                  label="Active Consultations"
                  value={metrics?.activeConsultations || 0}
                  subtext="Ongoing open public hearings"
                />
                <MetricCard
                  label="Dominant Sentiment"
                  value="Positive"
                  subtext={`${metrics?.sentimentDistribution?.positive}% of total feedback`}
                />
              </div>

              <div className="sentiment-container">
                <div className="sentiment-header">
                  <h3>Overall Sentiment Distribution</h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    Aggregated sentiment analysis from all comments.
                  </p>
                </div>
                <div className="sentiment-bars">
                  <SentimentBar
                    label="Positive"
                    percentage={metrics?.sentimentDistribution?.positive}
                    color="var(--sentiment-pos)"
                  />
                  <SentimentBar
                    label="Neutral"
                    percentage={metrics?.sentimentDistribution?.neutral}
                    color="var(--sentiment-neu)"
                  />
                  <SentimentBar
                    label="Negative"
                    percentage={metrics?.sentimentDistribution?.negative}
                    color="var(--sentiment-neg)"
                  />
                </div>
              </div>
            </div>
          )}

          {(activeTab === 'consultations' || activeTab === 'policies') && (
            <div className="view-consultations">
              {selectedPolicy ? (
                <PolicyDetail
                  policy={selectedPolicy}
                  onBack={() => setSelectedPolicy(null)}
                />
              ) : (
                <PoliciesList
                  onSelectPolicy={(policy) => setSelectedPolicy(policy)}
                />
              )}
            </div>
          )}

          {activeTab === 'global' && (
            <div className="view-global-engagement">
              <div className="page-header">
                <div className="header-text">
                  <h2>Global Engagement Analytics</h2>
                  <p>In-depth analysis of stakeholder engagement across all policy drafts.</p>
                </div>
              </div>

              <div className="panel-white">
                <CommentVolumeChart data={globalData} loading={loading} />
                <SentimentTrendLineChart data={globalData} loading={loading} />
                <div className="formal-chart-note">
                  <p>“Higher comment volume indicates increased stakeholder engagement and potential impact of draft provisions.”</p>
                </div>
              </div>
            </div>
          )}

          {['reports', 'feedback', 'settings'].includes(activeTab) && (
            <div className="view-placeholder">
              <div className="page-header">
                <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
              </div>
              <div className="chart-loading-placeholder">
                <p>Module integration in progress. This section is currently under official review.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

const SentimentBar = ({ label, percentage, color }) => {
  return (
    <div className="sentiment-item">
      <div className="sentiment-label-row">
        <span>{label}</span>
        <span>{percentage}%</span>
      </div>
      <div className="sentiment-bar-bg">
        <div
          className="sentiment-bar-fill"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};

export default App;
