import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import Cookies from 'js-cookie';
import './ClientHome.css';

const ClientHome = () => {
    const [user, setUser] = useState(Cookies.get('user') || 'User');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        document.title = 'Dark Pattern Detector';
        const verifySession = async () => {
            try {
                // Ping a protected route to verify the session hasn't been invalidated
                const res = await axios.get(`${API_BASE_URL}/dashboard`);
                setUser(res.data.user);
                setIsLoading(false);
            } catch (err) {
                Cookies.remove('user');
                window.location.href = '/login';
            } finally {
                setIsLoading(false);
            }
        };
        verifySession();
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

    const [viewState, setViewState] = useState('portal'); // 'portal' or 'dashboard'
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const handleMouseMove = (e) => {
            setMousePos({ x: e.clientX, y: e.clientY });
        };
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    if (isLoading) {
        return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fff', color: '#000' }}>Verifying Identity...</div>;
    }

    return (
        <div className={`client-portal-wrapper ${viewState}`}>
            {/* High-End Aegis Visualization Background */}
            <div 
                className="aegis-canvas" 
                style={{ 
                    '--m-x': `${mousePos.x}px`, 
                    '--m-y': `${mousePos.y}px` 
                }}
            >
                <div className="aegis-grid-top"></div>
                <div className="aegis-orb orb-primary"></div>
                <div className="aegis-orb orb-secondary"></div>
                <div className="aegis-orb orb-accent"></div>
                <div className="aegis-nodes-overlay"></div>
                <div className="grain-filtering"></div>
            </div>

            <nav className="portal-mini-nav fade-in">
                <div className="brand">
                    <div className="brand-logo">D</div>
                    {viewState === 'dashboard' && <span className="brand-label">AEGIS</span>}
                </div>
                <button className="btn-exit" onClick={handleLogout}>Sign Out</button>
            </nav>

            {/* PHASE 1: INITIAL PORTAL VIEW */}
            {viewState === 'portal' && (
                <div className="portal-landing fade-in">
                    <header className="portal-header">
                        <span className="security-tag">AEGIS PROTECTION ACTIVE</span>
                        <h1>Aegis <em>Secure</em> Console</h1>
                        <p>Welcome back, <strong>{user}</strong>. Establish a connection to begin.</p>
                    </header>
                    
                    <div className="portal-actions">
                        <Link to="/analyze" className="portal-btn primary-portal">
                            <div className="portal-icon">⚡</div>
                            <div className="portal-text">
                                <h3>Start Scan Website</h3>
                                <p>Launch the deep aegis analyzer instantly.</p>
                            </div>
                        </Link>

                        <Link to="/dashboard" className="portal-btn">
                            <div className="portal-icon">🗄️</div>
                            <div className="portal-text">
                                <h3>Open Aegis Archive</h3>
                                <p>Access historical patterns and reports.</p>
                            </div>
                        </Link>
                    </div>
                </div>
            )}

            {/* PHASE 2: DASHBOARD VIEW (Toolkit on the left) */}
            {viewState === 'dashboard' && (
                <div className="dashboard-layout fade-in">
                    <div className="dashboard-sidebar">
                        <div className="sidebar-header">
                            <span className="tag-micro">TOOLKIT</span>
                            <h2>Active Modules</h2>
                        </div>
                        
                        <div className="sidebar-options">
                            <Link to="/analyze" className="side-option stagger-1">
                                <div className="opt-icon">🔍</div>
                                <div className="opt-text">
                                    <h3>Aegis: Dark Pattern Detector</h3>
                                    <p>Scan links and text patterns.</p>
                                </div>
                            </Link>

                            <Link to="/dashboard" className="side-option stagger-2">
                                <div className="opt-icon">🕒</div>
                                <div className="opt-text">
                                    <h3>Audit History</h3>
                                    <p>Review last 10 reports.</p>
                                </div>
                            </Link>

                            <Link to="/dashboard?view=account" className="side-option stagger-3">
                                <div className="opt-icon">👤</div>
                                <div className="opt-text">
                                    <h3>Security Profile</h3>
                                    <p>Account & password settings.</p>
                                </div>
                            </Link>
                        </div>

                        <button className="btn-back" onClick={() => setViewState('portal')}>← Back to Portals</button>
                    </div>

                    <div className="dashboard-main-preview stagger-4">
                        <div className="preview-content">
                            <div className="shield-icon">🛡️</div>
                            <h1>Aegis is <em>Live.</em></h1>
                            <p>Select a module from the sidebar to start your security verification sequence.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ClientHome;
