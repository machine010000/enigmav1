// Set window.ENIGMA_API_BASE in index.html (or via a small inline <script> before this
// module loads) to point at a different backend without touching any JS file.
// Example for production: <script>window.ENIGMA_API_BASE = "https://enigma-api.onrender.com";</script>
export const API_BASE = window.ENIGMA_API_BASE || 'http://localhost:8000';
