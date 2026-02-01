/**
 * Job/Internship Form Validation
 * Provides real-time client-side validation for job posting forms
 * Similar to event validation with inline error messages
 */

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("jobForm");
    if (!form) return;

    const titleInput = document.getElementById("title");
    const companyInput = document.getElementById("company");
    const descriptionInput = document.getElementById("description");
    const jobTypeInput = document.getElementById("job_type");
    const deadlineInput = document.getElementById("application_deadline");
    const applyLinkInput = document.getElementById("apply_link");
    const contactEmailInput = document.getElementById("contact_email");
    const contactPhoneInput = document.getElementById("contact_phone");
    const submitBtn = document.getElementById("submitBtn");

    const rules = {
        title: {
            check: v => v.trim() !== "" && v.length >= 3 && v.length <= 150,
            msg: "Title must be 3-150 characters long"
        },
        company: {
            check: v => v.trim() !== "" && v.length >= 2 && v.length <= 100,
            msg: "Company name must be 2-100 characters long"
        },
        description: {
            check: v => v.trim() !== "" && v.length >= 20 && v.length <= 5000,
            msg: "Description must be 20-5000 characters long"
        },
        job_type: {
            check: v => v !== "" && ["Job", "Internship", "Both"].includes(v),
            msg: "Please select a valid job type"
        },
        application_deadline: {
            check: v => {
                if (!v) return true; // Optional field
                const d = new Date(v);
                const t = new Date();
                t.setHours(0, 0, 0, 0);
                return d >= t;
            },
            msg: "Application deadline must be today or in the future"
        },
        apply_link: {
            check: v => {
                if (!v) return true; // Optional field
                try {
                    new URL(v);
                    return true;
                } catch {
                    return false;
                }
            },
            msg: "Please enter a valid URL (e.g., https://example.com)"
        },
        contact_email: {
            check: v => {
                if (!v) return true; // Optional field
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(v);
            },
            msg: "Please enter a valid email address"
        },
        contact_phone: {
            check: v => {
                if (!v) return true; // Optional field
                const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
                return phoneRegex.test(v.replace(/\s/g, ''));
            },
            msg: "Please enter a valid phone number (e.g., +1 (555) 123-4567)"
        }
    };

    function feedback(el) {
        return el.parentElement.querySelector(".invalid-feedback");
    }

    function invalid(el, msg) {
        el.classList.add("is-invalid");
        el.classList.remove("is-valid");
        const feedbackEl = feedback(el);
        if (feedbackEl) {
            feedbackEl.textContent = msg;
        }
        toggleBtn();
    }

    function valid(el) {
        el.classList.remove("is-invalid");
        el.classList.add("is-valid");
        const feedbackEl = feedback(el);
        if (feedbackEl) {
            feedbackEl.textContent = "";
        }
        toggleBtn();
    }

    function toggleBtn() {
        // Check current mode
        const currentMode = document.querySelector('input[name="post-mode"]:checked')?.value || 'form';
        const bannerInput = document.getElementById('banner_image');
        const imagePreview = document.getElementById('imagePreview');
        
        if (currentMode === 'banner') {
            // For banner mode, check if a file is selected OR if there's an existing image preview
            const hasFileSelected = bannerInput && bannerInput.files && bannerInput.files.length > 0;
            const hasImagePreview = imagePreview && imagePreview.style.display !== 'none';
            submitBtn.disabled = !(hasFileSelected || hasImagePreview);
        } else {
            // For form mode, require all form fields to be valid
            submitBtn.disabled = !(
                titleInput.classList.contains("is-valid") &&
                companyInput.classList.contains("is-valid") &&
                descriptionInput.classList.contains("is-valid") &&
                jobTypeInput.classList.contains("is-valid") &&
                (deadlineInput.value === "" || deadlineInput.classList.contains("is-valid")) &&
                (applyLinkInput.value === "" || applyLinkInput.classList.contains("is-valid")) &&
                (contactEmailInput.value === "" || contactEmailInput.classList.contains("is-valid")) &&
                (contactPhoneInput.value === "" || contactPhoneInput.classList.contains("is-valid"))
            );
        }
    }

    // Real-time validation listeners
    titleInput.addEventListener("input", () => {
        rules.title.check(titleInput.value)
            ? valid(titleInput)
            : invalid(titleInput, rules.title.msg);
    });

    companyInput.addEventListener("input", () => {
        rules.company.check(companyInput.value)
            ? valid(companyInput)
            : invalid(companyInput, rules.company.msg);
    });

    descriptionInput.addEventListener("input", () => {
        rules.description.check(descriptionInput.value)
            ? valid(descriptionInput)
            : invalid(descriptionInput, rules.description.msg);
    });

    jobTypeInput.addEventListener("change", () => {
        rules.job_type.check(jobTypeInput.value)
            ? valid(jobTypeInput)
            : invalid(jobTypeInput, rules.job_type.msg);
    });

    deadlineInput.addEventListener("change", () => {
        rules.application_deadline.check(deadlineInput.value)
            ? valid(deadlineInput)
            : invalid(deadlineInput, rules.application_deadline.msg);
    });

    applyLinkInput.addEventListener("input", () => {
        rules.apply_link.check(applyLinkInput.value)
            ? valid(applyLinkInput)
            : invalid(applyLinkInput, rules.apply_link.msg);
    });

    contactEmailInput.addEventListener("input", () => {
        rules.contact_email.check(contactEmailInput.value)
            ? valid(contactEmailInput)
            : invalid(contactEmailInput, rules.contact_email.msg);
    });

    contactPhoneInput.addEventListener("input", () => {
        rules.contact_phone.check(contactPhoneInput.value)
            ? valid(contactPhoneInput)
            : invalid(contactPhoneInput, rules.contact_phone.msg);
    });

    form.addEventListener("submit", e => {
        // Check current mode - skip form validation in banner mode
        const currentMode = document.querySelector('input[name="post-mode"]:checked')?.value || 'form';
        if (currentMode === 'banner') {
            // In banner mode, don't validate form fields
            return;
        }

        if (!submitBtn.disabled) return;
        e.preventDefault();
        titleInput.dispatchEvent(new Event("input"));
        companyInput.dispatchEvent(new Event("input"));
        descriptionInput.dispatchEvent(new Event("input"));
        jobTypeInput.dispatchEvent(new Event("change"));
        deadlineInput.dispatchEvent(new Event("change"));
        applyLinkInput.dispatchEvent(new Event("input"));
        contactEmailInput.dispatchEvent(new Event("input"));
        contactPhoneInput.dispatchEvent(new Event("input"));
    });

    // Edit mode auto-validation
    if (titleInput.value) titleInput.dispatchEvent(new Event("input"));
    if (companyInput.value) companyInput.dispatchEvent(new Event("input"));
    if (descriptionInput.value) descriptionInput.dispatchEvent(new Event("input"));
    if (jobTypeInput.value) jobTypeInput.dispatchEvent(new Event("change"));
    if (deadlineInput.value) deadlineInput.dispatchEvent(new Event("change"));
    if (applyLinkInput.value) applyLinkInput.dispatchEvent(new Event("input"));
    if (contactEmailInput.value) contactEmailInput.dispatchEvent(new Event("input"));
    if (contactPhoneInput.value) contactPhoneInput.dispatchEvent(new Event("input"));
});

/**
 * Toggle Job Status (Activate/Deactivate)
 * @param {number} jobId - The ID of the job to toggle
 */
function toggleJobStatus(jobId) {
    if (!jobId) {
        alert('Invalid job ID');
        return;
    }

    fetch(`/placement/jobs/${jobId}/toggle-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.message || 'An unknown error occurred'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred: ' + error.message);
        });
}
