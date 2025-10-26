document.addEventListener("DOMContentLoaded", function() {
  // Icon definitions
  const iconEyeOpen = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
      <circle cx="12" cy="12" r="3"></circle>
    </svg>
  `;
  const iconEyeClosed = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  `;

  // Get all form elements
  const form = document.getElementById('signupForm');
  const nameInput = document.getElementById('fullName');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  
  // Get all error message elements
  const nameError = document.getElementById('nameError');
  const emailError = document.getElementById('emailError');
  const passwordError = document.getElementById('passwordError');
  const confirmPasswordError = document.getElementById('confirmPasswordError');
  const signupError = document.getElementById('signupError');

  // Get buttons
  const togglePassword = document.getElementById('togglePassword');
  const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
  const signupBtn = document.getElementById('signupBtn');
  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;

  // Password show/hide toggle for FIRST password field
  togglePassword.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    togglePassword.innerHTML = isPassword ? iconEyeClosed : iconEyeOpen;
  });

  // Password show/hide toggle for SECOND password field
  toggleConfirmPassword.addEventListener('click', () => {
    const isPassword = confirmPasswordInput.type === 'password';
    confirmPasswordInput.type = isPassword ? 'text' : 'password';
    // We must use .cloneNode(true) when using the img tag version
    // or the browser will move the same <img> element back and forth.
    toggleConfirmPassword.innerHTML = isPassword ? iconEyeClosed.cloneNode(true) : iconEyeOpen;
  });

  // Theme toggle (dark/light)
  themeToggle.addEventListener('click', () => {
    body.classList.toggle('light');
    themeToggle.textContent = body.classList.contains('light') ? '🌞 Light' : '🌙 Dark';
  });

  // Email validation function
  function validEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  // Main form submission logic
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Clear all previous errors
    nameError.style.display = 'none';
    emailError.style.display = 'none';
    passwordError.style.display = 'none';
    confirmPasswordError.style.display = 'none';
    signupError.style.display = 'none';

    let valid = true;
    
    // 1. Validate Full Name
    if (nameInput.value.trim() === '') {
      nameError.style.display = 'block';
      valid = false;
    }
    
    // 2. Validate Email
    if (!validEmail(emailInput.value.trim())) {
      emailError.style.display = 'block';
      valid = false;
    }
    
    // 3. Validate Password Length
    if (passwordInput.value.trim().length < 6) {
      passwordError.style.display = 'block';
      valid = false;
    }
    
    // 4. Validate Passwords Match
    if (passwordInput.value.trim() !== confirmPasswordInput.value.trim()) {
      confirmPasswordError.style.display = 'block';
      valid = false;
    } else if (confirmPasswordInput.value.trim() === '') {
      // Also check if confirm password is empty
      confirmPasswordError.textContent = 'Please confirm your password.'
      confirmPasswordError.style.display = 'block';
      valid = false;
    }

    if (!valid) return;

    signupBtn.disabled = true;
    signupBtn.textContent = 'Creating Account...';

    // Submit the form directly to Django
    form.submit();
  });

 const googleBtn = document.getElementById('googleBtn');
  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      const url = googleBtn.dataset.url || '/auth/google/login/';
      console.log('Google button clicked. Redirecting to:', url);
      window.location.href = url;
    });
  } else {
    console.error('Google button not found in the document');
  }

});