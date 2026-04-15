import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import './Auth.css';
import axios from 'axios';
import Cookies from 'js-cookie';
import API_BASE_URL from '../config';

// Ensure cookies are sent with every request
axios.defaults.withCredentials = true;

const AuthPage = () => {
    const location = useLocation();
    const isSignupUrl = location.pathname.includes('signup');

    const initialIsMobile = window.innerWidth <= 1024;
    const [isRightPanelActive, setIsRightPanelActive] = useState(isSignupUrl);
    const [forgotFlow, setForgotFlow] = useState(false);
    const [forgotPhase, setForgotPhase] = useState('email'); // 'email', 'otp', or 'new_pass'
    const [otpTimer, setOtpTimer] = useState(120);
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    // Mobile Flow States
    const [isMobile, setIsMobile] = useState(initialIsMobile);
    const [mobileScreen, setMobileScreen] = useState(isSignupUrl ? 'signup' : (location.pathname === '/login' ? 'login' : 'intro'));

    // Update state when location changes (in case of navigation between login/signup)
    useEffect(() => {
        setIsRightPanelActive(isSignupUrl);
        if (isSignupUrl) {
            setMobileScreen('signup');
        } else if (location.pathname === '/login') {
            setMobileScreen('login');
        }
    }, [isSignupUrl, location.pathname]);

    // Auth Form States
    const [loginData, setLoginData] = useState({ email: '', password: '' });
    const [signupData, setSignupData] = useState({ username: '', email: '', password: '', confirm_password: '' });
    const [forgotData, setForgotData] = useState({ email: '', otp: '', new_password: '' });

    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState({ login: false, signup: false, confirm: false, reset: false });
    const [windowFocused, setWindowFocused] = useState(true);

    // Track window focus for Anti-Screenshot protection & generic resize
    useEffect(() => {
        const handleFocus = () => setWindowFocused(true);
        const handleBlur = () => setWindowFocused(false);
        const handleResize = () => setIsMobile(window.innerWidth <= 1024);
        
        window.addEventListener('focus', handleFocus);
        window.addEventListener('blur', handleBlur);
        window.addEventListener('resize', handleResize);
        return () => {
            window.removeEventListener('focus', handleFocus);
            window.removeEventListener('blur', handleBlur);
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    // Check if already logged in on mount
    useEffect(() => {
        const checkLogin = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/dashboard`);
                if (res.data.user) {
                    console.log("User already logged in, redirecting...");
                    Cookies.set('user', res.data.user, { expires: 7, sameSite: 'Lax', path: '/' });
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

    const navigate = useNavigate();

    const togglePassword = (field) => {
        setShowPassword(prev => ({ ...prev, [field]: !prev[field] }));
    };

    const togglePanel = (active) => {
        setIsRightPanelActive(active);
        setMobileScreen(active ? 'signup' : 'login');
        setError('');
        navigate(active ? '/signup' : '/login');
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            console.log("Attempting Login with:", loginData.email);
            const res = await axios.post(`${API_BASE_URL}/login`, loginData);
            console.log("Login Success:", res.data);
            if (res.data.success) {
                Cookies.set('user', res.data.user, { expires: 7, sameSite: 'Lax', path: '/' });
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
        <div className={`auth-wrapper ${isMobile ? 'is-mobile-view' : ''} mobile-state-${mobileScreen}`}>
            <div className="bg-canvas">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
                <div className="orb orb-3"></div>
            </div>

            {/* Mobile Intro Screen (Reference Pic Flow) */}
            {isMobile && mobileScreen === 'intro' && (
                <div className="mobile-intro-screen fade-in">
                    <div className="pic-container">
                        <img src="/images/auth_illustration.png" alt="Welcome" />
                    </div>
                    <div className="intro-actions">
                        <button className="btn-mobile-solid" onClick={() => togglePanel(false)}>Login</button>
                        <button className="btn-mobile-outline" onClick={() => togglePanel(true)}>Register</button>
                        <span className="btn-mobile-guest" onClick={() => window.location.href='/'}>Continue as a guest</span>
                    </div>
                </div>
            )}

            <div className="auth-content-container" style={{ display: (isMobile && mobileScreen === 'intro') ? 'none' : 'flex' }}>
                
                {/* Mobile Back Button */}
                {isMobile && mobileScreen !== 'intro' && (
                    <div className="mobile-back-nav" onClick={() => setMobileScreen('intro')}>
                        <span className="back-icon">←</span>
                    </div>
                )}

                {/* Signup Form */}
                {isRightPanelActive && !forgotFlow && (
                    <div className="form-box sign-up-box fade-in">
                        <form onSubmit={handleSignup}>
                            <Link to="/" className="brand-header" style={{ textDecoration: 'none' }}>
                                <div className="brand-mark">D</div>
                                <span className="brand-name">Pattern Detection</span>
                            </Link>
                            <h2 className="form-title">{isMobile ? "Join the <strong>Security</strong> Circle" : <>Start your <strong>journey.</strong></>}</h2>
                            {error && <div className="error-msg error-visible">{error}</div>}
                            <div className="field-group">
                                <input type="text" placeholder={isMobile ? "Enter your username" : " "} required value={signupData.username} onChange={e => setSignupData({ ...signupData, username: e.target.value })} />
                                <label>Username</label>
                                <div className="bar"></div>
                            </div>
                            <div className="field-group">
                                <input
                                    type="email"
                                    name="email"
                                    autoComplete="email"
                                    placeholder={isMobile ? "Enter your email" : " "} required
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
                                    placeholder={isMobile ? "Enter your password" : " "} required
                                    value={signupData.password}
                                    onChange={e => setSignupData({ ...signupData, password: e.target.value })}
                                />
                                <label>Password</label>
                                <span className="toggle-btn" onClick={() => togglePassword('signup')}>
                                    {showPassword.signup ? "🙈" : "👁️"}
                                </span>
                                <div className="bar"></div>
                            </div>
                            <div className="field-group">
                                <input
                                    type={showPassword.confirm ? "text" : "password"}
                                    name="signup-confirm-password"
                                    autoComplete="new-password"
                                    placeholder={isMobile ? "Confirm your password" : " "} required
                                    value={signupData.confirm_password}
                                    onChange={e => setSignupData({ ...signupData, confirm_password: e.target.value })}
                                />
                                <label>Confirm Password</label>
                                <span className="toggle-btn" onClick={() => togglePassword('confirm')}>
                                    {showPassword.confirm ? "🙈" : "👁️"}
                                </span>
                                <div className="bar"></div>
                            </div>
                            <button className="btn-main" type="submit">Create Account →</button>
                            <span className="toggle-link" onClick={() => togglePanel(false)}>Already have an account? <strong>Login Now</strong></span>
                        </form>
                    </div>
                )}

                {/* Login Form */}
                {!isRightPanelActive && !forgotFlow && (
                    <div className="form-box sign-in-box fade-in">
                        <form onSubmit={handleLogin}>
                            <Link to="/" className="brand-header" style={{ textDecoration: 'none' }}>
                                <div className="brand-mark">D</div>
                                <span className="brand-name">Pattern Detection</span>
                            </Link>
                            <h2 className="form-title">{isMobile ? "Welcome back to <strong>Aegis</strong>" : <>Welcome <strong>Back.</strong></>}</h2>
                            {error && <div className="error-msg error-visible">{error}</div>}
                            <div className="field-group">
                                <input
                                    type="email"
                                    name="login-email"
                                    autoComplete="email"
                                    placeholder={isMobile ? "Enter your email" : " "} required
                                    value={loginData.email}
                                    onChange={e => setLoginData({ ...loginData, email: e.target.value })}
                                />
                                <label>Email Address</label>
                                <div className="bar"></div>
                            </div>
                            <div className="field-group">
                                <input
                                    type={showPassword.login ? "text" : "password"}
                                    className={showPassword.login && !windowFocused ? 'security-blur-inactive' : ''}
                                    name="login-password"
                                    autoComplete="off"
                                    placeholder={isMobile ? "Enter your password" : " "} required
                                    value={loginData.password}
                                    onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                                />
                                <label>Password</label>
                                <span className="toggle-btn" onClick={() => togglePassword('login')}>
                                    {showPassword.login ? "🙈" : "👁️"}
                                </span>
                                <div className="bar"></div>
                            </div>
                            <div className="forgot-pass-wrap">
                                <span className="forgot-pass" onClick={() => setForgotFlow(true)}>Forgot Credentials?</span>
                            </div>
                            <button className="btn-main" type="submit">Establish Connection →</button>
                            <span className="toggle-link" onClick={() => togglePanel(true)}>New to the system? <strong>Register Now</strong></span>
                        </form>
                    </div>
                )}

                {/* Forgot Password Flow */}
                {forgotFlow && (
                    <div className="form-box forgot-box fade-in">
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            if (forgotPhase === 'email') handleForgotRequest(e);
                            else if (forgotPhase === 'otp') handleVerifyOtp(e);
                            else if (forgotPhase === 'new_pass') handleReset(e);
                        }}>
                            <Link to="/" className="brand-header" style={{ textDecoration: 'none' }}>
                                <div className="brand-mark">D</div>
                                <span className="brand-name">Pattern Detection</span>
                            </Link>
                            <h2 className="form-title">Reset <strong>Access.</strong></h2>
                            {error && <div className="error-msg error-visible">{error}</div>}

                            {forgotPhase === 'email' && (
                                <>
                                    <div className="field-group">
                                        <input type="email" placeholder=" " required value={forgotData.email} onChange={e => setForgotData({ ...forgotData, email: e.target.value })} />
                                        <label>Recovery Email</label>
                                        <div className="bar"></div>
                                    </div>
                                    <button className={`btn-main ${isSubmitting ? 'btn-loading' : ''}`} type="submit" disabled={isSubmitting}>
                                        {isSubmitting ? 'Searching...' : 'Send Recovery Code →'}
                                    </button>
                                    <span className="forgot-pass" onClick={() => setForgotFlow(false)} style={{ display: 'block', textAlign: 'center', marginTop: '20px' }}>Return to Login</span>
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
                                        <span className="toggle-btn" onClick={() => togglePassword('reset')}>
                                            {showPassword.reset ? "🙈" : "👁️"}
                                        </span>
                                        <div className="bar"></div>
                                    </div>
                                    <button className="btn-main" type="submit">Update Password →</button>
                                </>
                            )}
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuthPage;
