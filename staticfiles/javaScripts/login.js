class LoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.submitBtn = document.getElementById('loginBtn');
        this.passwordToggle = document.getElementById('togglePassword');
        this.passwordInput = document.getElementById('password');
        this.usernameInput = document.getElementById('username');
        
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.restoreFormState();
    }

    attachEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Password toggle
        if (this.passwordToggle) {
            this.passwordToggle.addEventListener('click', (e) => this.togglePasswordVisibility(e));
        }

        // Real-time validation
        this.usernameInput.addEventListener('blur', () => this.validateUsername());
        this.passwordInput.addEventListener('blur', () => this.validatePassword());

        // Save form state to sessionStorage
        this.form.addEventListener('change', () => this.saveFormState());
    }

    /**
     * Handle form submission
     */
    handleSubmit(e) {
        e.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            return;
        }

        // Show loading state
        this.setLoading(true);

        // Simulate form submission (Django will handle actual submission)
        setTimeout(() => {
            this.form.submit();
        }, 500);
    }

    /**
     * Validate entire form
     */
    validateForm() {
        let isValid = true;

        // Reset all errors
        this.clearAllErrors();

        // Validate username
        if (!this.validateUsername()) {
            isValid = false;
        }

        // Validate password
        if (!this.validatePassword()) {
            isValid = false;
        }

        return isValid;
    }

    /**
     * Validate username field
     */
    validateUsername() {
        const value = this.usernameInput.value.trim();
        const errorElement = document.getElementById('username-error');

        if (!value) {
            this.showError(errorElement, 'Username or email is required');
            return false;
        }

        if (value.length < 3) {
            this.showError(errorElement, 'Username must be at least 3 characters');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Validate password field
     */
    validatePassword() {
        const value = this.passwordInput.value;
        const errorElement = document.getElementById('password-error');

        if (!value) {
            this.showError(errorElement, 'Password is required');
            return false;
        }

        if (value.length < 8) {
            this.showError(errorElement, 'Password must be at least 8 characters');
            return false;
        }

        this.clearError(errorElement);
        return true;
    }

    /**
     * Toggle password visibility
     */
    togglePasswordVisibility(e) {
        e.preventDefault();

        const isPassword = this.passwordInput.type === 'password';
        this.passwordInput.type = isPassword ? 'text' : 'password';

        // Update icon
        const icon = this.passwordToggle.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');

        // Update aria-label
        this.passwordToggle.setAttribute(
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
        const input = element.previousElementSibling;
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
        const input = element.previousElementSibling;
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
     * Save form state to sessionStorage
     */
    saveFormState() {
        const formData = {
            username: this.usernameInput.value,
            rememberMe: document.getElementById('remember_me').checked
        };
        sessionStorage.setItem('loginFormState', JSON.stringify(formData));
    }

    /**
     * Restore form state from sessionStorage
     */
    restoreFormState() {
        const saved = sessionStorage.getItem('loginFormState');
        if (saved) {
            try {
                const formData = JSON.parse(saved);
                if (formData.username) {
                    this.usernameInput.value = formData.username;
                }
                if (formData.rememberMe) {
                    document.getElementById('remember_me').checked = true;
                }
            } catch (e) {
                console.error('Error restoring form state:', e);
            }
        }
    }
}

// Initialize form handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LoginForm();
});

// Utility function for Bootstrap class helper
function addClass(element, className) {
    element?.classList.add(className);
}

function removeClass(element, className) {
    element?.classList.remove(className);
}