import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
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
import DraftManagement from './components/DraftManagement';

import LandingPage from './pages/LandingPage';
import OnboardingForm from './pages/OnboardingForm';
import ConsumerHome from './pages/ConsumerHome';
// import DraftManagement from './components/DraftManagement';

// Configure Axios to always send credentials
axios.defaults.withCredentials = true;

function App() {
  const location = useLocation();
  const navigate = useNavigate();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [stakeholderType, setStakeholderType] = useState('');

  const [activeTab, setActiveTab] = useState('home');
  const [metrics, setMetrics] = useState(null);
  const [globalData, setGlobalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [userRole, setUserRole] = useState('user');

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:5000/api/auth/logout');
    } catch(e) { console.error('Logout error:', e); }
    setIsAuthenticated(false);
    setUserRole(null);
    setNeedsOnboarding(false);
    navigate('/');
  };

  // URL Path Synchronization
  useEffect(() => {
    const path = location.pathname;
    
    if (!isAuthChecking) {
      if (!isAuthenticated && path !== '/') {
        navigate('/');
        return;
      }
      
      if (isAuthenticated) {
        if (needsOnboarding && path !== '/onboarding') {
          navigate('/onboarding');
          return;
        }
        
        if (!needsOnboarding) {
          if (userRole === 'admin' && !path.startsWith('/admin')) {
            navigate('/admin/dashboard');
            return;
          }
          if (userRole === 'consumer' && path !== '/consumer/home') {
            navigate('/consumer/home');
            return;
          }
        }
      }
    }

    if (path.startsWith('/admin/policy/')) {
        const id = path.split('/')[3];
        if (id && (!selectedPolicy || selectedPolicy.id !== id)) {
            setSelectedPolicy({ id });
            setActiveTab('policies');
        }
    } else if (path === '/admin/dashboard') {
        setActiveTab('dashboard');
    } else if (path === '/admin/global') {
        setActiveTab('global');
    } else if (path === '/admin/draftManagement') {
        setActiveTab('draftManagement');
    } else if (path === '/admin/home' || path === '/admin') {
        setActiveTab('home');
    }
  }, [location.pathname, isAuthChecking, isAuthenticated, needsOnboarding, userRole]);

  useEffect(() => {
    // Check Authentication Status
    const checkAuth = async () => {
      try {
        const res = await axios.get('http://localhost:5000/api/auth/status');
        if (res.data.isAuthenticated) {
          setIsAuthenticated(true);
          setUserRole(res.data.role || 'user');
          setNeedsOnboarding(res.data.needsOnboarding || false);
          setStakeholderType(res.data.stakeholderType || '');
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
          axios.get('http://localhost:5000/api/analytics/global').catch(() => ({data: {volumeData: [], trendData: [], totalComments: 0}}))
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

        const MOCK_GLOBAL_DATA = {
            totalComments: 14200,
            volumeData: [
                { draft_id: "D-2026-012", name: "Coastal Protection Regulation", total_comments: 4200 },
                { draft_id: "D-2026-011", name: "Electronic ID Standards", total_comments: 1200 },
                { draft_id: "D-2026-010", name: "Public Health Bill v1.2", total_comments: 2450 },
                { draft_id: "D-2026-009", name: "Urban Transport Policy", total_comments: 1820 },
                { draft_id: "D-2026-008", name: "Data Privacy Framework", total_comments: 3100 }
            ],
            trendData: [
                { name: "Jan", positive: 65, neutral: 20, negative: 15 },
                { name: "Feb", positive: 68, neutral: 22, negative: 10 }
            ]
        };

        setMetrics(MOCK_METRICS);
        setGlobalData(MOCK_GLOBAL_DATA);
        setError('Backend unavailable: ' + (err.response?.data?.message || err.message));
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
    return <LandingPage />;
  }

  if (needsOnboarding) {
    return <OnboardingForm onComplete={(type) => {
      setStakeholderType(type);
      setNeedsOnboarding(false);
      setUserRole('consumer'); 
      navigate('/consumer/home');
    }} />;
  }

  if (userRole === 'consumer') {
    return <ConsumerHome onLogout={handleLogout} />;
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
    if (tab === 'home') navigate('/admin/home');
    else navigate(`/admin/${tab}`);
  };



  return (
    <div className="app-container">
      <Header onLogout={handleLogout} />
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
                  userRole={userRole}
                  onBack={() => {
                      setSelectedPolicy(null);
                      navigate('/admin/policies');
                  }}
                />
              ) : (
                <PoliciesList
                  onSelectPolicy={(policy) => {
                      setSelectedPolicy(policy);
                      navigate(`/admin/policy/${policy.id}`);
                  }}
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
                <CommentVolumeChart data={globalData.volumeData || []} loading={loading} />
                <SentimentTrendLineChart data={globalData.trendData || []} loading={loading} />
                <div className="formal-chart-note">
                  <p>“Higher comment volume indicates increased stakeholder engagement and potential impact of draft provisions.”</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'draftManagement' && (
            <DraftManagement />
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
