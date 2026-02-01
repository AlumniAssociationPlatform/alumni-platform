document.addEventListener("DOMContentLoaded", () => {

    const email = document.getElementById("login_email");
    const password = document.getElementById("login_password");
    const loginBtn = document.getElementById("loginBtn");

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const passwordPattern =
        /^(?=.*[A-Za-z])(?=.*\d).{6,}$/; // basic secure password

    function setInvalid(el, msg) {
        el.classList.add("is-invalid");
        el.classList.remove("is-valid");
        el.nextElementSibling.innerText = msg;
        toggleButton();
    }

    function setValid(el) {
        el.classList.remove("is-invalid");
        el.classList.add("is-valid");
        toggleButton();
    }

    function toggleButton() {
        loginBtn.disabled = !(
            email.classList.contains("is-valid") &&
            password.classList.contains("is-valid")
        );
    }

    /* EMAIL */
    email.addEventListener("input", () => {
        emailPattern.test(email.value)
            ? setValid(email)
            : setInvalid(email, "Enter a valid email address");
    });

    /* PASSWORD */
    password.addEventListener("input", () => {
        passwordPattern.test(password.value)
            ? setValid(password)
            : setInvalid(password, "Password must be at least 6 characters and contain a number");
    });

    /* FINAL SUBMIT */
    document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();

        if (loginBtn.disabled) return;

        toastr.options = {
            "closeButton": true,
            "progressBar": true,
            "positionClass": "toast-top-right",
            "timeOut": "3000"
        };

        const formData = new FormData(document.getElementById("loginForm"));

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (data.status === "success") {
                toastr.success(data.message);
                setTimeout(() => {
                    window.location.href = data.redirect || "/";
                }, 1500);
            } else {
                toastr.error(data.message);
            }
        } catch (error) {
            toastr.error("Something went wrong. Please try again.");
        }
    });

    /* Password toggle (eye icon) */
    function setupPasswordToggles() {
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            const wrapper = toggle.closest('.position-relative') || toggle.parentElement;
            const input = wrapper ? wrapper.querySelector('input[type="password"], input[type="text"]') : null;
            if (!input) return;
            // initialize text and icon based on type
            if (input.type === 'password') {
                toggle.innerHTML = '<i class="bi bi-eye"></i> Show Password';
                toggle.setAttribute('aria-pressed', 'false');
                toggle.setAttribute('aria-label', 'Show password');
            } else {
                toggle.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Password';
                toggle.setAttribute('aria-pressed', 'true');
                toggle.setAttribute('aria-label', 'Hide password');
            }
            toggle.addEventListener('click', () => {
                if (input.type === 'password') {
                    input.type = 'text';
                    toggle.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Password';
                    toggle.setAttribute('aria-pressed', 'true');
                    toggle.setAttribute('aria-label', 'Hide password');
                } else {
                    input.type = 'password';
                    toggle.innerHTML = '<i class="bi bi-eye"></i> Show Password';
                    toggle.setAttribute('aria-pressed', 'false');
                    toggle.setAttribute('aria-label', 'Show password');
                }
                input.focus();
            });
            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle.click(); }
            });
        });
    }

    setupPasswordToggles();

});
