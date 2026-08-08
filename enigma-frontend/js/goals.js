import { showPage } from './router.js';
import { showToast } from './api.js';

export function selectGoal(goal) {
    document.getElementById('current-goal-tag').textContent = goal.replace('_', ' ');
    showToast(`تم اختيار الهدف: ${goal}`, 'success');
    showPage('workspace');
}
