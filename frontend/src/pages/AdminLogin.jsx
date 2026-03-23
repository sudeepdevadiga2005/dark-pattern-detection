import React, { useState } from 'react';
import axios from 'axios';
import { Shield, Lock, Mail, ChevronRight, AlertCircle, ArrowLeft } from 'lucide-react';
import './AdminLogin.css';

const API_BASE_URL = "http://localhost:5000/api";

const AdminLogin = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const res = await axios.post(`${API_BASE_URL}/admin/login`, {
                email,
                password
            }, { withCredentials: true });

            if (res.data.success) {
                // Successful login, redirect to admin dashboard
                window.location.href = '/admin';
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Gateway connection failed. Terminal timeout.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="admin-login-body">
            <div className="login-matrix-bg"></div>
            
            <div className="admin-login-container">
                <div className="admin-login-card">
                    <div className="login-header">
                        <div className="shield-icon-wrapper">
                            <Shield className="shield-pulse" size={40} />
                            <div className="shield-status-ring"></div>
                        </div>
                        <h2>NEUROSHIELD</h2>
                        <p className="subtitle">ADMINISTRATIVE SECURITY GATEWAY</p>
                    </div>

                    <form onSubmit={handleLogin} className="login-form">
                        {error && (
                            <div className="login-error-alert fade-in">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        <div className="input-field">
                            <Mail className="input-icon" size={18} />
                            <input 
                                type="email" 
                                placeholder="Admin Email" 
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required 
                            />
                            <div className="input-focus-border"></div>
                        </div>

                        <div className="input-field">
                            <Lock className="input-icon" size={18} />
                            <input 
                                type="password" 
                                placeholder="Auth Token (Password)" 
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required 
                            />
                            <div className="input-focus-border"></div>
                        </div>

                        <button 
                            type="submit" 
                            className={`login-submit-btn ${loading ? 'btn-scanning' : ''}`}
                            disabled={loading}
                        >
                            {loading ? (
                                <>SCANNING IDENTITY...</>
                            ) : (
                                <>VERIFY ACCESS <ChevronRight size={18} /></>
                            )}
                        </button>
                    </form>

                    <div className="login-footer">
                        <a href="/" className="back-link">
                            <ArrowLeft size={14} /> Back to Public Sector
                        </a>
                        <div className="security-notice">
                            UNAUTHORIZED ACCESS TO THIS TERMINAL IS MONITORED.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
