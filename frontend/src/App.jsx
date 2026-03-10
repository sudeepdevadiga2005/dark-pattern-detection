import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ClientHome from './pages/ClientHome';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import WebScraper from './pages/WebScraper';
import Cookies from 'js-cookie';
import './App.css';

function App() {
  const isLoggedIn = !!Cookies.get('user');

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
