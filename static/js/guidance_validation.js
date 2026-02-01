/**
 * Guidance Form Validation
 * Provides real-time client-side validation for guidance program forms
 * Similar to job validation with inline error messages
 */

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("guidanceForm");
    if (!form) return;

    const titleInput = document.getElementById("title");
    const descriptionInput = document.getElementById("description");
    const categoryInput = document.getElementById("category");
    const durationInput = document.getElementById("duration_weeks");
    const frequencyInput = document.getElementById("meeting_frequency");
    const methodInput = document.getElementById("preferred_method");
    const submitBtn = document.getElementById("submitBtn");
    const charCount = document.getElementById("charCount");

    const rules = {
        title: {
            check: v => v.trim() !== "" && v.length >= 5 && v.length <= 200,
            msg: "Title must be 5-200 characters long"
        },
        description: {
            check: v => v.trim() !== "" && v.length >= 20 && v.length <= 2000,
            msg: "Description must be 20-2000 characters long"
        },
        category: {
            check: v => v !== "" && ["Career", "Technical", "Personal", "Academic", "Placement"].includes(v),
            msg: "Please select a valid category"
        },
        duration_weeks: {
            check: v => {
                const num = parseInt(v);
                return !isNaN(num) && num >= 1 && num <= 52;
            },
            msg: "Duration must be between 1 and 52 weeks"
        },
        meeting_frequency: {
            check: v => v !== "" && ["Weekly", "Bi-weekly", "Monthly", "As needed"].includes(v),
            msg: "Please select a valid meeting frequency"
        },
        preferred_method: {
            check: v => v !== "" && ["Virtual", "In-person", "Both"].includes(v),
            msg: "Please select a valid preferred method"
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
        submitBtn.disabled = !(
            titleInput.classList.contains("is-valid") &&
            descriptionInput.classList.contains("is-valid") &&
            categoryInput.classList.contains("is-valid") &&
            durationInput.classList.contains("is-valid") &&
            frequencyInput.classList.contains("is-valid") &&
            methodInput.classList.contains("is-valid")
        );
    }

    titleInput.addEventListener("input", () => {
        rules.title.check(titleInput.value)
            ? valid(titleInput)
            : invalid(titleInput, rules.title.msg);
    });

    descriptionInput.addEventListener("input", () => {
        charCount.textContent = descriptionInput.value.length;
        rules.description.check(descriptionInput.value)
            ? valid(descriptionInput)
            : invalid(descriptionInput, rules.description.msg);
    });

    categoryInput.addEventListener("change", () => {
        rules.category.check(categoryInput.value)
            ? valid(categoryInput)
            : invalid(categoryInput, rules.category.msg);
    });

    durationInput.addEventListener("change", () => {
        rules.duration_weeks.check(durationInput.value)
            ? valid(durationInput)
            : invalid(durationInput, rules.duration_weeks.msg);
    });

    frequencyInput.addEventListener("change", () => {
        rules.meeting_frequency.check(frequencyInput.value)
            ? valid(frequencyInput)
            : invalid(frequencyInput, rules.meeting_frequency.msg);
    });

    methodInput.addEventListener("change", () => {
        rules.preferred_method.check(methodInput.value)
            ? valid(methodInput)
            : invalid(methodInput, rules.preferred_method.msg);
    });

    form.addEventListener("submit", e => {
        if (!submitBtn.disabled) return;
        e.preventDefault();
        titleInput.dispatchEvent(new Event("input"));
        descriptionInput.dispatchEvent(new Event("input"));
        categoryInput.dispatchEvent(new Event("change"));
        durationInput.dispatchEvent(new Event("change"));
        frequencyInput.dispatchEvent(new Event("change"));
        methodInput.dispatchEvent(new Event("change"));
    });

    // Edit mode auto-validation
    if (titleInput.value) titleInput.dispatchEvent(new Event("input"));
    if (descriptionInput.value) {
        descriptionInput.dispatchEvent(new Event("input"));
        charCount.textContent = descriptionInput.value.length;
    }
    if (categoryInput.value) categoryInput.dispatchEvent(new Event("change"));
    if (durationInput.value) durationInput.dispatchEvent(new Event("change"));
    if (frequencyInput.value) frequencyInput.dispatchEvent(new Event("change"));
    if (methodInput.value) methodInput.dispatchEvent(new Event("change"));
});

// Clear all error messages
function clearErrors() {
    document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
}