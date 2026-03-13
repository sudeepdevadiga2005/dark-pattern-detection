import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { Link } from 'react-router-dom';
import './Analyze.css';

// Device Detection Utility
function detectDeviceType() {
    const ua = navigator.userAgent.toLowerCase();
    if (/iphone|ipod|android.*mobile|windows phone|blackberry/i.test(ua)) return 'mobile';
    if (/ipad|android(?!.*mobile)|tablet/i.test(ua)) return 'tablet';
    if (/macintosh|windows|linux/i.test(ua) && window.innerWidth <= 1024) return 'tablet';
    return 'desktop';
}

function getLayoutFromWidth(w) {
    if (w <= 768) return 'mobile';
    if (w <= 1024) return 'tablet';
    return 'desktop';
}

const Analyze = () => {
    const [activeTab, setActiveTab] = useState('url');
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [user, setUser] = useState('');
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');
    const [deviceInfo, setDeviceInfo] = useState({ type: 'desktop', layout: 'desktop' });

    axios.defaults.withCredentials = true;

    // Detect device and send to backend on mount + window resize
    useEffect(() => {
        const sendDeviceInfo = async () => {
            const type = detectDeviceType();
            const width = window.innerWidth;
            const layout = getLayoutFromWidth(width);
            setDeviceInfo({ type, layout });

            try {
                await axios.post(`${API_BASE_URL}/detect-device`, {
                    device_type: type,
                    screen_width: width
                });
            } catch (e) {
                console.log('Device detection API unavailable');
            }
        };

        sendDeviceInfo();

        const handleResize = () => {
            const layout = getLayoutFromWidth(window.innerWidth);
            setDeviceInfo(prev => ({ ...prev, layout }));
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/dashboard`);
                setUser(res.data.user);
                setFetching(false);
            } catch (err) {
                if (err.response?.status === 401) {
                    window.location.href = '/login';
                } else {
                    setFetching(false);
                    setError("Connection error.");
                }
            }
        };
        fetchUserData();
    }, []);

    const handleAnalyze = async (e) => {
        e.preventDefault();
        if (!inputValue) return;

        setIsLoading(true);
        setResult(null);

        try {
            const endpoint = activeTab === 'url' ? '/analyze' : '/analyze-text';
            const payload = activeTab === 'url' ? { url: inputValue } : { text: inputValue };

            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
            setResult(res.data);
        } catch (err) {
            const errorMsg = err.response?.data?.error || "Analysis failed. The server might be busy or the model is retraining. Please try again in 10 seconds.";
            alert(errorMsg);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = async () => {
        try {
            await axios.get(`${API_BASE_URL}/logout`);
            window.location.href = '/login';
        } catch (err) {
            window.location.href = '/login';
        }
    };

    if (fetching || error) {
        return <div className="loading-screen">{error || "Loading Aegis: The Dark-Pattern Detector..."}</div>;
    }

    const isMobile = deviceInfo.layout === 'mobile';
    const isTablet = deviceInfo.layout === 'tablet';

    return (
        <div className={`analyze-wrapper layout-${deviceInfo.layout}`}>
            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
            </div>

            <nav className="dash-nav">
                <div className="brand">
                    <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: isMobile ? '8px' : '15px' }}>
                        <div className="brand-mark">D</div>
                        {!isMobile && <span className="brand-name">Aegis: The Dark-Pattern Detector</span>}
                    </Link>
                </div>
                <div className="user-profile">
                    {!isMobile && <Link to="/dashboard" className="nav-link-item">My History</Link>}
                    <span className="user-name">{isMobile ? user : `Welcome, ${user}`}</span>
                    <button className="btn-logout" onClick={handleLogout}>{isMobile ? '⏻' : 'Logout'}</button>
                </div>
            </nav>

            {/* Device info badge */}
            <div className="device-badge">
                {deviceInfo.type === 'mobile' ? '📱' : deviceInfo.type === 'tablet' ? '📟' : '💻'} {deviceInfo.layout.toUpperCase()} VIEW
            </div>

            <main className="analyze-main">
                <div className="analyzer-card">
                    <h2 className="tool-title">Dark Pattern Analyzer</h2>
                    <div className="switcher">
                        <button
                            className={activeTab === 'url' ? 'active' : ''}
                            onClick={() => setActiveTab('url')}
                        >Website URL</button>
                        <button
                            className={activeTab === 'text' ? 'active' : ''}
                            onClick={() => setActiveTab('text')}
                        >Raw Text</button>
                    </div>

                    <form onSubmit={handleAnalyze} className="analyzer-form">
                        {activeTab === 'url' ? (
                            <div className="input-group">
                                <input
                                    type="text"
                                    placeholder={isMobile ? "Enter URL..." : "Enter website URL (e.g. amazon.in)"}
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    required
                                />
                                <div className="input-bar"></div>
                            </div>
                        ) : (
                            <div className="input-group">
                                <textarea
                                    placeholder="Paste content here to detect manipulative language..."
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    required
                                ></textarea>
                                <div className="input-bar"></div>
                            </div>
                        )}
                        <button className={`btn-analyze ${isLoading ? 'loading' : ''}`} type="submit" disabled={isLoading}>
                            {isLoading ? 'Scanning Patterns...' : (isMobile ? 'Analyze →' : 'Run Deep Scan →')}
                        </button>
                    </form>

                    {isMobile && (
                        <Link to="/dashboard" className="mobile-history-link">📊 View Scan History</Link>
                    )}
                </div>

                {result && (
                    <div className={`result-card fade-in ${result.success ? '' : 'error'}`}>
                        {!result.success ? (
                            <div className="error-content">
                                <h3>Scan Interrupted</h3>
                                <p>{result.error}</p>
                            </div>
                        ) : (
                            <div className="success-content">
                                <div className="result-header">
                                    <div className="summary-left">
                                        <h3>Execution Summary</h3>
                                        <div className={`safety-badge ${result.safety_status.includes('Safe') || result.safety_status.includes('SAFE') ? 'safe' : 'warning'}`}>
                                            {result.safety_status}
                                        </div>
                                    </div>
                                    <div className="trust-meter">
                                        <div className="meter-val">{result.trust_score}%</div>
                                        <span>Trust Score</span>
                                    </div>
                                </div>

                                {result.security_warning && (
                                    <div className="security-alert-box bounce">
                                        <strong>🚨 SECURITY ALERT:</strong> {result.security_warning}
                                    </div>
                                )}

                                {result.web_intelligence && (
                                    <div className="intelligence-box">
                                        <div className="intel-label">Aegis Intelligence</div>
                                        <p>{result.web_intelligence}</p>
                                    </div>
                                )}

                                <div className="result-stats">
                                    <div className="stat-card">
                                        <div className="val">{result.total_patterns_found}</div>
                                        <div className="lbl">Patterns</div>
                                    </div>
                                    <div className="stat-card">
                                        <div className="val">{result.findings?.length || 0}</div>
                                        <div className="lbl">Categories</div>
                                    </div>
                                </div>

                                {result.findings?.length > 0 && (
                                    <div className="findings-list">
                                        <h4>Detected Patterns</h4>
                                        <div className="pills">
                                            {result.findings.map((f, i) => (
                                                <div key={i} className="finding-pill">
                                                    {f.category}: <strong>{f.count}</strong>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default Analyze;
