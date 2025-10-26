document.addEventListener("DOMContentLoaded", function() {

  // --- 1. Header Controls (Theme Toggle & Logout) ---
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

  // --- 2. Skillset Input Logic ---
  const skillInput = document.getElementById('skillInput');
  const skillContainer = document.getElementById('skillContainer');

  skillInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      const skillName = skillInput.value.trim();
      if (skillName) {
        addSkillTag(skillName);
        skillInput.value = '';
      }
    }
  });

  function addSkillTag(name) {
    const tag = document.createElement('div');
    tag.className = 'skill-tag';
    
    const tagName = document.createElement('span');
    tagName.textContent = name;
    
    const removeBtn = document.createElement('span');
    removeBtn.className = 'remove-tag';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => {
      tag.remove();
    };
    
    tag.appendChild(tagName);
    tag.appendChild(removeBtn);
    skillContainer.appendChild(tag);
  }

  // --- 3. Dynamic Section Logic (Add/Remove) ---

  // Reusable function to add dynamic items
  function setupDynamicSection(addButtonId, listContainerId, itemHtmlTemplate) {
    const addButton = document.getElementById(addButtonId);
    const listContainer = document.getElementById(listContainerId);

    addButton.addEventListener('click', () => {
      const item = document.createElement('div');
      item.className = 'dynamic-item';
      item.innerHTML = itemHtmlTemplate;
      
      // Add remove functionality to the new item's remove button
      item.querySelector('.btn-remove').addEventListener('click', () => {
        item.remove();
      });
      
      listContainer.appendChild(item);
    });
  }

  // HTML template for one "Experience" item
  const experienceTemplate = `
    <button type="button" class="btn-remove">&times;</button>
    <div class="grid-col-2">
      <div class="input-group">
        <label>Job Title</label>
        <input type="text" class="exp-title" placeholder="e.g., Senior Developer">
      </div>
      <div class="input-group">
        <label>Company</label>
        <input type="text" class="exp-company" placeholder="e.g., Google">
      </div>
    </div>
    <div class="grid-col-2">
      <div class="input-group">
        <label>Start Date</label>
        <input type="text" class="exp-start" placeholder="e.g., Jan 2020">
      </div>
      <div class="input-group">
        <label>End Date</label>
        <input type="text" class="exp-end" placeholder="e.g., Present">
      </div>
    </div>
    <div class="input-group">
      <label>Description / Responsibilities</label>
      <textarea class="exp-desc" placeholder="Describe your role and achievements..."></textarea>
    </div>
  `;

  // --- MODIFIED TEMPLATE ---
  // HTML template for one "Project" item
  const projectTemplate = `
    <button type="button" class="btn-remove">&times;</button>
    <div class="input-group">
      <label>Project Title</label>
      <input type="text" class="proj-title" placeholder="e.g., Smart Resume Analyzer">
    </div>
    <div class="input-group">
      <label>Description</label>
      <textarea class="proj-desc" placeholder="What the project does..."></textarea>
    </div>
    <div class="grid-col-2"> <div class="input-group">
        <label>Technologies Used</label>
        <input type="text" class="proj-tech" placeholder="e.g., HTML, CSS, JavaScript, AI">
      </div>
      <div class="input-group"> 
        <label>GitHub Project Link (Optional)</label> 
        <input type="url" class="proj-link" placeholder="https://github.com/user/repo"> 
      </div>
    </div>
  `;
  // --- END OF MODIFIED TEMPLATE ---

  // HTML template for one "Certification" item
  const certificationTemplate = `
    <button type="button" class="btn-remove">&times;</button>
    <div class="grid-col-2">
      <div class="input-group">
        <label>Certification Name</label>
        <input type="text" class="cert-name" placeholder="e.g., AWS Certified Cloud Practitioner">
      </div>
      <div class="input-group">
        <label>Issuing Organization</label>
        <input type="text" class="cert-org" placeholder="e.g., Amazon Web Services">
      </div>
    </div>
  `;
  
  // HTML template for one "Activity" item
  const activityTemplate = `
    <button type="button" class="btn-remove">&times;</button>
    <div class="input-group">
      <label>Activity / Role</label>
      <input type="text" class="act-name" placeholder="e.g., President, Coding Club">
    </div>
    <div class="input-group">
      <label>Description</label>
      <textarea class="act-desc" placeholder="What you did..."></textarea>
    </div>
  `;

  // Initialize all dynamic sections
  setupDynamicSection('add-experience', 'experience-list', experienceTemplate);
  setupDynamicSection('add-project', 'project-list', projectTemplate);
  setupDynamicSection('add-certification', 'certification-list', certificationTemplate);
  setupDynamicSection('add-activity', 'activity-list', activityTemplate);


  // --- 4. Form Submission Logic ---
  const profileForm = document.getElementById('profileForm');

  profileForm.addEventListener('submit', function(event) {
    event.preventDefault();
    
    const profileData = {};

    // 1. Get Basic Details
    profileData.details = {
      fullName: document.getElementById('fullName').value,
      jobTitle: document.getElementById('jobTitle').value,
      mailId: document.getElementById('mailId').value,
      linkedin: document.getElementById('linkedin').value
    };

    // 2. Get Skillset
    profileData.skillset = [];
    document.querySelectorAll('.skill-tag').forEach(tag => {
      // tag.firstChild.textContent gets just the name, ignoring the 'x'
      profileData.skillset.push(tag.firstChild.textContent);
    });

    // 3. Get Experience
    profileData.experience = [];
    document.querySelectorAll('#experience-list .dynamic-item').forEach(item => {
      profileData.experience.push({
        title: item.querySelector('.exp-title').value,
        company: item.querySelector('.exp-company').value,
        startDate: item.querySelector('.exp-start').value,
        endDate: item.querySelector('.exp-end').value,
        description: item.querySelector('.exp-desc').value
      });
    });

    // --- MODIFIED LOGIC ---
    // 4. Get Projects
    profileData.projects = [];
    document.querySelectorAll('#project-list .dynamic-item').forEach(item => {
      profileData.projects.push({
        title: item.querySelector('.proj-title').value,
        description: item.querySelector('.proj-desc').value,
        technologies: item.querySelector('.proj-tech').value,
        // Added the link field
        githubLink: item.querySelector('.proj-link').value 
      });
    });
    // --- END OF MODIFIED LOGIC ---

    // 5. Get Certifications
    profileData.certifications = [];
    document.querySelectorAll('#certification-list .dynamic-item').forEach(item => {
      profileData.certifications.push({
        name: item.querySelector('.cert-name').value,
        organization: item.querySelector('.cert-org').value
      });
    });
    
    // 6. Get Activities
    profileData.extracurricular = [];
    document.querySelectorAll('#activity-list .dynamic-item').forEach(item => {
      profileData.extracurricular.push({
        name: item.querySelector('.act-name').value,
        description: item.querySelector('.act-desc').value
      });
    });

    // Display the collected data (for testing)
    console.log(JSON.stringify(profileData, null, 2));
    alert('Profile Saved! Check the console (F12) to see the collected data.');
    
    // In a real app, you would send this 'profileData' object to your server.
  });
});