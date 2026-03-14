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

    if (isLoading) {
        return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0e0d0b', color: '#fff' }}>Verifying Identity...</div>;
    }
    return (
        <div className="client-home-wrapper">
            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
            </div>

            <nav className="client-nav">
                <div className="brand">
                    <div className="brand-mark">D</div>
                    <span className="brand-name">Aegis: The Dark-Pattern Detector</span>
                </div>
                <div className="nav-actions">
                    <span className="user-welcome">Welcome, <strong>{user}</strong></span>
                    <button className="logout-pill" onClick={handleLogout}>Logout</button>
                </div>
            </nav>

            <main className="client-main">
                <header className="client-header fade-in">
                    <h1>Enterprise Security <em>Console</em></h1>
                    <p>Access your personalized neural protection tools and historical archives.</p>
                </header>

                <div className="tools-grid fade-in">
                    <div className="tool-card main-tool">
                        <div className="tool-content">
                            <span className="tag">Primary Engine</span>
                            <h3>Deep Pattern Analyzer</h3>
                            <p>Verify e-commerce links and message fragments using our 15+ category ML model.</p>
                            <Link to="/analyze" className="btn-launch">Launch Tool →</Link>
                        </div>
                        <div className="tool-icon">🔍</div>
                    </div>

                    <div className="tool-card">
                        <div className="tool-content">
                            <span className="tag">Archive</span>
                            <h3>Audit History</h3>
                            <p>Review your last 10 security reports and trust scores.</p>
                            <Link to="/dashboard" className="btn-link">Open Vault</Link>
                        </div>
                        <div className="tool-icon">🕒</div>
                    </div>

                    <div className="tool-card">
                        <div className="tool-content">
                            <span className="tag">Identity</span>
                            <h3>Profile Settings</h3>
                            <p>Review your security profile and manage your account details.</p>
                            <Link to="/dashboard?view=account" className="btn-link">Account Settings</Link>
                        </div>
                        <div className="tool-icon">👤</div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ClientHome;
