/**
 * ENIGMA Workspaces Module
 * 
 * Handles workspace selection, navigation, state, and API communication.
 * This module is a Control Plane component - it displays workspace data
 * from the backend and does not implement any intelligence logic.
 */

import { apiCall, showToast } from './api.js';

let currentWorkspace = null;
let availableWorkspaces = [];

/**
 * Load available workspaces from the backend
 * @returns {Promise<Array>} List of available workspaces
 */
export async function loadWorkspaces() {
    try {
        const workspaces = await apiCall('/api/workspaces');
        availableWorkspaces = workspaces;
        renderWorkspaces(workspaces);
        return workspaces;
    } catch (error) {
        console.error('Failed to load workspaces:', error);
        showToast('Failed to load workspaces', 'error');
        return [];
    }
}

/**
 * Activate a workspace
 * @param {string} workspaceId - Workspace ID to activate
 * @returns {Promise<Object>} Updated workspace state
 */
export async function activateWorkspace(workspaceId) {
    try {
        const workspace = await apiCall(`/api/workspaces/${workspaceId}/activate`, {
            method: 'POST'
        });
        currentWorkspace = workspace;
        renderActiveWorkspace(workspace);
        showToast(`${workspace.name} activated`, 'success');
        return workspace;
    } catch (error) {
        console.error('Failed to activate workspace:', error);
        showToast('Failed to activate workspace', 'error');
        return null;
    }
}

/**
 * Deactivate the current workspace
 * @returns {Promise<Object>} Updated workspace state
 */
export async function deactivateWorkspace() {
    if (!currentWorkspace) return null;
    
    try {
        const workspace = await apiCall(`/api/workspaces/${currentWorkspace.id}/deactivate`, {
            method: 'POST'
        });
        currentWorkspace = null;
        renderActiveWorkspace(null);
        showToast('Workspace deactivated', 'success');
        return workspace;
    } catch (error) {
        console.error('Failed to deactivate workspace:', error);
        showToast('Failed to deactivate workspace', 'error');
        return null;
    }
}

/**
 * Switch to a different workspace
 * @param {string} workspaceId - Workspace ID to switch to
 * @returns {Promise<Object>} New active workspace
 */
export async function switchWorkspace(workspaceId) {
    try {
        const workspace = await apiCall(`/api/workspaces/${workspaceId}/switch`, {
            method: 'POST'
        });
        currentWorkspace = workspace;
        renderActiveWorkspace(workspace);
        showToast(`Switched to ${workspace.name}`, 'success');
        return workspace;
    } catch (error) {
        console.error('Failed to switch workspace:', error);
        showToast('Failed to switch workspace', 'error');
        return null;
    }
}

/**
 * Render available workspaces to the UI
 * @param {Array} workspaces - List of workspaces
 */
function renderWorkspaces(workspaces) {
    const container = document.getElementById('workspaces-list');
    if (!container) return;
    
    if (workspaces.length === 0) {
        container.innerHTML = '<div class="text-gray-500 text-sm">No workspaces available</div>';
        return;
    }
    
    container.innerHTML = workspaces.map(ws => `
        <div class="glass-card p-6 cursor-pointer hover:border-brand-purple/50 transition" onclick="activateWorkspace('${ws.id}')">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-br ${getWorkspaceGradient(ws.type)} flex items-center justify-center">
                        <i class="${getWorkspaceIcon(ws.type)} text-white text-xl"></i>
                    </div>
                    <div>
                        <h3 class="font-bold">${ws.name}</h3>
                        <p class="text-xs text-gray-400">${ws.type}</p>
                    </div>
                </div>
                <span class="tag ${getStateColor(ws.state)} text-xs">${ws.state}</span>
            </div>
            <p class="text-sm text-gray-400 mb-3">${ws.description || 'No description'}</p>
            ${ws.state === 'ACTIVE' ? '<button class="btn-primary w-full text-sm">Enter Workspace</button>' : '<button class="btn-secondary w-full text-sm">Activate</button>'}
        </div>
    `).join('');
}

/**
 * Render the active workspace to the UI
 * @param {Object|null} workspace - Active workspace or null
 */
function renderActiveWorkspace(workspace) {
    const container = document.getElementById('active-workspace-display');
    if (!container) return;
    
    if (!workspace) {
        container.innerHTML = '<div class="text-gray-500 text-sm">No active workspace</div>';
        return;
    }
    
    container.innerHTML = `
        <div class="glass-card p-6">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br ${getWorkspaceGradient(workspace.type)} flex items-center justify-center">
                    <i class="${getWorkspaceIcon(workspace.type)} text-white text-xl"></i>
                </div>
                <div>
                    <h3 class="font-bold text-lg">${workspace.name}</h3>
                    <p class="text-xs text-gray-400">${workspace.type} • ${workspace.state}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <button onclick="deactivateWorkspace()" class="btn-secondary text-xs py-2 px-4">Deactivate</button>
            </div>
        </div>
    `;
}

/**
 * Get workspace gradient based on type
 * @param {string} type - Workspace type
 * @returns {string} Tailwind gradient classes
 */
function getWorkspaceGradient(type) {
    const gradients = {
        'FREELANCING': 'from-brand-purple to-brand-blue',
        'BRAND_MARKETING': 'from-brand-blue to-brand-cyan',
        'KNOWLEDGE': 'from-brand-cyan to-emerald-500'
    };
    return gradients[type] || 'from-gray-600 to-gray-800';
}

/**
 * Get workspace icon based on type
 * @param {string} type - Workspace type
 * @returns {string} Font Awesome icon class
 */
function getWorkspaceIcon(type) {
    const icons = {
        'FREELANCING': 'fas fa-briefcase',
        'BRAND_MARKETING': 'fas fa-bullhorn',
        'KNOWLEDGE': 'fas fa-book'
    };
    return icons[type] || 'fas fa-cube';
}

/**
 * Get state color class
 * @param {string} state - Workspace state
 * @returns {string} Tailwind color class
 */
function getStateColor(state) {
    const colors = {
        'CREATED': 'yellow',
        'ACTIVE': 'green',
        'PAUSED': 'blue',
        'ARCHIVED': 'gray'
    };
    return colors[state] || 'gray';
}

/**
 * Get current active workspace
 * @returns {Object|null} Current workspace
 */
export function getCurrentWorkspace() {
    return currentWorkspace;
}

/**
 * Get available workspaces
 * @returns {Array} List of available workspaces
 */
export function getAvailableWorkspaces() {
    return availableWorkspaces;
}
