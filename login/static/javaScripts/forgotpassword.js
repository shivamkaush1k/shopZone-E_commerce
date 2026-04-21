document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('forgotForm');
  const email = document.getElementById('email');
  const submitBtn = document.getElementById('submitBtn');
  const spinner = document.getElementById('submitSpinner');

  // Email validator
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  function validateEmail(value) {
    return emailRegex.test(value.trim());
  }

  // Show / hide error
  function showError(field, message) {
    field.classList.add('is-invalid');
    const feedback = field.nextElementSibling;
    if (feedback) {
      feedback.textContent = message;
      feedback.style.display = 'block';
    }
  }
  function hideError(field) {
    field.classList.remove('is-invalid');
    const feedback = field.nextElementSibling;
    if (feedback) feedback.style.display = 'none';
  }

  // Real-time validation
  email.addEventListener('blur', () => {
    if (!email.value.trim()) {
      showError(email, 'Email is required');
    } else if (!validateEmail(email.value)) {
      showError(email, 'Enter a valid email');
    } else hideError(email);
  });
  email.addEventListener('input', () => {
    if (email.classList.contains('is-invalid') && validateEmail(email.value)) {
      hideError(email);
    }
  });

  // Form submit
  form.addEventListener('submit', e => {
    e.preventDefault();
    let valid = true;

    if (!email.value.trim()) {
      showError(email, 'Email is required');
      valid = false;
    } else if (!validateEmail(email.value)) {
      showError(email, 'Enter a valid email');
      valid = false;
    } else hideError(email);

    if (!valid) return;

    // Show loading
    submitBtn.disabled = true;
    spinner.classList.remove('d-none');
    submitBtn.querySelector('i').style.display = 'none';

    // Simulate API call (replace with real AJAX)
    setTimeout(() => {
      spinner.classList.add('d-none');
      submitBtn.querySelector('i').style.display = 'inline-block';
      submitBtn.disabled = false;
      form.reset();
      alert('If that email exists, a reset link has been sent.');
    }, 2000);
  });
});
  document.querySelector('form').addEventListener('submit', function(e) {
    const password = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    if (password !== confirmPassword) {
      e.preventDefault();
      alert('Passwords do not match!');
      document.getElementById('confirm_password').focus();
    }
  });