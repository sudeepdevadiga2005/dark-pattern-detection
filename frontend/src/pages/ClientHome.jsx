import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import Cookies from 'js-cookie';
import { 
    Shield, 
    Search, 
    History, 
    User, 
    LogOut, 
    Zap, 
    AlertTriangle, 
    CheckCircle2, 
    Globe, 
    FileText,
    TrendingUp,
    ShieldCheck
} from 'lucide-react';
import './ClientHome.css';

const ClientHome = () => {
    const [user, setUser] = useState(Cookies.get('user') || 'User');
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState({
        totalScans: 0,
        threatsDetected: 0,
        trustScore: 0,
        riskLevel: 'Calculating...'
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        document.title = 'Aegis Secure Console';
        const fetchData = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/dashboard`);
                setUser(res.data.user || Cookies.get('user') || 'User');
                const hData = res.data.history || [];
                setHistory(hData);
                
                // Calculate Stats
                const threats = hData.filter(item => 
                    item.safety_status && item.safety_status.toLowerCase() === 'unsafe'
                ).length;
                
                const avgTrust = hData.length > 0 
                    ? Math.round(hData.reduce((acc, curr) => acc + (curr.trust_score || 0), 0) / hData.length)
                    : 100;

                let risk = 'Low';
                if (avgTrust < 50) risk = 'High';
                else if (avgTrust < 80) risk = 'Medium';

                setStats({
                    totalScans: hData.length,
                    threatsDetected: threats,
                    trustScore: avgTrust,
                    riskLevel: hData.length > 0 ? risk : 'Low'
                });

            } catch (err) {
                console.error("Session verification failed", err);
                Cookies.remove('user');
                window.location.href = '/login';
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleLogout = async () => {
        try {
            await axios.get(`${API_BASE_URL}/logout`);
            Cookies.remove('user');
            window.location.href = '/login';
        } catch (err) {
            Cookies.remove('user');
            window.location.href = '/login';
        }
    };

    if (isLoading) {
        return (
            <div className="aegis-loading">
                <div className="loader-inner">
                    <Shield className="loader-icon" size={40} />
                    <span>Establishing Secure Connection...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="aegis-home-wrapper">
            {/* Background Glows */}
            <div className="bg-glow bg-glow-1"></div>
            <div className="bg-glow bg-glow-2"></div>

            <nav className="aegis-navbar">
                <div className="nav-container">
                    <div className="nav-left">
                        <Link to="/" className="nav-logo">
                            <div className="logo-box">
                                <Shield className="logo-icon" size={24} />
                            </div>
                            <span>Aegis</span>
                        </Link>
                    </div>
                    <div className="nav-right">
                        <div className="nav-profile">
                            <div className="avatar-circle">
                                {(user || 'U').charAt(0).toUpperCase()}
                            </div>
                            <span className="user-name-small">{user || 'User'}</span>
                        </div>
                        <button onClick={handleLogout} className="nav-logout-btn">
                            <LogOut size={16} />
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            <main className="aegis-main-content">
                {/* Hero Section */}
                <section className="hero-section">
                    <div className="hero-badge">
                        <Zap size={14} />
                        AI-Powered Security Enabled
                    </div>
                    <h1>Aegis <em>Secure</em> Console</h1>
                    <p className="subtitle">Detect dark patterns instantly with AI-powered analysis.</p>
                    <p className="welcome-msg">Welcome back, <strong>{user}</strong></p>
                    
                    <div className="hero-actions">
                        <Link to="/analyze" className="btn-primary">
                            <Zap size={20} />
                            Start Analysis
                        </Link>
                    </div>
                </section>

                {/* Stats Grid */}
                <section className="stats-grid">
                    <div className="glass-card stat-card">
                        <div className="stat-icon-wrap blue">
                            <Search size={24} />
                        </div>
                        <div className="stat-info">
                            <label>Total Scans</label>
                            <h3>{stats.totalScans}</h3>
                        </div>
                    </div>
                    
                    <div className="glass-card stat-card">
                        <div className="stat-icon-wrap red">
                            <AlertTriangle size={24} />
                        </div>
                        <div className="stat-info">
                            <label>Threats Detected</label>
                            <h3 className="text-danger">{stats.threatsDetected}</h3>
                        </div>
                    </div>

                    <div className="glass-card stat-card">
                        <div className="stat-icon-wrap purple">
                            <ShieldCheck size={24} />
                        </div>
                        <div className="stat-info">
                            <label>Trust Score</label>
                            <h3>{stats.trustScore}%</h3>
                        </div>
                    </div>

                    <div className="glass-card stat-card">
                        <div className="stat-icon-wrap gold">
                            <TrendingUp size={24} />
                        </div>
                        <div className="stat-info">
                            <label>Risk Level</label>
                            <h3 className={`risk-${(stats.riskLevel || 'Low').toLowerCase()}`}>{stats.riskLevel}</h3>
                        </div>
                    </div>
                </section>

                {/* Main Action Cards */}
                <section className="action-row">
                    <Link to="/analyze" className="glass-card action-card">
                        <div className="action-visual animate-float">
                            <Globe size={48} className="text-primary" />
                        </div>
                        <div className="action-details">
                            <h3>Scan Website</h3>
                            <p>Deep-scan any e-commerce URL for manipulative design patterns and deceptive tactics.</p>
                            <span className="action-link">Launch Scanner →</span>
                        </div>
                    </Link>

                    <Link to="/dashboard" className="glass-card action-card">
                        <div className="action-visual animate-float delay-1">
                            <History size={48} className="text-accent" />
                        </div>
                        <div className="action-details">
                            <h3>View Analysis History</h3>
                            <p>Access your vault of previous security reports and review identified threats.</p>
                            <span className="action-link">Open Archive →</span>
                        </div>
                    </Link>
                </section>


            </main>

            <footer className="aegis-footer">
                <p>&copy; 2026 Aegis Secure Console. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default ClientHome;
