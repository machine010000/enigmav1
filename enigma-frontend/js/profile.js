/**
 * ENIGMA Profile Module
 * 
 * Handles Enigma Profile loading, display, and API communication.
 * This module is a Control Plane component - it displays profile data
 * from the backend and does not implement any intelligence logic.
 */

import { apiCall, showToast } from './api.js';
import { USE_MOCK_DATA, IS_PRODUCTION } from './config.js';

let currentProfile = null;
let availableProfessions = [];
let availableCapabilities = [];

/**
 * Load the user's ENIGMA PROFILE from the backend
 * @returns {Promise<Object>} Profile data
 */
export async function loadProfile() {
    try {
        // GET the Enigma operational profile
        const profile = await apiCall('/api/enigma/profile');
        currentProfile = profile;
        renderProfile(profile);
        return profile;
    } catch (error) {
        console.error('Failed to load profile:', error);
        // Do not fallback to mocks here - surface error to admin
        showToast('Failed to load Enigma profile. Backend may be unavailable.', 'error');
        renderProfileError();
        return null;
    }
}

/**
 * Load available professions from backend
 * @returns {Promise<Array>} List of available professions
 */
export async function loadProfessions() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: GET /api/profile/professions
        const professions = await apiCall('/api/professions');
        availableProfessions = professions;
        return professions;
    } catch (error) {
        console.error('Failed to load professions:', error);
        // Use mock data for development
        availableProfessions = getMockProfessions();
        return availableProfessions;
    }
}

/**
 * Load available capabilities from backend
 * @returns {Promise<Array>} List of available capabilities
 */
export async function loadCapabilities() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: GET /api/profile/capabilities
        const capabilities = await apiCall('/api/capabilities');
        availableCapabilities = capabilities;
        return capabilities;
    } catch (error) {
        console.error('Failed to load capabilities:', error);
        // Use mock data for development
        availableCapabilities = getMockCapabilities();
        return availableCapabilities;
    }
}

/**
 * Update profile data
 * @param {Object} profileData - Profile data to update
 * @returns {Promise<Object>} Updated profile
 */
export async function updateProfile(profileData) {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: PUT /api/profile
        const updated = await apiCall('/api/user/profile', {
            method: 'PUT',
            body: profileData
        });
        currentProfile = updated;
        renderProfile(updated);
        showToast('Profile updated successfully', 'success');
        return updated;
    } catch (error) {
        console.error('Failed to update profile:', error);
        showToast('Failed to update profile', 'error');
        return null;
    }
}

/**
 * Update profession focus
 * @param {Object} professionData - Profession selection data
 * @returns {Promise<Object>} Updated profile
 */
export async function updateProfessions(professionData) {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: PUT /api/profile/professions
        const updated = await apiCall('/api/user/profile/professions', {
            method: 'PUT',
            body: professionData
        });
        currentProfile = updated;
        renderProfile(updated);
        showToast('Professions updated', 'success');
        return updated;
    } catch (error) {
        console.error('Failed to update professions:', error);
        showToast('Failed to update professions', 'error');
        return null;
    }
}

/**
 * Select capabilities for the profile
 * @param {Array<string>} capabilities - List of capability IDs
 * @returns {Promise<Object>} Updated profile
 */
export async function selectCapabilities(capabilities) {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: PUT /api/profile/capabilities
        const updated = await apiCall('/api/user/profile/capabilities', {
            method: 'PUT',
            body: { capabilities }
        });
        currentProfile = updated;
        renderProfile(updated);
        showToast('Capabilities updated', 'success');
        return updated;
    } catch (error) {
        console.error('Failed to update capabilities:', error);
        showToast('Failed to update capabilities', 'error');
        return null;
    }
}

/**
 * Load evidence from backend
 * @returns {Promise<Array>} List of evidence items
 */
