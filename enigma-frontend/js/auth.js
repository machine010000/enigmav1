import { apiCall, showToast } from './api.js';
import { showPage } from './router.js';
import { loadProducts } from './products.js';

export let currentUser = null;

export function getAuthToken() {
    return localStorage.getItem('enigma_token');
}

export async function loadUser() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Current: /auth/me
        // Target: /api/user/profile
        const user = await apiCall('/auth/me');
        currentUser = user;
        document.getElementById('user-name').textContent = user.name;
        document.getElementById('auth-pages').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        showPage('home');
        loadProducts();
    } catch (e) {
        logout();
    }
}

export function logout() {
    currentUser = null;
    localStorage.removeItem('enigma_token');
    document.getElementById('auth-pages').classList.remove('hidden');
    document.getElementById('main-app').classList.add('hidden');
    showPage('login');
}

export function skipAuth() {
    document.getElementById('auth-pages').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    showPage('home');
}

export function initAuthForms() {
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            // TODO: Update to USER Contract endpoint when implemented
            // Current: /auth/login
            // Target: /api/user/login
            const data = await apiCall('/auth/login', {
                method: 'POST',
                body: new URLSearchParams({ username: email, password: password })
            });
            localStorage.setItem('enigma_token', data.access_token);
            await loadUser();
            showToast('تم تسجيل الدخول بنجاح!', 'success');
        } catch (e) {
            // Error already surfaced via apiCall's toast
        }
    });

    document.getElementById('register-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        try {
            // TODO: Update to USER Contract endpoint when implemented
            // Current: /auth/register
            // Target: /api/user/register
            const data = await apiCall('/auth/register', {
                method: 'POST',
                body: { email, name, password }
            });
            localStorage.setItem('enigma_token', data.access_token);
            await loadUser();
            showToast('تم إنشاء الحساب بنجاح!', 'success');
        } catch (e) {}
    });
}
