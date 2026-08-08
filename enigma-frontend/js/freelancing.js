/**
 * FREELANCING Workspace Module
 * 
 * Handles the FREELANCING workspace functionality.
 * This module is a Control Plane component - it displays freelancing data
 * from the backend and does not implement any intelligence logic.
 * 
 * IMPORTANT: This module does NOT calculate readiness, match jobs, or perform research.
 * All intelligence comes from the backend via API contracts.
 * 
 * MOCK DATA POLICY: Mock data is development-only and should not be used in production.
 * Set USE_MOCK_DATA = false for production.
 */

import { apiCall, showToast } from './api.js';
import { getCurrentProfile } from './profile.js';

let freelancingData = null;
let isUsingMockData = false;

// DEVELOPMENT ONLY: Set to false for production
const USE_MOCK_DATA = false;

/**
 * Load freelancing workspace data from backend
 * @returns {Promise<Object>} Freelancing workspace data
 */
export async function loadFreelancing() {
    try {
        // Real API endpoint
        const data = await apiCall('/api/freelancing');
        freelancingData = data;
        isUsingMockData = false;
        renderFreelancing(data);
        return data;
    } catch (error) {
        console.error('Failed to load freelancing data:', error);
        
        // PRODUCTION: Do not use mock data - show error
        if (!USE_MOCK_DATA) {
            showToast('Failed to load freelancing data. Backend may be unavailable.', 'error');
            renderFreelancingError();
            return null;
        }
        
        // DEVELOPMENT ONLY: Use mock data for development
        const mockData = getMockFreelancing();
        freelancingData = mockData;
        isUsingMockData = true;
        renderFreelancing(mockData);
        return mockData;
    }
}

/**
 * Load platforms from backend
 * @returns {Promise<Array>} List of platforms
 */
export async function loadPlatforms() {
    try {
        // Real API endpoint
        const platforms = await apiCall('/api/freelancing/platforms');
        renderPlatforms(platforms);
        return platforms;
    } catch (error) {
        console.error('Failed to load platforms:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load platforms. Backend may be unavailable.', 'error');
            renderPlatformsError();
            return null;
        }
        
        const mockPlatforms = getMockPlatforms();
        renderPlatforms(mockPlatforms);
        return mockPlatforms;
    }
}

/**
 * Load capabilities from backend
 * @returns {Promise<Array>} List of capabilities with readiness
 */
export async function loadCapabilities() {
    try {
        // Real API endpoint
        const capabilities = await apiCall('/api/freelancing/capabilities');
        renderCapabilities(capabilities);
        return capabilities;
    } catch (error) {
        console.error('Failed to load capabilities:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load capabilities. Backend may be unavailable.', 'error');
            renderCapabilitiesError();
            return null;
        }
        
        const mockCapabilities = getMockCapabilities();
        renderCapabilities(mockCapabilities);
        return mockCapabilities;
    }
}

/**
 * Load jobs from backend
 * @returns {Promise<Array>} List of jobs
 */
export async function loadJobs() {
    try {
        // Real API endpoint
        const jobs = await apiCall('/api/freelancing/jobs');
        renderJobs(jobs);
        return jobs;
    } catch (error) {
        console.error('Failed to load jobs:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load jobs. Backend may be unavailable.', 'error');
            renderJobsError();
            return null;
        }
        
        const mockJobs = getMockJobs();
        renderJobs(mockJobs);
        return mockJobs;
    }
}

/**
 * Load job detail from backend
 * @param {string} jobId - Job ID
 * @returns {Promise<Object>} Job detail
 */
