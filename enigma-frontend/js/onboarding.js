import { apiCall, showToast } from './api.js';
import { loadProducts } from './products.js';

export async function startOnboarding(productId) {
    try {
        const data = await apiCall(`/products/${productId}/onboarding`);
        showOnboardingQuestions(data, productId);
    } catch (e) {}
}

function showOnboardingQuestions(data, productId) {
    const modal = document.createElement('div');
    modal.id = 'onboarding-modal';
    modal.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4';

    const allQuestions = [...data.basic_questions, ...data.smart_questions];
    let currentQ = 0;
    const answers = {};

    function renderQuestion() {
        const q = allQuestions[currentQ];
        modal.innerHTML = `
            <div class="glass-card p-8 w-full max-w-lg">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xl font-bold">تعريف المنتج</h3>
                    <span class="text-sm text-gray-400">${currentQ + 1} / ${allQuestions.length}</span>
                </div>
                <p class="text-lg mb-4">${q.question}</p>
                <textarea id="onboarding-answer" class="input-field h-24 resize-none mb-4" placeholder="اكتب إجابتك هنا..."></textarea>
                <div class="flex gap-3">
                    ${currentQ > 0 ? '<button data-action="prev" class="btn-secondary flex-1">السابق</button>' : ''}
                    <button data-action="next" class="btn-primary flex-1">${currentQ === allQuestions.length - 1 ? 'إنهاء' : 'التالي'}</button>
                </div>
                ${data.master_tips ? `<div class="mt-4 p-3 rounded-lg bg-brand-purple/10 border border-brand-purple/30"><p class="text-xs text-brand-purple"><i class="fas fa-lightbulb ml-1"></i>${data.master_tips.substring(0, 200)}...</p></div>` : ''}
            </div>
        `;
        modal.querySelector('[data-action="next"]').addEventListener('click', onNext);
        modal.querySelector('[data-action="prev"]')?.addEventListener('click', onPrev);
    }

    function onNext() {
        const answer = document.getElementById('onboarding-answer').value;
        if (!answer.trim()) return showToast('الرجاء الإجابة على السؤال', 'error');
        answers[allQuestions[currentQ].id] = answer;
        currentQ++;
        if (currentQ >= allQuestions.length) {
            submitOnboarding(productId, answers);
            modal.remove();
        } else {
            renderQuestion();
        }
    }

    function onPrev() { currentQ--; renderQuestion(); }

    document.body.appendChild(modal);
    renderQuestion();
}

async function submitOnboarding(productId, answers) {
    try {
        await apiCall(`/products/${productId}/onboarding`, {
            method: 'POST',
            body: { answers }
        });
        showToast('تم تحليل المنتج بنجاح!', 'success');
        loadProducts();
    } catch (e) {}
}
