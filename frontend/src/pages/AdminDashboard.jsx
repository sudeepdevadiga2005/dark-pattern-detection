import React, { useState, useEffect } from 'react';
import { 
    Activity, Users, Shield, Zap, Search, ArrowUpRight, 
    Download, RefreshCcw, LayoutDashboard, Database, 
    Bell, Settings, LogOut, ChevronRight, UserCheck, ShieldAlert,
    ArrowLeft
} from 'lucide-react';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, 
    Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import axios from 'axios';
import Swal from 'sweetalert2';
import './AdminDashboard.css';

const API_BASE_URL = "/api";

const AdminDashboard = () => {
    const [stats, setStats] = useState({ 
        total_users: 0, total_scans: 0, total_safe: 0, total_threats: 0, 
        hourly_stats: [], weekly_stats: [], monthly_stats: [] 
    });
    const [chartRange, setChartRange] = useState('W');
    const [users, setUsers] = useState([]);
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'users', 'scans', 'analytics', 'register'
    const [regForm, setRegForm] = useState({ username: '', email: '', password: '' });
    const [adminName, setAdminName] = useState('SD');
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const [heartbeatStatus, setHeartbeatStatus] = useState('stable'); // 'stable', 'checking', 'error'
    const [searchQuery, setSearchQuery] = useState('');
    const [viewingUserLogs, setViewingUserLogs] = useState(null); // stores user object to view logs for

    useEffect(() => {
        document.title = 'Dark Pattern Admin';
        fetchStats();
        fetchUsers();
        fetchScans();
        
        // Establish Aegis Pulse (Heartbeat) every 60 seconds
        const pulseInterval = setInterval(checkSessionPulse, 60000);
        return () => clearInterval(pulseInterval);
    }, []);

    const [isRefreshing, setIsRefreshing] = useState(false);

    const checkSessionPulse = async () => {
        try {
            setHeartbeatStatus('checking');
            const res = await axios.get(`${API_BASE_URL}/admin/stats`, { withCredentials: true });
            if (res.data) setHeartbeatStatus('stable');
        } catch (err) {
            if (err.response?.status === 401 || err.response?.status === 403) {
                setHeartbeatStatus('error');
                verifyAndLogout();
            }
        }
    };

    const verifyAndLogout = async () => {
        if (isLoggingOut) return;
        try {
            await axios.get(`${API_BASE_URL}/admin/stats`, { withCredentials: true });
            setHeartbeatStatus('stable');
        } catch (err) {
            if (err.response?.status === 401 || err.response?.status === 403) {
                window.location.href = '/admin/login';
            }
        }
    };

    const refreshDashboard = async () => {
        setIsRefreshing(true);
        await Promise.all([fetchStats(), fetchUsers(), fetchScans()]);
        setTimeout(() => setIsRefreshing(false), 500); // Small delay for UX
    };

    const fetchStats = async (retries = 6) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/admin/stats`, { withCredentials: true });
            setStats(res.data);
            if (res.data.admin_username) setAdminName(res.data.admin_username.substring(0, 2).toUpperCase());
            setLoading(false);
            setHeartbeatStatus('stable');
        } catch (err) {
            console.error(err);
            if (!err.response && retries > 0) {
                setTimeout(() => fetchStats(retries - 1), 2000);
            } else if (err.response?.status === 403 || err.response?.status === 401) {
                verifyAndLogout();
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

    const handleClearLogs = async () => {
        const { value: formValues } = await Swal.fire({
            title: viewingUserLogs ? `SURGICAL CLEAR: ${viewingUserLogs.username}` : 'TOTAL AEGIS PURGE',
            html: `
                <p style="color: rgba(255,255,255,0.6); margin-bottom: 20px; font-size: 14px;">
                    ${viewingUserLogs ? 'Clear all historical search records for this operative.' : 'Select purge mode for the entire administrative network.'}
                </p>
                
                ${!viewingUserLogs ? `
                <div style="margin-bottom: 20px; text-align: left;">
                    <label style="color: #64FFDA; font-size: 12px; font-weight: bold;">PURGE OPERATION TYPE:</label>
                    <select id="swal-input-mode" style="width: 100%; height: 50px; background: rgba(255,255,255,0.05); color: #fff; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; margin-top: 5px; padding: 0 10px;">
                        <option value="logs">CLEAR LOGS ONLY (Historical Scans)</option>
                        <option value="both">FULL RE-START (Delete All Clients + All Logs)</option>
                    </select>
                </div>
                ` : '<input type="hidden" id="swal-input-mode" value="logs">'}

                <div style="position: relative; width: 100%; display: flex; align-items: center; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <input type="password" id="swal-input-password" autocomplete="new-password" class="swal2-input" placeholder="Enter administrative passcode..." style="width: 100%; border: none; background: transparent; color: #fff; margin: 0; padding: 15px; height: 50px; font-size: 14px;">
                    <div id="toggle-pw-visibility" style="padding: 0 15px; cursor: pointer; color: #64FFDA; font-size: 18px; user-select: none;">
                        👁️
                    </div>
                </div>
            `,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ff4d4d',
            cancelButtonColor: '#64FFDA',
            confirmButtonText: 'PURGE SECURELY',
            background: '#020617',
            color: '#fff',
            focusConfirm: false,
            preConfirm: () => {
                const password = document.getElementById('swal-input-password').value;
                const mode = document.getElementById('swal-input-mode').value;
                if (!password) {
                    Swal.showValidationMessage('Administrative passcode is required to initiate purge.');
                    return false;
                }
                return { password, mode };
            },
            didOpen: () => {
                const input = document.getElementById('swal-input-password');
                const toggle = document.getElementById('toggle-pw-visibility');
                input.style.boxShadow = 'none';
                
                toggle.addEventListener('click', () => {
                    const isPassword = input.getAttribute('type') === 'password';
                    input.setAttribute('type', isPassword ? 'text' : 'password');
                    toggle.innerText = isPassword ? '🔒' : '👁️';
                });
            }
        });

        if (formValues && formValues.password) {
            try {
                const payload = { 
                    password: formValues.password, 
                    mode: formValues.mode
                };
                if (viewingUserLogs) payload.client_id = viewingUserLogs.client_id;
                
                const res = await axios.post(`${API_BASE_URL}/admin/clear-logs`, payload, { withCredentials: true });
                if (res.data.success) {
                    Swal.fire({
                        title: 'PURGED',
                        text: res.data.message,
                        icon: 'success',
                        background: '#020617',
                        color: '#64FFDA'
                    });
                    refreshDashboard();
                }
            } catch (err) {
                Swal.fire({
                    title: 'ACCESS DENIED',
                    text: err.response?.data?.message || 'Verification Failed',
                    icon: 'error',
                    background: '#020617',
                    color: '#ff4d4d'
                });
            }
        }
    };

    const handleLogout = async () => {
        const result = await Swal.fire({
            title: 'TERMINAL EXIT',
            text: "Are you sure you want to terminate the current administrative session?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ff4d4d',
            cancelButtonColor: '#64FFDA',
            confirmButtonText: 'YES, TERMINATE',
            cancelButtonText: 'STAY SECURE',
            background: '#020617',
            color: '#fff'
        });

        if (!result.isConfirmed) return;

        setIsLoggingOut(true);
        try {
            await axios.get(`${API_BASE_URL}/logout`, { withCredentials: true });
            document.cookie = "is_admin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = '/admin/login';
        } catch (err) {
            console.error(err);
            window.location.href = '/admin/login';
        }
    };

    if (loading) {
        return (
            <div className="admin-loading" style={{ flexDirection: 'column', gap: '20px' }}>
                <Activity size={40} style={{ color: '#64FFDA', filter: 'drop-shadow(0 0 10px rgba(100, 255, 218, 0.4))' }} />
                <div>INITIALIZING COMMAND CENTER...</div>
                <div style={{ fontSize: '10px', opacity: 0.6, letterSpacing: '0.1em', marginTop: '-10px', textTransform: 'uppercase' }}>
                    Establishing Aegis Link With Local Backend. Waiting for Machine Learning Model to boot up...
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
                        <h3>AEGIS</h3>
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
                        className={`nav-item ${activeTab === 'users' || viewingUserLogs ? 'active' : ''}`}
                        onClick={() => { setViewingUserLogs(null); setActiveTab('users'); }}
                    >
                        <Users size={18} /> USER ARCHIVE
                    </div>
                    {/* Scan logs sidebar entry removed as per request - accessible via User clicks */}
                    <div className="nav-spacer"></div>
                    <div className="nav-item logout" onClick={handleLogout}><LogOut size={18} /> TERMINAL EXIT</div>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="admin-main">
                <header className="admin-header">
                    <div className="header-search">
                        <Search size={18} />
                        <input 
                            type="text" 
                            placeholder="Find ID, Operative, or Target URL..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            autoComplete="off"
                        />
                    </div>
                    <div className="header-actions">
                        <div className="notification-bell" title={`Session Pulse: ${heartbeatStatus}`}>
                            <Bell size={18} />
                            <span className="bell-dot" style={{ background: heartbeatStatus === 'stable' ? '#64ffda' : (heartbeatStatus === 'checking' ? '#fbbf24' : '#ff4d4d') }}></span>
                        </div>
                        <Settings size={18} />
                        <div className="admin-profile" title={`Admin Identity: ${adminName}`}>{adminName}</div>
                    </div>
                </header>

                <div className="admin-viewport">
                    <div className="viewport-header">
                        <h2>
                            {viewingUserLogs ? `Aegis History: ${viewingUserLogs.username}` : (
                                activeTab === 'overview' ? 'System Command Center' :
                                activeTab === 'users' ? 'User Database Management' :
                                activeTab === 'analytics' ? 'Advanced Live Analytics' :
                                'Administrative Terminal'
                            )}
                        </h2>
                        <div className="report-actions">
                            {viewingUserLogs && (
                                <button className="btn-refresh" onClick={() => setViewingUserLogs(null)} style={{background: 'rgba(100,255,218,0.1)', color: '#64FFDA'}}>
                                    <ArrowLeft size={14} /> BACK TO ARCHIVE
                                </button>
                            )}
                            <button className="btn-refresh" onClick={refreshDashboard} disabled={isRefreshing}>
                                <RefreshCcw size={14} className={isRefreshing ? "spin" : ""} /> {isRefreshing ? "SYNCHING..." : "REFRESH"}
                            </button>
                            <button className="btn-download" onClick={() => {
                                const listToExport = viewingUserLogs ? scans.filter(s => s.client_id === viewingUserLogs.client_id) : scans;
                                const headers = "Timestamp,Operative,Target URL,Safety Status,Patterns Found,Aegis Conclusion\n";
                                const csvContent = "data:text/csv;charset=utf-8," + headers + listToExport.map(s => {
                                    const timestamp = s.timestamp || 'N/A';
                                    const user = s.username || 'Anonymous';
                                    const url = (s.url || 'N/A').replace(/,/g, ' '); 
                                    const status = s.safety_status || s.raw_classification || 'Unknown';
                                    const patterns = s.total_patterns_found !== undefined ? s.total_patterns_found : 0;
                                    const conclusion = (s.conclusion || "Analysis complete.").replace(/,/g, ' ');
                                    return `"${timestamp}","${user}","${url}","${status}","${patterns}","${conclusion}"`;
                                }).join("\n");
                                const encodedUri = encodeURI(csvContent);
                                const link = document.createElement("a");
                                link.setAttribute("href", encodedUri);
                                link.setAttribute("download", `Aegis_Audit_${new Date().toISOString().split('T')[0]}.csv`);
                                document.body.appendChild(link);
                                link.click();
                            }}>
                                <Download size={14} /> EXPORT REPORT
                            </button>
                             {viewingUserLogs && (
                                <button className="btn-download" onClick={handleClearLogs} style={{background: 'rgba(255, 77, 77, 0.1)', color: '#ff4d4d', border: '1px solid rgba(255, 77, 77, 0.2)'}}>
                                     🗑️ PURGE HISTORY
                                </button>
                            )}
                        </div>
                    </div>

                    {viewingUserLogs ? (
                         <div className="users-view fade-in">
                            <div className="data-table-container">
                                <table className="admin-table">
                                    <thead>
                                        <tr>
                                            <th>TIMESTAMP</th>
                                            <th>TARGET URL</th>
                                            <th>SAFETY STATUS</th>
                                            <th>THREATS</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {scans.filter(s => String(s.client_id) === String(viewingUserLogs.client_id)).map((scan) => (
                                            <tr key={scan._id}>
                                                <td style={{fontSize: '12px'}}>{scan.timestamp}</td>
                                                <td style={{maxWidth: '350px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '12px'}}>
                                                    <div style={{fontWeight: 'bold'}}>{scan.url}</div>
                                                    <div style={{opacity: 0.6, fontSize: '10px', marginTop: '4px'}}>
                                                       {scan.conclusion || "Analysis complete."}
                                                    </div>
                                                </td>
                                                <td>
                                                     {(() => {
                                                         const patterns = scan.total_patterns_found !== undefined ? scan.total_patterns_found : (scan.total_patterns !== undefined ? scan.total_patterns : 0);
                                                         let statusStr = (scan.safety_status || scan.status || scan.raw_classification || 'Unknown').toUpperCase();
                                                         let status = 'Unknown';
                                                         if (statusStr === 'SAFE') status = 'Safe';
                                                         else if (['UNSAFE', 'SCAM', 'FAKE', 'SUSPICIOUS'].includes(statusStr)) status = 'Unsafe';
                                                         else if (statusStr === 'UNKNOWN') status = patterns > 0 ? 'Unsafe' : 'Safe';

                                                         if (status === 'Safe') return <span style={{color: '#64FFDA'}}><Shield size={10} /> SAFE</span>;
                                                         return <span style={{color: '#ff4d4d'}}><ShieldAlert size={10} /> UNSAFE</span>;
                                                     })()}
                                                </td>
                                                <td>{scan.total_patterns_found || 0}</td>
                                            </tr>
                                        ))}
                                        {scans.filter(s => String(s.client_id) === String(viewingUserLogs.client_id)).length === 0 && (
                                            <tr><td colSpan="4" style={{textAlign:'center', opacity: 0.5, padding: '40px'}}>No scanned website found for this operative identity.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                         </div>
                    ) : activeTab === 'overview' ? (
                        <>
                            {/* Stats Grid */}
                            <div className="stats-grid">
                                <div className="stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('users')}>
                                    <div className="stat-icon users"><Users /></div>
                                    <div className="stat-info">
                                        <label>Total Intelligence Units (Users)</label>
                                        <h4>{stats.total_users}</h4>
                                        <span className="growth positive"><ArrowUpRight size={14} /> +12% this month</span>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon scans"><Activity /></div>
                                    <div className="stat-info">
                                        <label>Total Aegis Scans</label>
                                        <h4>{stats.total_scans}</h4>
                                        <span className="growth positive"><ArrowUpRight size={14} /> +28% this week</span>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon shield" style={{background: 'rgba(100, 255, 218, 0.1)', border: '1px solid rgba(100, 255, 218, 0.2)'}}><Shield style={{color: '#64FFDA'}}/></div>
                                    <div className="stat-info">
                                        <label>Total Safe Entities Identified</label>
                                        <h4 style={{color: '#64FFDA'}}>{stats.total_safe || 0}</h4>
                                        <span className="stability" style={{color: '#64FFDA'}}>SYSTEM VERIFIED</span>
                                    </div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-icon threat" style={{background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.2)'}}><ShieldAlert style={{color: '#ff4d4d'}}/></div>
                                    <div className="stat-info">
                                        <label>Aegis Threat Neutralizations</label>
                                        <h4 style={{color: '#ff4d4d'}}>{stats.total_threats || 0}</h4>
                                        <span className="growth threat" style={{color: '#ff4d4d'}}>BLOCKADE ACTIVE</span>
                                    </div>
                                </div>
                            </div>

                            {/* Charts Section */}
                            <div className="intelligence-grid" style={{ gridTemplateColumns: '1fr' }}>
                            <div className="chart-main-container">
                                <div className="chart-header">
                                    <h3>Aegis Scan Velocity Analytics</h3>
                                    <div className="range-selector">
                                        <button className={chartRange === 'D' ? 'active' : ''} onClick={() => setChartRange('D')}>DAILY (Hr)</button>
                                        <button className={chartRange === 'W' ? 'active' : ''} onClick={() => setChartRange('W')}>WEEKLY</button>
                                        <button className={chartRange === 'M' ? 'active' : ''} onClick={() => setChartRange('M')}>30-DAY ARCHIVE</button>
                                    </div>
                                </div>
                                <div className="chart-body" style={{ width: '100%', height: '350px' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartRange === 'D' ? stats.hourly_stats : (chartRange === 'M' ? stats.monthly_stats : stats.weekly_stats)}>
                                            <defs>
                                                <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={chartRange === 'D' ? "#3b82f6" : "#64FFDA"} stopOpacity={0.4}/>
                                                    <stop offset="95%" stopColor={chartRange === 'D' ? "#3b82f6" : "#64FFDA"} stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
                                            <XAxis 
                                                dataKey="name" 
                                                stroke="#64FFDA" 
                                                fontSize={11} 
                                                fontWeight={700}
                                                tickLine={true} 
                                                axisLine={{ stroke: '#ffffff33', strokeWidth: 1 }}
                                                interval={chartRange === 'M' ? 5 : (chartRange === 'D' ? 3 : 0)} 
                                                dy={10}
                                            />
                                            <YAxis 
                                                stroke="#64FFDA" 
                                                fontSize={11} 
                                                fontWeight={700}
                                                tickLine={true} 
                                                axisLine={{ stroke: '#ffffff33', strokeWidth: 1 }}
                                                dx={-10}
                                            />
                                            <Tooltip 
                                                contentStyle={{ background: '#0f172a', border: '1px solid #64FFDA', borderRadius: '12px', fontSize: '13px', boxShadow: '0 10px 40px rgba(0,0,0,0.5)' }}
                                                itemStyle={{ color: '#64FFDA', fontWeight: 'bold' }}
                                                cursor={{ stroke: '#64FFDA', strokeWidth: 2, strokeDasharray: '5 5' }}
                                            />
                                            <Area 
                                                type="monotone" 
                                                dataKey="scans" 
                                                stroke={chartRange === 'D' ? "#3b82f6" : "#64FFDA"} 
                                                strokeWidth={3}
                                                fillOpacity={1} 
                                                fill="url(#colorScans)" 
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
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
                                            <th>AEGIS ENGAGEMENT</th>
                                            <th>REGISTRATION DATE</th>
                                            <th>PRIVILEGE LEVEL</th>
                                            <th>ACTIONS</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {users.filter(u => 
                                            u.username.toLowerCase().includes(searchQuery.toLowerCase()) || 
                                            u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                            (u.client_id && u.client_id.toLowerCase().includes(searchQuery.toLowerCase()))
                                        ).map((user, idx) => (
                                            <tr key={user._id}>
                                                <td>
                                                    <div className="client-id-badge">{user.client_id || 'N/A'}</div>
                                                </td>
                                                <td>
                                                    <div className="user-cell-info" style={{ cursor: 'pointer' }} onClick={() => { 
                                                        setViewingUserLogs(user); 
                                                    }}>
                                                        <span className="username" style={{ color: '#64FFDA', textDecoration: 'underline', textDecorationColor: 'rgba(100, 255, 218, 0.2)', textUnderlineOffset: '4px' }}>
                                                             {user.username}
                                                        </span>
                                                        <small className="email">{user.email}</small>
                                                    </div>
                                                </td>
                                                <td>
                                                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                                                        <div style={{width: '60px', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden'}}>
                                                             <div style={{width: `${Math.min((user.scan_count || 0) * 5, 100)}%`, height: '100%', background: '#64FFDA'}}></div>
                                                        </div>
                                                        <span style={{fontSize: '11px', fontWeight: 'bold'}}>{user.scan_count || 0} scans</span>
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
                                            <th>PURGE</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {scans.filter(s => 
                                            s.username.toLowerCase().includes(searchQuery.toLowerCase()) || 
                                            s.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                            (s.client_id && s.client_id.toLowerCase().includes(searchQuery.toLowerCase()))
                                        ).map((scan) => (
                                            <tr key={scan._id}>
                                                <td style={{fontSize: '12px'}}>{scan.timestamp}</td>
                                                <td>
                                                    <div className="user-shield-box">
                                                        <span className="badge badge-user" style={{textTransform:'none'}}>{scan.username}</span>
                                                        <div style={{fontSize: '9px', color: '#64FFDA', opacity: 0.6, marginTop: '2px'}}>{scan.client_id || 'NS-GUEST'}</div>
                                                    </div>
                                                </td>
                                                <td style={{maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '12px'}}>
                                                    <div style={{fontWeight: 'bold'}}>{scan.url}</div>
                                                    {scan.type === 'text' && <div style={{color: '#8B5CF6', fontSize: '10px'}}>(Text Scan Segment)</div>}
                                                    <div style={{opacity: 0.6, fontSize: '10px', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis'}}>
                                                       {scan.conclusion || "Analysis complete."}
                                                    </div>
                                                </td>
                                                <td>
                                                    {(() => {
                                                        const patterns = scan.total_patterns_found !== undefined ? scan.total_patterns_found : (scan.total_patterns !== undefined ? scan.total_patterns : 0);
                                                        let statusStr = (scan.safety_status || scan.status || scan.raw_classification || 'Unknown').toUpperCase();
                                                        let status = 'Unknown';
                                                        
                                                        if (statusStr === 'SAFE') status = 'Safe';
                                                        else if (['UNSAFE', 'SCAM', 'FAKE', 'SUSPICIOUS'].includes(statusStr)) status = 'Unsafe';
                                                        else if (statusStr === 'UNKNOWN') status = patterns > 0 ? 'Unsafe' : 'Safe';

                                                        if (status === 'Safe') {
                                                            return <span style={{color: '#64FFDA', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px'}}><Shield size={12} />SAFE</span>;
                                                        } else if (status === 'Unsafe' || status === 'Scam' || status === 'Fake' || status === 'Suspicious') {
                                                            return <span style={{color: '#ff4d4d', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px'}}><ShieldAlert size={12} />UNSAFE</span>;
                                                        } else {
                                                            return <span style={{color: 'rgba(255,255,255,0.4)', fontWeight: 'bold'}}>{status.toUpperCase()}</span>;
                                                        }
                                                    })()}
                                                </td>
                                                <td>
                                                    {(() => {
                                                        const patterns = scan.total_patterns_found !== undefined ? scan.total_patterns_found : (scan.total_patterns !== undefined ? scan.total_patterns : 0);
                                                        return (
                                                            <span className={patterns > 0 ? "badge badge-admin" : "badge badge-user"} style={patterns > 0 ? {borderColor: '#ff4d4d', color: '#ff4d4d', background: 'rgba(255, 77, 77, 0.1)'} : {}}>
                                                                {patterns} Patterns
                                                            </span>
                                                        );
                                                    })()}
                                                </td>
                                                <td>
                                                    <button 
                                                        className="btn-table-action" 
                                                        style={{padding: '5px 10px', background: 'rgba(255, 77, 77, 0.1)'}}
                                                        onClick={async () => {
                                                            const confirm = await Swal.fire({
                                                                title: 'PURGE SEGMENT?',
                                                                text: "Remove this individual log entry?",
                                                                icon: 'question',
                                                                showCancelButton: true,
                                                                confirmButtonColor: '#ff4d4d',
                                                                cancelButtonColor: '#64FFDA',
                                                                confirmButtonText: 'YES, DELETE',
                                                                background: '#020617',
                                                                color: '#fff'
                                                            });
                                                            if (confirm.isConfirmed) {
                                                                try {
                                                                    await axios.delete(`${API_BASE_URL}/admin/delete-scan/${scan._id}`, { withCredentials: true });
                                                                    fetchScans();
                                                                } catch (err) {
                                                                    Swal.fire('Error', 'Deletion failed', 'error');
                                                                }
                                                            }
                                                        }}
                                                    >
                                                        🗑️
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : activeTab === 'analytics' ? (
                        <div className="users-view fade-in" style={{textAlign: 'center', padding: '100px 0'}}>
                            <Activity size={48} style={{color: '#64FFDA', margin: '0 auto 20px', opacity: 0.5}} />
                            <h3 style={{fontSize: '24px', marginBottom: '10px'}}>Aegis Link Establishing...</h3>
                            <p style={{color: 'rgba(255,255,255,0.4)', maxWidth: '400px', margin: '0 auto', fontSize: '14px', lineHeight: '1.6'}}>
                                Advanced real-time live analytics node is currently calibrating. Live stream visualizers will be fully operational in the next security patch.
                            </p>
                        </div>
                    ) : activeTab === 'register' ? (
                        <div className="admin-register-view fade-in">
                            <div className="register-container">
                                <div className="register-header">
                                    <Shield size={32} className="shield-pulse" />
                                    <h3>Administrative Enrollment</h3>
                                    <p>Register a new identity in the dark-pattern-admin secure archive.</p>
                                </div>
                                <form className="admin-reg-form" onSubmit={async (e) => {
                                    e.preventDefault();
                                    try {
                                        const res = await axios.post(`${API_BASE_URL}/admin/register`, regForm, { withCredentials: true });
                                        if (res.data.success) {
                                            Swal.fire({
                                                icon: 'success',
                                                title: 'Registration Successful',
                                                text: res.data.message,
                                                background: '#0A192F',
                                                color: '#64FFDA',
                                                confirmButtonColor: '#64FFDA'
                                            });
                                            setRegForm({ username: '', email: '', password: '' });
                                        }
                                    } catch (err) {
                                        Swal.fire({
                                            icon: 'error',
                                            title: 'Registration Failed',
                                            text: err.response?.data?.message || 'Error occurred',
                                            background: '#0A192F',
                                            color: '#ff4d4d',
                                            confirmButtonColor: '#ff4d4d'
                                        });
                                    }
                                }}>
                                    <div className="form-group">
                                        <label>ADMIN USERNAME</label>
                                        <input 
                                            type="text" 
                                            placeholder="Enter Admin Alias..." 
                                            value={regForm.username}
                                            onChange={(e) => setRegForm({...regForm, username: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>IDENTIFICATION EMAIL</label>
                                        <input 
                                            type="email" 
                                            placeholder="admin@aegis.core" 
                                            value={regForm.email}
                                            onChange={(e) => setRegForm({...regForm, email: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>SECURITY PASSCODE</label>
                                        <input 
                                            type="password" 
                                            placeholder="••••••••" 
                                            value={regForm.password}
                                            onChange={(e) => setRegForm({...regForm, password: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <button type="submit" className="btn-admin-submit">
                                        AUTHORIZE REGISTRATION
                                    </button>
                                </form>
                            </div>
                        </div>
                    ) : (
                        <div className="users-view fade-in" style={{textAlign: 'center', padding: '100px 0'}}>
                            <Activity size={48} style={{color: '#64FFDA', margin: '0 auto 20px', opacity: 0.5}} />
                            <h3 style={{fontSize: '24px', marginBottom: '10px'}}>Aegis Link Establishing...</h3>
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
