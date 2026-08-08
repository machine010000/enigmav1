import { apiCall, showToast } from './api.js';
import { showPage } from './router.js';

let currentDashboardTab = 'running';

export async function loadDashboard() {
    try {
        const data = await apiCall('/dashboard');
        const summary = data.summary;

        // Summary cards
        document.getElementById('summary-running').textContent = summary.running;
        document.getElementById('summary-completed').textContent = summary.completed;
        document.getElementById('summary-failed').textContent = summary.failed;
        document.getElementById('summary-total').textContent = summary.total_executions;
        document.getElementById('summary-llm').textContent = summary.total_llm_calls;
        document.getElementById('summary-avg-confidence').textContent =
            (summary.avg_confidence * 100).toFixed(1) + '%';

        // Registered workers (unified contract: API returns "workers")
        const workersContainer = document.getElementById('registered-workers');
        const workersList = data.workers || data.registered_workers || [];
        if (workersList.length > 0) {
            workersContainer.innerHTML = workersList.map(w => {
                const inputs = (w.input_schema || []).join(', ');
                const outputs = (w.output_schema || []).join(', ');
                return `
                    <div class="glass-card p-4 rounded-xl">
                        <div class="flex items-center gap-3 mb-2">
                            <div class="w-8 h-8 rounded-lg bg-brand-purple/20 flex items-center justify-center">
                                <i class="fas fa-cog text-brand-purple"></i>
                            </div>
                            <div>
                                <h4 class="font-semibold">${w.name}</h4>
                                <p class="text-xs text-gray-400">${w.description || 'No description'}</p>
                            </div>
                        </div>
                        ${inputs ? `<p class="text-xs text-gray-500">Input: ${inputs}</p>` : ''}
                        ${outputs ? `<p class="text-xs text-gray-500">Output: ${outputs}</p>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            workersContainer.innerHTML = '<div class="text-gray-500 text-sm">لا توجد workers مسجلة</div>';
        }

        // Running
        const runningContainer = document.getElementById('dashboard-running');
        if (data.recent_executions && data.recent_executions.some(e => e.status === 'running')) {
            runningContainer.innerHTML = data.recent_executions
                .filter(e => e.status === 'running')
                .map(e => renderExecutionCard(e))
                .join('');
        } else {
            runningContainer.innerHTML = '<div class="text-gray-500 text-sm">No running workers</div>';
        }

        // Completed
        const completedContainer = document.getElementById('dashboard-completed');
        const completed = data.recent_executions.filter(e => e.status === 'success');
        completedContainer.innerHTML = completed.length > 0
            ? completed.map(e => renderExecutionCard(e)).join('')
            : '<div class="text-gray-500 text-sm">No completed executions</div>';

        // Failed
        const failedContainer = document.getElementById('dashboard-failed');
        const failed = data.recent_executions.filter(e => e.status === 'failed');
        failedContainer.innerHTML = failed.length > 0
            ? failed.map(e => renderExecutionCard(e)).join('')
            : '<div class="text-gray-500 text-sm">No failed executions</div>';

        // Logs
        const logsContainer = document.getElementById('dashboard-logs');
        logsContainer.innerHTML = (data.recent_logs || [])
            .map(e => renderLog(e)).join('') || '<div class="text-gray-500 text-sm">No logs</div>';

        // Decisions
        const decisionsContainer = document.getElementById('dashboard-decisions');
        decisionsContainer.innerHTML = (data.recent_decisions || [])
            .map(d => renderDecisionCard(d)).join('') || '<div class="text-gray-500 text-sm">No decisions recorded</div>';

    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

function renderExecutionCard(e) {
    const statusColor = e.status === 'success' ? 'tag-green' :
                         e.status === 'failed' ? 'tag-red' : 'tag-yellow';
    return `
        <div class="p-4 rounded-xl bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                    <span class="tag ${statusColor} text-xs">${e.status}</span>
                    <span class="font-semibold">${e.worker_name}</span>
                </div>
                <span class="text-xs text-gray-400">${e.execution_time?.toFixed(2) || '0.00'}s</span>
            </div>
            <div class="grid grid-cols-3 gap-4 text-xs text-gray-400">
                <div>Confidence: <span class="text-gray-300">${(e.confidence * 100).toFixed(0)}%</span></div>
                <div>LLM Calls: <span class="text-gray-300">${e.llm_calls || 0}</span></div>
                <div>Memory: <span class="text-gray-300">${e.memory_usage_mb?.toFixed(2) || '-'} MB</span></div>
            </div>
            ${e.error ? `<p class="text-xs text-red-400 mt-2">${e.error}</p>` : ''}
        </div>
    `;
}

function renderDecisionCard(d) {
    const statusColor = d.status === 'completed' ? 'tag-green' : d.status === 'failed' ? 'tag-red' : 'tag-yellow';
    const capability = d.selected_capability || 'unassigned';
    const worker = d.selected_worker || 'pending';
    return `
        <div class="p-4 rounded-xl bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                    <span class="tag ${statusColor} text-xs">${d.status}</span>
                    <span class="font-semibold">${escapeHtml(d.goal || d.title || 'Decision')}</span>
                </div>
                <span class="text-xs text-gray-400">${d.confidence ? (d.confidence * 100).toFixed(0) + '%' : 'n/a'}</span>
            </div>
            <div class="grid grid-cols-2 gap-4 text-xs text-gray-400 mb-2">
                <div>Capability: <span class="text-gray-300">${escapeHtml(capability)}</span></div>
                <div>Worker: <span class="text-gray-300">${escapeHtml(worker)}</span></div>
            </div>
            <p class="text-sm text-gray-300">${escapeHtml(d.reasoning || d.next_action || 'No reasoning recorded')}</p>
            ${d.execution_result && Object.keys(d.execution_result).length ? `<p class="text-xs text-gray-500 mt-2">Outcome: ${escapeHtml(JSON.stringify(d.execution_result))}</p>` : ''}
        </div>
    `;
}

function renderLog(e) {
    const iconClass = {
        started: 'fa-play text-blue-400',
        finished: 'fa-check text-green-400',
        error: 'fa-times text-red-400',
        progress: 'fa-circle-notch text-yellow-400',
        worker_registered: 'fa-cog text-purple-400',
    }[e.event_type] || 'fa-circle text-gray-500';

    const time = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
    return `
        <div class="flex items-start gap-3 p-2 rounded-lg hover:bg-dark-800 transition">
            <div class="mt-0.5"><i class="fas ${iconClass} text-xs"></i></div>
            <div class="flex-1">
                <div class="flex items-center gap-2">
                    <span class="text-xs font-mono text-gray-500">${e.worker_name}</span>
                    <span class="text-xs text-gray-400">${e.event_type}</span>
                    <span class="text-xs text-gray-600">${time}</span>
                </div>
                <p class="text-sm text-gray-300">${escapeHtml(e.message)}</p>
            </div>
        </div>
    `;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

export function refreshDashboard() {
    loadDashboard();
}

export function switchDashboardTab(tab) {
    currentDashboardTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    event && event.target.classList.add('active');
    document.getElementById('tab-' + tab)?.classList.add('active');
}

export { loadDashboard as initDashboard };
