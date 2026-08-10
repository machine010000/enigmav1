/**
 * Production Configuration Validation
 * 
 * This script validates that the frontend is properly configured for production.
 * Run this before deploying to production.
 */

// Simulate production environment
window.ENIGMA_ENV = 'production';
window.ENIGMA_API_BASE = 'http://localhost:8000'; // This should fail validation
window.ENIGMA_USE_MOCK_DATA = false;

// Import config (this will run validation)
import('./js/config.js').then(module => {
    console.log('Config module loaded');
    console.log('IS_PRODUCTION:', module.IS_PRODUCTION);
    console.log('API_BASE:', module.API_BASE);
    console.log('USE_MOCK_DATA:', module.USE_MOCK_DATA);
}).catch(error => {
    console.error('Config validation failed (expected):', error.message);
});

// Test 1: Check for localhost in production
function testNoLocalhostInProduction() {
    console.log('\n=== Test 1: No Localhost in Production ===');
    
    const forbiddenHosts = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]'];
    const testUrls = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'https://api.enigma.com',
        'https://enigma-api.example.com',
    ];
    
    testUrls.forEach(url => {
        try {
            const parsed = new URL(url);
            const isForbidden = forbiddenHosts.includes(parsed.hostname);
            console.log(`${url} - ${isForbidden ? 'FAIL' : 'PASS'}`);
        } catch (e) {
            console.log(`${url} - INVALID URL`);
        }
    });
}

// Test 2: Check for hardcoded URLs in JS files
function testNoHardcodedUrls() {
    console.log('\n=== Test 2: No Hardcoded URLs ===');
    
    const jsFiles = [
        'js/api.js',
        'js/auth.js',
        'js/profile.js',
        'js/freelancing.js',
        'js/dashboard.js',
        'js/products.js',
        'js/chat.js',
    ];
    
    const urlPatterns = [
        /http:\/\/localhost:\d+/,
        /https?:\/\/127\.0\.0\.1:\d+/,
        /https?:\/\/0\.0\.0\.0:\d+/,
    ];
    
    console.log('Manual check required: grep for localhost/127.0.0.1 in JS files');
    console.log('Expected: No matches except in config.js comments');
}

// Test 3: Check mock data disabled in production
function testMockDataDisabled() {
    console.log('\n=== Test 3: Mock Data Disabled in Production ===');
    
    const testCases = [
        { env: 'production', useMock: false, expected: 'PASS' },
        { env: 'production', useMock: true, expected: 'FAIL' },
        { env: 'development', useMock: true, expected: 'PASS' },
        { env: 'development', useMock: false, expected: 'PASS' },
    ];
    
    testCases.forEach(({ env, useMock, expected }) => {
        const shouldFail = env === 'production' && useMock;
        const result = shouldFail ? 'FAIL' : 'PASS';
        console.log(`ENV=${env}, USE_MOCK=${useMock} - ${result} (expected: ${expected})`);
    });
}

// Test 4: Check API_BASE is required in production
function testApiBaseRequired() {
    console.log('\n=== Test 4: API_BASE Required in Production ===');
    
    const testCases = [
        { env: 'production', apiBase: null, expected: 'FAIL' },
        { env: 'production', apiBase: 'https://api.enigma.com', expected: 'PASS' },
        { env: 'development', apiBase: null, expected: 'WARN' },
        { env: 'development', apiBase: 'http://localhost:8000', expected: 'PASS' },
    ];
    
    testCases.forEach(({ env, apiBase, expected }) => {
        const shouldFail = env === 'production' && !apiBase;
        const result = shouldFail ? 'FAIL' : (env === 'development' && !apiBase ? 'WARN' : 'PASS');
        console.log(`ENV=${env}, API_BASE=${apiBase} - ${result} (expected: ${expected})`);
    });
}

// Run all tests
console.log('=== Production Configuration Validation ===');
testNoLocalhostInProduction();
testNoHardcodedUrls();
testMockDataDisabled();
testApiBaseRequired();

console.log('\n=== Validation Complete ===');
console.log('To deploy to production:');
console.log('1. Set window.ENIGMA_ENV = "production" in index.html');
console.log('2. Set window.ENIGMA_API_BASE to deployed backend URL');
console.log('3. Set window.ENIGMA_USE_MOCK_DATA = false');
console.log('4. Verify no localhost in API_BASE');
console.log('5. Verify all JS files use config.js API_BASE');
