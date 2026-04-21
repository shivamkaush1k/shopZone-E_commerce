class SignupForm {
    constructor() {
        this.form = document.getElementById('signupForm');
        this.submitBtn = document.getElementById('signupBtn');
        
        // Form inputs
        this.firstNameInput = document.getElementById('first_name');
        this.lastNameInput = document.getElementById('last_name');
        this.usernameInput = document.getElementById('username');
        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.confirmPasswordInput = document.getElementById('confirm_password');
        this.phoneInput = document.getElementById('phone');
        this.termsCheckbox = document.getElementById('terms');
        
        // Password toggles
        this.passwordToggle = document.getElementById('togglePassword');
        this.confirmPasswordToggle = document.getElementById('toggleConfirmPassword');
        
        // Password strength elements
        this.strengthFill = document.getElementById('strengthFill');
        this.strengthText = document.getElementById('strengthText');
        
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.restoreFormState();
    }

    attachEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Password toggles
        if (this.passwordToggle) {
            this.passwordToggle.addEventListener('click', (e) => 
                this.togglePasswordVisibility(e, this.passwordInput)
            );
        }

        if (this.confirmPasswordToggle) {
            this.confirmPasswordToggle.addEventListener('click', (e) => 
                this.togglePasswordVisibility(e, this.confirmPasswordInput)
            );
        }

        // Real-time validation
        this.firstNameInput.addEventListener('blur', () => this.validateFirstName());
        this.lastNameInput.addEventListener('blur', () => this.validateLastName());
        this.usernameInput.addEventListener('blur', () => this.validateUsername());
        this.emailInput.addEventListener('blur', () => this.validateEmail());
        this.passwordInput.addEventListener('input', () => this.validatePassword());
        this.confirmPasswordInput.addEventListener('blur', () => this.validatePasswordMatch());
        this.phoneInput.addEventListener('blur', () => this.validatePhone());
        this.termsCheckbox.addEventListener('change', () => this.validateTerms());

        // Save form state on change
        this.form.addEventListener('change', () => this.saveFormState());
        this.form.addEventListener('input', () => this.saveFormState());
    }

    /**
     * Handle form submission
     */
    handleSubmit(e) {
        e.preventDefault();

        // Validate entire form
        if (!this.validateForm()) {
            this.scrollToFirstError();
            return;
        }

        // Show loading state
        this.setLoading(true);

        // Submit form after a short delay
        setTimeout(() => {
            this.form.submit();
        }, 500);
    }

    /**
     * Validate entire form
     */
    validateForm() {
        let isValid = true;

        // Clear all errors first
        this.clearAllErrors();

        // Validate all fields
        if (!this.validateFirstName()) isValid = false;
        if (!this.validateLastName()) isValid = false;
        if (!this.validateUsername()) isValid = false;
        if (!this.validateEmail()) isValid = false;
        if (!this.validatePassword()) isValid = false;
        if (!this.validatePasswordMatch()) isValid = false;
        if (!this.validateTerms()) isValid = false;
        if (this.phoneInput.value && !this.validatePhone()) isValid = false;

        return isValid;
    }

    /**
     * Validate first name
     */
    validateFirstName() {
        const value = this.firstNameInput.value.trim();
        const errorElement = document.getElementById('first_name-error');

        if (!value) {
            this.showError(errorElement, 'First name is required');
            return false;
        }

        if (value.length < 2) {
            this.showError(errorElement, 'First name must be at least 2 characters');
            return false;
        }

        if (!/^[a-zA-Z\s]+$/.test(value)) {
            this.showError(errorElement, 'First name can only contain letters');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate last name
     */
    validateLastName() {
        const value = this.lastNameInput.value.trim();
        const errorElement = document.getElementById('last_name-error');

        if (!value) {
            this.showError(errorElement, 'Last name is required');
            return false;
        }

        if (value.length < 2) {
            this.showError(errorElement, 'Last name must be at least 2 characters');
            return false;
        }

        if (!/^[a-zA-Z\s]+$/.test(value)) {
            this.showError(errorElement, 'Last name can only contain letters');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate username
     */
    validateUsername() {
        const value = this.usernameInput.value.trim();
        const errorElement = document.getElementById('username-error');

        if (!value) {
            this.showError(errorElement, 'Username is required');
            return false;
        }

        if (value.length < 3) {
            this.showError(errorElement, 'Username must be at least 3 characters');
            return false;
        }

        if (value.length > 30) {
            this.showError(errorElement, 'Username must not exceed 30 characters');
            return false;
        }

        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
            this.showError(errorElement, 'Username can only contain letters, numbers, and underscores');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate email
     */
    validateEmail() {
        const value = this.emailInput.value.trim();
        const errorElement = document.getElementById('email-error');

        if (!value) {
            this.showError(errorElement, 'Email is required');
            return false;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            this.showError(errorElement, 'Please enter a valid email address');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate password and calculate strength
     */
    validatePassword() {
        const value = this.passwordInput.value;
        const errorElement = document.getElementById('password-error');

        if (!value) {
            this.showError(errorElement, 'Password is required');
            this.updatePasswordStrength(0);
            return false;
        }

        if (value.length < 8) {
            this.showError(errorElement, 'Password must be at least 8 characters');
            this.updatePasswordStrength(1);
            return false;
        }

        // Check password strength
        const strength = this.calculatePasswordStrength(value);
        this.updatePasswordStrength(strength);

        if (strength < 2) {
            this.showError(errorElement, 'Password is too weak. Use uppercase, lowercase, numbers, and symbols');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Calculate password strength
     * Returns 0-4 (0=invalid, 1=weak, 2=fair, 3=good, 4=strong)
     */
    calculatePasswordStrength(password) {
        if (!password || password.length < 8) return 0;

        let strength = 0;

        // Check for lowercase
        if (/[a-z]/.test(password)) strength++;

        // Check for uppercase
        if (/[A-Z]/.test(password)) strength++;

        // Check for numbers
        if (/\d/.test(password)) strength++;

        // Check for special characters
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strength++;

        // Length bonus
        if (password.length >= 12) strength++;

        return Math.min(strength, 4);
    }

    /**
     * Update password strength indicator
     */
    updatePasswordStrength(strength) {
        const strengthLevels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
        const strengthColors = ['', '#ef4444', '#f59e0b', '#3b82f6', '#10b981'];

        if (strength === 0) {
            this.strengthText.textContent = 'Enter password';
            this.strengthFill.style.width = '0%';
            this.strengthFill.style.backgroundColor = 'transparent';
        } else {
            this.strengthText.textContent = strengthLevels[strength];
            const percentage = (strength / 4) * 100;
            this.strengthFill.style.width = percentage + '%';
            this.strengthFill.style.backgroundColor = strengthColors[strength];
        }
    }

    /**
     * Validate password match
     */
    validatePasswordMatch() {
        const password = this.passwordInput.value;
        const confirmPassword = this.confirmPasswordInput.value;
        const errorElement = document.getElementById('confirm_password-error');

        if (!confirmPassword) {
            this.showError(errorElement, 'Please confirm your password');
            return false;
        }

        if (password !== confirmPassword) {
            this.showError(errorElement, 'Passwords do not match');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate phone number (optional field)
     */
    validatePhone() {
        const value = this.phoneInput.value.trim();
        const errorElement = document.getElementById('phone-error');

        if (!value) {
            // Phone is optional
            this.clearError(errorElement);
            return true;
        }

        // Basic phone validation (10-15 digits with optional +, -, (), space)
        const phoneRegex = /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/;
        
        if (!phoneRegex.test(value)) {
            this.showError(errorElement, 'Please enter a valid phone number');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate terms acceptance
     */
    validateTerms() {
        const errorElement = document.getElementById('terms-error');

        if (!this.termsCheckbox.checked) {
            this.showError(errorElement, 'You must agree to the terms and conditions');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Toggle password visibility
     */
    togglePasswordVisibility(e, inputElement) {
        e.preventDefault();

        const isPassword = inputElement.type === 'password';
        inputElement.type = isPassword ? 'text' : 'password';

        // Update icon
        const icon = e.currentTarget.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');

        // Update aria-label
        e.currentTarget.setAttribute(
            'aria-label',
            isPassword ? 'Hide password' : 'Show password'
        );
    }

    /**
     * Show error message
     */
    showError(element, message) {
        element.textContent = message;
        element.style.display = 'block';
        element.classList.add('show');

        // Add error class to input
        const input = element.previousElementSibling || element.closest('.form-group').querySelector('.form-control');
        if (input && input.classList.contains('form-control')) {
            input.classList.add('is-invalid');
        }
    }

    /**
     * Clear error message
     */
    clearError(element) {
        element.textContent = '';
        element.style.display = 'none';
        element.classList.remove('show');

        // Remove error class from input
        const input = element.previousElementSibling || element.closest('.form-group').querySelector('.form-control');
        if (input && input.classList.contains('form-control')) {
            input.classList.remove('is-invalid');
        }
    }

    /**
     * Clear all error messages
     */
    clearAllErrors() {
        const errorElements = this.form.querySelectorAll('.error-text');
        errorElements.forEach(element => this.clearError(element));
    }

    /**
     * Set loading state on submit button
     */
    setLoading(isLoading) {
        this.submitBtn.disabled = isLoading;
        
        if (isLoading) {
            this.submitBtn.querySelector('.btn-text').classList.add('d-none');
            this.submitBtn.querySelector('.btn-loader').classList.remove('d-none');
        } else {
            this.submitBtn.querySelector('.btn-text').classList.remove('d-none');
            this.submitBtn.querySelector('.btn-loader').classList.add('d-none');
        }
    }

    /**
     * Scroll to first error field
     */
    scrollToFirstError() {
        const firstError = this.form.querySelector('.error-text.show');
        if (firstError) {
            firstError.closest('.form-group').scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Save form state to sessionStorage
     */
    saveFormState() {
        const formData = {
            firstName: this.firstNameInput.value,
            lastName: this.lastNameInput.value,
            username: this.usernameInput.value,
            email: this.emailInput.value,
            phone: this.phoneInput.value,
            newsletter: document.getElementById('newsletter').checked
        };
        sessionStorage.setItem('signupFormState', JSON.stringify(formData));
    }

    /**
     * Restore form state from sessionStorage
     */
    restoreFormState() {
        const saved = sessionStorage.getItem('signupFormState');
        if (saved) {
            try {
                const formData = JSON.parse(saved);
                if (formData.firstName) this.firstNameInput.value = formData.firstName;
                if (formData.lastName) this.lastNameInput.value = formData.lastName;
                if (formData.username) this.usernameInput.value = formData.username;
                if (formData.email) this.emailInput.value = formData.email;
                if (formData.phone) this.phoneInput.value = formData.phone;
                if (formData.newsletter) document.getElementById('newsletter').checked = true;
            } catch (e) {
                console.error('Error restoring form state:', e);
            }
        }
    }
}

// Initialize form handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SignupForm();
});