import { loadAllPartials, showPage } from './router.js';
import { loadUser, logout, skipAuth, initAuthForms, getAuthToken } from './auth.js';
import { initAdminLogin } from './auth.js';
import { showAddProductModal, hideAddProductModal, selectProduct, initProductForms } from './products.js';
import { initChat } from './chat.js';
import { setUserType } from './userbrain.js';
import { selectGoal } from './goals.js';
import { initDashboard } from './dashboard.js';
import { initLiveConsole } from './live-console.js';
import { loadProfile, loadEvidence, loadReadiness, renderEditForm, initProfileForms } from './profile.js';
import { loadFreelancing, showFreelancingTab, closeJobDetailModal } from './freelancing.js';

// The fetched HTML fragments still use inline onclick="..." attributes (same as the
// original single-file app) so they need these on `window`.
window.showPage = showPage;
window.logout = logout;
window.skipAuth = skipAuth;
window.showAddProductModal = showAddProductModal;
window.hideAddProductModal = hideAddProductModal;
window.selectProduct = selectProduct;
window.setUserType = setUserType;
window.selectGoal = selectGoal;
window.refreshDashboard = initDashboard;
window.initLiveConsole = initLiveConsole;
window.toggleWs = () => {};
window.clearConsole = () => {};
window.switchDashboardTab = (tab) => {};
window.showFreelancingTab = showFreelancingTab;
window.closeJobDetailModal = closeJobDetailModal;

// Patch showPage to init dashboard / live-console / profile / freelancing pages
const _originalShowPage = showPage;
window.showPage = (pageName) => {
    _originalShowPage(pageName);
    if (pageName === 'dashboard') {
        initDashboard();
    } else if (pageName === 'live-console') {
        initLiveConsole();
    } else if (pageName === 'profile') {
        // Require authentication for admin/profile access
        if (!getAuthToken()) {
            showPage('admin-login');
            return;
        }
        loadProfile();
    } else if (pageName === 'profile-edit') {
        renderEditForm();
    } else if (pageName === 'freelancing') {
        loadFreelancing();
    }
};

async function boot() {
    await loadAllPartials();

    initAuthForms();
    initAdminLogin();
    initProductForms();
    initChat();
    initProfileForms();

    if (getAuthToken()) {
        loadUser();
    } else {
        showPage('login');
    }
}

document.addEventListener('DOMContentLoaded', boot);
