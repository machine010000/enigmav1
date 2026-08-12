/**
 * Enigma Frontend Configuration
 * 
 * Environment-specific API configuration with production safety.
 * 
 * SETUP:
 * 1. Development: Set window.ENIGMA_API_BASE to local backend (e.g., http://localhost:8000)
 * 2. Test: Set window.ENIGMA_API_BASE to test backend
 * 3. Production: Set window.ENIGMA_API_BASE to deployed backend (REQUIRED)
 * 
 * PRODUCTION SAFETY:
 * - No localhost fallback in production
 * - Explicit error if API_BASE not configured
 * - Mock data disabled in production
 */

// Environment detection
const ENVIRONMENT = window.ENIGMA_ENV || 'development';

// API Base URL - MUST be set in production
const API_BASE = window.ENIGMA_API_BASE;
const WEBSOCKET_BASE = API_BASE
    ? API_BASE.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
    : undefined;

// Mock data flag - MUST be false in production
export const USE_MOCK_DATA = window.ENIGMA_USE_MOCK_DATA === true && ENVIRONMENT === 'development';

// Validate configuration
function validateConfig() {
    const errors = [];
    
    // Check API_BASE is set
    if (!API_BASE) {
        errors.push('ENIGMA_API_BASE is not configured. Set window.ENIGMA_API_BASE in index.html.');
    }
    
    // Check for localhost in production
    if (ENVIRONMENT === 'production') {
        const forbiddenHosts = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]'];
        const url = new URL(API_BASE || '');
        if (forbiddenHosts.includes(url.hostname)) {
            errors.push(`Production cannot use localhost (${url.hostname}). Set ENIGMA_API_BASE to deployed backend.`);
        }
        
        // Ensure mock data is disabled
        if (USE_MOCK_DATA) {
            errors.push('Mock data must be disabled in production. Set ENIGMA_USE_MOCK_DATA to false.');
        }
    }
    
    // Check API_BASE is valid URL
    if (API_BASE) {
        try {
            new URL(API_BASE);
        } catch (e) {
            errors.push(`ENIGMA_API_BASE is not a valid URL: ${API_BASE}`);
        }
    }
    
    return errors;
}

// Run validation on load
const configErrors = validateConfig();
if (configErrors.length > 0) {
    console.error('Configuration Error:', configErrors.join('\n'));
    
    // In production, fail fast with visible error
    if (ENVIRONMENT === 'production') {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #050507; color: #e5e7eb; font-family: Cairo, sans-serif;">
                    <div style="text-align: center; padding: 2rem;">
                        <h1 style="color: #ef4444; margin-bottom: 1rem;">Configuration Error</h1>
                        <p style="color: #9ca3af; margin-bottom: 1rem;">The application is not properly configured.</p>
                        <pre style="background: #1f2937; padding: 1rem; border-radius: 8px; text-align: left; overflow-x: auto; color: #f87171;">${configErrors.join('\n')}</pre>
                        <p style="color: #6b7280; margin-top: 1rem; font-size: 0.875rem;">Please contact your administrator.</p>
                    </div>
                </div>
            `;
        });
        throw new Error(`Configuration Error: ${configErrors.join(', ')}`);
    } else {
        // In development, show warning but continue
        console.warn('Configuration Warning (Development Mode):', configErrors.join('\n'));
    }
}

// Export validated configuration
export { API_BASE, WEBSOCKET_BASE, ENVIRONMENT };
export const IS_PRODUCTION = ENVIRONMENT === 'production';
export const IS_DEVELOPMENT = ENVIRONMENT === 'development';
export const IS_TEST = ENVIRONMENT === 'test';