export async function loadEvidence() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: GET /api/profile/evidence
        const evidence = await apiCall('/api/user/profile/evidence');
        renderEvidence(evidence);
        return evidence;
    } catch (error) {
        console.error('Failed to load evidence:', error);
        // Use mock data for development
        const mockEvidence = getMockEvidence();
        renderEvidence(mockEvidence);
        return mockEvidence;
    }
}

/**
 * Load readiness scores from backend
 * @returns {Promise<Object>} Readiness scores
 */
export async function loadReadiness() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Target: GET /api/profile/readiness
        const readiness = await apiCall('/api/user/profile/readiness');
        renderReadiness(readiness);
        return readiness;
    } catch (error) {
        console.error('Failed to load readiness:', error);
        // Use mock data for development
        const mockReadiness = getMockReadiness();
        renderReadiness(mockReadiness);
        return mockReadiness;
    }
}

/**
 * Render profile data to the UI
 * @param {Object} profile - Profile data
 */
function renderProfile(profile) {
    // Update profile display elements
    const nameEl = document.getElementById('profile-name');
    const taglineEl = document.getElementById('profile-tagline');
    const professionEl = document.getElementById('profile-profession');
    const readinessEl = document.getElementById('profile-readiness');
    
    if (nameEl) nameEl.textContent = 'ENIGMA';
    if (taglineEl) taglineEl.textContent = 'Operational capability profile';
    if (professionEl) professionEl.textContent = 'Expertise domains are not exposed by the current profile API';
    // UI-derived ratio from the real profile counts; this is not a backend field.
    const totalCapabilities = Number(profile.total_capabilities) || 0;
    const readyCapabilities = Number(profile.ready_for_freelance_count) || 0;
    const overallReadiness = totalCapabilities > 0 ? readyCapabilities / totalCapabilities : 0;
    if (readinessEl) readinessEl.textContent = `${(overallReadiness * 100).toFixed(0)}%`;
    
    // Render professions
    const professionsEl = document.getElementById('profile-professions');
    if (professionsEl) {
        professionsEl.innerHTML = '<div class="text-gray-500 text-sm">Expertise domains are not exposed by the current profile API.</div>';
    }
    
    // Render capabilities
    const capabilitiesEl = document.getElementById('profile-capabilities');
    if (capabilitiesEl) {
        const capabilities = Array.isArray(profile.capabilities) ? profile.capabilities : [];
        capabilitiesEl.innerHTML = capabilities.length ? capabilities.map(cap => {
            const confidence = Number.isFinite(cap.confidence) ? cap.confidence : 0;
            const threshold = Number.isFinite(cap.freelance_readiness_threshold) ? cap.freelance_readiness_threshold : 0;
            const status = cap.status || 'unknown';
            return `
            <div class="p-3 rounded-lg bg-dark-800 border border-gray-700">
                <div class="flex items-center justify-between mb-1">
                    <span class="font-semibold text-sm">${cap.name}</span>
                    <span class="tag tag-${getStatusColor(status)} text-xs">${status}</span>
                </div>
                <p class="text-xs text-gray-400 mb-2">${cap.description || 'No description available'}</p>
                <div class="grid grid-cols-2 gap-1 text-xs text-gray-400">
                    <span>Category: <span class="text-gray-300">${cap.category || 'Not specified'}</span></span>
                    <span>Module: <span class="text-gray-300">${cap.module || 'Not specified'}</span></span>
                    <span>Confidence: <span class="text-gray-300">${(confidence * 100).toFixed(0)}%</span></span>
                    <span>Evidence: <span class="text-gray-300">${Number(cap.evidence_count) || 0}</span></span>
                    <span>Successful: <span class="text-gray-300">${Number(cap.successful_executions) || 0}</span></span>
                    <span>Failed: <span class="text-gray-300">${Number(cap.failed_executions) || 0}</span></span>
                    <span>Execution: <span class="text-gray-300">${cap.execution_available ? 'Available' : 'Unavailable'}</span></span>
                    <span>Threshold: <span class="text-gray-300">${(threshold * 100).toFixed(0)}%</span></span>
                </div>
                <p class="text-xs mt-2 ${cap.meets_threshold ? 'text-green-400' : 'text-yellow-400'}">${cap.meets_threshold ? 'Meets freelance threshold' : 'Does not meet freelance threshold'}</p>
            </div>
        `;
        }).join('') : '<div class="text-gray-500 text-sm">No capabilities are available in the current profile.</div>';
    }
    
    // Render workspaces
    const workspacesEl = document.getElementById('profile-workspaces');
    if (workspacesEl) {
        workspacesEl.innerHTML = '<div class="text-gray-500 text-sm">Workspace data is not exposed by the current profile API.</div>';
    }

    renderProfileEvidenceSummary(profile.capabilities);
    renderProfileReadinessSummary(profile);
}

