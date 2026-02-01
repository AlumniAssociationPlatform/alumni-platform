// Wait for toastr to be loaded
function initToastr() {
    if (typeof toastr === 'undefined') {
        setTimeout(initToastr, 100);
        return;
    }

    // Toastr Notification Configuration
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "slideDown",
        "hideMethod": "slideUp"
    };
}

// Initialize toastr when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToastr);
} else {
    initToastr();
}

/**
 * Show a success notification
 * @param {string} message - The notification message
 * @param {string} title - Optional title for the notification
 */
function showSuccessNotification(message, title = "Success") {
    if (typeof toastr !== 'undefined') {
        toastr.success(message, title);
    } else {
        console.warn('Toastr library not loaded');
        alert(message);
    }
}

/**
 * Show an error notification
 * @param {string} message - The notification message
 * @param {string} title - Optional title for the notification
 */
function showErrorNotification(message, title = "Error") {
    if (typeof toastr !== 'undefined') {
        toastr.error(message, title);
    } else {
        console.error(message);
        alert(message);
    }
}

/**
 * Show an info notification
 * @param {string} message - The notification message
 * @param {string} title - Optional title for the notification
 */
function showInfoNotification(message, title = "Info") {
    if (typeof toastr !== 'undefined') {
        toastr.info(message, title);
    } else {
        console.info(message);
    }
}

/**
 * Show a warning notification
 * @param {string} message - The notification message
 * @param {string} title - Optional title for the notification
 */
function showWarningNotification(message, title = "Warning") {
    if (typeof toastr !== 'undefined') {
        toastr.warning(message, title);
    } else {
        console.warn(message);
    }
}

/**
 * Handle form submission with AJAX and show notifications
 * @param {string} formId - The ID of the form to submit
 * @param {string} successMessage - Message to show on success
 * @param {string} redirectUrl - URL to redirect to on success (optional)
 */
function handleFormSubmissionWithNotification(formId, successMessage, redirectUrl = null) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID '${formId}' not found`);
        return;
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const action = form.getAttribute('action') || form.getAttribute('data-action');

        fetch(action, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessNotification(data.message || successMessage);

                    if (redirectUrl) {
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 1500);
                    } else if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1500);
                    }
                } else {
                    showErrorNotification(data.message || 'An error occurred');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorNotification('An unexpected error occurred. Please try again.');
            });
    });
}

/**
 * Show flash messages from Flask as Toastr notifications
 */
document.addEventListener('DOMContentLoaded', function () {
    // Check for flash message data attributes
    const flashContainer = document.querySelector('[data-flash-messages]');

    if (flashContainer) {
        const messages = JSON.parse(flashContainer.getAttribute('data-flash-messages'));

        messages.forEach(msg => {
            const type = msg.category || 'info';
            const message = msg.message;

            switch (type) {
                case 'success':
                    showSuccessNotification(message);
                    break;
                case 'error':
                    showErrorNotification(message);
                    break;
                case 'warning':
                    showWarningNotification(message);
                    break;
                case 'info':
                default:
                    showInfoNotification(message);
                    break;
            }
        });
    }
});
