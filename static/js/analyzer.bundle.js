document.addEventListener('DOMContentLoaded', () => {
    // --- Element references ---
    const form = document.getElementById('analyze-form');
    const fileInput = document.getElementById('id_resume_file');
    const fileNameDisplay = document.getElementById('selected-file');
    const jobDescription = document.getElementById('id_job_description');
    const targetRole = document.getElementById('id_target_role');
    const resultCard = document.getElementById('result-card');
    const skillsList = document.getElementById('skills-list');
    const recommendationsList = document.getElementById('recommendations-list');

    // --- File name display ---
    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            fileNameDisplay.textContent = file ? file.name : 'No file chosen';
        });
    }

    // --- Helper to get CSRF token (needed for Django POST requests) ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // --- Handle form submit ---
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            // Validation
            const fileChosen = fileInput && fileInput.files.length > 0;
            const textPasted = jobDescription && jobDescription.value.trim() !== '';
            const roleGiven = targetRole && targetRole.value.trim() !== '';

            if (!roleGiven) {
                alert('Please enter your target job role.');
                return;
            }
            if (!fileChosen && !textPasted) {
                alert('Please upload a resume file or paste text.');
                return;
            }

            // Create form data
            const formData = new FormData();
            if (fileChosen) {
                formData.append('resume_file', fileInput.files[0]);
            }
            if (textPasted) {
                formData.append('job_description', jobDescription.value.trim());
            }
            formData.append('target_role', targetRole.value.trim());

            // --- Show loading state ---
            resultCard.style.display = 'block';
            resultCard.innerHTML = `
                <div style="text-align:center; padding:20px;">
                    <div class="spinner"></div>
                    <p>Analyzing your resume...</p>
                </div>
            `;

            // --- Send request to Django view ---
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => {
                const contentType = res.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return res.json();
                } else {
                    return res.text();
                }
            })
            .then(data => {
                // --- Handle JSON response ---
                if (typeof data === 'object') {
                    resultCard.style.display = 'block';
                    // Helper function to convert **bold** to HTML <strong>
function parseBold(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Inside your form submission handler, where you render recommendations:
resultCard.innerHTML = `
    <h4>Recommendations</h4>
    <ul id="recommendations-list" class="recommendations">
        ${(data.recommendations || []).map(rec => `<li>${parseBold(rec)}</li>`).join('')}
    </ul>

    ${data.feedback ? `<div id="feedback-box"><strong>AI Feedback:</strong><br>${parseBold(data.feedback).replace(/\n/g, "<br>")}</div>` : ''}
`;


                } else {
                    // --- If server returns HTML ---
                    document.querySelector('.analyzer-section').innerHTML = data;
                }
            })
            .catch(err => {
                console.error('Error:', err);
                resultCard.style.display = 'block';
                resultCard.innerHTML = `
                    <p style="color:red;">An error occurred while analyzing. Please try again.</p>
                `;
            });
        });
    }

    // --- Optional: simple dark/light mode toggle ---
    const modeToggle = document.getElementById('modeToggle');
    if (modeToggle) {
        modeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            modeToggle.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
        });
    }
});