function renderProfileEvidenceSummary(capabilities) {
    const items = Array.isArray(capabilities) ? capabilities : [];
    const count = items.reduce((sum, cap) => sum + (Number(cap.evidence_count) || 0), 0);
    const countEl = document.getElementById('profile-evidence-count');
    const evidenceEl = document.getElementById('profile-evidence');
    if (countEl) countEl.textContent = count;
    if (evidenceEl) evidenceEl.innerHTML = '<div class="text-gray-500 text-sm">Detailed evidence history is not available in this view yet.</div>';
}

function renderProfileReadinessSummary(profile) {
    const readinessEl = document.getElementById('profile-readiness-scores');
    if (!readinessEl) return;
    readinessEl.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div class="p-3 rounded-lg bg-dark-800">Total capabilities: <span class="font-semibold">${profile.total_capabilities || 0}</span></div>
            <div class="p-3 rounded-lg bg-dark-800">Qualified: <span class="font-semibold">${profile.qualified_count || 0}</span></div>
            <div class="p-3 rounded-lg bg-dark-800">Freelance ready: <span class="font-semibold">${profile.ready_for_freelance_count || 0}</span></div>
        </div>`;
}

/**
 * Render evidence vault
 * @param {Array} evidence - List of evidence items
 */
function renderEvidence(evidence) {
    const evidenceEl = document.getElementById('profile-evidence');
    const countEl = document.getElementById('profile-evidence-count');
    
    if (countEl) countEl.textContent = evidence.length;
    
    if (!evidenceEl) return;
    
    if (evidence.length === 0) {
        evidenceEl.innerHTML = '<div class="text-gray-500 text-sm">No evidence yet</div>';
        return;
    }
    
    evidenceEl.innerHTML = evidence.map(ev => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-brand-blue/20 flex items-center justify-center">
                        <i class="fas fa-file-alt text-brand-blue text-sm"></i>
                    </div>
                    <span class="font-semibold text-sm">${ev.capability}</span>
                </div>
                <span class="tag tag-${getFreshnessColor(ev.freshness)} text-xs">${ev.freshness}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-2">
                <div>Knowledge Level: <span class="text-gray-300">${ev.knowledge_level}</span></div>
                <div>Confidence: <span class="text-gray-300">${(ev.confidence * 100).toFixed(0)}%</span></div>
                <div>Evidence: <span class="text-gray-300">${ev.evidence_count}</span></div>
                <div>Source: <span class="text-gray-300">${ev.source}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render readiness scores
 * @param {Object} readiness - Readiness scores by capability
 */
function renderReadiness(readiness) {
    const readinessEl = document.getElementById('profile-readiness-scores');
    if (!readinessEl) return;
    
    if (!readiness || Object.keys(readiness).length === 0) {
        readinessEl.innerHTML = '<div class="text-gray-500 text-sm">No readiness data available</div>';
        return;
    }
    
    readinessEl.innerHTML = Object.entries(readiness).map(([capability, score]) => `
        <div class="space-y-1">
            <div class="flex items-center justify-between text-sm">
                <span class="font-semibold">${capability}</span>
                <span class="text-gray-400">${(score * 100).toFixed(0)}%</span>
            </div>
            <div class="w-full bg-dark-600 rounded-full h-2">
                <div class="progress-bar h-2 rounded-full" style="width: ${score * 100}%"></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render an error state for the profile page
 */
export function renderProfileError() {
    const nameEl = document.getElementById('profile-name');
    const taglineEl = document.getElementById('profile-tagline');
    const capabilitiesEl = document.getElementById('profile-capabilities');
    const professionsEl = document.getElementById('profile-professions');
    const readinessEl = document.getElementById('profile-readiness');
    const readinessScoresEl = document.getElementById('profile-readiness-scores');
    const evidenceEl = document.getElementById('profile-evidence');

    if (nameEl) nameEl.textContent = 'Unavailable';
    if (taglineEl) taglineEl.textContent = 'Unable to load profile data';
    if (professionsEl) professionsEl.innerHTML = '<div class="text-red-400 text-sm">Failed to load professions</div>';
    if (capabilitiesEl) capabilitiesEl.innerHTML = '<div class="text-red-400 text-sm">Failed to load capabilities</div>';
    if (readinessEl) readinessEl.textContent = '-';
    if (readinessScoresEl) readinessScoresEl.innerHTML = '<div class="text-red-400 text-sm">Failed to load readiness scores</div>';
    if (evidenceEl) evidenceEl.innerHTML = '<div class="text-red-400 text-sm">Failed to load evidence</div>';
}

/**
 * Render edit form with available options
 */
export async function renderEditForm() {
    await loadProfessions();
    await loadCapabilities();
    
    // Populate professions
    const professionsEl = document.getElementById('edit-professions');
    if (professionsEl && availableProfessions.length > 0) {
        professionsEl.innerHTML = availableProfessions.map(prof => `
            <label class="flex items-center gap-3 p-3 rounded-lg bg-dark-800 border border-gray-700 cursor-pointer hover:border-brand-purple/50 transition">
                <input type="checkbox" name="profession" value="${prof.id}" class="w-4 h-4 rounded">
                <div>
                    <p class="font-semibold text-sm">${prof.name}</p>
                    <p class="text-xs text-gray-400">${prof.description}</p>
                </div>
            </label>
        `).join('');
    }
    
    // Populate capabilities
    const capabilitiesEl = document.getElementById('edit-capabilities');
    if (capabilitiesEl && availableCapabilities.length > 0) {
        capabilitiesEl.innerHTML = availableCapabilities.map(cap => `
            <label class="flex items-center gap-3 p-3 rounded-lg bg-dark-800 border border-gray-700 cursor-pointer hover:border-brand-purple/50 transition">
                <input type="checkbox" name="capability" value="${cap.id}" class="w-4 h-4 rounded">
                <div>
                    <p class="font-semibold text-sm">${cap.name}</p>
                    <p class="text-xs text-gray-400">${cap.description}</p>
                </div>
            </label>
        `).join('');
    }
    
    // Pre-fill current values
    if (currentProfile) {
        const nameEl = document.getElementById('edit-name');
        const taglineEl = document.getElementById('edit-tagline');
        const positioningEl = document.getElementById('edit-positioning');
        
        if (nameEl) nameEl.value = currentProfile.name || '';
        if (taglineEl) taglineEl.value = currentProfile.tagline || '';
        if (positioningEl) positioningEl.value = currentProfile.profession_focus || '';
    }
}

/**
 * Get maturity level color class
 * @param {string} level - Maturity level
 * @returns {string} Tailwind color class
 */
function getStatusColor(level) {
    const colors = {
        'proven': 'green',
        'qualified': 'green',
        'practicing': 'blue',
        'learning': 'yellow',
        'unknown': 'gray'
    };
    return colors[level] || 'gray';
}

/**
 * Get freshness color class
 * @param {string} freshness - Freshness level
 * @returns {string} Tailwind color class
 */
function getFreshnessColor(freshness) {
    const colors = {
        'Fresh': 'green',
        'Recent': 'blue',
        'Aging': 'yellow',
        'Stale': 'red'
    };
    return colors[freshness] || 'gray';
}

/**
 * Get current profile
 * @returns {Object|null} Current profile data
 */
export function getCurrentProfile() {
    return currentProfile;
}

/**
 * Initialize profile forms
 */
export function initProfileForms() {
    const editForm = document.getElementById('profile-edit-form');
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Collect selected professions
            const professionCheckboxes = document.querySelectorAll('input[name="profession"]:checked');
            const selectedProfessions = Array.from(professionCheckboxes).map(cb => cb.value);
            
            // Collect selected capabilities
            const capabilityCheckboxes = document.querySelectorAll('input[name="capability"]:checked');
            const selectedCapabilities = Array.from(capabilityCheckboxes).map(cb => cb.value);
            
            const data = {
                name: document.getElementById('edit-name').value,
                tagline: document.getElementById('edit-tagline').value,
                profession_focus: document.getElementById('edit-positioning').value,
                professions: selectedProfessions,
                capabilities: selectedCapabilities
            };
            
            await updateProfile(data);
            await updateProfessions({ professions: selectedProfessions });
            await selectCapabilities(selectedCapabilities);
            
            showPage('profile');
        });
    }
}

