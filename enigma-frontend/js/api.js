import { API_BASE } from './config.js';
import { logout } from './auth.js';

export function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const msg = document.getElementById('toast-message');
    msg.textContent = message;
    icon.className = type === 'error' ? 'fas fa-exclamation-circle text-red-500' :
                    type === 'success' ? 'fas fa-check-circle text-green-500' :
                    'fas fa-info-circle text-brand-purple';
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

export function showLoading() { document.getElementById('loading').classList.remove('hidden'); }
export function hideLoading() { document.getElementById('loading').classList.add('hidden'); }

export async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const authToken = localStorage.getItem('enigma_token');
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        },
        ...options
    };
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        showLoading();
        const response = await fetch(url, config);
        hideLoading();

        if (response.status === 401) {
            logout();
            throw new Error('Unauthorized');
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        return data;
    } catch (error) {
        hideLoading();
        showToast(error.message, 'error');
        throw error;
    }
}
