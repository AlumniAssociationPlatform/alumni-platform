document.addEventListener("DOMContentLoaded", () => {

    const submitBtn = document.getElementById("submitBtn");

    const onlyLetters = /^[A-Za-z ]+$/;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const passwordPattern =
        /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/;
    const phonePattern = /^\d{10}$/;

    function isOnlySpaces(v) {
        return v.trim().length === 0;
    }

    function setInvalid(el, msg) {
        el.classList.add("is-invalid");
        el.classList.remove("is-valid");
        el.nextElementSibling.innerText = msg;
        toggleSubmit();
    }

    function setValid(el) {
        el.classList.remove("is-invalid");
        el.classList.add("is-valid");
        toggleSubmit();
    }

    function toggleSubmit() {
        const required = [
            first_name,
            last_name,
            email,
            password,
            confirm_password,
            role
        ];

        if (role.value === "alumni") {
            required.push(passout_year, alumni_department, current_company, designation, alumni_phone_number, alumni_linkedin_profile);
        }

        if (role.value === "student") {
            required.push(gr_no, department, batch_year, phone_number, student_linkedin_profile);
        }

        if (role.value === "faculty") {
            required.push(faculty_id, faculty_department, faculty_designation, faculty_phone_number, faculty_linkedin_profile);
        }

        submitBtn.disabled = !required.every(f => f.classList.contains("is-valid"));
    }

    /* BASIC */
    first_name.addEventListener("input", () => {
        if (first_name.value.length < 2)
            setInvalid(first_name, "Minimum 2 characters required");
        else if (!onlyLetters.test(first_name.value))
            setInvalid(first_name, "Only alphabets allowed");
        else if (isOnlySpaces(first_name.value))
            setInvalid(first_name, "Cannot be only spaces");
        else setValid(first_name);
    });

    last_name.addEventListener("input", () => {
        if (last_name.value.length < 2)
            setInvalid(last_name, "Minimum 2 characters required");
        else if (!onlyLetters.test(last_name.value))
            setInvalid(last_name, "Only alphabets allowed");
        else if (isOnlySpaces(last_name.value))
            setInvalid(last_name, "Cannot be only spaces");
        else setValid(last_name);
    });

    email.addEventListener("input", () => {
        emailPattern.test(email.value)
            ? setValid(email)
            : setInvalid(email, "Invalid email address");
    });

    password.addEventListener("input", () => {
        passwordPattern.test(password.value)
            ? setValid(password)
            : setInvalid(password, "Weak password");
    });

    confirm_password.addEventListener("input", () => {
        confirm_password.value === password.value
            ? setValid(confirm_password)
            : setInvalid(confirm_password, "Passwords do not match");
    });

    profile_photo.addEventListener("change", () => {
        const file = profile_photo.files[0];
        if (!file) {
            // Photo is optional, so just mark as valid if empty
            setValid(profile_photo);
            return;
        }

        const validFormats = ["image/png", "image/jpeg", "image/webp"];
        const maxSize = 1 * 1024 * 1024; // 1 MB

        if (!validFormats.includes(file.type)) {
            setInvalid(profile_photo, "Only PNG, JPG, JPEG, and WEBP formats allowed");
            return;
        }

        if (file.size > maxSize) {
            setInvalid(profile_photo, "File size must be less than 1 MB");
            return;
        }

        setValid(profile_photo);
    });

    role.addEventListener("change", () => {
        alumniFields.classList.toggle("d-none", role.value !== "alumni");
        studentFields.classList.toggle("d-none", role.value !== "student");
        facultyFields.classList.toggle("d-none", role.value !== "faculty");

        role.value
            ? setValid(role)
            : setInvalid(role, "Role is required");
    });

    /* ALUMNI */
    passout_year.addEventListener("input", () => {
        const year = passout_year.value.trim();
        
        // Check if empty
        if (!year) {
            setInvalid(passout_year, "Passout year is required");
            return;
        }
        
        // Check if it's a valid positive number (integers only)
        if (!/^\d+$/.test(year)) {
            setInvalid(passout_year, "Passout year must be a positive number");
            return;
        }
        
        const yearNum = parseInt(year, 10);
        
        // Check if year is within valid range (1950-2025)
        if (yearNum < 1950 || yearNum > 2025) {
            setInvalid(passout_year, "Passout year must be between 1950 and 2025");
            return;
        }
        
        setValid(passout_year);
    });

    alumni_department.addEventListener("change", () => {
        alumni_department.value
            ? setValid(alumni_department)
            : setInvalid(alumni_department, "Department required");
    });

    current_company.addEventListener("input", () => {
        /[A-Za-z]/.test(current_company.value) && !isOnlySpaces(current_company.value)
            ? setValid(current_company)
            : setInvalid(current_company, "Invalid company name");
    });

    designation.addEventListener("input", () => {
        /[A-Za-z]/.test(designation.value) && !isOnlySpaces(designation.value)
            ? setValid(designation)
            : setInvalid(designation, "Invalid designation");
    });

    alumni_phone_number.addEventListener("input", () => {
        phonePattern.test(alumni_phone_number.value)
            ? setValid(alumni_phone_number)
            : setInvalid(alumni_phone_number, "Phone must be exactly 10 digits");
    });

    alumni_linkedin_profile.addEventListener("input", () => {
        alumni_linkedin_profile.value && !isOnlySpaces(alumni_linkedin_profile.value)
            ? setValid(alumni_linkedin_profile)
            : setInvalid(alumni_linkedin_profile, "Invalid LinkedIn URL");
    });

    /* STUDENT */
    gr_no.addEventListener("input", () => {
        /^\d{12}$/.test(gr_no.value)
            ? setValid(gr_no)
            : setInvalid(gr_no, "GR must be exactly 12 digits");
    });

    department.addEventListener("change", () => {
        department.value
            ? setValid(department)
            : setInvalid(department, "Department required");
    });

    batch_year.addEventListener("change", () => {
        batch_year.value
            ? setValid(batch_year)
            : setInvalid(batch_year, "Batch year required");
    });

    skills.addEventListener("input", () => {
        !skills.value || (/[A-Za-z]/.test(skills.value) && !isOnlySpaces(skills.value))
            ? setValid(skills)
            : setInvalid(skills, "Invalid skills");
    });

    phone_number.addEventListener("input", () => {
        phonePattern.test(phone_number.value)
            ? setValid(phone_number)
            : setInvalid(phone_number, "Phone must be exactly 10 digits");
    });

    student_linkedin_profile.addEventListener("input", () => {
        student_linkedin_profile.value && !isOnlySpaces(student_linkedin_profile.value)
            ? setValid(student_linkedin_profile)
            : setInvalid(student_linkedin_profile, "Invalid LinkedIn URL");
    });

    /* FACULTY */
    faculty_id.addEventListener("input", () => {
        faculty_id.value && !isOnlySpaces(faculty_id.value)
            ? setValid(faculty_id)
            : setInvalid(faculty_id, "Faculty ID required");
    });

    faculty_department.addEventListener("change", () => {
        faculty_department.value
            ? setValid(faculty_department)
            : setInvalid(faculty_department, "Department required");
    });

    faculty_designation.addEventListener("input", () => {
        /[A-Za-z]/.test(faculty_designation.value) && !isOnlySpaces(faculty_designation.value)
            ? setValid(faculty_designation)
            : setInvalid(faculty_designation, "Invalid designation");
    });

    faculty_phone_number.addEventListener("input", () => {
        phonePattern.test(faculty_phone_number.value)
            ? setValid(faculty_phone_number)
            : setInvalid(faculty_phone_number, "Phone must be exactly 10 digits");
    });

    faculty_linkedin_profile.addEventListener("input", () => {
        faculty_linkedin_profile.value && !isOnlySpaces(faculty_linkedin_profile.value)
            ? setValid(faculty_linkedin_profile)
            : setInvalid(faculty_linkedin_profile, "Invalid LinkedIn URL");
    });

});

/* Password toggle (eye icon) for registration fields */
function setupPasswordTogglesAuth() {
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

document.addEventListener('DOMContentLoaded', setupPasswordTogglesAuth);

document.getElementById("registerForm").addEventListener("submit", function (e) {
    e.preventDefault();

    toastr.options = {
        "closeButton": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "timeOut": "3000"
    };

    const formData = new FormData(this);

    fetch("/auth/register", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                toastr.success(data.message);
                document.getElementById("registerForm").reset();

                setTimeout(() => {
                    window.location.href = "/auth/login";
                }, 2000);

            } else {
                toastr.error(data.message);
            }
        })
        .catch(() => {
            toastr.error("Something went wrong. Try again.");
        });
});

