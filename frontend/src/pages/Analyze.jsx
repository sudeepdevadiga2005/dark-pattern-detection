import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import { ShieldCheck, ShieldAlert, Info, Search, RefreshCw, ArrowLeft, Activity, Target, Zap } from 'lucide-react';
import './Analyze.css';

const Analyze = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [input, setInput] = useState('');
    const [inputType, setInputType] = useState('url');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [controller, setController] = useState(null);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const mode = params.get('mode');
        if (mode === 'text') setInputType('text');
        else if (mode === 'url') setInputType('url');
    }, [location]);

    const handleAnalyze = async () => {
        if (!input || !input.trim()) return;
        
        const cleanInput = input.trim();
        const lowerInput = cleanInput.toLowerCase();
        const isUrlPattern = /^https?:\/\//.test(lowerInput) || /^www\./.test(lowerInput) || /^[a-z0-9-]+\.[a-z]{2,}$/.test(lowerInput);

        // STRICT VALIDATION
        if (inputType === 'url' && !isUrlPattern) {
            setResult({ error: "Please enter a valid URL or Domain in this field. For text analysis, use the 'Text Audit' tab." });
            return;
        }
        
        if (inputType === 'text' && isUrlPattern) {
            setResult({ error: "This tab is for Text Analysis only. Please enter a URL in the 'URL Analysis' tab." });
            return;
        }

        setIsAnalyzing(true);
        setResult(null);

        const abortController = new AbortController();
        setController(abortController);

        try {
            const endpoint = inputType === 'url' ? '/analyze' : '/analyze-text';
            const payload = inputType === 'url' ? { url: cleanInput } : { text: input.trim() }; // Keep case for text

            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload, {
                signal: abortController.signal
            });

            // "Cinematic" delay for AI feeling
            setTimeout(() => {
                // If backend gives an error inside a 200 OK, wrap it. Otherwise set raw result.
                setResult(res.data);
                setIsAnalyzing(false);
                setController(null);
            }, 1800);
        } catch (err) {
            if (axios.isCancel(err)) return;
            setIsAnalyzing(false);
            setResult({ error: err.response?.data?.error || "Connection interrupted. Please check your secure link." });
            setController(null);
        }
    };

    const trySample = () => {
        const samples = {
            url: "https://amazon-security-alert.net/login",
            text: "Final Warning! Your account will be permanently deactivated in 5 minutes unless you verify your identity now. Click here to prevent immediate loss of data!"
        };
        setInput(samples[inputType]);
    };

    const getStatusInfo = (status, score) => {
        const s = status ? status.toUpperCase() : '';
        if (s === 'SAFE') return { label: 'Safe', color: '#00ff9d', desc: 'This content appears safe and trustworthy.', recommend: 'You can proceed normally.' };
        if (s === 'MEDIUM_RISK') return { label: 'Suspicious', color: '#ffcc00', desc: 'Some elements may be misleading or manipulative.', recommend: 'Proceed with caution.' };
        if (s === 'HIGH_RISK') return { label: 'High Risk', color: '#ff4d4d', desc: 'This content contains strong deceptive patterns.', recommend: 'Avoid interacting with this content.' };
        
        // Final fallback for URL analysis or unexpected labels
        if (s === 'SUSPICIOUS') return { label: 'Suspicious', color: '#ffcc00', desc: 'Potentially manipulative content detected.', recommend: 'Verify before proceeding.' };
        if (s === 'UNSAFE') return { label: 'High Risk', color: '#ff4d4d', desc: 'This content exhibits signatures of active fraud.', recommend: 'Avoid interacting.' };
        
        return { label: 'Threat Detected', color: '#ff4d4d', desc: 'Malicious markers identified in input.', recommend: 'Do not follow these instructions.' };
    };

    const getCleanExplanation = (result) => {
        if (result.message) return result.message;
        if (result.status === 'SAFE') return "No suspicious patterns were detected in the content.";
        return "The content includes messaging that may influence user choices unfairly.";
    };

    const analyzeFindings = (findings = []) => {
        const threats = [];
        const signals = [];

        findings.forEach(f => {
            if (typeof f === 'string') {
                const isSignal = 
                    f.toLowerCase().includes('matched valid') || 
                    f.toLowerCase().includes('network check') || 
                    f.toLowerCase().includes('no definitive') ||
                    f.toLowerCase().includes('shows signs');
                
                if (isSignal) {
                    signals.push(f);
                } else {
                    threats.push(f);
                }
            } else {
                threats.push(f);
            }
        });

        return { threats, signals };
    };

    const getDarkPatternDesc = (cat) => {
        const c = cat ? cat.toLowerCase() : '';
        if (c.includes('urgency')) return "This creates artificial time pressure to force an immediate decision.";
        if (c.includes('cost') || c.includes('hidden')) return "Undisclosed fees or requirements may be hidden in the fine print.";
        if (c.includes('misdirection')) return "This technique influences choice by highlighting specific information while hiding others.";
        if (c.includes('social proof') || c.includes('trending')) return "Uses potentially fabricated community activity to pressure purchases.";
        if (c.includes('forced action')) return "Forces the user to take an unnecessary action to proceed.";
        if (c.includes('obstruction')) return "Makes it artificially difficult to cancel or back out of an action.";
        if (c.includes('security pressure')) return "Uses alarming security warnings (e.g. account suspension) to bypass critical thinking.";
        if (c.includes('scarcity')) return "Indicates limited availability to trigger impulsive buying behavior.";
        if (c.includes('loss aversion')) return "Frames the choice in terms of potential losses rather than gains to manipulate decisions.";
        if (c.includes('neural') || c.includes('classification')) return "The neural engine detected complex linguistic patterns typical of deceptive design.";
        
        return "Manipulative pattern designed to influence user behavior.";
    };

    const parsedFindings = result && !result.error ? analyzeFindings(result.findings) : { threats: [], signals: [] };

    return (
        <div className={`analyze-portal-wrapper ${isAnalyzing ? 'is-scanning' : ''}`}>
            {/* Advanced Background Nexus */}
            <div className="background-nexus">
                <div className="nexus-base-gradient"></div>
                <div className="nexus-grid"></div>
                <div className="nexus-noise"></div>
                <div className="nexus-blobs">
                    <div className="blob blob-cyan"></div>
                    <div className="blob blob-purple"></div>
                    <div className="blob blob-teal"></div>
                </div>
            </div>

            <nav className="analyze-nav fade-in">
                <div className="nav-left">
                    <Link to="/dashboard" className="nav-logo">
                        <div className="logo-box">A</div>
                        <div className="logo-text">
                            <span className="logo-main">AEGIS</span>
                            <span className="logo-sub">SECURE CONSOLE</span>
                        </div>
                    </Link>
                </div>
                <div className="nav-right">
                    <button className="nav-action-btn" onClick={() => navigate('/dashboard')}>
                        <LayoutGrid size={16} /> DASHBOARD
                    </button>
                </div>
            </nav>

            <main className="analyze-main">
                {!result && !isAnalyzing && (
                    <div className="analyze-hero fade-in">
                        <div className="hero-badge">
                            <Zap size={14} className="flash-icon" /> AI SECURITY ENGINE
                        </div>
                        <h1>Dark Pattern Detection Console</h1>
                        <p>Advanced neural analysis for deceptive design and manipulative content</p>
                    </div>
                )}

                {!result && (
                    <div className="glass-card analyzer-card stagger-1">
                        <div className="card-tabs">
                            <button 
                                className={`tab-btn ${inputType === 'url' ? 'active' : ''}`}
                                onClick={() => setInputType('url')}
                                disabled={isAnalyzing}
                            >
                                <Target size={18} /> URL Analysis
                            </button>
                            <button 
                                className={`tab-btn ${inputType === 'text' ? 'active' : ''}`}
                                onClick={() => setInputType('text')}
                                disabled={isAnalyzing}
                            >
                                <Activity size={18} /> Text Audit
                            </button>
                        </div>

                        <div className="analyzer-input-box">
                            <textarea 
                                placeholder={inputType === 'url' ? "Enter website URL to scan..." : "Paste suspicious content or promotional text here..."}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                disabled={isAnalyzing}
                                className="styled-textarea"
                            />
                            
                            <div className="card-actions">
                                <div className="action-left">
                                    <button className="btn-secondary" onClick={() => setInput('')} disabled={isAnalyzing}>Clear</button>
                                    <button className="btn-secondary" onClick={trySample} disabled={isAnalyzing}>Try Sample</button>
                                </div>
                                <button 
                                    className={`btn-primary ${isAnalyzing ? 'loading' : ''}`} 
                                    onClick={handleAnalyze} 
                                    disabled={isAnalyzing || !input.trim()}
                                >
                                    {isAnalyzing ? <RefreshCw className="spin-icon" /> : <Search size={20} />}
                                    {isAnalyzing ? "Analyzing Patterns..." : "Launch Deep Analysis"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {isAnalyzing && (
                    <div className="scanning-ui fade-in">
                        <div className="neural-rings">
                            <div className="ring"></div>
                            <div className="ring delay-1"></div>
                            <div className="ring delay-2"></div>
                        </div>
                        <h3>Security Pipeline Active</h3>
                        <p>Scanning for neural manipulation markers...</p>
                    </div>
                )}

                {result && !isAnalyzing && result.error && (
                    <div className="glass-card error-card fade-in">
                        <ShieldAlert size={48} className="error-icon" />
                        <h3>Secure Analysis Blocked</h3>
                        <p>{result.error}</p>
                        <button className="btn-primary" onClick={() => setResult(null)}>Try Again</button>
                    </div>
                )}

                {result && !isAnalyzing && !result.error && (
                    <div className="result-view fade-in">
                        <div className="result-grid">
                            <div className="glass-card result-summary-card">
                                <div className="summary-header">
                                    <div className="status-indicator">
                                        <div className="status-label">SECURITY STATUS</div>
                                        <h2 style={{ color: getStatusInfo(result.status).color }}>
                                            {getStatusInfo(result.status).label}
                                        </h2>
                                    </div>
                                    <div className="trust-gauge">
                                        <svg viewBox="0 0 100 100" className="gauge-svg">
                                            <circle className="gauge-bg" cx="50" cy="50" r="45" />
                                            <circle 
                                                className="gauge-fill" 
                                                cx="50" cy="50" r="45" 
                                                style={{ 
                                                    strokeDasharray: `${result.trust_score * 2.82} 282`,
                                                    stroke: getStatusInfo(result.status).color
                                                }} 
                                            />
                                        </svg>
                                        <div className="gauge-text">
                                            <span className="gauge-val">{result.trust_score}%</span>
                                            <label>TRUST</label>
                                        </div>
                                    </div>
                                </div>
                                <p className="status-message">{getStatusInfo(result.status).desc}</p>
                            </div>

                            <div className="glass-card explanation-card">
                                <h3>Analysis Insight</h3>
                                <p className="insight-text">{getCleanExplanation(result)}</p>
                                
                                <div className="recommendation-pill" style={{ background: `${getStatusInfo(result.status).color}15`, color: getStatusInfo(result.status).color }}>
                                    {getStatusInfo(result.status).recommend}
                                </div>
                            </div>
                        </div>

                        {parsedFindings.threats.length === 0 ? (
                            <div className="patterns-section">
                                <div 
                                    className="glass-card pattern-element-card" 
                                    style={{ 
                                        textAlign: 'center', 
                                        padding: '30px', 
                                        borderColor: result.status === 'SAFE' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 204, 0, 0.2)' 
                                    }}
                                >
                                    {result.status === 'SAFE' ? (
                                        <ShieldCheck size={36} style={{ color: '#00ff9d', margin: '0 auto 12px' }} />
                                    ) : (
                                        <Info size={36} style={{ color: '#ffcc00', margin: '0 auto 12px' }} />
                                    )}
                                    <h4 style={{ 
                                        color: result.status === 'SAFE' ? '#00ff9d' : '#ffcc00', 
                                        fontSize: '18px', 
                                        marginBottom: '8px' 
                                    }}>
                                        {result.status === 'SAFE' ? 'No Dark Patterns Detected' : 'No Explicit Threats Found'}
                                    </h4>
                                    <p className="pattern-desc" style={{ maxWidth: '500px', margin: '0 auto' }}>
                                        {result.status === 'SAFE' 
                                            ? "The analysis engine found no malicious markers or manipulative tactics in the content." 
                                            : "The engine found no direct malicious patterns, but the trust score remains low due to unverified network or official signals."}
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="patterns-section">
                                <h3 className="section-title">Detected Patterns</h3>
                                <div className="patterns-grid">
                                    {parsedFindings.threats.map((f, i) => (
                                        <div key={i} className="glass-card pattern-element-card">
                                            <div className="pattern-header">
                                                <ShieldAlert size={18} className="text-danger" />
                                                <h4>{typeof f === 'string' ? "URL Security Risk" : f.category}</h4>
                                            </div>
                                            <p className="pattern-desc">
                                                {typeof f === 'string' ? f : getDarkPatternDesc(f.category)}
                                            </p>
                                            {f.evidence && (
                                                <div className="evidence-box">
                                                    <label>EVIDENCE</label>
                                                    <code>"{f.evidence}"</code>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {parsedFindings.signals.length > 0 && (
                            <div className="patterns-section" style={{ marginTop: '30px' }}>
                                <h3 className="section-title">Verification Evidence</h3>
                                <div className="patterns-grid">
                                    {parsedFindings.signals.map((sig, i) => (
                                        <div key={`sig-${i}`} className="glass-card pattern-element-card" style={{ padding: '20px', borderColor: 'rgba(34, 197, 94, 0.15)', background: 'rgba(34, 197, 94, 0.02)' }}>
                                            <div className="pattern-header">
                                                <ShieldCheck size={18} style={{ color: '#00ff9d' }} />
                                                <h4 style={{ color: '#00ff9d' }}>Safety Signal</h4>
                                            </div>
                                            <p className="pattern-desc" style={{ marginTop: '8px' }}>{sig}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="result-nav-actions">
                            <button className="btn-secondary-large" onClick={() => setResult(null)}>
                                <RefreshCw size={18} /> Scan Another
                            </button>
                            <button className="btn-secondary-large" onClick={() => navigate('/dashboard?view=history')}>
                                <Activity size={18} /> View History
                            </button>
                            <button className="btn-primary-large" onClick={() => navigate('/dashboard')}>
                                <ArrowLeft size={18} /> Back to Dashboard
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

const LayoutGrid = ({ size }) => <Target size={size} />;

export default Analyze;
