// Wait for the DOM to load before running the script
document.addEventListener("DOMContentLoaded", function() {

  const iconEyeOpen = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
      <circle cx="12" cy="12" r="3"></circle>
    </svg>
  `;

  // inline SVG fallback for closed eye (no external file dependency)
  const iconEyeClosed = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-4.97 0-9-3.11-11-8 1.05-2.44 2.8-4.5 4.86-5.93"></path>
      <path d="M1 1l22 22"></path>
    </svg>
  `;

  const form = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const emailError = document.getElementById('emailError');
  const passwordError = document.getElementById('passwordError');
  const loginError = document.getElementById('loginError');
  const togglePassword = document.getElementById('togglePassword');
  const loginBtn = document.getElementById('loginBtn');
  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;

  // guard: some elements might be missing
  if (togglePassword) {
    togglePassword.addEventListener('click', () => {
      const isPassword = passwordInput && passwordInput.type === 'password';
      if (!passwordInput) return;
      passwordInput.type = isPassword ? 'text' : 'password';
      togglePassword.innerHTML = isPassword ? iconEyeClosed : iconEyeOpen;
    });
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      body.classList.toggle('light');
      themeToggle.textContent = body.classList.contains('light') ? '🌞 Light' : '🌙 Dark';
    });
  }

  function validEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      // e.preventDefault();
      if (emailError) emailError.style.display = passwordError.style.display = loginError.style.display = 'none';

      let valid = true;

      if (!emailInput || !validEmail(emailInput.value.trim())) {
        if (emailError) emailError.style.display = 'block';
        valid = false;
      }

      if (!passwordInput || passwordInput.value.trim().length < 6) {
        if (passwordError) passwordError.style.display = 'block';
        valid = false;
      }

      if (!valid) {
        e.preventDefault();
        return;
      }
      
      if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Signing in...';
      }
      
      // Form will be submitted normally to Django view

      // try {
      //   await new Promise((resolve, reject) => {
      //     setTimeout(() => {
      //       if (emailInput && emailInput.value.trim() === 'fail@example.com') {
      //         reject(new Error('Invalid credentials.'));
      //       } else {
      //         resolve();
      //       }
      //     }, 1000);
      //   });

      //   alert('Login successful! Redirecting...');
      //   window.location.href = dashboardUrl;
      // } catch (err) {
      //   if (loginError) {
      //     loginError.textContent = err.message || 'Something went wrong.';
      //     loginError.style.display = 'block';
      //   }
      // } finally {
      //   if (loginBtn) {
      //     loginBtn.disabled = false;
      //     loginBtn.textContent = 'Sign In';
      //   }
      // }
    });
  }

  // Google button: read data-url attribute (set by Django) with fallback
  const googleBtn = document.getElementById('googleBtn');
  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      const url = googleBtn.dataset.url || '/auth/google/login/';
      window.location.href = url;
    });
  }

});