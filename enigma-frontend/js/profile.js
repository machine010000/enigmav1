/**
 * ENIGMA Profile Module
 * 
 * Handles Enigma Profile loading, display, and API communication.
 * This module is a Control Plane component - it displays profile data
 * from the backend and does not implement any intelligence logic.
 */

import { apiCall, showToast } from './api.js';

let currentProfile = null;
let availableProfessions = [];
let availableCapabilities = [];

/**
 * Load the user's ENIGMA PROFILE from the backend
 * @returns {Promise<Object>} Profile data
 */
export async function loadProfile() {
    try {
        // TODO: Update to USER Contract endpoint when implemented
        // Current: Using mock data structure
        // Target: GET /api/profile
        const profile = await apiCall('/api/user/profile');
        currentProfile = profile;
        renderProfile(profile);
        return profile;
    } catch (error) {
        console.error('Failed to load profile:', error);
        // Use mock data for development if endpoint doesn't exist
        const mockProfile = getMockProfile();
        currentProfile = mockProfile;
        renderProfile(mockProfile);
        return mockProfile;
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
    
    if (nameEl) nameEl.textContent = profile.name || 'Enigma';
    if (taglineEl) taglineEl.textContent = profile.tagline || 'Your AI Business Brain';
    if (professionEl) professionEl.textContent = profile.profession_focus || 'Not set';
    if (readinessEl) readinessEl.textContent = `${(profile.overall_readiness * 100).toFixed(0)}%`;
    
    // Render professions
    const professionsEl = document.getElementById('profile-professions');
    if (professionsEl && profile.professions) {
        professionsEl.innerHTML = profile.professions.map((prof, index) => `
            <div class="flex items-center gap-3 p-3 rounded-lg bg-dark-800 border ${index === 0 ? 'border-brand-purple/50' : 'border-gray-700'}">
                <div class="w-8 h-8 rounded-lg bg-brand-purple/20 flex items-center justify-center">
                    <i class="fas fa-check text-brand-purple text-sm"></i>
                </div>
                <div>
                    <p class="font-semibold text-sm">${prof.name}</p>
                    <p class="text-xs text-gray-400">${index === 0 ? 'Primary Focus' : 'Secondary'}</p>
                </div>
            </div>
        `).join('');
    }
    
    // Render capabilities
    const capabilitiesEl = document.getElementById('profile-capabilities');
    if (capabilitiesEl && profile.capabilities) {
        capabilitiesEl.innerHTML = profile.capabilities.map(cap => `
            <div class="p-3 rounded-lg bg-dark-800 border border-gray-700">
                <div class="flex items-center justify-between mb-1">
                    <span class="font-semibold text-sm">${cap.name}</span>
                    <span class="tag tag-${getMaturityColor(cap.maturity_level)} text-xs">${cap.maturity_level}</span>
                </div>
                <p class="text-xs text-gray-400">Readiness: ${(cap.readiness * 100).toFixed(0)}%</p>
            </div>
        `).join('');
    }
    
    // Render workspaces
    const workspacesEl = document.getElementById('profile-workspaces');
    if (workspacesEl && profile.active_workspaces) {
        workspacesEl.innerHTML = profile.active_workspaces.map(ws => `
            <div class="flex items-center justify-between p-3 rounded-lg bg-dark-800 border border-gray-700">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-brand-purple/20 flex items-center justify-center">
                        <i class="fas fa-briefcase text-brand-purple text-sm"></i>
                    </div>
                    <span class="font-semibold text-sm">${ws.name}</span>
                </div>
                <span class="tag tag-green text-xs">${ws.state}</span>
            </div>
        `).join('');
    }
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
function getMaturityColor(level) {
    const colors = {
        'Applied': 'green',
        'Supported': 'blue',
        'Emerging': 'yellow',
        'Theoretical': 'gray'
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