// Mock data functions for development (will be removed when backend APIs are ready)
function getMockProfile() {
    return {
        name: 'Enigma',
        tagline: 'Your AI Business Brain',
        profession_focus: 'AI-powered business intelligence',
        overall_readiness: 0.78,
        professions: [
            { id: 'seo', name: 'SEO Specialist' },
            { id: 'social', name: 'Social Media Manager' }
        ],
        capabilities: [
            { id: 'keyword', name: 'Keyword Research', maturity_level: 'Applied', readiness: 0.91 },
            { id: 'audit', name: 'SEO Audit', maturity_level: 'Applied', readiness: 0.82 },
            { id: 'content', name: 'Content Strategy', maturity_level: 'Supported', readiness: 0.64 }
        ],
        active_workspaces: [
            { id: 'freelancing', name: 'Freelancing', state: 'ACTIVE' }
        ]
    };
}

function getMockProfessions() {
    return [
        { id: 'seo', name: 'SEO Specialist', description: 'Search engine optimization' },
        { id: 'social', name: 'Social Media Manager', description: 'Social media strategy' },
        { id: 'ads', name: 'Ads Manager', description: 'Paid advertising' },
        { id: 'content', name: 'Content Strategist', description: 'Content planning' }
    ];
}

function getMockCapabilities() {
    return [
        { id: 'keyword', name: 'Keyword Research', description: 'Keyword analysis and research' },
        { id: 'audit', name: 'SEO Audit', description: 'Website SEO analysis' },
        { id: 'content', name: 'Content Strategy', description: 'Content planning and strategy' },
        { id: 'technical', name: 'Technical SEO', description: 'Technical SEO optimization' },
        { id: 'audience', name: 'Audience Analysis', description: 'Audience research and analysis' }
    ];
}

function getMockEvidence() {
    return [
        { capability: 'SEO Audit', knowledge_level: 'Applied', confidence: 0.87, evidence_count: 5, freshness: 'Fresh', source: 'Research' },
        { capability: 'Content Strategy', knowledge_level: 'Supported', confidence: 0.74, evidence_count: 3, freshness: 'Aging', source: 'Academy' },
        { capability: 'Keyword Research', knowledge_level: 'Applied', confidence: 0.91, evidence_count: 7, freshness: 'Fresh', source: 'Memory' }
    ];
}

function getMockReadiness() {
    return {
        'SEO Audit': 0.82,
        'Keyword Research': 0.91,
        'Content Strategy': 0.64,
        'Audience Analysis': 0.73,
        'Technical SEO': 0.45
    };
}
