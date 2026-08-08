// Every page used to be a single <div class="page" id="page-xxx"> living in one 1000-line
// index.html. Now each one lives in its own file under /pages/. This module fetches every
// fragment once at startup and injects it into the right container, so the rest of the app
// (showPage, event listeners set up on DOMContentLoaded) behaves exactly like the old
// single-file version.

const AUTH_PAGES = ['login', 'register'];
const APP_PAGES = [
    'home', 'profile', 'profile-edit', 'workspaces', 'freelancing', 'brand',
    'workspace', 'brain', 'user-brain', 'products',
    'research', 'decisions', 'strategy', 'execution', 'analytics', 'learning',
    'dashboard', 'live-console'
];

async function fetchText(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
    return res.text();
}

async function injectInto(containerId, path) {
    const html = await fetchText(path);
    document.getElementById(containerId).insertAdjacentHTML('beforeend', html);
}

export async function loadAllPartials() {
    await injectInto('sidebar-container', 'components/sidebar.html');
    await injectInto('mobile-header-container', 'components/mobile-header.html');

    for (const name of AUTH_PAGES) {
        await injectInto('auth-pages', `pages/${name}.html`);
    }
    for (const name of APP_PAGES) {
        await injectInto('page-container', `pages/${name}.html`);
    }
    await injectInto('page-container', 'components/add-product-modal.html');
}

export function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    const target = document.getElementById('page-' + pageName);
    if (target) target.classList.add('active');

    document.querySelectorAll('.sidebar-item').forEach(item => item.classList.remove('active'));
    const sidebarItem = document.querySelector(`a[onclick="showPage('${pageName}')"]`);
    if (sidebarItem) sidebarItem.classList.add('active');

    window.scrollTo(0, 0);
}
