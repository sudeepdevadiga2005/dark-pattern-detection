import React, { useState, useEffect } from 'react';
import './Auth.css';
import axios from 'axios';
import API_BASE_URL from '../config';

// Ensure cookies are sent with every request
axios.defaults.withCredentials = true;

const AuthPage = () => {
    const [isRightPanelActive, setIsRightPanelActive] = useState(false);
    const [forgotFlow, setForgotFlow] = useState(false);
    const [forgotPhase, setForgotPhase] = useState('email'); // 'email', 'otp', or 'new_pass'
    const [otpTimer, setOtpTimer] = useState(120);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Auth Form States
    const [loginData, setLoginData] = useState({ email: '', password: '' });
    const [signupData, setSignupData] = useState({ username: '', email: '', password: '', confirm_password: '' });
    const [forgotData, setForgotData] = useState({ email: '', otp: '', new_password: '' });

    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState({ login: false, signup: false, confirm: false, reset: false });

    // Check if already logged in on mount
    useEffect(() => {
        const checkLogin = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/dashboard`);
                if (res.data.user) {
                    console.log("User already logged in, redirecting...");
                    window.location.href = window.location.origin + '/';
                }
            } catch (err) {
                console.log("No active session found.");
            }
        };
        checkLogin();
    }, []);

    // OTP Timer countdown effect
    useEffect(() => {
        let interval;
        if (forgotPhase === 'otp' && otpTimer > 0) {
            interval = setInterval(() => {
                setOtpTimer(prev => prev - 1);
            }, 1000);
        } else if (otpTimer === 0) {
            clearInterval(interval);
        }
        return () => clearInterval(interval);
    }, [forgotPhase, otpTimer]);

    // Handle password visibility toggle with 5-sec auto-hide
    const togglePassword = (field) => {
        setShowPassword(prev => ({ ...prev, [field]: true }));
        setTimeout(() => {
            setShowPassword(prev => ({ ...prev, [field]: false }));
        }, 5000);
    };

    const togglePanel = (active) => {
        setIsRightPanelActive(active);
        setError('');
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            console.log("Attempting Login with:", loginData.email);
            const res = await axios.post(`${API_BASE_URL}/login`, loginData);
            console.log("Login Success:", res.data);
            if (res.data.success) {
                window.location.href = window.location.origin + '/';
            }
        } catch (err) {
            console.error("Login Error:", err);
            const msg = err.response?.data?.message || 'Connection Error: Is the backend running?';
            setError(msg);
        }
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        if (signupData.password !== signupData.confirm_password) {
            setError('Passwords do not match');
            return;
        }
        try {
            const res = await axios.post(`${API_BASE_URL}/signup`, signupData);
            if (res.data.success) {
                alert('Registration complete! Please sign in.');
                togglePanel(false);
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed');
        }
    };

    const handleForgotRequest = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const res = await axios.post(`${API_BASE_URL}/forgot-password`, { email: forgotData.email });
            if (res.data.success) {
                setForgotPhase('otp');
                setOtpTimer(120); // Reset timer to 120 seconds
                alert(res.data.debug_otp ? `DEMO MODE: OTP is ${res.data.debug_otp}` : 'A 6-digit OTP code has been successfully sent to your email Address. Please check your inbox / spam folder.');
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Email not found');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post(`${API_BASE_URL}/verify-otp`, {
                email: forgotData.email,
                otp: forgotData.otp
            });
            if (res.data.success) {
                setForgotPhase('new_pass');
                setError('');
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Invalid or expired OTP';
            setError(msg);
            if (msg.includes('Maximum attempt fails') || msg.includes('OTP expired') || msg.includes('No OTP requested')) {
                setTimeout(() => {
                    setForgotPhase('email');
                    setForgotData(prev => ({ ...prev, otp: '' }));
                    setOtpTimer(120);
                }, 2500);
            }
        }
    };

    const handleReset = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post(`${API_BASE_URL}/reset-password`, {
                email: forgotData.email,
                otp: forgotData.otp,
                new_password: forgotData.new_password
            });
            if (res.data.success) {
                alert('Password reset successful!');
                setForgotFlow(false);
                setForgotPhase('email');
                setForgotData({ email: '', otp: '', new_password: '' });
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'Invalid or expired OTP';
            setError(msg);
            if (msg.includes('Maximum attempt fails') || msg.includes('OTP expired') || msg.includes('expired or not requested')) {
                setTimeout(() => {
                    setForgotPhase('email');
                    setForgotData(prev => ({ ...prev, otp: '', new_password: '' }));
                }, 2500);
            }
        }
    };

    return (
        <div className="auth-wrapper">
            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
            </div>

            <div className={`auth-card ${isRightPanelActive ? 'right-panel-active' : ''}`} id="authCard">
                {/* Signup Form */}
                <div className="form-container sign-up-container">
                    <form onSubmit={handleSignup}>
                        <h2 className="form-title">Create Account</h2>
                        {error && <div className="error-msg error-visible">{error}</div>}
                        <div className="field-group">
                            <input type="text" placeholder=" " required value={signupData.username} onChange={e => setSignupData({ ...signupData, username: e.target.value })} />
                            <label>Username</label>
                            <div className="bar"></div>
                        </div>
                        <div className="field-group">
                            <input
                                type="email"
                                name="email"
                                autoComplete="email"
                                placeholder=" " required
                                value={signupData.email}
                                onChange={e => setSignupData({ ...signupData, email: e.target.value })}
                            />
                            <label>Email Address</label>
                            <div className="bar"></div>
                        </div>
                        <div className="field-group">
                            <input
                                type={showPassword.signup ? "text" : "password"}
                                name="signup-password"
                                autoComplete="new-password"
                                placeholder=" " required
                                value={signupData.password}
                                onChange={e => setSignupData({ ...signupData, password: e.target.value })}
                            />
                            <label>Password</label>
                            <span className="toggle-btn" onClick={() => togglePassword('signup')}>👁️</span>
                            <div className="bar"></div>
                        </div>
                        <div className="field-group">
                            <input
                                type={showPassword.confirm ? "text" : "password"}
                                name="signup-confirm-password"
                                autoComplete="new-password"
                                placeholder=" " required
                                value={signupData.confirm_password}
                                onChange={e => setSignupData({ ...signupData, confirm_password: e.target.value })}
                            />
                            <label>Confirm Password</label>
                            <span className="toggle-btn" onClick={() => togglePassword('confirm')}>👁️</span>
                            <div className="bar"></div>
                        </div>
                        <button className="btn-main" type="submit">Complete Registration</button>
                        <span className="mobile-toggle" onClick={() => togglePanel(false)}>Already have an account? Sign In</span>
                    </form>
                </div>

                {/* Login Form */}
                <div className={`form-container sign-in-container ${forgotFlow ? 'hidden-flow' : ''}`}>
                    <form onSubmit={handleLogin}>
                        <h2 className="form-title">Welcome Back.</h2>
                        {error && <div className="error-msg error-visible">{error}</div>}
                        <div className="field-group">
                            <input
                                type="email"
                                name="login-email"
                                autoComplete="email"
                                placeholder=" " required
                                value={loginData.email}
                                onChange={e => setLoginData({ ...loginData, email: e.target.value })}
                            />
                            <label>Email Address</label>
                            <div className="bar"></div>
                        </div>
                        <div className="field-group">
                            <input
                                type={showPassword.login ? "text" : "password"}
                                name="login-password"
                                autoComplete="off"
                                placeholder=" " required
                                value={loginData.password}
                                onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                            />
                            <label>Password</label>
                            <span className="toggle-btn" onClick={() => togglePassword('login')}>👁️</span>
                            <div className="bar"></div>
                        </div>
                        <span className="forgot-pass" onClick={() => setForgotFlow(true)}>Forgotten your password?</span>
                        <button className="btn-main" type="submit">Sign In →</button>
                        <span className="mobile-toggle" onClick={() => togglePanel(true)}>Don't have an account? Sign Up</span>
                    </form>
                </div>

                {/* Forgot Password Flow */}
                {forgotFlow && (
                    <div className="form-container forgot-container">
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            if (forgotPhase === 'email') handleForgotRequest(e);
                            else if (forgotPhase === 'otp') handleVerifyOtp(e);
                            else if (forgotPhase === 'new_pass') handleReset(e);
                        }}>
                            <h2 className="form-title">Reset Access.</h2>
                            {error && <div className="error-msg error-visible">{error}</div>}

                            {forgotPhase === 'email' && (
                                <>
                                    <div className="field-group">
                                        <input type="email" placeholder=" " required value={forgotData.email} onChange={e => setForgotData({ ...forgotData, email: e.target.value })} />
                                        <label>Email Address</label>
                                        <div className="bar"></div>
                                    </div>
                                    <button className={`btn-main ${isSubmitting ? 'btn-loading' : ''}`} type="submit" disabled={isSubmitting}>
                                        {isSubmitting ? 'Verifying...' : 'Verify Email →'}
                                    </button>
                                    <span className="forgot-pass" onClick={() => setForgotFlow(false)}>Back to Login</span>
                                </>
                            )}

                            {forgotPhase === 'otp' && (
                                <>
                                    <div className="field-group">
                                        <input
                                            type="text"
                                            placeholder=" "
                                            required
                                            maxLength="6"
                                            inputMode="numeric"
                                            pattern="[0-9]*"
                                            value={forgotData.otp}
                                            onChange={e => {
                                                const val = e.target.value.replace(/[^0-9]/g, '');
                                                setForgotData({ ...forgotData, otp: val });
                                            }}
                                        />
                                        <label>6-Digit Code</label>
                                        <div className="bar"></div>
                                    </div>
                                    <div className="timer-display" style={{ textAlign: 'center', marginBottom: '15px', color: otpTimer <= 15 ? '#e53e3e' : 'var(--ink)', fontSize: '16px', fontWeight: '600', letterSpacing: '1px' }}>
                                        {otpTimer > 0 ? `Time remaining: ${otpTimer}s` : "OTP Expired"}
                                    </div>
                                    <button className="btn-main" type="submit" disabled={forgotData.otp.length !== 6 || otpTimer === 0}>Verify Code →</button>
                                </>
                            )}

                            {forgotPhase === 'new_pass' && (
                                <>
                                    <div className="field-group">
                                        <input
                                            type={showPassword.reset ? "text" : "password"}
                                            placeholder=" " required
                                            value={forgotData.new_password}
                                            onChange={e => setForgotData({ ...forgotData, new_password: e.target.value })}
                                        />
                                        <label>New Password</label>
                                        <span className="toggle-btn" onClick={() => togglePassword('reset')}>👁️</span>
                                        <div className="bar"></div>
                                    </div>
                                    <button className="btn-main" type="submit">Update Password →</button>
                                </>
                            )}
                        </form>
                    </div>
                )}

                {/* Overlay Panel */}
                <div className="overlay-container">
                    <div className="overlay">
                        <div className="brand">
                            <div className="brand-mark">D</div>
                            <span className="brand-name">Pattern Detection</span>
                        </div>
                        <div className="overlay-panel overlay-left">
                            <h1 className="overlay-headline">Hello, <em>Again!</em></h1>
                            <p className="overlay-subtitle">Ready to continue your journey? Dive back into the world of insights.</p>
                            <button className="btn-ghost" onClick={() => togglePanel(false)}>Sign In →</button>
                        </div>
                        <div className="overlay-panel overlay-right">
                            <h1 className="overlay-headline">Start your <em>journey</em></h1>
                            <p className="overlay-subtitle">Join thousands of creators building the future. Your story begins now.</p>
                            <button className="btn-ghost" onClick={() => togglePanel(true)}>Create Account</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AuthPage;
