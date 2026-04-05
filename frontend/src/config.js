// Use a relative path so requests go through the Vite proxy in dev mode.
// This keeps API calls same-origin, which is required for Flask session cookies.
// In production (Flask serves the built React app), /api routes are handled directly.
const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export default API_BASE_URL;
