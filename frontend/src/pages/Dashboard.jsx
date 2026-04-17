import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import { Link, useLocation } from 'react-router-dom';
import { 
    LayoutDashboard, 
    History, 
    ShieldCheck, 
    ShieldAlert, 
    Settings, 
    LogOut, 
    Search, 
    TrendingUp, 
    Bell, 
    HelpCircle, 
    Shield, 
    Activity,
    CheckCircle2,
    AlertTriangle,
    FileText,
    Globe,
    ChevronRight,
    User,
    Mail,
    Calendar,
    Lock,
    Info,
    Trash2
} from 'lucide-react';
import Swal from 'sweetalert2';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
    const location = useLocation();
    const [history, setHistory] = useState([]);
    const [user, setUser] = useState('');
    const [profile, setProfile] = useState(null);
    const [view, setView] = useState('overview'); 
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        document.title = 'Aegis Secure Console';
        const queryParams = new URLSearchParams(location.search);
        const viewParam = queryParams.get('view');
        if (viewParam) setView(viewParam);
        fetchDashboardData();
    }, [location]);

    const fetchDashboardData = async () => {
        try {
            const res = await axios.get(`${API_BASE_URL}/dashboard`, { withCredentials: true });
            setUser(res.data.user || 'Member');
            setProfile(res.data.profile || null);
            setHistory(res.data.history || []);
            setFetching(false);
        } catch (err) {
            if (err.response?.status === 401) {
                window.location.href = '/login';
            } else {
                setFetching(false);
                setError("Unable to synchronize with Aegis Core.");
            }
        }
    };

    const handleLogout = async () => {
        try {
            await axios.get(`${API_BASE_URL}/logout`, { withCredentials: true });
            window.location.href = '/login';
        } catch (err) {
            window.location.href = '/login';
        }
    };
    
    const handleHideAnalysis = async (id) => {
        const result = await Swal.fire({
            title: 'ERASE RECORD?',
            text: "This link/text will be removed from your display but preserved in the secure archive for total security metrics.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ff4d4d',
            cancelButtonColor: '#64FFDA',
            confirmButtonText: 'YES, ERASE',
            cancelButtonText: 'KEEP RECORD',
            background: '#111827',
            color: '#fff'
        });

        if (result.isConfirmed) {
            try {
                await axios.post(`${API_BASE_URL}/hide-analysis`, { id }, { withCredentials: true });
                // Update local state to remove the item from view immediately
                setHistory(prev => prev.filter(item => item._id !== id));
                
                Swal.fire({
                    title: 'ERASED',
                    text: 'The item has been removed from your audit log.',
                    icon: 'success',
                    timer: 1500,
                    showConfirmButton: false,
                    background: '#111827',
                    color: '#64FFDA'
                });
            } catch (err) {
                Swal.fire({
                    title: 'ERROR',
                    text: 'Unable to process erasure request.',
                    icon: 'error',
                    background: '#111827',
                    color: '#ff4d4d'
                });
            }
        }
    };

    // Calculate Analytics
    const stats = useMemo(() => {
        const total = history.length;
        const safe = history.filter(h => h.safety_status?.toLowerCase() === 'safe').length;
        const threats = history.filter(h => h.safety_status?.toLowerCase() === 'unsafe').length;
        const avgTrust = total > 0 ? Math.round(history.reduce((a, b) => a + (b.trust_score || 0), 0) / total) : 100;
        
        let risk = 'Low';
        if (avgTrust < 50) risk = 'High';
        else if (avgTrust < 80) risk = 'Medium';

        return { total, safe, threats, avgTrust, risk };
    }, [history]);

    // Chart Data Preparation
    const chartData = useMemo(() => {
        // Last 7 days scan activity
        const data = [];
        for(let i = 6; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            
            // Count scans for this date in history (assuming timestamp format matches loosely)
            const count = history.filter(h => {
                const hDate = new Date(h.timestamp);
                return hDate.toDateString() === d.toDateString();
            }).length;

            data.push({ name: dateStr, scans: count });
        }
        return data;
    }, [history]);

    const pieData = [
        { name: 'Safe', value: stats.safe, color: '#22C55E' },
        { name: 'Threats', value: stats.threats, color: '#EF4444' }
    ];

    if (fetching) {
        return (
            <div className="aegis-loader-screen">
                <Shield className="pulse-icon" size={48} />
                <span>Decrypting Vault Items...</span>
            </div>
        );
    }

    return (
        <div className="dashboard-layout">
            {/* Sidebar */}
            <aside className="aegis-sidebar">
                <Link to="/" className="sidebar-brand">
                    <div className="brand-logo-box">
                        <Shield size={20} />
                    </div>
                    <span>AEGIS <em>CORE</em></span>
                </Link>

                <div className="sidebar-profile">
                    <div className="profile-avatar">{user.charAt(0).toUpperCase()}</div>
                    <div className="profile-info">
                        <span className="profile-name">{user}</span>
                        <span className="profile-tag">SECURITY OPERATIVE</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <button className={`nav-item ${view === 'overview' ? 'active' : ''}`} onClick={() => setView('overview')}>
                        <LayoutDashboard size={20} /> Dashboard
                    </button>
                    <button className={`nav-item ${view === 'history' ? 'active' : ''}`} onClick={() => setView('history')}>
                        <History size={20} /> Full History
                    </button>
                    <button className={`nav-item ${view === 'safe' ? 'active' : ''}`} onClick={() => setView('safe')}>
                        <ShieldCheck size={20} /> Safe Sites
                    </button>
                    <button className={`nav-item ${view === 'unsafe' ? 'active' : ''}`} onClick={() => setView('unsafe')}>
                        <ShieldAlert size={20} /> Threats Blocked
                    </button>
                    <button className={`nav-item ${view === 'account' ? 'active' : ''}`} onClick={() => setView('account')}>
                        <User size={20} /> Account Profile
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <button className="sidebar-logout" onClick={handleLogout}>
                        <LogOut size={20} /> Logout System
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="dashboard-main">
                <div className="dashboard-container">
                    <header className="main-header">
                        <div className="header-left">
                        <h1>
                            {view === 'overview' && 'Security Overview'}
                            {view === 'history' && 'Neural Audit Log'}
                            {view === 'safe' && 'Verified Safe Vault'}
                            {view === 'unsafe' && 'Threat Archive'}
                            {view === 'account' && 'Intelligence Profile'}
                        </h1>
                        <p>
                            {view === 'safe' ? 'Verified domains in the Aegis database' : 
                             view === 'account' ? 'Manage your security credentials' :
                             `Operational status for operative: `}
                            {(view !== 'safe' && view !== 'account') && <strong>{user}</strong>}
                            {(view !== 'safe' && view !== 'account') && ' 👋'}
                        </p>
                    </div>

                    <div className="header-right">
                        <Link to="/analyze" className="btn-scan-analyzer">
                            <Search size={18} /> Launch Scanner
                        </Link>
                    </div>
                </header>

                <div className="view-container fade-in">
                    {view === 'overview' && (
                        <div className="overview-view">
                            {/* Stats Grid */}
                            <div className="stats-grid">
                                <div className="glass-card stat-tile">
                                    <div className="tile-icon icon-purple"><Activity size={24} /></div>
                                    <div className="tile-content">
                                        <label>Total Scans</label>
                                        <h3>{profile?.stats?.total_scans || 0}</h3>
                                    </div>
                                </div>
                                <div className="glass-card stat-tile">
                                    <div className="tile-icon icon-red"><ShieldAlert size={24} /></div>
                                    <div className="tile-content">
                                        <label>Threats Detected</label>
                                        <h3 className="text-danger">{profile?.stats?.threats || 0}</h3>
                                    </div>
                                </div>
                                <div className="glass-card stat-tile">
                                    <div className="tile-icon icon-green"><ShieldCheck size={24} /></div>
                                    <div className="tile-content">
                                        <label>Safe Sites</label>
                                        <h3 className="text-success">{profile?.stats?.safe || 0}</h3>
                                    </div>
                                </div>
                                <div className="glass-card stat-tile">
                                    <div className="tile-icon icon-gold"><TrendingUp size={24} /></div>
                                    <div className="tile-content">
                                        <label>Risk Level</label>
                                        <h3 className={`risk-${stats.risk.toLowerCase()}`}>{stats.risk}</h3>
                                    </div>
                                </div>
                            </div>

                            {/* Charts Row */}
                            <div className="charts-row">
                                <div className="glass-card chart-container">
                                    <div className="chart-header">
                                        <h3>Scan Activity (Last 7 Days)</h3>
                                        <span className="chart-subtitle">Neural traffic monitoring</span>
                                    </div>
                                    <div className="chart-body">
                                        <ResponsiveContainer width="100%" height={250}>
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                                                        <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                                <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                                                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                                                <Tooltip 
                                                    contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                                    itemStyle={{ color: '#fff' }}
                                                />
                                                <Area type="monotone" dataKey="scans" stroke="#7C3AED" strokeWidth={3} fillOpacity={1} fill="url(#colorScans)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                <div className="glass-card chart-container mini">
                                    <div className="chart-header">
                                        <h3>Threat Distribution</h3>
                                        <span className="chart-subtitle">Safe vs Dangerous</span>
                                    </div>
                                    <div className="chart-body">
                                        <ResponsiveContainer width="100%" height={250}>
                                            <PieChart>
                                                <Pie
                                                    data={pieData}
                                                    innerRadius={60}
                                                    outerRadius={80}
                                                    paddingAngle={10}
                                                    dataKey="value"
                                                >
                                                    {pieData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                                    ))}
                                                </Pie>
                                                <Tooltip 
                                                     contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                                />
                                            </PieChart>
                                        </ResponsiveContainer>
                                        <div className="pie-legend">
                                            <div className="legend-item"><span className="dot dot-green"></span> Safe</div>
                                            <div className="legend-item"><span className="dot dot-red"></span> Threats</div>
                                        </div>
                                    </div>
                                </div>
                            </div>


                        </div>
                    )}

                    {view === 'account' && profile && (
                        <div className="account-view fade-in">
                            <div className="profile-grid">
                                <div className="glass-card profile-main-card">
                                    <div className="profile-header-large">
                                        <div className="avatar-huge">{user.charAt(0).toUpperCase()}</div>
                                        <div className="profile-titles">
                                            <h2>{profile.username}</h2>
                                            <span className="badge-role">{profile.role}</span>
                                        </div>
                                    </div>

                                    <div className="profile-details-list">
                                        <div className="detail-item">
                                            <Mail size={18} className="text-purple" />
                                            <div className="detail-content">
                                                <label>Email Address</label>
                                                <span>{profile.email}</span>
                                            </div>
                                        </div>
                                        <div className="detail-item">
                                            <Calendar size={18} className="text-purple" />
                                            <div className="detail-content">
                                                <label>Member Since</label>
                                                <span>{profile.created_at}</span>
                                            </div>
                                        </div>
                                        <div className="detail-item">
                                            <Info size={18} className="text-purple" />
                                            <div className="detail-content">
                                                <label>Clearance Level</label>
                                                <span>Standard Operations</span>
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>
                    )}

                    {/* History View (Table style) */}
                    {(view === 'history' || view === 'safe' || view === 'unsafe') && (
                        <div className="table-view">
                            <div className="glass-card table-container">
                                <table className="aegis-table">
                                    <thead>
                                        <tr>
                                            <th>Safety Level</th>
                                            <th>Format</th>
                                            <th>Target Identity</th>
                                            <th>Trust Weight</th>
                                            <th>Captured At</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history
                                            .filter(h => {
                                                const status = h.safety_status?.toLowerCase();
                                                if (view === 'safe') return status === 'safe';
                                                if (view === 'unsafe') return status !== 'safe' && status !== 'unknown';
                                                return true;
                                            })
                                            .map((h, i) => (
                                                <tr key={i}>
                                                    <td>
                                                        <div className={`table-badge ${h.safety_status?.toLowerCase() === 'safe' ? 'badge-safe' : 'badge-danger'}`}>
                                                            {h.safety_status}
                                                        </div>
                                                    </td>
                                                    <td className="format-cell">{(h.type || 'unknown').toUpperCase()}</td>
                                                    <td className="target-cell">
                                                        <div className="identity-text">{h.url !== 'N/A' ? h.url : 'Neural Fragment'}</div>
                                                    </td>
                                                    <td>
                                                        <div className="trust-meter">
                                                            <div className="meter-bg"><div className="meter-fill" style={{ width: `${h.trust_score}%` }}></div></div>
                                                            <span className="meter-val">{h.trust_score}%</span>
                                                        </div>
                                                    </td>
                                                    <td className="date-cell">{h.timestamp}</td>
                                                    <td className="action-cell">
                                                        <button 
                                                            className="btn-erase" 
                                                            title="Erase from display"
                                                            onClick={() => handleHideAnalysis(h._id)}
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                                {history.filter(h => {
                                    const status = h.safety_status?.toLowerCase();
                                    if (view === 'safe') return status === 'safe';
                                    if (view === 'unsafe') return status !== 'safe' && status !== 'unknown';
                                    return true;
                                }).length === 0 && (
                                    <div className="empty-audit-state" style={{ padding: '60px', textAlign: 'center', opacity: 0.5 }}>
                                        <p>{view === 'safe' ? "No safe sites detected yet" : "No records found in this category"}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}


                </div>
                </div> { /* End dashboard-container */ }
            </main>
        </div>
    );
};

export default Dashboard;
