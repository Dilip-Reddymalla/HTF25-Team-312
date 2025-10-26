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

  // --- History Loading Logic (Placeholder) ---
  const historyContainer = document.getElementById('historyContainer');
  const noHistoryMessage = document.getElementById('noHistoryMessage');

  // In a real application, you would fetch data here.
  // Example: const historyData = await fetch('/api/history').then(res => res.json());
  const historyData = []; // Assume empty for this example, keeping the static card visible

  if (historyData.length === 0) {
    // If no *real* history data exists from a fetch, the static example card remains.
    // You could optionally show the "No history" message alongside the example if desired.
    // noHistoryMessage.style.display = 'block';
  } else {
    // If you fetch real history data:
    // 1. You would likely hide or remove the static example card first.
    //    Example: historyContainer.querySelector('.history-card').style.display = 'none';
    // 2. Then, loop through historyData and create/append new card elements dynamically.
    noHistoryMessage.style.display = 'none'; // Ensure message is hidden when real data is loaded
  }

  // --- END History Loading Logic ---

});