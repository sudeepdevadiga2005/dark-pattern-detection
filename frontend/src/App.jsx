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
import Cookies from 'js-cookie';
import './App.css';

// Ensure cookies are sent with every globally verified request
axios.defaults.withCredentials = true;

function App() {
  const isLoggedIn = !!Cookies.get('user');

  // Continually verify session state if we think we are logged in
  useEffect(() => {
    if (!isLoggedIn) return;

    const interval = setInterval(async () => {
      try {
        await axios.get(`${API_BASE_URL}/verify-session`);
      } catch (err) {
        if (err.response?.status === 401) {
          // The backend says we are no longer valid (e.g. logged in on another device)
          Cookies.remove('user');
          window.location.href = '/login'; // Instantly force the user out to the login page
        }
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [isLoggedIn]);

  return (
    <Router>
      <Routes>
        <Route path="/" element={isLoggedIn ? <ClientHome /> : <LandingPage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/signup" element={<AuthPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/scraper" element={<WebScraper />} />
      </Routes>
    </Router>
  );
}

export default App;
