// Wait for the HTML document to be fully loaded before running the script
document.addEventListener("DOMContentLoaded", function() {
  
  const toggle = document.getElementById('modeToggle');
  
  toggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
    toggle.textContent = document.body.classList.contains('light-mode') ? '☀️' : '🌙';
  });

});