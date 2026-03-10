import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useLocation } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
    const location = useLocation();
    const [history, setHistory] = useState([]);
    const [user, setUser] = useState('');
    const [view, setView] = useState('history'); // 'history', 'safe', 'unsafe', 'account'
    const [stats, setStats] = useState({ total: 0, safe: 0, unsafe: 0 });
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');
    const [showAbout, setShowAbout] = useState(false);
    const [showHelp, setShowHelp] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);

    // Ensure cookies are sent with every request
    axios.defaults.withCredentials = true;

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const viewParam = queryParams.get('view');
        if (viewParam === 'account') {
            setView('account');
        }
        fetchDashboardData();
    }, [location]);

    const fetchDashboardData = async () => {
        setFetching(true);
        try {
            const res = await axios.get('http://localhost:5000/dashboard');
            const data = res.data.history || [];
            setUser(res.data.user);
            setHistory(data);

            // Calculate Stats
            setStats({
                total: data.length,
                safe: data.filter(h => h.safety_status === 'Safe' || h.safety_status.includes('SAFE')).length,
                unsafe: data.filter(h => h.safety_status !== 'Safe' && !h.safety_status.includes('SAFE')).length
            });

            setFetching(false);
        } catch (err) {
            if (err.response?.status === 401) {
                window.location.href = '/login';
            } else {
                setFetching(false);
                setError("Connection failure.");
            }
        }
    };

    const handleLogout = async () => {
        try {
            await axios.get('http://localhost:5000/logout');
            window.location.href = '/login';
        } catch (err) {
            window.location.href = '/login';
        }
    };

    const filteredHistory = history.filter(item => {
        if (view === 'safe') return item.safety_status === 'Safe' || item.safety_status.includes('SAFE');
        if (view === 'unsafe') return item.safety_status !== 'Safe' && !item.safety_status.includes('SAFE');
        return true;
    });

    if (fetching || error) {
        return (
            <div className="dashboard-wrapper loading-center">
                <div className="bg-canvas">
                    <div className="orb orb-1"></div>
                    <div className="orb orb-2"></div>
                </div>
                <div className="brand-mark">D</div>
                <p>{error || "Fetching History..."}</p>
            </div>
        );
    }

    return (
        <div className="dashboard-layout">
            <aside className="dash-sidebar">
                <div className="sidebar-brand">
                    <Link to="/" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div className="brand-mark">D</div>
                        <span>Aegis: The Dark-Pattern Detector</span>
                    </Link>
                </div>

                <div className="sidebar-user-profile">
                    <div className="sidebar-avatar">{user.charAt(0).toUpperCase()}</div>
                    <div className="sidebar-user-name">{user}</div>
                </div>

                <div className="sidebar-nav">
                    <button
                        className={`nav-btn ${view === 'history' ? 'active' : ''} `}
                        onClick={() => setView('history')}
                    >
                        <span className="icon">📊</span>
                        Full History
                        <span className="count">{stats.total}</span>
                    </button>
                    <button
                        className={`nav-btn ${view === 'safe' ? 'active' : ''} `}
                        onClick={() => setView('safe')}
                    >
                        <span className="icon">🛡️</span>
                        Safe Sites
                        <span className="count safe">{stats.safe}</span>
                    </button>
                    <button
                        className={`nav-btn ${view === 'unsafe' ? 'active' : ''} `}
                        onClick={() => setView('unsafe')}
                    >
                        <span className="icon">🚨</span>
                        Threats Blocked
                        <span className="count unsafe">{stats.unsafe}</span>
                    </button>
                    <button
                        className={`nav-btn ${view === 'account' ? 'active' : ''} `}
                        onClick={() => setView('account')}
                    >
                        <span className="icon">👤</span>
                        Account Settings
                    </button>
                    <Link to="/scraper" className="nav-btn" style={{ textDecoration: 'none' }}>
                        <span className="icon">🌐</span>
                        Web Scraper
                    </Link>
                </div>

                <div className="sidebar-footer">
                    <button className="logout-btn" onClick={handleLogout}>🚪 Logout</button>
                </div>
            </aside>

            <main className="dash-content">
                <header className="content-header">
                    <h2>
                        {view === 'history' && 'Security Audit Log'}
                        {view === 'safe' && 'Verified Safe Vault'}
                        {view === 'unsafe' && 'Detected Threats Archive'}
                        {view === 'account' && 'Account Management'}
                    </h2>
                    <Link to="/analyze" className="btn-new-scan">🔍 Deep Scan Analyzer</Link>
                </header>

                {view === 'account' ? (
                    <div className="account-view fade-in">
                        <div className="account-grid">
                            <div className="account-card main-profile">
                                <div className="profile-header">
                                    <div className="avatar">{user.charAt(0).toUpperCase()}</div>
                                    <div className="profile-meta">
                                        <h3>{user}</h3>
                                        <p className="status-verified">Verified Security Member</p>
                                    </div>
                                </div>
                            </div>

                            <div className="settings-menu">
                                <button className="menu-tile" onClick={() => setView('history')}>
                                    <span className="icon">📊</span>
                                    <div className="tile-info">
                                        <strong>Dashboard</strong>
                                        <p>Return to your security overview and logs.</p>
                                    </div>
                                    <span className="chevron">→</span>
                                </button>

                                <div className={`menu-accordion ${showNotifications ? 'expanded' : ''}`}>
                                    <button className="menu-tile" onClick={() => setShowNotifications(!showNotifications)}>
                                        <span className="icon">🔔</span>
                                        <div className="tile-info">
                                            <strong>Notifications</strong>
                                            <p>Manage security alerts and system updates.</p>
                                        </div>
                                        <span className={`chevron ${showNotifications ? 'rotate' : ''}`}>→</span>
                                    </button>

                                    {showNotifications && (
                                        <div className="accordion-content fade-in">
                                            <div className="accordion-section">
                                                <h4>Push Alerts</h4>
                                                <p>Get instantly notified when Aegis detects a high-risk manipulative pattern.</p>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px', cursor: 'pointer' }}>
                                                    <input type="checkbox" defaultChecked />
                                                    <span style={{ opacity: 0.8, fontSize: '14px' }}>Enable Push Notifications</span>
                                                </label>
                                            </div>
                                            <div className="accordion-section">
                                                <h4>Email Summaries</h4>
                                                <p>Receive a weekly digest of your Dark Pattern scan logs and trust score changes.</p>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px', cursor: 'pointer' }}>
                                                    <input type="checkbox" />
                                                    <span style={{ opacity: 0.8, fontSize: '14px' }}>Enable Weekly Emails</span>
                                                </label>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className={`menu-accordion ${showHelp ? 'expanded' : ''}`}>
                                    <button className="menu-tile" onClick={() => setShowHelp(!showHelp)}>
                                        <span className="icon">❓</span>
                                        <div className="tile-info">
                                            <strong>Help / Support</strong>
                                            <p>Get assistance or read our documentation.</p>
                                        </div>
                                        <span className={`chevron ${showHelp ? 'rotate' : ''}`}>→</span>
                                    </button>

                                    {showHelp && (
                                        <div className="accordion-content fade-in">
                                            <div className="accordion-section">
                                                <h4>How to use Deep Scan</h4>
                                                <p>Navigate to the "Deep Scan Analyzer" via the top right button or from your client home. Paste any e-commerce product URL or raw text snippet, and Aegis will detect pressure tactics mathematically.</p>
                                            </div>
                                            <div className="accordion-section">
                                                <h4>Report False Positives</h4>
                                                <p>If Aegis wrongly flagged a safe site as "manipulative," you can soon report it in your Audit History. This helps train our neural engine to reduce false positives.</p>
                                            </div>
                                            <div className="accordion-section">
                                                <h4>Contact Security Team</h4>
                                                <p>Email <strong>support@aegis-scanner.io</strong> for enterprise integration guides or manual review requests.</p>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className={`menu-accordion ${showAbout ? 'expanded' : ''}`}>
                                    <button className="menu-tile" onClick={() => setShowAbout(!showAbout)}>
                                        <span className="icon">ℹ️</span>
                                        <div className="tile-info">
                                            <strong>About & Privacy Policy</strong>
                                            <p>Aegis Version 2.4.0 (Production Build) & Data Handling.</p>
                                        </div>
                                        <span className={`chevron ${showAbout ? 'rotate' : ''}`}>→</span>
                                    </button>

                                    {showAbout && (
                                        <div className="accordion-content fade-in">
                                            <div className="accordion-section">
                                                <h4>About Aegis</h4>
                                                <p>Aegis: The Dark-Pattern Detector is an advanced neural engine designed to proactively identify and neutralize manipulative web elements, protecting your psychological agency online.</p>
                                            </div>
                                            <div className="accordion-section">
                                                <h4>Privacy & Data Sovereignty</h4>
                                                <p>We run on a zero-trust architecture. Your scan logs and structural web data are processed securely. We explicitly do not track personal identifiers across sessions, and your vault data is not sold to any third-party marketing firms.</p>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <button className="menu-tile logout-tile" onClick={handleLogout}>
                                    <span className="icon">🚪</span>
                                    <div className="tile-info">
                                        <strong>Logout</strong>
                                        <p>Securely end your current session.</p>
                                    </div>
                                    <span className="chevron">→</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="audit-table-container fade-in">
                        {filteredHistory.length > 0 ? (
                            <table className="audit-table">
                                <thead>
                                    <tr>
                                        <th>Status</th>
                                        <th>Method</th>
                                        <th>Target</th>
                                        <th>Trust Index</th>
                                        <th>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredHistory.map((item, idx) => (
                                        <tr key={idx} className="audit-row">
                                            <td>
                                                <div className={`audit-badge ${item.safety_status === 'Safe' || item.safety_status.includes('SAFE') ? 'safe' : 'unsafe'} `}>
                                                    {item.safety_status}
                                                </div>
                                            </td>
                                            <td><span className="method-tag">{item.type.toUpperCase()}</span></td>
                                            <td className="target-cell">{item.url !== 'N/A' ? item.url : 'Fragment Analysis'}</td>
                                            <td>
                                                <div className="trust-cell">
                                                    <div className="mini-bar-bg"><div className="mini-bar-fill" style={{ width: `${item.trust_score}% ` }}></div></div>
                                                    <span>{item.trust_score}%</span>
                                                </div>
                                            </td>
                                            <td className="time-cell">{item.timestamp}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="no-audit">
                                <p>No records found in this category.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
