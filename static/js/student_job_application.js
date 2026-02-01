/**
 * Job Application Module
 * Handles job/internship application functionality
 */

class JobApplicationManager {
    constructor() {
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.loadSavedApplications();
    }

    attachEventListeners() {
        // Application form submission
        const applicationForm = document.getElementById('applicationForm');
        if (applicationForm) {
            applicationForm.addEventListener('submit', (e) => this.handleApplicationSubmit(e));
        }

        // Apply button in modals
        const applyButtons = document.querySelectorAll('[data-apply-job]');
        applyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.confirmApplication(e, btn.dataset.applyJob));
        });

        // Withdraw application (if exists)
        const withdrawButtons = document.querySelectorAll('[data-withdraw-application]');
        withdrawButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.withdrawApplication(e, btn.dataset.withdrawApplication));
        });
    }

    /**
     * Validate application form
     */
    validateApplicationForm(form) {
        const confirmCheck = form.querySelector('#confirmCheck');
        
        if (!confirmCheck || !confirmCheck.checked) {
            this.showNotification('error', 'Please confirm that your profile information is accurate');
            return false;
        }
        
        return true;
    }

    /**
     * Handle application form submission
     */
    handleApplicationSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        if (!this.validateApplicationForm(form)) {
            return;
        }

        const jobId = form.dataset.jobId;
        if (!jobId) {
            this.showNotification('error', 'Job ID not found');
            return;
        }

        this.submitApplication(jobId, form);
    }

    /**
     * Submit application via AJAX
     */
    submitApplication(jobId, form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        fetch(`/student/jobs/${jobId}/apply`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Application failed');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification('success', data.message);
                
                // Close modal and refresh
                const modal = form.closest('.modal');
                if (modal) {
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    if (bootstrapModal) bootstrapModal.hide();
                }
                
                // Refresh page after 1.5 seconds
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                this.showNotification('error', data.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Application Error:', error);
            this.showNotification('error', error.message || 'An error occurred while submitting your application');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
    }

    /**
     * Confirm application before submission
     */
    confirmApplication(e, jobId) {
        e.preventDefault();
        
        const confirmed = confirm('Are you sure you want to apply for this position? Your profile information will be shared with the employer.');
        
        if (confirmed) {
            this.submitApplication(jobId);
        }
    }

    /**
     * Withdraw application
     */
    withdrawApplication(e, applicationId) {
        e.preventDefault();
        
        if (!confirm('Are you sure you want to withdraw your application? This action cannot be undone.')) {
            return;
        }

        const withdrawBtn = e.target;
        const originalText = withdrawBtn.innerHTML;
        
        withdrawBtn.disabled = true;
        withdrawBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Withdrawing...';

        fetch(`/student/applications/${applicationId}/withdraw`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Withdrawal failed');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showNotification('success', 'Application withdrawn successfully');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                this.showNotification('error', data.message);
                withdrawBtn.disabled = false;
                withdrawBtn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Withdrawal Error:', error);
            this.showNotification('error', error.message || 'An error occurred');
            withdrawBtn.disabled = false;
            withdrawBtn.innerHTML = originalText;
        });
    }

    /**
     * Show notification using toastr or fallback to alert
     */
    showNotification(type, message) {
        if (typeof toastr !== 'undefined') {
            if (type === 'success') {
                toastr.success(message);
            } else if (type === 'error') {
                toastr.error(message);
            } else if (type === 'info') {
                toastr.info(message);
            } else if (type === 'warning') {
                toastr.warning(message);
            }
        } else {
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Load saved applications from localStorage (optional feature)
     */
    loadSavedApplications() {
        try {
            const saved = localStorage.getItem('savedApplications');
            if (saved) {
                const applications = JSON.parse(saved);
                console.log('Saved applications:', applications);
            }
        } catch (e) {
            console.log('No saved applications found');
        }
    }

    /**
     * Save application draft to localStorage (optional feature)
     */
    saveApplicationDraft(jobId, formData) {
        try {
            const saved = JSON.parse(localStorage.getItem('savedApplications')) || {};
            saved[jobId] = {
                data: formData,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('savedApplications', JSON.stringify(saved));
        } catch (e) {
            console.log('Could not save draft');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.jobApplicationManager = new JobApplicationManager();
});

/**
 * Utility function to check if student has already applied
 */
function hasApplied(jobId) {
    const applicationCard = document.querySelector(`[data-job-id="${jobId}"]`);
    return applicationCard && applicationCard.classList.contains('already-applied');
}

/**
 * Format date helper
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Check application deadline
 */
function isDeadlinePassed(deadlineDate) {
    if (!deadlineDate) return false;
    const deadline = new Date(deadlineDate);
    return deadline < new Date();
}

/**
 * Format remaining time until deadline
 */
function getTimeUntilDeadline(deadlineDate) {
    if (!deadlineDate) return null;
    
    const deadline = new Date(deadlineDate);
    const now = new Date();
    const diff = deadline - now;

    if (diff <= 0) {
        return 'Deadline passed';
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (days > 0) {
        return `${days} day${days > 1 ? 's' : ''} left`;
    } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''} left`;
    } else {
        return 'Less than 1 hour left';
    }
}

/**
 * Filter jobs by criteria
 */
function filterJobs(criteria) {
    const jobCards = document.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        let match = true;

        // Check job type filter
        if (criteria.jobType && !card.dataset.jobType?.includes(criteria.jobType)) {
            match = false;
        }

        // Check location filter
        if (criteria.location && !card.dataset.location?.toLowerCase().includes(criteria.location.toLowerCase())) {
            match = false;
        }

        // Display based on filter result
        card.style.display = match ? 'block' : 'none';
    });
}

/**
 * Sort jobs by criteria
 */
function sortJobs(sortBy) {
    const jobsContainer = document.querySelector('.jobs-container');
    if (!jobsContainer) return;

    const cards = Array.from(document.querySelectorAll('.job-card'));
    
    cards.sort((a, b) => {
        switch(sortBy) {
            case 'newest':
                return new Date(b.dataset.posted) - new Date(a.dataset.posted);
            case 'oldest':
                return new Date(a.dataset.posted) - new Date(b.dataset.posted);
            case 'salary-high':
                return (parseInt(b.dataset.salary) || 0) - (parseInt(a.dataset.salary) || 0);
            case 'salary-low':
                return (parseInt(a.dataset.salary) || 0) - (parseInt(b.dataset.salary) || 0);
            default:
                return 0;
        }
    });

    // Re-append sorted cards
    cards.forEach(card => jobsContainer.appendChild(card));
}
