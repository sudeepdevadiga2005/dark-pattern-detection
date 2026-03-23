import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import Cookies from 'js-cookie';
import './Analyze.css';

const Analyze = () => {
    const [input, setInput] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [deviceInfo, setDeviceInfo] = useState({
        device: 'Desktop',
        layout: 'desktop'
    });

    // Device layout toggle logic
    const toggleLayout = () => {
        const layouts = ['desktop', 'tablet', 'mobile'];
        const currentIndex = layouts.indexOf(deviceInfo.layout);
        const nextIndex = (currentIndex + 1) % layouts.length;
        
        setDeviceInfo(prev => ({
            ...prev,
            layout: layouts[nextIndex]
        }));
    };

    const handleAnalyze = async () => {
        if (!input) return;
        setIsAnalyzing(true);
        setResult(null);

        // Simple domain check regex
        const isUrl = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?:\.[a-z]{2,})?$/i.test(input.replace('http://', '').replace('https://', '').split('/')[0]);

        try {
            const endpoint = isUrl ? '/analyze' : '/analyze-text';
            const payload = isUrl ? { url: input } : { text: input };
            
            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
            
            // Simulate neural delay for "wow" effect
            setTimeout(() => {
                setResult(res.data);
                setIsAnalyzing(false);
            }, 1200);
        } catch (err) {
            console.error(err);
            setIsAnalyzing(false);
        }
    };

    return (
        <div className={`analyze-portal-wrapper ${isAnalyzing ? 'is-scanning' : ''} ${result && result.threat_level === 'High' ? 'danger-alert' : ''} ${deviceInfo.layout}`}>
            {/* The Cinematic Background Layer */}
            <div className="analyze-bg-overlay">
                <div className="neural-scan-lines"></div>
                <div className="dynamic-glow-sphere"></div>
            </div>

            <nav className="analyze-mini-nav fade-in">
                <div className="brand">
                    <div className="brand-mark">A</div>
                    <span className="brand-title">NEURAL <em>AUDITOR</em></span>
                </div>
                <Link to="/" className="btn-back-home">← TERMINAL EXIT</Link>
            </nav>

            <main className="analyze-content fade-in">
                <header className="terminal-header">
                    <span className="live-badge">SYSTEM: ONLINE</span>
                    <h1>Deep Pattern <em>Analyzer</em></h1>
                    <p>Input target URL or content fragments for real-time ML security verification.</p>
                </header>

                <div className="glass-terminal stagger-1">
                    <div className="terminal-controls">
                        <div className="input-group-main">
                            <textarea 
                                placeholder="Paste deep-content, emails, or URLs here for full neural audit..." 
                                value={input} 
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && e.ctrlKey) handleAnalyze();
                                }}
                                disabled={isAnalyzing}
                                className="elastic-textarea"
                                rows={input.split('\n').length > 5 ? 10 : 3}
                            />
                            <div className="terminal-actions">
                                <button 
                                    className={`btn-primary-scan ${isAnalyzing ? 'scanning-pulse' : ''}`}
                                    onClick={handleAnalyze} 
                                    disabled={isAnalyzing || !input}
                                >
                                    {isAnalyzing ? 'NEURAL AGENT ACTIVE...' : 'LAUNCH DEEP ANALYSIS'}
                                    <span className="btn-glow"></span>
                                </button>
                                <div className="btn-hint">Press <strong>CTRL + ENTER</strong> to scan</div>
                            </div>
                        </div>
                    </div>

                    {isAnalyzing && (
                        <div className="scanning-visualization fade-in">
                            <div className="pulse-ring"></div>
                            <div className="pulse-ring delay-1"></div>
                            <p>METRICS-PROCESSING: 15 CATEGORIES ACTIVE...</p>
                        </div>
                    )}

                    {result && !isAnalyzing && (
                        <div className="result-container-premium fade-in">
                            {result.success === false ? (
                                <div className="result-summary danger-badge">
                                    <div className="indicator-icon">❌</div>
                                    <div className="indicator-text">
                                        <h2>INVALID TARGET DETECTED</h2>
                                        <p>{result.error || "The system could not recognize this input as a valid URL or pattern."}</p>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className={`result-summary ${result.threat_level === 'High' || (result.trust_score !== undefined && result.trust_score < 45) ? 'danger-badge' : 'safe-badge'}`}>
                                        <div className="indicator-icon">
                                            {result.threat_level === 'High' || (result.trust_score !== undefined && result.trust_score < 45) ? '⚠️' : '✅'}
                                        </div>
                                        <div className="indicator-text">
                                            <h2>
                                                {result.domain_category && !result.is_ecommerce 
                                                    ? 'VERIFIED OFFICIAL'
                                                    : (result.threat_level === 'High' || (result.trust_score !== undefined && result.trust_score < 45) ? 'THREAT DETECTED' : 'SECURE CONNECTION')}
                                            </h2>
                                            <p>{result.security_warning || "Our ML engine has completed its verification sequence."}</p>
                                        </div>
                                        {(result.type === 'text' || (result.type === 'url' && (!result.domain_category || result.is_ecommerce))) && (
                                            <div className="score-ring">
                                                <span className="score-val">{result.trust_score ?? (result.threat_level === 'High' ? 0 : 100)}%</span>
                                                <span className="score-label">TRUST</span>
                                            </div>
                                        )}
                                        {result.type === 'url' && result.domain_category && !result.is_ecommerce && (
                                            <div className="category-badge-main">
                                                <span className="category-val">{result.domain_category.toUpperCase()}</span>
                                                <span className="category-label">CATEGORY</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Intelligence Rationale */}
                                    {result.reasons && result.reasons.length > 0 && (
                                        <div className="intelligence-rationale fade-in">
                                            <div className="rationale-header">
                                                <span className="rationale-tag">INTELLIGENCE RATIONALE</span>
                                                <h3>Neural Decision Summary</h3>
                                            </div>
                                            <ul className="rationale-list">
                                                {result.reasons.map((r, idx) => (
                                                    <li key={idx}>
                                                        <span className="rationale-bullet"></span>
                                                        {r}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {/* Forensic Comparison for Fakes (URL Mode) */}
                                    {result.type === 'url' && result.official_url && (
                                        <div className="forensic-analysis fade-in">
                                            <div className="forensic-header">
                                                <span className="forensic-tag">FORENSIC COMPARISON</span>
                                                <h3>Visual Pattern Mismatch</h3>
                                            </div>
                                            <div className="comparison-card">
                                                <div className="cmp-row">
                                                    <span className="cmp-label">OFFICIAL SOURCE:</span>
                                                    <span className="cmp-val safe">{result.official_url}</span>
                                                </div>
                                                <div className="cmp-divider">VS</div>
                                                <div className="cmp-row">
                                                    <span className="cmp-label">SCANNED TARGET:</span>
                                                    <span className="cmp-val danger">{result.target_url}</span>
                                                </div>
                                                <div className="cmp-details">
                                                    <strong>SECURITY ANALYSIS:</strong> Minor spelling variations detected in the scanned URL. This is a common tactic used in phishing scams to impersonate legitimate brands.
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Hidden Links Extraction for Text Mode */}
                                    {result.type === 'text' && result.url_analysis && result.url_analysis.length > 0 && (
                                        <div className="forensic-analysis fade-in">
                                            <div className="forensic-header">
                                                <span className="forensic-tag">HIDDEN LINK EXTRACTION</span>
                                                <h3>Embedded URL Security Audit</h3>
                                            </div>
                                            <div className="hidden-links-list">
                                                {result.url_analysis.map((link, idx) => (
                                                    <div key={idx} className="comparison-card" style={{ marginTop: '20px' }}>
                                                        <div className="cmp-row">
                                                            <span className="cmp-label">DETECTED LINK:</span>
                                                            <span className="cmp-val danger">{link.url}</span>
                                                        </div>
                                                        <div className="cmp-details">
                                                            <strong>THREAT:</strong> This link is impersonating <strong>{link.official}</strong>. It is designed to look official but leads to a malicious site.
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="threat-details-grid">
                                        {result.findings && result.findings.length > 0 ? (
                                            result.findings.map((f, index) => (
                                                <div key={index} className="pattern-pill">
                                                    <span className="pattern-dot"></span>
                                                    {f.category} ({f.count})
                                                </div>
                                            ))
                                        ) : (
                                            <div className="pattern-pill clear">
                                                <span className="pattern-dot safe"></span>
                                                Zero Manipulation Patterns Detected
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </main>

            {/* Clickable Device Badge Updated for Premium View */}
            <div 
                className="device-badge-premium" 
                onClick={toggleLayout}
                title="Toggle Responsive View (Desktop / Tablet / Mobile)"
            >
                <span className="badge-label">SIMULATOR: </span>
                <span className="badge-val">{deviceInfo.layout.toUpperCase()}</span>
                <div className="badge-hint">Click to Cycle Views</div>
            </div>
        </div>
    );
};

export default Analyze;
