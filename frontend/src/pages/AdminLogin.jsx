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

    // Premium Interaction: Dynamic mouse tracking gradient
    const handleMouseMove = (e) => {
        const body = e.currentTarget;
        const rect = body.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        body.style.setProperty('--mouse-x', `${x}%`);
        body.style.setProperty('--mouse-y', `${y}%`);
    };

    const handleAuth = async (e, isRegisterMode) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        const endpoint = isRegisterMode ? '/admin/register' : '/admin/login';
        const payload = isRegisterMode ? { username, email, password } : { email, password };

        try {
            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload, { withCredentials: true });

            if (res.data.success) {
                if (isRegisterMode) {
                    setSuccess('Admin Identity Registered. You may now login.');
                    setIsRegister(false);
                    setPassword('');
                } else {
                    window.location.href = '/admin';
                }
            } else {
                setError(res.data.message || (isRegisterMode ? 'Registration failed. Try a different alias.' : 'Invalid credentials.'));
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Gateway connection failed. Terminal timeout.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="admin-login-body" onMouseMove={handleMouseMove}>
            <div className="admin-login-container">
                <div className="admin-login-card">

                    {/* Left Split: Cyber Security Image */}
                    <div className="login-image-side">
                        <img src="/neuroshield-bg.png" alt="Aegis Core" className="bg-image-split" />
                        <div className="image-overlay-content">
                            <h2>{isRegister ? 'New Enrollment' : 'Aegis Core'}</h2>
                            <p>Administrative Security Gateway to protect your internal systems and monitor aegis grid integrity.</p>
                        </div>
                    </div>

                    {/* Right Split: Auth Form */}
                    <div className="login-form-side dark-theme-form">
                        <div className="auth-tabs">
                            <span 
                                className={`auth-tab ${!isRegister ? 'active' : ''}`}
                                onClick={() => { setIsRegister(false); setError(''); setSuccess(''); }}
                            >
                                Sign In
                            </span>
                            <span 
                                className={`auth-tab ${isRegister ? 'active' : ''}`}
                                onClick={() => { setIsRegister(true); setError(''); setSuccess(''); }}
                            >
                                Sign Up
                            </span>
                        </div>

                        {error && (
                            <div className="login-error-alert fade-in" style={{background: 'rgba(157, 23, 77, 0.3)', color: '#fbcfe8', borderColor: '#be185d'}}>
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        {success && (
                            <div className="login-success-alert fade-in" style={{ background: 'rgba(255, 255, 255, 0.1)', color: '#fbcfe8', padding: '10px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', fontSize: '14px' }}>
                                <Shield size={18} />
                                <span>{success}</span>
                            </div>
                        )}

                        <div className="login-slider-wrapper">
                            <div className={`login-slider ${isRegister ? 'slide-left' : ''}`}>
                                
                                {/* Sign In Panel */}
                                <div className="login-panel">
                                    <form onSubmit={(e) => handleAuth(e, false)} className="login-form dark-inputs">
                                        <div className="input-group">
                                            <label>Your email</label>
                                            <input
                                                type="email"
                                                placeholder="bob.8888@gmail.com"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                            />
                                        </div>

                                        <div className="input-group">
                                            <label>Your password</label>
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                placeholder="••••••••"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                required
                                            />
                                        </div>

                                        <div className="auth-options-row">
                                            <label className="keep-logged-in">
                                                <input type="checkbox" />
                                                <span className="checkmark"></span>
                                                Keep me logged in
                                            </label>
                                            <a href="#" className="forgot-pwd">Forgot password?</a>
                                        </div>

                                        <button
                                            type="submit"
                                            className={`login-submit-btn pill-btn ${loading && !isRegister ? 'btn-scanning' : ''}`}
                                            disabled={loading}
                                        >
                                            {loading && !isRegister ? 'PROCESSING...' : 'SIGN IN'}
                                        </button>
                                        
                                        <div className="bottom-links">
                                            <a href="/">Privacy</a> • <a href="/">Terms</a> • <a href="/">About</a>
                                        </div>
                                    </form>
                                </div>
                                
                                {/* Sign Up Panel */}
                                <div className="login-panel">
                                    <form onSubmit={(e) => handleAuth(e, true)} className="login-form dark-inputs">
                                        <div className="input-group">
                                            <label>Admin alias</label>
                                            <input
                                                type="text"
                                                placeholder="e.g. root_admin"
                                                value={username}
                                                onChange={(e) => setUsername(e.target.value)}
                                                required
                                            />
                                        </div>

                                        <div className="input-group">
                                            <label>Your email</label>
                                            <input
                                                type="email"
                                                placeholder="bob.8888@gmail.com"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                            />
                                        </div>

                                        <div className="input-group">
                                            <label>Your password</label>
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                placeholder="••••••••"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                required
                                            />
                                        </div>

                                        <button
                                            type="submit"
                                            style={{ marginTop: '20px' }}
                                            className={`login-submit-btn pill-btn ${loading && isRegister ? 'btn-scanning' : ''}`}
                                            disabled={loading}
                                        >
                                            {loading && isRegister ? 'PROCESSING...' : 'SIGN UP'}
                                        </button>
                                    </form>
                                </div>

                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
