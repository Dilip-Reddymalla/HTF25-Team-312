document.addEventListener("DOMContentLoaded", function() {

  // --- Header Controls ---
  const toggle = document.getElementById('modeToggle');
  const logoutBtn = document.getElementById('logoutBtn');
  const body = document.body;

  toggle.addEventListener('click', () => {
    body.classList.toggle('light-mode');
    toggle.textContent = body.classList.contains('light-mode') ? '☀️' : '🌙';
  });

  logoutBtn.addEventListener('click', () => {
    alert("Logging out...");
    window.location.href = 'login.html'; // Redirect to login page
  });

  // --- File Input Display ---
  const resumeFileInput = document.getElementById('resumeFile');
  const fileNameDisplay = document.getElementById('fileName');

  resumeFileInput.addEventListener('change', function() {
    if (resumeFileInput.files.length > 0) {
      fileNameDisplay.textContent = resumeFileInput.files[0].name;
    } else {
      fileNameDisplay.textContent = 'No file chosen';
    }
  });

  // --- Form Validation ---
  const analyzerForm = document.getElementById('analyzerForm');
  const resumeText = document.getElementById('resumeText');
  const jobRoleInput = document.getElementById('jobRole');

  const resumeError = document.getElementById('resumeError');
  const roleError = document.getElementById('roleError');
  const submitError = document.getElementById('submitError');

  analyzerForm.addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    // Clear previous errors
    resumeError.style.display = 'none';
    roleError.style.display = 'none';
    submitError.style.display = 'none';

    let isValid = true;

    // 1. Check if Job Role is filled
    const jobRole = jobRoleInput.value.trim();
    if (jobRole === '') {
      roleError.style.display = 'block';
      isValid = false;
    }

    // 2. Check if EITHER file is uploaded OR text is pasted
    const fileChosen = resumeFileInput.files.length > 0;
    const textPasted = resumeText.value.trim() !== '';
    if (!fileChosen && !textPasted) {
      resumeError.style.display = 'block';
      isValid = false;
    }

    // If form is valid, proceed (simulate analysis for now)
    if (isValid) {
      console.log('Form is valid. Starting analysis...');
      console.log('Job Role:', jobRole);
      if (fileChosen) {
        console.log('Resume File:', resumeFileInput.files[0].name);
      } else {
        console.log('Resume Text Provided:', textPasted);
      }
      
      alert('Validation successful! Starting analysis... (Check console)');
      
      // In a real application, you would now:
      // - Read the PDF content if a file was uploaded (requires server-side or complex JS library)
      // - Get the text from the textarea
      // - Send the resume data and job role to your backend API for analysis.
      // - Redirect to a results page or display results dynamically.
      
      // For now, let's just clear the form as an example
      // analyzerForm.reset();
      // fileNameDisplay.textContent = 'No file chosen';

    } else {
      submitError.textContent = 'Please fix the errors above.';
      submitError.style.display = 'block';
    }
  });

});