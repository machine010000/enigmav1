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
import { USE_MOCK_DATA, IS_PRODUCTION } from './config.js';

let freelancingData = null;
let isUsingMockData = false;

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
        if (IS_PRODUCTION || !USE_MOCK_DATA) {
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
 * Load marketplace account economics from backend
 * @param {string} platform - Platform name (upwork, freelancer, mostaql, fiverr)
 * @returns {Promise<Object>} Marketplace account economics
 */
export async function loadMarketplaceAccountEconomics(platform) {
    try {
        // Real API endpoint
        const economics = await apiCall(`/api/freelancing/platforms/${platform}/economics`);
        renderMarketplaceAccountEconomics(economics);
        return economics;
    } catch (error) {
        console.error('Failed to load marketplace economics:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load marketplace economics. Backend may be unavailable.', 'error');
            return null;
        }
        
        const mockEconomics = getMockMarketplaceEconomics(platform);
        renderMarketplaceAccountEconomics(mockEconomics);
        return mockEconomics;
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
 * Assess opportunity against ENIGMA profile
 * @param {Object} opportunity - Opportunity data
 * @returns {Promise<Object>} Assessment result
 */
export async function assessOpportunity(opportunity) {
    try {
        const assessment = await apiCall('/api/freelancing/opportunities/assess', {
            method: 'POST',
            body: opportunity
        });
        return assessment;
    } catch (error) {
        console.error('Failed to assess opportunity:', error);
        showToast('Failed to assess opportunity. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Generate development plan for opportunity
 * @param {Object} opportunity - Opportunity data
 * @param {string} targetId - Optional target ID
 * @returns {Promise<Object>} Development plan
 */
export async function generateDevelopmentPlan(opportunity, targetId = null) {
    try {
        const body = {
            ...opportunity,
            target_id: targetId
        };
        const plan = await apiCall('/api/freelancing/opportunities/development-plan', {
            method: 'POST',
            body
        });
        return plan;
    } catch (error) {
        console.error('Failed to generate development plan:', error);
        showToast('Failed to generate development plan. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Execute development plan action
 * @param {Object} opportunity - Opportunity data
 * @param {string} planId - Plan ID
 * @param {string} targetId - Optional target ID
 * @returns {Promise<Object>} Execution result
 */
export async function executeDevelopmentAction(opportunity, planId, targetId = null) {
    try {
        const body = {
            ...opportunity,
            plan_id: planId,
            target_id: targetId
        };
        const result = await apiCall('/api/freelancing/opportunities/development-plan/execute', {
            method: 'POST',
            body
        });
        showToast('Development action executed', 'success');
        return result;
    } catch (error) {
        console.error('Failed to execute development action:', error);
        showToast('Failed to execute development action. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Build application package for opportunity
 * @param {Object} opportunity - Opportunity data
 * @param {string} opportunityId - Optional opportunity ID
 * @param {string} targetId - Optional target ID
 * @returns {Promise<Object>} Application package
 */
export async function buildApplicationPackage(opportunity, opportunityId = null, targetId = null) {
    try {
        const body = {
            ...opportunity,
            opportunity_id: opportunityId,
            target_id: targetId
        };
        const package = await apiCall('/api/freelancing/opportunities/application-package', {
            method: 'POST',
            body
        });
        showToast('Application package created', 'success');
        return package;
    } catch (error) {
        console.error('Failed to build application package:', error);
        showToast('Failed to build application package. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Load application package by ID
 * @param {string} applicationId - Application ID
 * @returns {Promise<Object>} Application package
 */
export async function loadApplicationPackage(applicationId) {
    try {
        const package = await apiCall(`/api/freelancing/application-packages/${applicationId}`);
        return package;
    } catch (error) {
        console.error('Failed to load application package:', error);
        showToast('Failed to load application package. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * List application packages
 * @param {number} limit - Limit
 * @param {number} offset - Offset
 * @returns {Promise<Array>} List of packages
 */
export async function listApplicationPackages(limit = 20, offset = 0) {
    try {
        const packages = await apiCall(`/api/freelancing/application-packages?limit=${limit}&offset=${offset}`);
        return packages;
    } catch (error) {
        console.error('Failed to list application packages:', error);
        showToast('Failed to list application packages. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Review application package (approve/reject)
 * @param {string} applicationId - Application ID
 * @param {boolean} approved - Approval decision
 * @returns {Promise<Object>} Reviewed package
 */
export async function reviewApplicationPackage(applicationId, approved) {
    try {
        const package = await apiCall(`/api/freelancing/application-packages/${applicationId}/review`, {
            method: 'POST',
            body: { approved }
        });
        showToast(approved ? 'Package approved' : 'Package rejected', approved ? 'success' : 'info');
        return package;
    } catch (error) {
        console.error('Failed to review application package:', error);
        showToast('Failed to review application package. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Create submission intent for approved package
 * @param {string} applicationId - Application ID
 * @returns {Promise<Object>} Submission intent
 */
export async function createSubmissionIntent(applicationId) {
    try {
        const intent = await apiCall(`/api/freelancing/application-packages/${applicationId}/submission-intent`, {
            method: 'POST'
        });
        showToast('Submission intent created', 'success');
        return intent;
    } catch (error) {
        console.error('Failed to create submission intent:', error);
        showToast('Failed to create submission intent. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Load submission intent by ID
 * @param {string} submissionId - Submission ID
 * @returns {Promise<Object>} Submission intent
 */
export async function loadSubmissionIntent(submissionId) {
    try {
        const intent = await apiCall(`/api/freelancing/submission-intents/${submissionId}`);
        return intent;
    } catch (error) {
        console.error('Failed to load submission intent:', error);
        showToast('Failed to load submission intent. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * List submission intents
 * @param {number} limit - Limit
 * @param {number} offset - Offset
 * @returns {Promise<Object>} List of intents
 */
export async function listSubmissionIntents(limit = 20, offset = 0) {
    try {
        const intents = await apiCall(`/api/freelancing/submission-intents?limit=${limit}&offset=${offset}`);
        return intents;
    } catch (error) {
        console.error('Failed to list submission intents:', error);
        showToast('Failed to list submission intents. Backend may be unavailable.', 'error');
        return null;
    }
}

/**
 * Cancel submission intent
 * @param {string} submissionId - Submission ID
 * @param {string} note - Optional cancellation note
 * @returns {Promise<Object>} Cancelled intent
 */
export async function cancelSubmissionIntent(submissionId, note = null) {
    try {
        const intent = await apiCall(`/api/freelancing/submission-intents/${submissionId}/cancel`, {
            method: 'POST',
            body: { note }
        });
        showToast('Submission intent cancelled', 'success');
        return intent;
    } catch (error) {
        console.error('Failed to cancel submission intent:', error);
        showToast('Failed to cancel submission intent. Backend may be unavailable.', 'error');
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
            <button onclick="loadMarketplaceAccountEconomics('${platform.id}')" class="btn-secondary text-xs py-1 px-3 mt-3">
                <i class="fas fa-chart-line ml-1"></i>View Economics
            </button>
        </div>
    `).join('');
}

/**
 * Render marketplace account economics
 * @param {Object} economics - Marketplace account economics
 */
function renderMarketplaceAccountEconomics(economics) {
    const economicsEl = document.getElementById('marketplace-economics-display');
    if (!economicsEl) return;
    
    if (!economics) {
        economicsEl.innerHTML = '<div class="text-gray-500 text-sm">No economics data available</div>';
        return;
    }
    
    const balance = economics.account_balance || {};
    const cost = economics.application_cost || {};
    const assessment = economics.assessment || {};
    
    economicsEl.innerHTML = `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-bold">${economics.platform.toUpperCase()} Account</h4>
                <span class="tag tag-${getDecisionColor(economics.decision)} text-xs">${economics.decision.replace('_', ' ')}</span>
            </div>
            
            <!-- Account Balance -->
            <div class="mb-4">
                <p class="text-sm text-gray-400 mb-2">Account Balance</p>
                <div class="flex items-center justify-between p-3 rounded bg-dark-900">
                    <div>
                        <p class="text-2xl font-bold text-brand-purple">${balance.available || 0}</p>
                        <p class="text-xs text-gray-400">${balance.unit || 'N/A'} available</p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm text-gray-300">${balance.total || 0} total</p>
                        <p class="text-xs text-gray-400">${balance.currency || 'USD'}</p>
                    </div>
                </div>
            </div>
            
            <!-- This Job Cost -->
            <div class="mb-4">
                <p class="text-sm text-gray-400 mb-2">This Job</p>
                <div class="flex items-center justify-between p-3 rounded bg-dark-900">
                    <div>
                        <p class="text-2xl font-bold ${cost.is_free ? 'text-green-400' : 'text-brand-purple'}">${cost.amount || 0}</p>
                        <p class="text-xs text-gray-400">${cost.unit || 'N/A'} required</p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm text-gray-300">${cost.monetary_value ? '$' + cost.monetary_value.toFixed(2) : 'Free'}</p>
                        <p class="text-xs text-gray-400">${cost.currency || 'USD'}</p>
                    </div>
                </div>
            </div>
            
            <!-- After Application -->
            <div class="mb-4">
                <p class="text-sm text-gray-400 mb-2">After Application</p>
                <div class="flex items-center justify-between p-3 rounded bg-dark-900">
                    <div>
                        <p class="text-2xl font-bold text-brand-blue">${economics.remaining_balance_after_apply || balance.available || 0}</p>
                        <p class="text-xs text-gray-400">remaining balance</p>
                    </div>
                </div>
            </div>
            
            <!-- Economic Assessment -->
            ${assessment.economic_value !== null && assessment.economic_value !== undefined ? `
                <div class="mb-4">
                    <p class="text-sm text-gray-400 mb-2">Economic Assessment</p>
                    <div class="p-3 rounded bg-dark-900">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Expected Revenue:</span>
                            <span class="text-sm font-semibold text-gray-300">${assessment.expected_revenue ? '$' + assessment.expected_revenue.toFixed(2) : 'N/A'}</span>
                        </div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Win Probability:</span>
                            <span class="text-sm font-semibold text-gray-300">${assessment.win_probability ? (assessment.win_probability * 100).toFixed(0) + '%' : 'N/A'}</span>
                        </div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Economic Value:</span>
                            <span class="text-sm font-semibold ${assessment.economic_value > 0 ? 'text-green-400' : 'text-red-400'}">${assessment.economic_value > 0 ? '+' : ''}$${assessment.economic_value.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <!-- Decision Reason -->
            <div class="p-3 rounded bg-dark-900">
                <p class="text-sm text-gray-400 mb-1">Decision:</p>
                <p class="text-sm text-gray-300">${economics.decision_reason || 'No reason provided'}</p>
            </div>
            
            <!-- Status Indicators -->
            <div class="flex gap-2 mt-4">
                <span class="tag ${economics.can_afford ? 'tag-green' : 'tag-red'} text-xs">
                    ${economics.can_afford ? '✓ Can Afford' : '✗ Cannot Afford'}
                </span>
                <span class="tag ${economics.has_quota ? 'tag-green' : 'tag-red'} text-xs">
                    ${economics.has_quota ? '✓ Has Quota' : '✗ No Quota'}
                </span>
            </div>
        </div>
    `;
}

function getDecisionColor(decision) {
    const colors = {
        'apply': 'green',
        'dont_apply': 'red',
        'insufficient_balance': 'red',
        'insufficient_quota': 'red',
        'requires_money': 'red',
        'requires_account_setup': 'yellow',
        'not_applicable': 'gray',
        'wait': 'yellow',
        'need_information': 'orange'
    };
    return colors[decision] || 'gray';
}

/**
 * Load marketplace economics dashboard
 * @returns {Promise<Array>} List of platform economics
 */
export async function loadMarketplaceEconomicsDashboard() {
    try {
        // Real API endpoint
        const economics = await apiCall('/api/freelancing/platforms/economics');
        renderMarketplaceEconomicsDashboard(economics);
        return economics;
    } catch (error) {
        console.error('Failed to load marketplace economics dashboard:', error);
        
        if (!USE_MOCK_DATA) {
            showToast('Failed to load marketplace economics. Backend may be unavailable.', 'error');
            return null;
        }
        
        const mockEconomics = getMockMarketplaceEconomicsDashboard();
        renderMarketplaceEconomicsDashboard(mockEconomics);
        return mockEconomics;
    }
}

/**
 * Render marketplace economics dashboard
 * @param {Array} economics - List of platform economics
 */
function renderMarketplaceEconomicsDashboard(economics) {
    const dashboardEl = document.getElementById('marketplace-economics-dashboard');
    if (!dashboardEl) return;
    
    if (!economics || economics.length === 0) {
        dashboardEl.innerHTML = '<div class="text-gray-500 text-sm">No economics data available</div>';
        return;
    }
    
    dashboardEl.innerHTML = `
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr class="border-b border-gray-700">
                        <th class="text-left py-2 px-3 text-gray-400">Platform</th>
                        <th class="text-left py-2 px-3 text-gray-400">Application Model</th>
                        <th class="text-left py-2 px-3 text-gray-400">Cost</th>
                        <th class="text-left py-2 px-3 text-gray-400">Status</th>
                        <th class="text-left py-2 px-3 text-gray-400">Last Verified</th>
                    </tr>
                </thead>
                <tbody>
                    ${economics.map(econ => `
                        <tr class="border-b border-gray-800">
                            <td class="py-2 px-3 font-semibold">${econ.platform}</td>
                            <td class="py-2 px-3">
                                <span class="tag tag-${getApplicationModelColor(econ.application_model)} text-xs">
                                    ${econ.application_model}
                                </span>
                            </td>
                            <td class="py-2 px-3 text-gray-400">${econ.cost_display || 'N/A'}</td>
                            <td class="py-2 px-3">
                                <span class="tag tag-${getVerificationStatusColor(econ.verification_status)} text-xs">
                                    ${econ.verification_status}
                                </span>
                            </td>
                            <td class="py-2 px-3 text-gray-400 text-xs">${econ.last_verified || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function getApplicationModelColor(model) {
    const colors = {
        'credit_based': 'blue',
        'fee_based': 'purple',
        'free': 'green',
        'mixed': 'yellow',
        'no_direct_application': 'gray',
        'unknown': 'orange'
    };
    return colors[model] || 'gray';
}

function getVerificationStatusColor(status) {
    const colors = {
        'verified': 'green',
        'unknown': 'orange',
        'not_applicable': 'gray'
    };
    return colors[status] || 'gray';
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
    if (tabName === 'assessment') {
        // Assessment form is static, no data load needed
    }
    if (tabName === 'packages') loadPackages();
    if (tabName === 'intents') loadIntents();
    if (tabName === 'jobs') loadJobs();
    if (tabName === 'applications') loadApplications();
    if (tabName === 'active-work') loadActiveWork();
}

/**
 * Run opportunity assessment
 */
export async function runAssessment() {
    const title = document.getElementById('assessment-title').value;
    const description = document.getElementById('assessment-description').value;
    const platform = document.getElementById('assessment-platform').value;
    const externalId = document.getElementById('assessment-external-id').value;
    const skillsStr = document.getElementById('assessment-skills').value;
    const requiredSkills = skillsStr.split(',').map(s => s.trim()).filter(s => s);

    if (!title || !description) {
        showToast('Please enter title and description', 'error');
        return;
    }

    const opportunity = {
        title,
        description,
        platform,
        external_id: externalId || null,
        required_skills: requiredSkills
    };

    const assessment = await assessOpportunity(opportunity);
    if (assessment) {
        renderAssessmentResult(assessment);
    }
}

/**
 * Render assessment result
 * @param {Object} assessment - Assessment result
 */
function renderAssessmentResult(assessment) {
    const resultEl = document.getElementById('assessment-result');
    const contentEl = document.getElementById('assessment-result-content');

    if (!resultEl || !contentEl) return;

    resultEl.classList.remove('hidden');

    const decision = assessment.decision || 'UNKNOWN';
    const readiness = assessment.readiness || 'UNKNOWN';
    const decisionColor = decision === 'READY_TO_APPLY' ? 'green' : decision === 'LEARN_FIRST' ? 'yellow' : 'red';

    contentEl.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <span class="font-semibold">Decision</span>
                <span class="tag tag-${decisionColor}">${decision}</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-400">Readiness</span>
                <span class="text-sm">${readiness}</span>
            </div>
            ${assessment.missing_capabilities && assessment.missing_capabilities.length > 0 ? `
                <div>
                    <p class="text-sm text-gray-400 mb-2">Missing Capabilities</p>
                    <div class="flex flex-wrap gap-2">
                        ${assessment.missing_capabilities.map(cap => `<span class="tag tag-red text-xs">${cap}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            ${assessment.blocking_capability ? `
                <div>
                    <p class="text-sm text-gray-400 mb-2">Blocking Capability</p>
                    <span class="tag tag-red text-xs">${assessment.blocking_capability}</span>
                </div>
            ` : ''}
            ${decision === 'LEARN_FIRST' ? `
                <button onclick="generateDevelopmentPlanFromAssessment()" class="btn-secondary text-xs py-2 px-4 mt-2">
                    <i class="fas fa-graduation-cap ml-1"></i>Generate Development Plan
                </button>
            ` : ''}
            ${decision === 'READY_TO_APPLY' ? `
                <button onclick="buildPackageFromAssessment()" class="btn-primary text-xs py-2 px-4 mt-2">
                    <i class="fas fa-box ml-1"></i>Build Application Package
                </button>
            ` : ''}
        </div>
    `;
}

/**
 * Generate development plan from current assessment
 */
export async function generateDevelopmentPlanFromAssessment() {
    const title = document.getElementById('assessment-title').value;
    const description = document.getElementById('assessment-description').value;
    const platform = document.getElementById('assessment-platform').value;
    const externalId = document.getElementById('assessment-external-id').value;
    const skillsStr = document.getElementById('assessment-skills').value;
    const requiredSkills = skillsStr.split(',').map(s => s.trim()).filter(s => s);

    const opportunity = {
        title,
        description,
        platform,
        external_id: externalId || null,
        required_skills: requiredSkills
    };

    const plan = await generateDevelopmentPlan(opportunity);
    if (plan) {
        renderDevelopmentPlan(plan);
    }
}

/**
 * Render development plan
 * @param {Object} plan - Development plan
 */
function renderDevelopmentPlan(plan) {
    const contentEl = document.getElementById('assessment-result-content');
    if (!contentEl) return;

    const actions = plan.development_actions || [];

    contentEl.innerHTML = `
        <div class="space-y-4">
            <h4 class="font-semibold">Development Plan</h4>
            <p class="text-sm text-gray-400">Assessment: ${plan.assessment_readiness}</p>
            <p class="text-sm text-gray-400">Decision: ${plan.decision}</p>
            <div class="space-y-3 mt-4">
                ${actions.map(action => `
                    <div class="p-3 rounded-lg bg-dark-900 border border-gray-700">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-semibold text-sm">${action.capability_id}</span>
                            <span class="tag tag-blue text-xs">${action.training_mode}</span>
                        </div>
                        <p class="text-xs text-gray-400 mb-2">${action.action}</p>
                        <button onclick="executeDevelopmentActionFromPlan('${action.plan_id}')" class="btn-secondary text-xs py-1 px-3">
                            <i class="fas fa-play ml-1"></i>Execute
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Execute development action from plan
 */
export async function executeDevelopmentActionFromPlan(planId) {
    const title = document.getElementById('assessment-title').value;
    const description = document.getElementById('assessment-description').value;
    const platform = document.getElementById('assessment-platform').value;
    const externalId = document.getElementById('assessment-external-id').value;
    const skillsStr = document.getElementById('assessment-skills').value;
    const requiredSkills = skillsStr.split(',').map(s => s.trim()).filter(s => s);

    const opportunity = {
        title,
        description,
        platform,
        external_id: externalId || null,
        required_skills: requiredSkills
    };

    const result = await executeDevelopmentAction(opportunity, planId);
    if (result) {
        showToast('Development action executed successfully', 'success');
        // Refresh profile to see updated capability status
        const { loadProfile } = await import('./profile.js');
        await loadProfile();
    }
}

/**
 * Build application package from current assessment
 */
export async function buildPackageFromAssessment() {
    const title = document.getElementById('assessment-title').value;
    const description = document.getElementById('assessment-description').value;
    const platform = document.getElementById('assessment-platform').value;
    const externalId = document.getElementById('assessment-external-id').value;
    const skillsStr = document.getElementById('assessment-skills').value;
    const requiredSkills = skillsStr.split(',').map(s => s.trim()).filter(s => s);

    const opportunity = {
        title,
        description,
        platform,
        external_id: externalId || null,
        required_skills: requiredSkills
    };

    const pkg = await buildApplicationPackage(opportunity, externalId);
    if (pkg) {
        showToast('Application package created successfully', 'success');
        showFreelancingTab('packages');
    }
}

/**
 * Load application packages
 */
export async function loadPackages() {
    const packages = await listApplicationPackages();
    if (packages) {
        renderPackages(packages);
    }
}

/**
 * Render application packages
 * @param {Object} data - Packages data
 */
function renderPackages(data) {
    const packagesEl = document.getElementById('packages-list');
    if (!packagesEl) return;

    const packages = data.packages || [];

    if (packages.length === 0) {
        packagesEl.innerHTML = '<div class="text-gray-500 text-sm">No application packages</div>';
        return;
    }

    packagesEl.innerHTML = packages.map(pkg => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <p class="font-semibold">${pkg.opportunity_title}</p>
                    <p class="text-xs text-gray-400">${pkg.platform} • ${pkg.application_id}</p>
                </div>
                <span class="tag tag-${getPackageStateColor(pkg.state)} text-xs">${pkg.state}</span>
            </div>
            <div class="flex items-center gap-4 text-xs text-gray-400 mb-3">
                <div>Created: <span class="text-gray-300">${new Date(pkg.created_at).toLocaleString()}</span></div>
                <div>Readiness: <span class="text-gray-300">${pkg.readiness_decision}</span></div>
            </div>
            ${pkg.state === 'READY_FOR_HUMAN_APPROVAL' ? `
                <div class="flex gap-2">
                    <button onclick="reviewPackage('${pkg.application_id}', true)" class="btn-primary text-xs py-2 px-4 flex-1">
                        <i class="fas fa-check ml-1"></i>Approve
                    </button>
                    <button onclick="reviewPackage('${pkg.application_id}', false)" class="btn-secondary text-xs py-2 px-4 flex-1">
                        <i class="fas fa-times ml-1"></i>Reject
                    </button>
                </div>
            ` : ''}
            ${pkg.state === 'APPROVED' ? `
                <button onclick="createIntentFromPackage('${pkg.application_id}')" class="btn-primary text-xs py-2 px-4 w-full">
                    <i class="fas fa-paper-plane ml-1"></i>Create Submission Intent
                </button>
            ` : ''}
        </div>
    `).join('');
}

/**
 * Get package state color
 */
function getPackageStateColor(state) {
    const colors = {
        'READY_FOR_HUMAN_APPROVAL': 'yellow',
        'APPROVED': 'green',
        'REJECTED': 'red'
    };
    return colors[state] || 'gray';
}

/**
 * Review application package
 */
export async function reviewPackage(applicationId, approved) {
    const pkg = await reviewApplicationPackage(applicationId, approved);
    if (pkg) {
        loadPackages();
    }
}

/**
 * Create submission intent from package
 */
export async function createIntentFromPackage(applicationId) {
    const intent = await createSubmissionIntent(applicationId);
    if (intent) {
        showToast('Submission intent created successfully', 'success');
        showFreelancingTab('intents');
    }
}

/**
 * Load submission intents
 */
export async function loadIntents() {
    const intents = await listSubmissionIntents();
    if (intents) {
        renderIntents(intents);
    }
}

/**
 * Render submission intents
 * @param {Object} data - Intents data
 */
function renderIntents(data) {
    const intentsEl = document.getElementById('intents-list');
    if (!intentsEl) return;

    const intents = data.intents || [];

    if (intents.length === 0) {
        intentsEl.innerHTML = '<div class="text-gray-500 text-sm">No submission intents</div>';
        return;
    }

    intentsEl.innerHTML = intents.map(intent => `
        <div class="p-4 rounded-lg bg-dark-800 border border-gray-700">
            <div class="flex items-center justify-between mb-3">
                <div>
                    <p class="font-semibold">${intent.opportunity_title}</p>
                    <p class="text-xs text-gray-400">${intent.platform} • ${intent.submission_id}</p>
                </div>
                <span class="tag tag-${getIntentStateColor(intent.state)} text-xs">${intent.state}</span>
            </div>
            <div class="flex items-center gap-4 text-xs text-gray-400 mb-3">
                <div>Created: <span class="text-gray-300">${new Date(intent.created_at).toLocaleString()}</span></div>
                <div>External: <span class="text-gray-300">${intent.external_submission_attempted ? 'Yes' : 'No'}</span></div>
            </div>
            ${intent.state === 'PENDING_EXTERNAL_SUBMISSION' ? `
                <button onclick="cancelIntent('${intent.submission_id}')" class="btn-secondary text-xs py-2 px-4 w-full">
                    <i class="fas fa-times ml-1"></i>Cancel Intent
                </button>
            ` : ''}
        </div>
    `).join('');
}

/**
 * Get intent state color
 */
function getIntentStateColor(state) {
    const colors = {
        'PENDING_EXTERNAL_SUBMISSION': 'blue',
        'CANCELLED': 'gray'
    };
    return colors[state] || 'gray';
}

/**
 * Cancel submission intent
 */
export async function cancelIntent(submissionId) {
    const note = prompt('Enter cancellation note (optional):');
    const intent = await cancelSubmissionIntent(submissionId, note);
    if (intent) {
        loadIntents();
    }
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
        }
    ];
}

function getMockMarketplaceEconomics(platform) {
    const platformData = {
        'upwork': {
            platform: 'upwork',
            decision: 'apply',
            decision_reason: 'Positive economic value',
            can_afford: true,
            has_quota: true,
            meets_wallet_requirements: true,
            account_balance: {
                unit: 'connects',
                available: 42,
                total: 80,
                currency: 'USD',
                monetary_value: 6.30
            },
            application_cost: {
                unit: 'connects',
                amount: 18,
                currency: 'USD',
                monetary_value: 2.70,
                is_free: false
            },
            remaining_balance_after_apply: 24,
            assessment: {
                expected_revenue: 500,
                win_probability: 0.35,
                execution_readiness: 0.85,
                evidence_strength: 0.72,
                economic_value: 172.30
            }
        },
        'freelancer': {
            platform: 'freelancer',
            decision: 'apply',
            decision_reason: 'Positive economic value',
            can_afford: true,
            has_quota: true,
            meets_wallet_requirements: true,
            account_balance: {
                unit: 'bids',
                available: 25,
                total: 50,
                currency: 'USD',
                monetary_value: 2.50
            },
            application_cost: {
                unit: 'bids',
                amount: 1,
                currency: 'USD',
                monetary_value: 0.10,
                is_free: false
            },
            remaining_balance_after_apply: 24,
            assessment: {
                expected_revenue: 300,
                win_probability: 0.40,
                execution_readiness: 0.80,
                evidence_strength: 0.68,
                economic_value: 119.90
            }
        },
        'mostaql': {
            platform: 'mostaql',
            decision: 'insufficient_quota',
            decision_reason: 'Offer quota exhausted',
            can_afford: true,
            has_quota: false,
            meets_wallet_requirements: true,
            account_balance: {
                unit: 'offers',
                available: 0,
                total: 20,
                currency: 'USD',
                monetary_value: 0.00
            },
            application_cost: {
                unit: 'offers',
                amount: 1,
                currency: 'USD',
                monetary_value: 0.15,
                is_free: false
            },
            remaining_balance_after_apply: 0,
            assessment: {
                expected_revenue: 200,
                win_probability: 0.30,
                execution_readiness: 0.75,
                evidence_strength: 0.60,
                economic_value: 59.85
            }
        },
        'fiverr': {
            platform: 'fiverr',
            decision: 'apply',
            decision_reason: 'Positive economic value (gig economy)',
            can_afford: true,
            has_quota: true,
            meets_wallet_requirements: true,
            account_balance: {
                unit: 'none',
                available: 150.00,
                total: 150.00,
                currency: 'USD',
                monetary_value: 150.00
            },
            application_cost: {
                unit: 'none',
                amount: 0,
                currency: 'USD',
                monetary_value: 0.00,
                is_free: true
            },
            remaining_balance_after_apply: 150.00,
            assessment: {
                expected_revenue: 100,
                win_probability: 0.50,
                execution_readiness: 0.90,
                evidence_strength: 0.85,
                economic_value: 50.00
            }
        }
    };
    
    return platformData[platform] || platformData['upwork'];
}

function getMockActiveWork() {
    return [];
}
