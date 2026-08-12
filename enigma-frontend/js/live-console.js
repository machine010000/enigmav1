import { WEBSOCKET_BASE } from './config.js';

/**
 * Live Console Module (TASK-006)
 *
 * Connects to the backend WebSocket at /ws/events and renders every
 * WorkerEvent in real time.  Workers emit events like:
 *   "verification_started", "research_started", "audience_started",
 *   "keyword_started", "finished", "error", "progress"
 */

let ws = null;
let reconnectTimer = null;
let messageCounter = 0;

export function initLiveConsole() {
    connectWebSocket();
}

function connectWebSocket() {
    const wsUrl = `${WEBSOCKET_BASE}/ws/events`;

    const statusEl = document.getElementById('ws-status');
    statusEl.textContent = 'Connecting…';
    statusEl.className = 'tag tag-yellow text-xs';

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        statusEl.textContent = 'Connected';
        statusEl.className = 'tag tag-green text-xs';
        console.log('[LiveConsole] WebSocket connected');
        hideEmptyState();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            appendEvent(data);
        } catch (err) {
            console.error('[LiveConsole] Failed to parse event:', err);
        }
    };

    ws.onerror = (err) => {
        console.error('[LiveConsole] WebSocket error:', err);
    };

    ws.onclose = () => {
        statusEl.textContent = 'Disconnected';
        statusEl.className = 'tag tag-red text-xs';
        console.log('[LiveConsole] WebSocket disconnected, attempting reconnect…');

        if (reconnectTimer) return;
        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connectWebSocket();
        }, 3000);
    };
}

function hideEmptyState() {
    const empty = document.getElementById('console-empty');
    if (empty) empty.classList.add('hidden');
}

function appendEvent(e) {
    messageCounter++;
    const feed = document.getElementById('event-feed');
    if (!feed) return;

    // Auto-hide old messages if getting too many (keep last 500)
    if (messageCounter > 500) {
        feed.innerHTML = '';
        messageCounter = 0;
    }

    const iconMap = {
        started: 'fa-play-circle',
        finished: 'fa-flag-checkered',
        error: 'fa-exclamation-triangle',
        progress: 'fa-circle-notch',
        worker_registered: 'fa-cog',
        execution_started: 'fa-rocket',
        verification_started: 'fa-shield-alt',
        research_started: 'fa-search',
        audience_started: 'fa-users',
        keyword_started: 'fa-key',
    };
    const colorMap = {
        started: 'text-blue-400',
        finished: 'text-green-400',
        error: 'text-red-400',
        progress: 'text-yellow-400',
        worker_registered: 'text-purple-400',
        execution_started: 'text-indigo-400',
        verification_started: 'text-cyan-400',
        research_started: 'text-blue-300',
        audience_started: 'text-pink-400',
        keyword_started: 'text-orange-400',
    };

    const icon = iconMap[e.type] || 'fa-circle';
    const color = colorMap[e.type] || 'text-gray-500';
    const time = e.timestamp
        ? new Date(e.timestamp).toLocaleTimeString()
        : '';
    const dataStr = e.data && Object.keys(e.data).length > 0
        ? `<pre class="text-xs text-gray-600 mt-1 whitespace-pre-wrap">${escapeJson(e.data)}</pre>`
        : '';

    const el = document.createElement('div');
    el.className = 'flex items-start gap-3 p-3 rounded-lg bg-dark-800 border border-gray-700 animate-fadeIn';
    el.innerHTML = `
        <div class="mt-0.5 flex-shrink-0">
            <i class="fas ${icon} ${color} text-xs"></i>
        </div>
        <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
                <span class="text-xs font-mono text-gray-500">${e.worker_name || 'system'}</span>
                <span class="text-xs text-gray-400">${e.type}</span>
                <span class="text-xs text-gray-600">${time}</span>
            </div>
            <p class="text-sm text-gray-300 mt-1">${escapeHtml(e.message || '')}</p>
            ${dataStr}
        </div>
    `;

    feed.insertBefore(el, feed.firstChild);
}

function escapeJson(obj) {
    return escapeHtml(JSON.stringify(obj, null, 2));
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

export function toggleWs() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
        setTimeout(connectWebSocket, 500);
    } else {
        connectWebSocket();
    }
}

export function clearConsole() {
    const feed = document.getElementById('event-feed');
    if (feed) feed.innerHTML = '';
    messageCounter = 0;
    const empty = document.getElementById('console-empty');
    if (empty) empty.classList.remove('hidden');
}

// Auto-connect when the live-console module is loaded via main.js
document.addEventListener('DOMContentLoaded', () => {
    const feed = document.getElementById('event-feed');
    if (feed) {
        initLiveConsole();
    }
});
