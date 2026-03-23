import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import API_BASE_URL from './config';
import LandingPage from './pages/LandingPage';
import ClientHome from './pages/ClientHome';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import WebScraper from './pages/WebScraper';
import AdminDashboard from './pages/AdminDashboard';
import AdminLogin from './pages/AdminLogin';
import Cookies from 'js-cookie';
import './App.css';

// Ensure cookies are sent with every globally verified request
axios.defaults.withCredentials = true;

function App() {
  const isLoggedIn = !!Cookies.get('user');
  const isAdmin = !!Cookies.get('is_admin');

  // Continually verify session state if we think we are logged in
  useEffect(() => {
    if (!isLoggedIn && !isAdmin) return;

    const interval = setInterval(async () => {
      try {
        await axios.get(`${API_BASE_URL}/verify-session`);
      } catch (err) {
        if (err.response?.status === 401) {
          // The backend says we are no longer valid (e.g. logged in on another device)
          Cookies.remove('user');
          Cookies.remove('is_admin');
          if (window.location.pathname.startsWith('/admin')) {
            window.location.href = '/admin/login';
          } else {
            window.location.href = '/login';
          }
        }
      }
    }, 60000); // Check once per minute to reduce terminal noise

    return () => clearInterval(interval);
  }, [isLoggedIn, isAdmin]);

  return (
    <Router>
      <Routes>
        <Route path="/" element={isLoggedIn ? <ClientHome /> : <LandingPage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/signup" element={<AuthPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/scraper" element={<WebScraper />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route 
          path="/admin" 
          element={isAdmin ? <AdminDashboard /> : <AdminLogin />} 
        />
      </Routes>
    </Router>
  );
}

export default App;
