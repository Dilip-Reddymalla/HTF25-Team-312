// Wait for the DOM to load before running the script
document.addEventListener("DOMContentLoaded", function() {

  const iconEyeOpen = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
      <circle cx="12" cy="12" r="3"></circle>
    </svg>
  `;
  
  // Make sure 'eye_closed.svg' is in the same folder as this login.html file
  const iconEyeClosed = `
    <img src="eye_closed.svg" alt="Hide password">
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

  togglePassword.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    togglePassword.innerHTML = isPassword ? iconEyeClosed : iconEyeOpen;
  });

  themeToggle.addEventListener('click', () => {
    body.classList.toggle('light');
    themeToggle.textContent = body.classList.contains('light') ? '🌞 Light' : '🌙 Dark';
  });

  function validEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    emailError.style.display = passwordError.style.display = loginError.style.display = 'none';

    let valid = true;

    if (!validEmail(emailInput.value.trim())) {
      emailError.style.display = 'block';
      valid = false;
    }

    if (passwordInput.value.trim().length < 6) {
      passwordError.style.display = 'block';
      valid = false;
    }

    if (!valid) return;

    loginBtn.disabled = true;
    loginBtn.textContent = 'Signing in...';

    try {
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (emailInput.value.trim() === 'fail@example.com') {
            reject(new Error('Invalid credentials.'));
          } else {
            resolve();
          }
        }, 1000);
      });

      alert('Login successful! Redirecting...');
      window.location.href = 'dashboard.html'; // This is the page AFTER login
    } catch (err) {
      loginError.textContent = err.message || 'Something went wrong.';
      loginError.style.display = 'block';
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Sign In';
    }
  });

  document.getElementById('googleBtn').addEventListener('click', () => {
    alert("Simulating Google Login...");
  });
  
  document.getElementById('githubBtn').addEventListener('click', () => {
    alert("Simulating GitHub Login...");
  });
  
});