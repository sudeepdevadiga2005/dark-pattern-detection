const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = import.meta.env.VITE_API_URL || (isLocalhost ? "http://localhost:5000" : "https://dark-pattern-api-production.up.railway.app"); 
// Note: User should update VITE_API_URL in their environment or replace the default above.

export default API_BASE_URL;
