import React, { useState, useEffect } from 'react';
import { 
    Activity, Users, Shield, Zap, Search, ArrowUpRight, 
    Download, RefreshCcw, LayoutDashboard, Database, 
    Bell, Settings, LogOut, ChevronRight, UserCheck, ShieldAlert
} from 'lucide-react';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, 
    Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import axios from 'axios';
import './AdminDashboard.css';

const API_BASE_URL = "http://localhost:5000/api";

const AdminDashboard = () => {
    const [stats, setStats] = useState({ total_users: 0, total_scans: 0, daily_stats: [] });
    const [users, setUsers] = useState([]);
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'users', 'scans', 'analytics'

    useEffect(() => {
        fetchStats();
        fetchUsers();
        fetchScans();
    }, []);

    const fetchStats = async (retries = 6) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/admin/stats`, { withCredentials: true });
            setStats(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            if (!err.response && retries > 0) {
                // Connection refused or network error - server is booting up. Retry in 2 seconds.
                setTimeout(() => fetchStats(retries - 1), 2000);
            } else if (err.response?.status === 403 || err.response?.status === 401) {
                window.location.href = '/admin/login';
            } else {
                setLoading(false);
            }
        }
    };

    const fetchUsers = async (retries = 6) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/admin/users`, { withCredentials: true });
            setUsers(res.data);
        } catch (err) {
            console.error(err);
            if (!err.response && retries > 0) {
                setTimeout(() => fetchUsers(retries - 1), 2000);
            }
        }
    };

    const fetchScans = async (retries = 6) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/admin/scans`, { withCredentials: true });
            setScans(res.data);
        } catch (err) {
            console.error(err);
            if (!err.response && retries > 0) {
                setTimeout(() => fetchScans(retries - 1), 2000);
            }
        }
    };

    const handleLogout = async () => {
        try {
            await axios.get(`${API_BASE_URL}/logout`, { withCredentials: true });
            // Remove admin cookie
            document.cookie = "is_admin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = '/admin/login';
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) {
        return (
            <div className="admin-loading" style={{ flexDirection: 'column', gap: '20px' }}>
                <Activity size={40} style={{ color: '#64FFDA', filter: 'drop-shadow(0 0 10px rgba(100, 255, 218, 0.4))' }} />
                <div>INITIALIZING COMMAND CENTER...</div>
                <div style={{ fontSize: '10px', opacity: 0.6, letterSpacing: '0.1em', marginTop: '-10px', textTransform: 'uppercase' }}>
                    Establishing Neural Link With Local Backend. Waiting for Machine Learning Model to boot up...
                </div>
            </div>
        );
    }

    return (
        <div className="admin-wrapper fade-in">
            {/* Sidebar */}
            <aside className="admin-sidebar">
                <div className="admin-brand">
                    <Shield size={28} className="brand-glow" />
                    <div className="brand-text">
                        <h3>NEURAL</h3>
                        <p>COMMAND CENTER</p>
                    </div>
                </div>

                <nav className="admin-nav">
                    <div 
                        className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        <LayoutDashboard size={18} /> OVERVIEW
                    </div>
                    <div 
                        className={`nav-item ${activeTab === 'users' ? 'active' : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        <Users size={18} /> USER ARCHIVE
                    </div>
                    <div 
                        className={`nav-item ${activeTab === 'scans' ? 'active' : ''}`}
                        onClick={() => setActiveTab('scans')}
                    ><Database size={18} /> SCAN LOGS</div>
                    <div 
                        className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
                        onClick={() => setActiveTab('analytics')}
                    ><Activity size={18} /> LIVE ANALYTICS</div>
                    <div className="nav-spacer"></div>
                    <div className="nav-item logout" onClick={handleLogout}><LogOut size={18} /> TERMINAL EXIT</div>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="admin-main">
                <header className="admin-header">
                    <div className="header-search">
                        <Search size={18} />
                        <input type="text" placeholder="Search Neural Archive..." />
                    </div>
                    <div className="header-actions">
                        <div className="notification-bell"><Bell size={18} /><span className="bell-dot"></span></div>
                        <Settings size={18} />
                        <div className="admin-profile">SD</div>
                    </div>
                </header>

                <div className="admin-viewport">
                    <div className="viewport-header">
                        <h2>
                            {activeTab === 'overview' && 'System Command Center'}
                            {activeTab === 'users' && 'User Database Management'}
                            {activeTab === 'scans' && 'Global Neural Scan Logs'}
                            {activeTab === 'analytics' && 'Advanced Live Analytics'}
                        </h2>
                        <div className="report-actions">
                            <button className="btn-refresh" onClick={() => {
                                if (activeTab === 'overview') fetchStats();
                                else if (activeTab === 'users') fetchUsers();
                                else if (activeTab === 'scans') fetchScans();
                            }}>
                                <RefreshCcw size={14} /> REFRESH
                            </button>
                            <button className="btn-download"><Download size={14} /> EXPORT REPORT</button>
                        </div>
                    </div>

                    {activeTab === 'overview' ? (
                        <>
                            {/* Stats Grid */}
                            <div className="stats-grid">
                                <div className="stat-card">
                                    <div className="stat-icon users"><Users /></div>
                                    <div className="stat-info">
                                        <label>Total Intelligence Units (Users)</label>
                                        <h4>{stats.total_users}</h4>
                                        <span className="growth positive"><ArrowUpRight size={14} /> +12% this month</span>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon scans"><Zap /></div>
                                    <div className="stat-info">
                                        <label>Total Neural Scans Conducted</label>
                                        <h4>{stats.total_scans}</h4>
                                        <span className="growth positive"><ArrowUpRight size={14} /> +28% this week</span>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon shield"><Shield /></div>
                                    <div className="stat-info">
                                        <label>System Integrity Level</label>
                                        <h4>99.8%</h4>
                                        <span className="stability">SYSTEM STABLE</span>
                                    </div>
                                </div>
                            </div>

                            {/* Charts Section */}
                            <div className="charts-main">
                                <div className="chart-container">
                                    <div className="chart-header">
                                        <h3>7-Day Scan Velocity</h3>
                                        <div className="period-tabs"><span>D</span><span className="active">W</span><span>M</span></div>
                                    </div>
                                    <div className="chart-wrapper">
                                        <ResponsiveContainer width="100%" height={300}>
                                            <AreaChart data={stats.daily_stats}>
                                                <defs>
                                                    <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#64FFDA" stopOpacity={0.3}/>
                                                        <stop offset="95%" stopColor="#64FFDA" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                                <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" />
                                                <YAxis stroke="rgba(255,255,255,0.3)" />
                                                <Tooltip 
                                                    contentStyle={{ background: '#0A192F', border: '1px solid #64FFDA' }}
                                                    itemStyle={{ color: '#64FFDA' }}
                                                />
                                                <Area type="monotone" dataKey="scans" stroke="#64FFDA" fillOpacity={1} fill="url(#colorScans)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                <div className="stats-sidebar">
                                    <div className="recent-activity">
                                        <h3>Neural Log Stream</h3>
                                        <div className="activity-list">
                                            <div className="activity-item">
                                                <div className="activity-mark"></div>
                                                <div className="activity-details">
                                                    <p>New Intelligence Registered</p>
                                                    <small>2 minutes ago</small>
                                                </div>
                                                <ChevronRight size={16} />
                                            </div>
                                            <div className="activity-item">
                                                <div className="activity-mark threat"></div>
                                                <div className="activity-details">
                                                    <p>Blockade Active: amaz0n.com</p>
                                                    <small>45 mins ago</small>
                                                </div>
                                                <ChevronRight size={16} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : activeTab === 'users' ? (
                        <div className="users-view fade-in">
                            <div className="data-table-container">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>ID / AVATAR</th>
                                            <th>IDENTITY</th>
                                            <th>REGISTRATION DATE</th>
                                            <th>PRIVILEGE LEVEL</th>
                                            <th>ACTIONS</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.map((user, idx) => (
                                            <tr key={user._id}>
                                                <td>
                                                    <div className="user-idx-box">#{idx + 1}</div>
                                                </td>
                                                <td>
                                                    <div className="user-cell-info">
                                                        <span className="username">{user.username}</span>
                                                        <small className="email">{user.email}</small>
                                                    </div>
                                                </td>
                                                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                                                <td>
                                                    {user.is_admin ? (
                                                        <span className="badge badge-admin"><Shield size={12} /> ADMINISTRATOR</span>
                                                    ) : (
                                                        <span className="badge badge-user"><UserCheck size={12} /> OPERATIVE</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <button className="btn-table-action"><ShieldAlert size={14} /> REVOKE</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : activeTab === 'scans' ? (
                        <div className="users-view fade-in">
                            <div className="data-table-container">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>TIMESTAMP</th>
                                            <th>OPERATIVE</th>
                                            <th>TARGET URL</th>
                                            <th>SAFETY STATUS</th>
                                            <th>THREATS FOUND</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {scans.map((scan) => (
                                            <tr key={scan._id}>
                                                <td style={{fontSize: '12px'}}>{scan.timestamp}</td>
                                                <td><span className="badge badge-user" style={{textTransform:'none'}}>{scan.username}</span></td>
                                                <td style={{maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '12px'}}>
                                                    {scan.url}
                                                    {scan.type === 'text' && <span style={{color: '#8B5CF6', marginLeft: '5px'}}>(Text Scan)</span>}
                                                </td>
                                                <td>
                                                    {scan.safety_status === 'Safe' ? 
                                                        <span style={{color: '#64FFDA', fontWeight: 'bold'}}><Shield size={12} style={{marginRight:'5px'}}/>SAFE</span> : 
                                                        <span style={{color: '#ff4d4d', fontWeight: 'bold'}}>{scan.safety_status}</span>
                                                    }
                                                </td>
                                                <td>
                                                    <span className={scan.total_patterns_found > 0 ? "badge badge-admin" : "badge badge-user"} style={scan.total_patterns_found > 0 ? {borderColor: '#ff4d4d', color: '#ff4d4d', background: 'rgba(255, 77, 77, 0.1)'} : {}}>
                                                        {scan.total_patterns_found} Patterns
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="users-view fade-in" style={{textAlign: 'center', padding: '100px 0'}}>
                            <Activity size={48} style={{color: '#64FFDA', margin: '0 auto 20px', opacity: 0.5}} />
                            <h3 style={{fontSize: '24px', marginBottom: '10px'}}>Neural Link Establishing...</h3>
                            <p style={{color: 'rgba(255,255,255,0.4)', maxWidth: '400px', margin: '0 auto', fontSize: '14px', lineHeight: '1.6'}}>
                                Advanced real-time live analytics node is currently calibrating. Live stream visualizers will be fully operational in the next security patch.
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default AdminDashboard;
