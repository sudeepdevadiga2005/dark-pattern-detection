import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Lock, Mail, ChevronRight, AlertCircle, ArrowLeft } from 'lucide-react';
import './AdminLogin.css';

// Use relative /api to go through the Vite proxy (same as rest of app)
const API_BASE_URL = "/api";

const AdminLogin = () => {
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    useEffect(() => {
        document.title = 'Dark Pattern Admin';
    }, []);

    const handleAuth = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        const endpoint = isRegister ? '/admin/register' : '/admin/login';
        const payload = isRegister ? { username, email, password } : { email, password };

        try {
            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload, { withCredentials: true });

            if (res.data.success) {
                if (isRegister) {
                    setSuccess('Admin Identity Registered. You may now login.');
                    setIsRegister(false);
                    setPassword('');
                } else {
                    window.location.href = '/admin';
                }
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
            <div className="admin-login-container">
                <div className="admin-login-card">

                    {/* Left Split: Cyber Security Image */}
                    <div className="login-image-side">
                        <img src="/aegis-bg.png" alt="aegis Core" className="bg-image-split" />
                        <div className="image-overlay-content">
                            <h2>{isRegister ? 'New Enrollment' : 'aegis Core'}</h2>
                            <p>Administrative Security Gateway to protect your internal systems and monitor aegis grid integrity.</p>
                        </div>
                    </div>

                    {/* Right Split: Auth Form */}
                    <div className="login-form-side">
                        <div className="login-header-mini">
                            <Shield className="shield-pulse" size={36} />
                            <h2>{isRegister ? 'Create Admin' : 'Welcome'}</h2>
                            <p>{isRegister ? 'Register Secure Identity' : 'Login with Identity Token'}</p>
                        </div>

                        <form onSubmit={handleAuth} className="login-form">
                            {error && (
                                <div className="login-error-alert fade-in">
                                    <AlertCircle size={18} />
                                    <span>{error}</span>
                                </div>
                            )}

                            {success && (
                                <div className="login-success-alert fade-in" style={{ background: 'rgba(100, 255, 218, 0.1)', color: '#64FFDA', padding: '10px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', fontSize: '14px' }}>
                                    <Shield size={18} />
                                    <span>{success}</span>
                                </div>
                            )}

                            {isRegister && (
                                <div className="input-field">
                                    <Lock className="input-icon" size={26} style={{ transform: 'rotate(-45deg)', opacity: 0.5 }} />
                                    <input
                                        type="text"
                                        placeholder="Admin Alias (Username)"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        required
                                    />
                                </div>
                            )}

                            <div className="input-field">
                                <Mail className="input-icon" size={26} />
                                <input
                                    type="email"
                                    placeholder="Admin Email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>

                            <div className="input-field" style={{ position: 'relative' }}>
                                <Lock className="input-icon" size={26} />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Auth Token (Password)"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    style={{ paddingRight: '50px' }}
                                />
                                <div
                                    className="password-toggle-icon"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{
                                        position: 'absolute',
                                        right: '15px',
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        cursor: 'pointer',
                                        color: '#64FFDA',
                                        opacity: 0.7
                                    }}
                                >
                                    {showPassword ? '🔒' : '👁️'}
                                </div>
                            </div>

                            <div className="auth-options">
                                <a href="/">← Back to Public Sector</a>
                                <span
                                    onClick={() => { setIsRegister(!isRegister); setError(''); setSuccess(''); }}
                                >
                                    {isRegister ? 'Login Instead' : 'Create Admin Account'}
                                </span>
                            </div>

                            <button
                                type="submit"
                                className={`login-submit-btn ${loading ? 'btn-scanning' : ''}`}
                                disabled={loading}
                            >
                                {loading ? 'PROCESSING...' : (isRegister ? 'REGISTER IDENTITY' : 'LOGIN')}
                            </button>
                        </form>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
