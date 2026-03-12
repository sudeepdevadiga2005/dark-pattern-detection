import React, { useState } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { Link } from 'react-router-dom';
import './WebScraper.css';

const WebScraper = () => {
    const [url, setUrl] = useState('');
    const [status, setStatus] = useState('Ready to scan website details.');
    const [isScanning, setIsScanning] = useState(false);
    const [results, setResults] = useState(null);

    // Ensure cookies are sent with requests
    axios.defaults.withCredentials = true;

    const handleScrape = async () => {
        if (!url) {
            setStatus("Please enter a valid URL.");
            return;
        }

        setIsScanning(true);
        setStatus("Scraping page details from backend...");
        setResults(null);

        try {
            const res = await axios.post(`${API_BASE_URL}/scrape-details`, { url });

            if (res.data.success) {
                setResults(res.data);
                setStatus("Scraping Complete!");
            } else {
                setStatus(`Error: ${res.data.error || 'Failed to scrape.'}`);
            }
        } catch (err) {
            if (err.response?.status === 401) {
                window.location.href = '/login';
            } else {
                setStatus("Error: Backend unreachable. Make sure the local server is running.");
            }
        } finally {
            setIsScanning(false);
        }
    };

    const handleAnalyze = async () => {
        if (!url) {
            setStatus("Please enter a valid URL.");
            return;
        }

        setIsScanning(true);
        setStatus("Sending to Dark Pattern Analyzer...");
        setResults(null);

        try {
            const res = await axios.post(`${API_BASE_URL}/analyze`, { url });

            if (res.data.success || res.data.total_patterns_found !== undefined) {
                setStatus(`Analysis Complete: Detected ${res.data.total_patterns_found || 0} patterns!`);
                // Check dashboard for full results.
            } else {
                setStatus(`Analysis Error: ${res.data.error || "Failed analysis."}`);
            }
        } catch (err) {
            setStatus("Error connecting to analyzer.");
        } finally {
            setIsScanning(false);
        }
    };

    return (
        <div className="scraper-layout">
            <header className="scraper-header">
                <Link to="/dashboard" className="back-btn">← Back to Dashboard</Link>
                <h1>Ultimate Web Scraper</h1>
                <p className="subtitle-scraper">Analyze & Extract Details natively inside the app.</p>
            </header>

            <div className="scraper-content">
                <div className="input-group">
                    <input
                        type="text"
                        className="scraper-input"
                        placeholder="https://example.com"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                    />
                </div>

                <div className={`status-panel-scraper ${isScanning ? 'scanning' : ''}`}>
                    {status}
                </div>

                {results && (
                    <div className="results-panel-scraper fade-in">
                        <div className="data-row-scraper">
                            <span className="label">Title</span>
                            <span className="value truncate">{results.title || "N/A"}</span>
                        </div>
                        <div className="data-row-scraper">
                            <span className="label">Scraped URL</span>
                            <span className="value truncate">{results.url || "N/A"}</span>
                        </div>
                        <div className="stats-grid-scraper">
                            <div className="stat-box-scraper">
                                <span className="stat-val">{results.linksCount || 0}</span>
                                <span className="stat-label">Links Found</span>
                            </div>
                            <div className="stat-box-scraper">
                                <span className="stat-val">{results.imagesCount || 0}</span>
                                <span className="stat-label">Images</span>
                            </div>
                            <div className="stat-box-scraper">
                                <span className="stat-val">{results.words || 0}</span>
                                <span className="stat-label">Total Words</span>
                            </div>
                        </div>
                    </div>
                )}

                <div className="actions-scraper">
                    <button onClick={handleScrape} disabled={isScanning} className="primary-btn-scraper">
                        {isScanning ? 'Processing...' : 'Scrape Basic Details'}
                    </button>
                    <button onClick={handleAnalyze} disabled={isScanning} className="secondary-btn-scraper">
                        Run Deep Dark Pattern Analysis
                    </button>
                </div>
            </div>
        </div>
    );
};

export default WebScraper;
