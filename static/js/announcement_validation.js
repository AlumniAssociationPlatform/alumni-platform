document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("announcementForm");
    if (!form) return;

    const titleInput = document.getElementById("title");
    const descInput = document.getElementById("description");
    const submitBtn = document.getElementById("submitBtn");
    const charCount = document.getElementById("charCount");

    const rules = {
        title: {
            check: v => v.trim() !== "" && v.length <= 150 && /^[A-Za-z0-9 ]+$/.test(v),
            msg: "Title must contain only letters, numbers, and spaces (max 150 characters)"
        },
        description: {
            check: v => v.length <= 1000,
            msg: "Description cannot exceed 1000 characters"
        }
    };

    function feedback(el) {
        return el.parentElement.querySelector(".invalid-feedback");
    }

    function invalid(el, msg) {
        el.classList.add("is-invalid");
        el.classList.remove("is-valid");
        feedback(el).textContent = msg;
        toggleBtn();
    }

    function valid(el) {
        el.classList.remove("is-invalid");
        el.classList.add("is-valid");
        feedback(el).textContent = "";
        toggleBtn();
    }

    function toggleBtn() {
        submitBtn.disabled = !(
            titleInput.classList.contains("is-valid") &&
            (descInput.value === "" || descInput.classList.contains("is-valid"))
        );
    }

    titleInput.addEventListener("input", () => {
        titleInput.value = titleInput.value.replace(/[^A-Za-z0-9 ]/g, "");
        rules.title.check(titleInput.value)
            ? valid(titleInput)
            : invalid(titleInput, rules.title.msg);
    });

    descInput.addEventListener("input", () => {
        charCount.textContent = descInput.value.length;
        rules.description.check(descInput.value)
            ? valid(descInput)
            : invalid(descInput, rules.description.msg);
    });

    form.addEventListener("submit", e => {
        if (!submitBtn.disabled) return;
        e.preventDefault();
        titleInput.dispatchEvent(new Event("input"));
        descInput.dispatchEvent(new Event("input"));
    });

    // Edit mode auto-validation
    if (titleInput.value) titleInput.dispatchEvent(new Event("input"));
    if (descInput.value) descInput.dispatchEvent(new Event("input"));
});
