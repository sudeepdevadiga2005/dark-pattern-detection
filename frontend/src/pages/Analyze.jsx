import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import Cookies from 'js-cookie';
import './Analyze.css';

const Analyze = () => {
    const [input, setInput] = useState('');
    const [inputType, setInputType] = useState('url');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [controller, setController] = useState(null);

    const handleAnalyze = async () => {
        if (!input || !input.trim()) return;
        setIsAnalyzing(true);
        setResult(null);

        const cleanInput = input.trim();

        // 🛡️ High-Fidelity Validation 
        const isUrlPattern = (inputText) => {
            // If it has newlines or many spaces, it's a block of text, not a single URL
            if (inputText.includes('\n') || inputText.trim().split(/\s+/).length > 1) return false;

            const host = inputText.replace('http://', '').replace('https://', '').split('/')[0];
            const urlRegex = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}(?:\.[a-z]{2,})?$/i;
            return urlRegex.test(host);
        };

        const isPureUrl = isUrlPattern(cleanInput);

        if (inputType === 'url') {
            const typoUrlRegex = /^[a-z0-9.-]+\,[a-z]{2,4}$/i;
            const host = cleanInput.replace('http://', '').replace('https://', '').split('/')[0];
            const isMalformedUrl = typoUrlRegex.test(host) && !isPureUrl;

            if (isMalformedUrl) {
                setResult({
                    success: false,
                    error: "INVALID URL FORMAT DETECTED: You appear to have used a comma (,) instead of a dot (.) in your domain. Please correct the URL (e.g. amazon.com) and try again."
                });
                setIsAnalyzing(false);
                return;
            }

            if (!isPureUrl && cleanInput.includes(' ')) {
                setResult({
                    success: false,
                    error: "INVALID TARGET: You entered a block of text. Please switch to TEXT AUDIT mode to analyze paragraphs or sentences."
                });
                setIsAnalyzing(false);
                return;
            }

            if (!isPureUrl) {
                setResult({
                    success: false,
                    error: "INVALID URL: The provided string does not look like a valid domain or URL."
                });
                setIsAnalyzing(false);
                return;
            }
        }

        if (inputType === 'text') {
            if (isPureUrl) {
                setResult({
                    success: false,
                    error: "INVALID TARGET: You entered a single URL. Please switch to URL SCAN mode for specialized domain logic."
                });
                setIsAnalyzing(false);
                return;
            }
        }

        const abortController = new AbortController();
        setController(abortController);

        try {
            const endpoint = inputType === 'url' ? '/analyze' : '/analyze-text';
            const payload = inputType === 'url' ? { url: cleanInput } : { text: cleanInput };

            const res = await axios.post(`${API_BASE_URL}${endpoint}`, payload, {
                signal: abortController.signal
            });

            // Simulate aegis delay for "wow" effect
            setTimeout(() => {
                setResult(res.data);
                setIsAnalyzing(false);
                setController(null);
            }, 1200);
        } catch (err) {
            if (axios.isCancel(err)) {
                console.log("Analysis aborted by user.");
                return;
            }
            console.error(err);
            setIsAnalyzing(false);
            setResult({ success: false, error: "Aegis Network Link Failure. Check if the backend server is online." });
            setController(null);
        }
    };

    const handleStopAnalyze = () => {
        if (controller) {
            controller.abort();
            setIsAnalyzing(false);
            setController(null);
            setResult({ success: false, error: "AEGIS SCAN ABORTED BY OPERATIVE. Connection terminated." });
        }
    };

    return (
        <div className={`analyze-portal-wrapper ${isAnalyzing ? 'is-scanning' : ''} ${result && (result.classification === 'Scam' || result.classification === 'Fake') ? 'danger-alert' : result && result.classification === 'Suspicious' ? 'warning-alert' : ''}`}>
            {/* The Cinematic Background Layer */}
            <div className="analyze-bg-overlay">
                <div className="aegis-scan-lines"></div>
                <div className="dynamic-glow-sphere"></div>
            </div>

            <nav className="analyze-mini-nav fade-in">
                <div className="brand">
                    <div className="brand-mark">A</div>
                    <span className="brand-title">AEGIS <em>AUDITOR</em></span>
                </div>
                <Link to="/" className="btn-back-home">← TERMINAL EXIT</Link>
            </nav>

            <main className="analyze-content fade-in">
                <header className="terminal-header">
                    <span className="live-badge">SYSTEM: ONLINE</span>
                    <h1>Dark Pattern <em>Analyzer</em></h1>
                    <p>Input target URL or content fragments for real-time ML security verification.</p>
                </header>

                <div className="glass-terminal stagger-1">
                    <div className="terminal-controls">

                        <div className="input-type-toggle">
                            <div className="analyze-toggle-bg">
                                <div className={`analyze-toggle-slider ${inputType === 'text' ? 'slide-right' : ''}`}></div>
                            </div>
                            <button
                                className={`analyze-toggle-btn ${inputType === 'url' ? 'active' : ''}`}
                                onClick={() => { setInputType('url'); setInput(''); setResult(null); }}
                                disabled={isAnalyzing}
                            >
                                URL SCAN
                            </button>
                            <button
                                className={`analyze-toggle-btn ${inputType === 'text' ? 'active' : ''}`}
                                onClick={() => { setInputType('text'); setInput(''); setResult(null); }}
                                disabled={isAnalyzing}
                            >
                                TEXT AUDIT
                            </button>
                        </div>

                        <div className="input-group-main">
                            <textarea
                                placeholder={inputType === 'url' ? "Paste target URL here for full aegis audit..." : "Paste deep-content or emails here for textual aegis audit..."}
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
                                    {isAnalyzing ? (
                                        <>
                                            <span className="spinner-aegis"></span>
                                            AEGIS AGENT ACTIVE...
                                        </>
                                    ) : 'LAUNCH DEEP ANALYSIS'}
                                </button>

                                {isAnalyzing && (
                                    <button
                                        className="btn-abort-scan fade-in"
                                        onClick={handleStopAnalyze}
                                    >
                                        STOP AEGIS AGENT
                                    </button>
                                )}
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
                                    <div className={`result-summary ${(result.status === 'SUSPICIOUS' || result.status === 'FAKE')
                                        ? 'danger-badge'
                                        : (result.status === 'POTENTIALLY_SUSPICIOUS')
                                            ? 'warning-badge'
                                            : (result.status === 'UNKNOWN' || result.status === 'INVALID_INPUT' || result.status === 'NOT_ENOUGH_DATA')
                                                ? 'neutral-badge'
                                                : 'safe-badge'
                                        }`}>
                                        <div className="indicator-icon">
                                            {(result.status === 'SUSPICIOUS' || result.status === 'FAKE') ? '🚨' :
                                                (result.status === 'POTENTIALLY_SUSPICIOUS') ? '⚠️' :
                                                    (result.status === 'UNKNOWN' || result.status === 'INVALID_INPUT' || result.status === 'NOT_ENOUGH_DATA') ? 'ℹ️' : '✅'}
                                        </div>
                                        <div className="indicator-text">
                                            <h2>
                                                {result.status === 'FAKE'
                                                    ? 'FAKE SITE DETECTED'
                                                    : result.status === 'SUSPICIOUS'
                                                        ? 'THREAT DETECTED'
                                                        : result.status === 'POTENTIALLY_SUSPICIOUS'
                                                            ? 'SUSPICIOUS ACTIVITY'
                                                            : result.status === 'INVALID_INPUT'
                                                                ? 'NOT APPLICABLE'
                                                                : result.status === 'UNKNOWN'
                                                                    ? 'SYSTEM UNKNOWN'
                                                                    : (result.status === 'SAFE' || result.status === 'LIKELY_SAFE' || result.status === 'LOW_RISK_TEXT')
                                                                        ? (result.input_type === 'text' ? 'LOW RISK TEXT' : 'VERIFIED OFFICIAL')
                                                                        : 'URL NOT FOUND'}
                                            </h2>
                                            <p>{result.message || "This item is not in our official verification archive. Please proceed with caution if it asks for personal metadata."}</p>
                                        </div>
                                        {/* Score ring mapping using actual trust_score */}
                                        <div className="score-ring" style={{ borderColor: result.trust_score < 40 ? '#e53e3e' : result.trust_score < 70 ? '#ecc94b' : '#38a169' }}>
                                            <span className="score-val" style={{ color: result.trust_score < 40 ? '#e53e3e' : result.trust_score < 70 ? '#ecc94b' : '#38a169' }}>
                                                {result.trust_score || 0}%
                                            </span>
                                            <span className="score-label">TRUST</span>
                                        </div>
                                        {/* Authenticity Stage Output */}
                                        {result.source && (
                                            <div className="category-badge-main">
                                                <span className="category-val">{result.source.replace(/_/g, ' ').toUpperCase()}</span>
                                                <span className="category-label">INTELLIGENCE SOURCE</span>
                                            </div>
                                        )}
                                        {/* Optional Category */}
                                        {result.category && (
                                            <div className="category-badge-main" style={{ minWidth: '150px' }}>
                                                <span className="category-val">{result.category.toUpperCase()}</span>
                                                <span className="category-label">CATEGORY</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Intelligence Rationale */}
                                    {result.reasons && result.reasons.length > 0 && (
                                        <div className="intelligence-rationale fade-in">
                                            <div className="rationale-header">
                                                <span className="rationale-tag">INTELLIGENCE RATIONALE</span>
                                                <h3>Aegis Decision Summary</h3>
                                            </div>

                                            {result.conclusion_from_internet && (
                                                <div className="conclusion-internet-box" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '15px', borderRadius: '12px', marginBottom: '25px', borderLeft: '4px solid #64FFDA' }}>
                                                    <span style={{ fontSize: '10px', color: '#64FFDA', fontWeight: '800', display: 'block', marginBottom: '8px', letterSpacing: '0.1em' }}>AEGIS INTERNET CONCLUSION:</span>
                                                    <p style={{ fontSize: '14px', lineHeight: '1.5', opacity: 0.9, color: '#fff' }}>{result.conclusion_from_internet}</p>
                                                </div>
                                            )}
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
                                    {result.type === 'url' && result.official_url && result.official_url !== result.target_url && (
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
                                                <span className="forensic-tag">EMBEDDED LINK AUDIT</span>
                                                <h3>Scanned Routing Vectors</h3>
                                            </div>
                                            <div className="hidden-links-list">
                                                {result.url_analysis.map((link, idx) => (
                                                    <div key={idx} className="comparison-card" style={{ marginTop: '20px' }}>
                                                        <div className="cmp-row" style={{ background: link.is_safe ? 'rgba(100, 255, 218, 0.05)' : 'rgba(255, 77, 77, 0.05)' }}>
                                                            <span className="cmp-label">DETECTED LINK:</span>
                                                            <span className={`cmp-val ${link.is_safe ? 'safe' : 'danger'}`}>{link.url}</span>
                                                        </div>
                                                        <div className="cmp-details" style={{ color: link.is_safe ? '#64FFDA' : '#ff4d4d', background: link.is_safe ? 'rgba(100,255,218,0.05)' : 'rgba(255,255,255,0.03)' }}>
                                                            {link.is_safe ? (
                                                                <><strong>VERIFIED SECURE:</strong> This link was routed through internet domain verification and confirmed as a <strong>{link.official}</strong>.</>
                                                            ) : (
                                                                <><strong>THREAT:</strong> This link is impersonating <strong>{link.official}</strong>. It is designed to look official but leads to an unverified or malicious site.</>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Live Scrape Details */}
                                    {result.type === 'url' && result.scraped_details && (
                                        <div className="forensic-analysis fade-in">
                                            <div className="forensic-header">
                                                <span className="forensic-tag">LIVE INTERNET SCRAPE</span>
                                                <h3>Extracted Target Details</h3>
                                            </div>
                                            <div className="comparison-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
                                                <div className="cmp-row" style={{ gridColumn: '1 / -1', marginBottom: '10px' }}>
                                                    <span className="cmp-label">PAGE TITLE:</span>
                                                    <span className="cmp-val" style={{ marginLeft: '10px', fontWeight: '500' }}>{result.scraped_details.title}</span>
                                                </div>
                                                <div className="cmp-row" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: 'none' }}>
                                                    <span className="cmp-val safe" style={{ fontSize: '24px' }}>{result.scraped_details.linksCount}</span>
                                                    <span className="cmp-label" style={{ marginTop: '5px' }}>LINKS FOUND</span>
                                                </div>
                                                <div className="cmp-row" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: 'none' }}>
                                                    <span className="cmp-val safe" style={{ fontSize: '24px' }}>{result.scraped_details.imagesCount}</span>
                                                    <span className="cmp-label" style={{ marginTop: '5px' }}>IMAGES DETECTED</span>
                                                </div>
                                                <div className="cmp-row" style={{ gridColumn: '1 / -1', display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: 'none' }}>
                                                    <span className="cmp-val safe" style={{ fontSize: '24px' }}>{result.scraped_details.words}</span>
                                                    <span className="cmp-label" style={{ marginTop: '5px' }}>TOTAL WORDS</span>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    <div className="threat-details-grid">
                                        {result.findings && result.findings.length > 0 ? (
                                            result.findings.map((f, index) => (
                                                <div key={index} className="pattern-pill">
                                                    <span className="pattern-dot"></span>
                                                    {typeof f === 'string' ? f : `${f.category || 'Threat'} (${f.count || 1})`}
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
        </div>
    );
};

export default Analyze;
