import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Cookies from 'js-cookie';
import './Landing.css';

const LandingPage = () => {
    const isLoggedIn = !!Cookies.get('session') || !!Cookies.get('user');

    useEffect(() => {
        // App logic if needed later
    }, []);

    return (
        <div className="landing-wrapper">

            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
            </div>

            <nav className="navbar">
                <div className="brand">
                    <div className="brand-mark">D</div>
                    <span className="brand-name">Pattern Detection</span>
                </div>
                <div className="nav-links">
                    <a href="#features">Solutions</a>
                    <a href="#about">Research</a>
                    {isLoggedIn ? (
                        <>
                            <Link to="/dashboard" className="btn-auth btn-login">Dashboard</Link>
                            <Link to="/logout" className="btn-auth btn-signup">Logout</Link>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="btn-auth btn-login">Sign In</Link>
                            <Link to="/signup" className="btn-auth btn-signup">Join Now</Link>
                        </>
                    )}
                </div>
            </nav>

            <section className="hero">
                {isLoggedIn ? (
                    <div className="client-welcome-section fade-in">
                        <h1 className="hero-title">
                            Security Console: <em>{Cookies.get('user') || 'User'}</em>
                        </h1>
                        <p className="hero-subtitle">
                            Welcome to your unified protection hub. Monitor your history,
                            verify mysterious links, and analyze suspicious text patterns
                            using our aegis detection engine.
                        </p>
                        <div className="hero-btns" style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginTop: '30px' }}>
                            <Link to="/analyze" className="btn-auth btn-hero">Start Analysis Tool →</Link>
                            <Link to="/dashboard" className="btn-auth btn-login" style={{ padding: '20px 40px', borderRadius: '40px' }}>View History Logs</Link>
                        </div>

                        <div className="client-options-grid" style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(3, 1fr)',
                            gap: '25px',
                            marginTop: '80px',
                            textAlign: 'left'
                        }}>
                            <div className="option-card" style={{ background: 'rgba(255,255,255,0.03)', padding: '30px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '32px', marginBottom: '15px' }}>🌐</div>
                                <h4 style={{ fontSize: '20px', marginBottom: '10px' }}>Domain Reputation</h4>
                                <p style={{ fontSize: '14px', opacity: 0.6 }}>Check if a domain is blacklisted or flagged by global security databases.</p>
                                <Link to="/analyze" style={{ color: '#c4562a', textDecoration: 'none', fontSize: '14px', fontWeight: '600', marginTop: '15px', display: 'block' }}>Launch Scan →</Link>
                            </div>
                            <div className="option-card" style={{ background: 'rgba(255,255,255,0.03)', padding: '30px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '32px', marginBottom: '15px' }}>💬</div>
                                <h4 style={{ fontSize: '20px', marginBottom: '10px' }}>NLP Pattern Check</h4>
                                <p style={{ fontSize: '14px', opacity: 0.6 }}>Our AI analyzes text for manipulative linguistic patterns used by scammers.</p>
                                <Link to="/analyze" style={{ color: '#c4562a', textDecoration: 'none', fontSize: '14px', fontWeight: '600', marginTop: '15px', display: 'block' }}>Paste Text →</Link>
                            </div>
                            <div className="option-card" style={{ background: 'rgba(255,255,255,0.03)', padding: '30px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ fontSize: '32px', marginBottom: '15px' }}>🕒</div>
                                <h4 style={{ fontSize: '20px', marginBottom: '10px' }}>Recent Archive</h4>
                                <p style={{ fontSize: '14px', opacity: 0.6 }}>Access your last 10 security reports and verified safety statuses.</p>
                                <Link to="/dashboard" style={{ color: '#c4562a', textDecoration: 'none', fontSize: '14px', fontWeight: '600', marginTop: '15px', display: 'block' }}>Open Logs →</Link>
                            </div>
                        </div>
                    </div>
                ) : (
                    <>
                        <h1 className="hero-title">
                            Detect Dark <em>Patterns</em><br />With Precision.
                        </h1>
                        <p className="hero-subtitle">
                            The world's most advanced AI-driven scanner for deceptive design.
                            Protect your users from manipulative interfaces and data extraction.
                        </p>
                        <Link to="/login" className="btn-auth btn-hero">Start Security Scan →</Link>
                    </>
                )}
            </section>

            <section className="features" id="features">
                <div className="feature-card">
                    <div className="feature-icon">🔍</div>
                    <h3>Aegis Scan</h3>
                    <p>Multi-layered heuristic analysis for 15+ categories of deceptive design.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">🛡️</div>
                    <h3>Trust Guard</h3>
                    <p>Real-time protection scoring for e-commerce and SaaS platforms.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">📊</div>
                    <h3>Evidence Lab</h3>
                    <p>Exportable detailed reports with specific pattern documentation and remediation.</p>
                </div>
            </section>

            <footer className="footer">
                <p>&copy; 2026 Dark Pattern Detection Research Lab. All Rights Reserved.</p>
            </footer>
        </div>
    );
};

export default LandingPage;
