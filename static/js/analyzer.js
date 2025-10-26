document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.file-upload');
    const fileInput = document.querySelector('.file-input');
    const uploadBtn = document.querySelector('.upload-btn');
    const analysisProgress = document.querySelector('.analysis-progress');
    const progressBar = document.querySelector('.progress-bar-fill');
    const analysisResult = document.querySelector('.analysis-result');

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

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    function handleFile(file) {
        if (!file) return;

        // Check file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            alert('Please upload a PDF or Word document.');
            return;
        }

        // Show progress
        analysisProgress.style.display = 'block';
        analysisResult.style.display = 'none';

        // Create form data
        const formData = new FormData();
        formData.append('resume', file);

        // Simulate progress (in real implementation, this would be based on actual upload progress)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress > 90) clearInterval(progressInterval);
            progressBar.style.width = `${progress}%`;
        }, 100);

        // Send to server
        fetch('/analyze/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            
            // Wait a bit before showing results
            setTimeout(() => {
                analysisProgress.style.display = 'none';
                displayResults(data);
            }, 500);
        })
        .catch(error => {
            clearInterval(progressInterval);
            analysisProgress.style.display = 'none';
            alert('Error analyzing resume. Please try again.');
            console.error('Error:', error);
        });
    }

    function displayResults(data) {
        // Update UI with results
        document.querySelector('.score-value').textContent = data.score;
        
        // Update skills
        const skillTags = document.querySelector('.skill-tags');
        skillTags.innerHTML = data.skills
            .map(skill => `<span class="skill-tag">${skill}</span>`)
            .join('');

        // Update recommendations
        const recommendations = document.querySelector('.recommendations');
        recommendations.innerHTML = data.recommendations
            .map(rec => `<li>${rec}</li>`)
            .join('');

        // Show results
        analysisResult.style.display = 'block';
    }

    // Helper function to get CSRF token
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