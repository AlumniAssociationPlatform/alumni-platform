document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("eventForm");
    if (!form) return;

    const titleInput = document.getElementById("title");
    const descInput = document.getElementById("description");
    const dateInput = document.getElementById("event_date");
    const deptCheckboxes = document.querySelectorAll(".department-checkbox");
    const submitBtn = document.getElementById("submitBtn");
    const charCount = document.getElementById("charCount");

    const rules = {
        title: {
            check: v => v.trim() !== "" && v.length <= 125 && /^[A-Za-z0-9 ]+$/.test(v),
            msg: "Title must contain only letters, numbers, and spaces"
        },
        description: {
            check: v => v.length <= 1000,
            msg: "Description cannot exceed 1000 characters"
        },
        event_date: {
            check: v => {
                if (!v) return false;
                const d = new Date(v);
                const t = new Date();
                t.setHours(0, 0, 0, 0);
                return d >= t;
            },
            msg: "Event date must be today or future"
        },
        department: {
            check: v => v,
            msg: "Please select at least one department"
        }
    };

    function feedback(el) {
        return el.parentElement.parentElement.querySelector(".invalid-feedback");
    }

    function invalid(msg) {
        const deptContainer = document.querySelector(".department-checkboxes");
        deptContainer.classList.add("is-invalid");
        deptContainer.classList.remove("is-valid");
        const feedbackEl = deptContainer.parentElement.querySelector(".invalid-feedback");
        if (feedbackEl) {
            feedbackEl.textContent = msg;
        }
        toggleBtn();
    }

    function valid() {
        const deptContainer = document.querySelector(".department-checkboxes");
        deptContainer.classList.remove("is-invalid");
        deptContainer.classList.add("is-valid");
        const feedbackEl = deptContainer.parentElement.querySelector(".invalid-feedback");
        if (feedbackEl) {
            feedbackEl.textContent = "";
        }
        toggleBtn();
    }

    function toggleBtn() {
        const selectedDepts = Array.from(deptCheckboxes).some(cb => cb.checked);
        submitBtn.disabled = !(
            titleInput.classList.contains("is-valid") &&
            (descInput.value === "" || descInput.classList.contains("is-valid")) &&
            dateInput.classList.contains("is-valid") &&
            selectedDepts
        );
    }

    function getSelectedFeedback(el) {
        return el.parentElement.querySelector(".invalid-feedback");
    }

    function invalidSingle(el, msg) {
        el.classList.add("is-invalid");
        el.classList.remove("is-valid");
        getSelectedFeedback(el).textContent = msg;
        toggleBtn();
    }

    function validSingle(el) {
        el.classList.remove("is-invalid");
        el.classList.add("is-valid");
        getSelectedFeedback(el).textContent = "";
        toggleBtn();
    }

    titleInput.addEventListener("input", () => {
        titleInput.value = titleInput.value.replace(/[^A-Za-z0-9 ]/g, "");
        rules.title.check(titleInput.value)
            ? validSingle(titleInput)
            : invalidSingle(titleInput, rules.title.msg);
    });

    descInput.addEventListener("input", () => {
        charCount.textContent = descInput.value.length;
        rules.description.check(descInput.value)
            ? validSingle(descInput)
            : invalidSingle(descInput, rules.description.msg);
    });

    dateInput.addEventListener("change", () => {
        rules.event_date.check(dateInput.value)
            ? validSingle(dateInput)
            : invalidSingle(dateInput, rules.event_date.msg);
    });

    // Department checkbox change handler
    deptCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", () => {
            const selectedDepts = Array.from(deptCheckboxes).some(cb => cb.checked);
            selectedDepts ? valid() : invalid(rules.department.msg);
        });
    });

    // Select All and Deselect All functionality
    const selectAllBtn = document.getElementById("selectAllBtn");
    const deselectAllBtn = document.getElementById("deselectAllBtn");

    if (selectAllBtn) {
        selectAllBtn.addEventListener("click", (e) => {
            e.preventDefault();
            deptCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            deptCheckboxes[0].dispatchEvent(new Event("change"));
        });
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener("click", (e) => {
            e.preventDefault();
            deptCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            deptCheckboxes[0].dispatchEvent(new Event("change"));
        });
    }

    form.addEventListener("submit", e => {
        if (!submitBtn.disabled) return;
        e.preventDefault();
        titleInput.dispatchEvent(new Event("input"));
        descInput.dispatchEvent(new Event("input"));
        dateInput.dispatchEvent(new Event("change"));
        deptCheckboxes[0].dispatchEvent(new Event("change"));
    });

    // Edit mode auto-validation
    if (titleInput.value) titleInput.dispatchEvent(new Event("input"));
    if (descInput.value) descInput.dispatchEvent(new Event("input"));
    if (dateInput.value) dateInput.dispatchEvent(new Event("change"));
    if (Array.from(deptCheckboxes).some(cb => cb.checked)) deptCheckboxes[0].dispatchEvent(new Event("change"));
});
