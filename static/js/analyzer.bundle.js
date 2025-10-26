document.addEventListener('DOMContentLoaded', () => {
    // --- Part A: Drag & Drop + Upload (updated to match template selectors) ---
    const dropZone = document.querySelector('.file-row') || document.querySelector('.file-upload');
    const fileInput = document.getElementById('id_resume_file') || document.querySelector('.file-input');
    const uploadBtn = document.querySelector('.upload-button') || document.querySelector('.upload-btn');
    const analysisProgress = document.querySelector('.analysis-progress');
    const progressBar = document.querySelector('.progress-bar-fill');
    const analysisResult = document.querySelector('.result-card') || document.querySelector('.analysis-result');

    if (dropZone) {
        // Drag and drop handlers
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.classList.add('dragover');
        }

        function unhighlight(e) {
            dropZone.classList.remove('dragover');
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const file = dt.files[0];
            handleFile(file);
        }

        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                if (fileInput) fileInput.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                handleFile(file);
            });
        }

        function handleFile(file) {
            if (!file) return;

            // Check file type
            const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please upload a PDF or Word document.');
                return;
            }

            // Place the file into the visible file input so the submit handler will send it
            try {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                if (fileInput) fileInput.files = dataTransfer.files;
            } catch (err) {
                // Some older browsers may not support DataTransfer; just warn and continue
                console.warn('Unable to programmatically set file input. User may need to use the file chooser.');
            }

            // Update the filename display if present
            const selectedNameEl = document.getElementById('selected-file') || document.getElementById('fileName');
            if (selectedNameEl) selectedNameEl.textContent = file.name;
            // Hide any previous results
            if (analysisResult) analysisResult.style.display = 'none';
        }

        function displayResults(data) {
            if (!data) return;
            const scoreEl = document.querySelector('.score-value');
            if (scoreEl) scoreEl.textContent = data.score ?? scoreEl.textContent;

            const skillTags = document.querySelector('.skill-tags');
            if (skillTags && Array.isArray(data.skills)) {
                skillTags.innerHTML = data.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('');
            }

            const recommendations = document.querySelector('.recommendations');
            if (recommendations && Array.isArray(data.recommendations)) {
                recommendations.innerHTML = data.recommendations.map(rec => `<li>${rec}</li>`).join('');
            }

            if (analysisResult) analysisResult.style.display = 'block';
        }
    }

    // --- Part B: Form validation & UI small helpers (adapted to new template IDs) ---
    const resumeFileInput = document.getElementById('id_resume_file');
    const fileNameDisplay = document.getElementById('selected-file');
    const analyzerForm = document.getElementById('analyze-form');
    const jobDescriptionInput = document.getElementById('id_job_description');
    const jobRoleInput = document.getElementById('id_target_role');
    const resumeError = document.getElementById('resumeError');
    const roleError = document.getElementById('roleError');
    const submitError = document.getElementById('submitError');

    if (resumeFileInput && fileNameDisplay) {
        resumeFileInput.addEventListener('change', function() {
            if (resumeFileInput.files.length > 0) {
                fileNameDisplay.textContent = resumeFileInput.files[0].name;
            } else {
                fileNameDisplay.textContent = 'No file chosen';
            }
        });
    }

    if (analyzerForm) {
        analyzerForm.addEventListener('submit', function(event) {
            event.preventDefault();

            // Clear previous errors
            if (resumeError) resumeError.style.display = 'none';
            if (roleError) roleError.style.display = 'none';
            if (submitError) submitError.style.display = 'none';

            let isValid = true;

            // Job role validation
            const jobRole = jobRoleInput ? jobRoleInput.value.trim() : '';
            if (!jobRole) {
                if (roleError) roleError.style.display = 'block';
                isValid = false;
            }

            // Check if file or text exists
            const fileChosen = (resumeFileInput && resumeFileInput.files.length > 0) || (fileInput && fileInput.files && fileInput.files.length > 0);
            const textPasted = jobDescriptionInput ? jobDescriptionInput.value.trim() !== '' : false;
            if (!fileChosen && !textPasted) {
                if (resumeError) resumeError.style.display = 'block';
                isValid = false;
            }

            if (isValid) {
                // For now, if file chosen we let the drag/drop handler/process handle upload.
                // If resume text is provided, send it to the server.
                const payload = new FormData();
                if (resumeFileInput && resumeFileInput.files.length > 0) {
                    payload.append('resume_file', resumeFileInput.files[0]);
                } else if (fileInput && fileInput.files.length > 0) {
                    payload.append('resume_file', fileInput.files[0]);
                }
                if (jobDescriptionInput) payload.append('job_description', jobDescriptionInput.value.trim());
                if (jobRoleInput) payload.append('target_role', jobRoleInput.value.trim());

                // show a simple progress indicator if available
                if (analysisProgress) analysisProgress.style.display = 'block';

                fetch('/upload_resume/', {
                    method: 'POST',
                    body: payload,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(res => {
                    // Check if response has JSON content
                    const contentType = res.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return res.json();
                    }
                    // If not JSON, get the text content
                    return res.text();
                })
                .then(data => {
                    if (analysisProgress) analysisProgress.style.display = 'none';
                    
                    if (typeof data === 'object') {
                        // Handle JSON response
                        displayResults(data);
                    } else {
                        // Handle text/HTML response
                        document.querySelector('.analyzer-section').innerHTML = data;
                    }
                })
                .catch(err => {
                    if (analysisProgress) analysisProgress.style.display = 'none';
                    console.error(err);
                    if (submitError) { 
                        submitError.style.display = 'block'; 
                        submitError.textContent = 'Resume upload failed. Please try again.'; 
                    }
                });
            } else {
                if (submitError) { submitError.textContent = 'Please fix the errors above.'; submitError.style.display = 'block'; }
            }
        });
    }

    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
