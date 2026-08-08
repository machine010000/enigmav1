import { showLoading, hideLoading, showToast } from './api.js';

// NOTE: this still simulates the result with setTimeout, exactly like the original
// single-file version did. There is no backend endpoint for this yet — app/ai/user_brain.py
// exists on the backend but is not wired into any router. Wire this up to a real
// POST /users/{id}/type-detect (or similar) once that endpoint exists.
export function setUserType(type) {
    showLoading();
    setTimeout(() => {
        hideLoading();
        document.getElementById('user-type-badge').textContent = type;
        document.getElementById('user-type-badge').className = 'tag tag-green';
        document.getElementById('user-type-result').classList.remove('hidden');
        document.getElementById('user-type-text').textContent = `تم التعرف على نوعك: ${type}. سيتم تخصيص الأنظمة لك.`;

        document.getElementById('user-journey-content').innerHTML = `
            <div class="space-y-2">
                <div class="p-3 rounded-lg bg-brand-purple/10 border border-brand-purple/30">
                    <p class="font-semibold text-sm text-brand-purple">Discovery</p>
                    <p class="text-xs text-gray-400">اكتشاف ENIGMA وفهم الميزات</p>
                </div>
                <div class="p-3 rounded-lg bg-dark-800">
                    <p class="font-semibold text-sm">Onboarding</p>
                    <p class="text-xs text-gray-400">إضافة أول منتج وبدء البحث</p>
                </div>
                <div class="p-3 rounded-lg bg-dark-800">
                    <p class="font-semibold text-sm">Daily Usage</p>
                    <p class="text-xs text-gray-400">متابعة المهام والتنفيذ اليومي</p>
                </div>
            </div>
        `;
        showToast(`تم التعرف: ${type}`, 'success');
    }, 1500);
}
