import { apiCall, showToast } from './api.js';
import { showPage } from './router.js';
import { startOnboarding } from './onboarding.js';

export let currentProduct = null;

export async function loadProducts() {
    if (!localStorage.getItem('enigma_token')) return;
    try {
        const products = await apiCall('/products');
        renderProducts(products);
    } catch (e) {}
}

function renderProducts(products) {
    const grid = document.getElementById('products-grid');
    const list = document.getElementById('products-list');

    if (products.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center text-gray-500 py-12">لا توجد منتجات. أضف منتجاً جديداً!</div>';
        list.innerHTML = '<div class="p-4 rounded-xl bg-dark-800 text-center text-gray-500">لا توجد منتجات</div>';
        return;
    }

    grid.innerHTML = products.map(p => `
        <div class="glass-card p-6 cursor-pointer hover:border-brand-purple/50 transition" onclick="selectProduct('${p.id}')">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold">${p.name}</h3>
                <span class="tag ${p.status === 'active' ? 'tag-green' : 'tag-yellow'} text-xs">${p.status}</span>
            </div>
            <p class="text-sm text-gray-400 mb-3">${p.category}${p.subcategory ? ' / ' + p.subcategory : ''}</p>
            <div class="w-full bg-dark-600 rounded-full h-1.5">
                <div class="progress-bar w-[${p.status === 'onboarding' ? '20' : p.status === 'researching' ? '40' : p.status === 'strategizing' ? '60' : '80'}%]"></div>
            </div>
        </div>
    `).join('');

    list.innerHTML = products.slice(0, 3).map(p => `
        <div class="p-4 rounded-xl bg-dark-800 border ${p.status === 'active' ? 'border-brand-purple/30' : 'border-gray-700/50'} cursor-pointer" onclick="selectProduct('${p.id}')">
            <div class="flex items-center justify-between mb-2">
                <span class="font-semibold">${p.name}</span>
                <span class="tag ${p.status === 'active' ? 'tag-green' : 'tag-yellow'} text-xs">${p.status}</span>
            </div>
            <div class="w-full bg-dark-600 rounded-full h-1.5"><div class="progress-bar w-[${p.status === 'onboarding' ? '20' : '40'}%]"></div></div>
        </div>
    `).join('');
}

export function showAddProductModal() {
    document.getElementById('add-product-modal').classList.remove('hidden');
}
export function hideAddProductModal() {
    document.getElementById('add-product-modal').classList.add('hidden');
}

export function selectProduct(productId) {
    currentProduct = productId;
    showPage('products');
}

export function initProductForms() {
    document.getElementById('add-product-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('product-name').value,
            category: document.getElementById('product-category').value,
            subcategory: document.getElementById('product-subcategory').value,
            target_market: document.getElementById('product-market').value,
            description: document.getElementById('product-description').value
        };

        try {
            const product = await apiCall('/products', { method: 'POST', body: data });
            hideAddProductModal();
            showToast('تم إنشاء المنتج بنجاح!', 'success');
            loadProducts();
            startOnboarding(product.id);
        } catch (e) {}
    });
}
