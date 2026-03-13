import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { Link } from 'react-router-dom';
import './Analyze.css';

const Analyze = () => {
    const [activeTab, setActiveTab] = useState('url'); // 'url' or 'text'
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [user, setUser] = useState('');
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');

    // Ensure cookies are sent with every request
    axios.defaults.withCredentials = true;

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

    return (
        <div className="analyze-wrapper">
            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
            </div>

            <nav className="dash-nav">
                <div className="brand">
                    <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div className="brand-mark">D</div>
                        <span className="brand-name">Aegis: The Dark-Pattern Detector</span>
                    </Link>
                </div>
                <div className="user-profile">
                    <Link to="/dashboard" className="nav-link-item">My History</Link>
                    <span className="user-name">Welcome, {user}</span>
                    <button className="btn-logout" onClick={handleLogout}>Logout</button>
                </div>
            </nav>

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
                                    placeholder="Enter website URL (e.g. amazon.in)"
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
                            {isLoading ? 'Scanning Patterns...' : 'Run Deep Scan →'}
                        </button>
                    </form>
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
                                        <div className="intel-label">Aegis: The Dark-Pattern Detector Intelligence</div>
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