export async function loadJobDetail(jobId) {
    try {
        // Real API endpoint
        const job = await apiCall(`/api/freelancing/jobs/${jobId}`);
        return job;
    } catch (error) {
        console.error('Failed to load job detail:', error);
        showToast('Failed to load job detail. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Load applications from backend
 * @returns {Promise<Array>} List of applications
 */
export async function loadApplications() {
    try {
        // Real API endpoint
        const applications = await apiCall('/api/freelancing/applications');
        renderApplications(applications);
        return applications;
    } catch (error) {
        console.error('Failed to load applications:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load applications. Backend may be unavailable.', 'error');
            renderApplicationsError();
            return null;
        }
        
        const mockApplications = getMockApplications();
        renderApplications(mockApplications);
        return mockApplications;
    }
}

/**
 * Load active work from backend
 * @returns {Promise<Array>} List of active work
 */
export async function loadActiveWork() {
    try {
        // Real API endpoint
        const activeWork = await apiCall('/api/freelancing/active-work');
        renderActiveWork(activeWork);
        return activeWork;
    } catch (error) {
        console.error('Failed to load active work:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load active work. Backend may be unavailable.', 'error');
            renderActiveWorkError();
            return null;
        }
        
        const mockActiveWork = getMockActiveWork();
        renderActiveWork(mockActiveWork);
        return mockActiveWork;
    }
}

/**
 * Check job readiness from backend
 * @param {string} jobId - Job ID
 * @returns {Promise<Object>} Readiness assessment
 */
export async function checkJobReadiness(jobId) {
    try {
        // Real API endpoint
        const readiness = await apiCall(`/api/freelancing/jobs/${jobId}/assessment`);
        return readiness;
    } catch (error) {
        console.error('Failed to check job readiness:', error);
        showToast('Failed to check job readiness. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Start research for a job
 * @param {string} jobId - Job ID
 * @returns {Promise<Object>} Research status
 */
export async function startJobResearch(jobId) {
    try {
        // Real API endpoint
        const result = await apiCall(`/api/freelancing/jobs/${jobId}/research`, {
            method: 'POST'
        });
        showToast('Research started', 'success');
        return result;
    } catch (error) {
        console.error('Failed to start research:', error);
        showToast('Failed to start research. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Create application draft
 * @param {string} jobId - Job ID
 * @returns {Promise<Object>} Application draft
 */
export async function createApplicationDraft(jobId) {
    try {
        // Real API endpoint
        const application = await apiCall('/api/freelancing/applications', {
            method: 'POST',
            body: { job_id: jobId }
        });
        showToast('Application draft created', 'success');
        return application;
    } catch (error) {
        console.error('Failed to create application draft:', error);
        showToast('Failed to create application draft. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Check if using mock data
 * @returns {boolean} True if using mock data
 */
export function isMockDataActive() {
    return isUsingMockData;
}

/**
 * Render freelancing overview
 * @param {Object} data - Freelancing data
 */
function renderFreelancing(data) {
    const statusEl = document.getElementById('freelancing-status');
    const platformsEl = document.getElementById('overview-platforms');
    const capabilitiesEl = document.getElementById('overview-capabilities');
    const readinessEl = document.getElementById('overview-readiness');
    const jobsEl = document.getElementById('overview-jobs');
    const applicationsEl = document.getElementById('overview-applications');
    
    if (statusEl) {
        statusEl.textContent = data.status || 'ACTIVE';
        statusEl.className = `tag tag-${getStatusColor(data.status)} text-xs`;
    }
    if (platformsEl) platformsEl.textContent = data.platforms_connected || 0;
    if (capabilitiesEl) capabilitiesEl.textContent = data.capabilities_ready || 0;
    if (readinessEl) readinessEl.textContent = `${(data.overall_readiness * 100).toFixed(0)}%`;
    if (jobsEl) jobsEl.textContent = data.jobs_discovered || 0;
    if (applicationsEl) applicationsEl.textContent = data.applications_total || 0;
}

/**
 * Render error state for freelancing overview
 */
function renderFreelancingError() {
    const statusEl = document.getElementById('freelancing-status');
    if (statusEl) {
        statusEl.textContent = 'ERROR';
        statusEl.className = 'tag tag-red text-xs';
    }
}

/**
 * Render error state for platforms
 */
function renderPlatformsError() {
    const platformsEl = document.getElementById('platforms-list');
    if (platformsEl) {
        platformsEl.innerHTML = '<div class="text-red-500 text-sm">Failed to load platforms. Backend may be unavailable.</div>';
    }
}

/**
 * Render error state for capabilities
 */
function renderCapabilitiesError() {
    const capabilitiesEl = document.getElementById('capabilities-list');
    if (capabilitiesEl) {
        capabilitiesEl.innerHTML = '<div class="text-red-500 text-sm">Failed to load capabilities. Backend may be unavailable.</div>';
    }
}

/**
 * Render error state for jobs
 */
function renderJobsError() {
    const jobsEl = document.getElementById('jobs-list');
    if (jobsEl) {
        jobsEl.innerHTML = '<div class="text-red-500 text-sm">Failed to load jobs. Backend may be unavailable.</div>';
    }
}

/**
 * Render error state for applications
 */
function renderApplicationsError() {
    const applicationsEl = document.getElementById('applications-list');
    if (applicationsEl) {
        applicationsEl.innerHTML = '<div class="text-red-500 text-sm">Failed to load applications. Backend may be unavailable.</div>';
    }
}

/**
 * Render error state for active work
 */
function renderActiveWorkError() {
    const activeWorkEl = document.getElementById('active-work-list');
    if (activeWorkEl) {
        activeWorkEl.innerHTML = '<div class="text-red-500 text-sm">Failed to load active work. Backend may be unavailable.</div>';
    }
}

/**
 * Render platforms
 * @param {Array} platforms - List of platforms
 */
function renderPlatforms(platforms) {
    const platformsEl = document.getElementById('platforms-list');
    if (!platformsEl) return;
    
    if (!platforms || platforms.length === 0) {
        platformsEl.innerHTML = '<div class="text-gray-500 text-sm">No platforms connected</div>';
        return;
    }
    
    platformsEl.innerHTML = platforms.map(platform => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-brand-purple/20 flex items-center justify-center">
                        <i class="fas fa-globe text-brand-purple"></i>
                    </div>
                    <div>
                        <p class="font-semibold">${platform.name}</p>
                        <p class="text-xs text-gray-400">${platform.application_model}</p>
                    </div>
                </div>
                <span class="tag tag-${getConnectionColor(platform.connection_status)} text-xs">${platform.connection_status}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
                <div>Auth: <span class="text-gray-300">${platform.auth_status}</span></div>
                <div>Profile: <span class="text-gray-300">${platform.profile_status}</span></div>
                <div>Credits: <span class="text-gray-300">${platform.credits_available || 'N/A'}</span></div>
                <div>Availability: <span class="text-gray-300">${platform.availability}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render capabilities
 * @param {Array} capabilities - List of capabilities
 */
function renderCapabilities(capabilities) {
    const capabilitiesEl = document.getElementById('capabilities-list');
    if (!capabilitiesEl) return;
    
    if (!capabilities || capabilities.length === 0) {
        capabilitiesEl.innerHTML = '<div class="text-gray-500 text-sm">No capabilities mapped</div>';
        return;
    }
    
    capabilitiesEl.innerHTML = capabilities.map(cap => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-brand-blue/20 flex items-center justify-center">
                        <i class="fas fa-cogs text-brand-blue"></i>
                    </div>
                    <div>
                        <p class="font-semibold">${cap.name}</p>
                        <p class="text-xs text-gray-400">Knowledge: ${cap.knowledge_maturity}</p>
                    </div>
                </div>
                <span class="tag tag-${getReadinessColor(cap.readiness_status)} text-xs">${cap.readiness_status}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
                <div>Readiness: <span class="text-gray-300">${(cap.readiness_score * 100).toFixed(0)}%</span></div>
                <div>Evidence: <span class="text-gray-300">${cap.evidence_count}</span></div>
                <div>Freshness: <span class="text-gray-300">${cap.freshness}</span></div>
                <div>Status: <span class="text-gray-300">${cap.status}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render jobs
 * @param {Array} jobs - List of jobs
 */
function renderJobs(jobs) {
    const jobsEl = document.getElementById('jobs-list');
    if (!jobsEl) return;
    
    if (!jobs || jobs.length === 0) {
        jobsEl.innerHTML = '<div class="text-gray-500 text-sm">No jobs discovered</div>';
        return;
    }
    
    jobsEl.innerHTML = jobs.map(job => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700 cursor-pointer hover:border-brand-purple/50 transition" onclick="viewJobDetail('${job.id}')">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <p class="font-semibold">${job.title}</p>
                    <p class="text-xs text-gray-400">${job.platform} • ${job.client}</p>
                </div>
                <div class="text-right">
                    <p class="font-bold text-brand-purple">${job.budget}</p>
                    <span class="tag tag-${getReadinessColor(job.readiness_status)} text-xs">${job.readiness_status}</span>
                </div>
            </div>
            <div class="flex items-center gap-4 text-xs text-gray-400">
                <div>Match: <span class="text-gray-300">${(job.match_score * 100).toFixed(0)}%</span></div>
                <div>Required: <span class="text-gray-300">${job.required_capabilities.join(', ')}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render applications
 * @param {Array} applications - List of applications
 */
function renderApplications(applications) {
    const applicationsEl = document.getElementById('applications-list');
    if (!applicationsEl) return;
    
    if (!applications || applications.length === 0) {
        applicationsEl.innerHTML = '<div class="text-gray-500 text-sm">No applications</div>';
        return;
    }
    
    applicationsEl.innerHTML = applications.map(app => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <p class="font-semibold">${app.job_title}</p>
                    <p class="text-xs text-gray-400">${app.platform}</p>
                </div>
                <span class="tag tag-${getApplicationStatusColor(app.status)} text-xs">${app.status}</span>
            </div>
            <div class="flex items-center gap-4 text-xs text-gray-400">
                <div>Submitted: <span class="text-gray-300">${app.submitted_at || 'N/A'}</span></div>
                <div>Proposal: <span class="text-gray-300">${app.proposal_status || 'DRAFT'}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Render active work
 * @param {Array} activeWork - List of active work
 */
function renderActiveWork(activeWork) {
    const activeWorkEl = document.getElementById('active-work-list');
    if (!activeWorkEl) return;
    
    if (!activeWork || activeWork.length === 0) {
        activeWorkEl.innerHTML = '<div class="text-gray-500 text-sm">No active work</div>';
        return;
    }
    
    activeWorkEl.innerHTML = activeWork.map(work => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <p class="font-semibold">${work.job_title}</p>
                    <p class="text-xs text-gray-400">${work.platform}</p>
                </div>
                <span class="tag tag-${getWorkStatusColor(work.state)} text-xs">${work.state}</span>
            </div>
            <div class="flex items-center gap-4 text-xs text-gray-400">
                <div>Started: <span class="text-gray-300">${work.started_at}</span></div>
                <div>Deadline: <span class="text-gray-300">${work.deadline}</span></div>
            </div>
        </div>
    `).join('');
}

/**
 * Show freelancing tab
 * @param {string} tabName - Tab name
 */
export function showFreelancingTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.freelancing-tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.freelancing-tab').forEach(btn => {
        btn.classList.remove('active', 'bg-brand-purple/20', 'text-brand-purple', 'border-brand-purple/50');
        btn.classList.add('bg-dark-800', 'text-gray-400', 'border-gray-700');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`freelancing-tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Add active class to selected button
    const buttons = document.querySelectorAll('.freelancing-tab');
    buttons.forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tabName.replace('-', ' '))) {
            btn.classList.add('active', 'bg-brand-purple/20', 'text-brand-purple', 'border-brand-purple/50');
            btn.classList.remove('bg-dark-800', 'text-gray-400', 'border-gray-700');
        }
    });
    
    // Load data for the tab
    if (tabName === 'platforms') loadPlatforms();
    if (tabName === 'capabilities') loadCapabilities();
    if (tabName === 'jobs') loadJobs();
    if (tabName === 'applications') loadApplications();
    if (tabName === 'active-work') loadActiveWork();
}

/**
 * View job detail
 * @param {string} jobId - Job ID
 */
export async function viewJobDetail(jobId) {
    const job = await loadJobDetail(jobId);
    if (job) {
        renderJobDetail(job);
        const modal = document.getElementById('job-detail-modal');
        if (modal) modal.classList.remove('hidden');
    }
}

/**
 * Close job detail modal
 */
export function closeJobDetailModal() {
    const modal = document.getElementById('job-detail-modal');
    if (modal) modal.classList.add('hidden');
}

/**
 * Render job detail in modal
 * @param {Object} job - Job detail
 */
function renderJobDetail(job) {
    const contentEl = document.getElementById('job-detail-content');
    if (!contentEl) return;
    
    contentEl.innerHTML = `
        <div class="space-y-6">
            <!-- Job Info -->
            <div>
                <h4 class="font-bold text-lg mb-2">${job.title}</h4>
                <div class="flex items-center gap-4 text-sm text-gray-400 mb-4">
                    <span>${job.platform}</span>
                    <span>•</span>
                    <span>${job.client}</span>
                    <span>•</span>
                    <span class="text-brand-purple font-bold">${job.budget}</span>
                </div>
            </div>
            
            <!-- Requirements -->
            <div>
                <h5 class="font-semibold mb-2">Requirements</h5>
                <p class="text-sm text-gray-400">${job.requirements || 'No requirements specified'}</p>
            </div>
            
            <!-- Required Skills -->
            <div>
                <h5 class="font-semibold mb-2">Required Skills</h5>
                <div class="flex flex-wrap gap-2">
                    ${(job.required_skills || []).map(skill => `
                        <span class="tag tag-gray text-xs">${skill}</span>
                    `).join('')}
                </div>
            </div>
            
            <!-- Required Capabilities -->
            <div>
                <h5 class="font-semibold mb-2">Required Capabilities</h5>
                <div class="flex flex-wrap gap-2">
                    ${(job.required_capabilities || []).map(cap => `
                        <span class="tag tag-blue text-xs">${cap}</span>
                    `).join('')}
                </div>
            </div>
            
            <!-- Deliverables -->
            <div>
                <h5 class="font-semibold mb-2">Deliverables</h5>
                <p class="text-sm text-gray-400">${job.deliverables || 'No deliverables specified'}</p>
            </div>
            
            <!-- Deadline -->
            <div>
                <h5 class="font-semibold mb-2">Deadline</h5>
                <p class="text-sm text-gray-400">${job.deadline || 'Not specified'}</p>
            </div>
            
            <!-- Enigma Readiness Assessment -->
            <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
                <h5 class="font-semibold mb-3">Enigma Readiness Assessment</h5>
                <div class="flex items-center justify-between mb-3">
                    <span>Overall Readiness</span>
                    <span class="tag tag-${getReadinessColor(job.readiness_status)} text-xs">${job.readiness_status}</span>
                </div>
                <div class="flex items-center gap-2 mb-3">
                    <span class="text-sm text-gray-400">Match Score:</span>
                    <span class="text-sm font-semibold">${(job.match_score * 100).toFixed(0)}%</span>
                </div>
                
                <!-- Missing Capabilities -->
                ${job.missing_capabilities && job.missing_capabilities.length > 0 ? `
                    <div class="mb-3">
                        <p class="text-sm text-gray-400 mb-1">Missing Capabilities:</p>
                        <div class="flex flex-wrap gap-2">
                            ${job.missing_capabilities.map(cap => `
                                <span class="tag tag-red text-xs">${cap}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Missing Knowledge -->
                ${job.missing_knowledge && job.missing_knowledge.length > 0 ? `
                    <div class="mb-3">
                        <p class="text-sm text-gray-400 mb-1">Missing Knowledge:</p>
                        <div class="flex flex-wrap gap-2">
                            ${job.missing_knowledge.map(know => `
                                <span class="tag tag-yellow text-xs">${know}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Research Required -->
                ${job.requires_research ? `
                    <div class="mb-3">
                        <p class="text-sm text-gray-400 mb-1">Required Research:</p>
                        <p class="text-sm text-gray-300">${job.requires_research}</p>
                        <button onclick="startJobResearch('${job.id}')" class="btn-secondary text-xs py-2 px-4 mt-2">
                            <i class="fas fa-search ml-1"></i>Start Research
                        </button>
                    </div>
                ` : ''}
                
                <!-- Application Blockers -->
                ${job.application_blockers && job.application_blockers.length > 0 ? `
                    <div class="mb-3">
                        <p class="text-sm text-gray-400 mb-1">Application Blockers:</p>
                        <div class="space-y-1">
                            ${job.application_blockers.map(blocker => `
                                <div class="flex items-center gap-2 text-sm">
                                    <i class="fas fa-times text-red-400"></i>
                                    <span class="text-gray-300">${blocker}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <!-- Actions -->
            <div class="flex gap-3">
                ${job.can_apply ? `
                    <button onclick="createApplicationDraft('${job.id}')" class="btn-primary flex-1">
                        <i class="fas fa-paper-plane ml-1"></i>Create Application
                    </button>
                ` : `
                    <button disabled class="btn-secondary flex-1 opacity-50 cursor-not-allowed">
                        <i class="fas fa-lock ml-1"></i>Cannot Apply Yet
                    </button>
                `}
                <button onclick="closeJobDetailModal()" class="btn-secondary flex-1">
                    Close
                </button>
            </div>
        </div>
    `;
}

// Helper functions for color coding
function getStatusColor(status) {
    const colors = {
        'ACTIVE': 'green',
        'INACTIVE': 'gray',
        'LOADING': 'yellow'
    };
    return colors[status] || 'gray';
}

function getConnectionColor(status) {
    const colors = {
        'CONNECTED': 'green',
        'NOT_CONNECTED': 'gray',
        'REQUIRES_SETUP': 'yellow',
        'UNAVAILABLE': 'red'
    };
    return colors[status] || 'gray';
}

function getReadinessColor(status) {
    const colors = {
        'READY': 'green',
        'PARTIALLY_READY': 'yellow',
        'NOT_READY': 'red',
        'REQUIRES_RESEARCH': 'blue'
    };
    return colors[status] || 'gray';
}

function getApplicationStatusColor(status) {
    const colors = {
        'DRAFT': 'gray',
        'READY': 'green',
        'SUBMITTED': 'blue',
        'VIEWED': 'purple',
        'INTERVIEW': 'orange',
        'ACCEPTED': 'green',
        'REJECTED': 'red',
        'WITHDRAWN': 'gray'
    };
    return colors[status] || 'gray';
}

function getWorkStatusColor(status) {
    const colors = {
        'ACCEPTED': 'green',
        'ONBOARDING': 'blue',
        'EXECUTION': 'purple',
        'REVIEW': 'orange',
        'DELIVERY': 'pink',
        'COMPLETED': 'green',
        'REFLECTION': 'gray',
        'LEARNING': 'yellow'
    };
    return colors[status] || 'gray';
}

// Mock data functions for development (will be removed when backend APIs are ready)
// These are clearly isolated and marked as mock data
function getMockFreelancing() {
    return {
        status: 'ACTIVE',
        platforms_connected: 2,
        capabilities_ready: 3,
        overall_readiness: 0.78,
        jobs_discovered: 15,
        applications_total: 5
    };
}

function getMockPlatforms() {
    return [
        {
            id: 'upwork',
            name: 'Upwork',
            connection_status: 'CONNECTED',
            auth_status: 'AUTHENTICATED',
            profile_status: 'COMPLETE',
            application_model: 'Proposal-based',
            credits_available: 10,
            availability: 'AVAILABLE'
        },
        {
            id: 'freelancer',
            name: 'Freelancer',
            connection_status: 'CONNECTED',
            auth_status: 'AUTHENTICATED',
            profile_status: 'COMPLETE',
            application_model: 'Bid-based',
            credits_available: null,
            availability: 'AVAILABLE'
        },
        {
            id: 'fiverr',
            name: 'Fiverr',
            connection_status: 'NOT_CONNECTED',
            auth_status: 'NOT_AUTHENTICATED',
            profile_status: 'NOT_SET_UP',
            application_model: 'Gig-based',
            credits_available: null,
            availability: 'REQUIRES_SETUP'
        }
    ];
}

function getMockCapabilities() {
    return [
        {
            id: 'seo-audit',
            name: 'SEO Audit',
            knowledge_maturity: 'Applied',
            readiness_status: 'READY',
            readiness_score: 0.82,
            evidence_count: 7,
            freshness: 'Fresh',
            status: 'READY'
        },
        {
            id: 'keyword-research',
            name: 'Keyword Research',
            knowledge_maturity: 'Applied',
            readiness_status: 'READY',
            readiness_score: 0.91,
            evidence_count: 5,
            freshness: 'Fresh',
            status: 'READY'
        },
        {
            id: 'content-strategy',
            name: 'Content Strategy',
            knowledge_maturity: 'Supported',
            readiness_status: 'PARTIALLY_READY',
            readiness_score: 0.64,
            evidence_count: 3,
            freshness: 'Aging',
            status: 'READY'
        }
    ];
}

function getMockJobs() {
    return [
        {
            id: 'job-1',
            title: 'SEO Audit for E-commerce Site',
            platform: 'Upwork',
            client: 'Tech Startup Inc',
            budget: '$50–$100',
            readiness_status: 'READY',
            match_score: 0.87,
            required_capabilities: ['SEO Audit', 'Keyword Research']
        },
        {
            id: 'job-2',
            title: 'Facebook Ads Campaign Setup',
            platform: 'Freelancer',
            client: 'Retail Brand LLC',
            budget: '$150–$300',
            readiness_status: 'REQUIRES_RESEARCH',
            match_score: 0.62,
            required_capabilities: ['Ads Management', 'Market Research']
        },
        {
            id: 'job-3',
            title: 'Content Strategy for SaaS',
            platform: 'Upwork',
            client: 'Cloud Solutions',
            budget: '$100–$200',
            readiness_status: 'READY',
            match_score: 0.91,
            required_capabilities: ['Content Strategy', 'SEO Audit']
        }
    ];
}

function getMockApplications() {
    return [
        {
            id: 'app-1',
            job_title: 'SEO Audit for E-commerce Site',
            platform: 'Upwork',
            status: 'SUBMITTED',
            submitted_at: '2024-01-15',
            proposal_status: 'SENT'
        },
        {
            id: 'app-2',
            job_title: 'Content Strategy for SaaS',
            platform: 'Upwork',
            status: 'DRAFT',
            submitted_at: null,
            proposal_status: 'DRAFT'
        }
    ];
}

function getMockActiveWork() {
    return [];
}
