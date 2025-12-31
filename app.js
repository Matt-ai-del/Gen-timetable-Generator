// DOM Elements
const authContainer = document.getElementById('authContainer');
const appContainer = document.getElementById('appContainer');
const loginForm = document.getElementById('loginFormElement');
const registerForm = document.getElementById('registerFormElement');
const usernameDisplay = document.getElementById('usernameDisplay');
const logoutBtn = document.getElementById('logoutBtn');
const generateBtn = document.getElementById('generateBtn');
const loadingIndicator = document.getElementById('loadingIndicator');

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        const tab = button.dataset.tab;
        
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Show corresponding content
        if (tab === 'login' || tab === 'register') {
            document.getElementById('loginForm').classList.toggle('active', tab === 'login');
            document.getElementById('registerForm').classList.toggle('active', tab === 'register');
        } else {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.toggle('active', content.id === `${tab}Tab`);
            });
        }
    });
});

// Authentication Functions
async function login(username, password) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.token);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

async function register(username, password) {
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        return response.ok;
    } catch (error) {
        console.error('Registration error:', error);
        return false;
    }
}

// Form Event Listeners
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (await login(username, password)) {
        usernameDisplay.textContent = username;
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
    } else {
        alert('Invalid credentials');
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    if (await register(username, password)) {
        alert('Registration successful! Please login.');
        document.querySelector('[data-tab="login"]').click();
    } else {
        alert('Registration failed. Username might already exist.');
    }
});

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('token');
    authContainer.classList.remove('hidden');
    appContainer.classList.add('hidden');
});

// Generate Timetable
generateBtn.addEventListener('click', async () => {
    const settings = {
        minHours: parseInt(document.getElementById('minHours').value),
        maxHours: parseInt(document.getElementById('maxHours').value),
        populationSize: parseInt(document.getElementById('populationSize').value),
        generations: parseInt(document.getElementById('generations').value),
        mutationRate: parseFloat(document.getElementById('mutationRate').value)
    };
    
    generateBtn.disabled = true;
    loadingIndicator.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            const timetable = await response.json();
            displayResults(timetable);
            document.querySelector('[data-tab="results"]').click();
        } else {
            alert('Failed to generate timetable');
        }
    } catch (error) {
        console.error('Generation error:', error);
        alert('An error occurred while generating the timetable');
    } finally {
        generateBtn.disabled = false;
        loadingIndicator.classList.add('hidden');
    }
});

// Display Results
function displayResults(timetable) {
    const resultsContainer = document.querySelector('.results-container');
    resultsContainer.innerHTML = '';
    
    // Room-wise Timetable
    const roomSection = document.createElement('div');
    roomSection.innerHTML = `
        <h2>Room-wise Timetable</h2>
        <div class="timetable-grid"></div>
    `;
    resultsContainer.appendChild(roomSection);
    
    // Faculty-wise Timetable
    const facultySection = document.createElement('div');
    facultySection.innerHTML = `<h2>Faculty Schedules</h2>`;
    // Render lecturer statistics if present
    if (timetable.lecturer_statistics && Array.isArray(timetable.lecturer_statistics)) {
        timetable.lecturer_statistics.forEach(lecturer => {
            const lecturerDiv = document.createElement('div');
            lecturerDiv.className = 'lecturer-statistics';
            lecturerDiv.innerHTML = `
                <h3>${lecturer.lecturer}</h3>
                <p><strong>Total Hours:</strong> ${lecturer.scheduled_hours} / ${lecturer.required_hours}</p>
                <p><strong>Status:</strong> ${lecturer.status === 'complete' ? '✅' : '❌'}</p>
            `;
            // List slots with student groups
            if (lecturer.slots && lecturer.slots.length > 0) {
                const slotsList = document.createElement('ul');
                lecturer.slots.forEach(slot => {
                    const slotItem = document.createElement('li');
                    slotItem.innerHTML = `
                        <strong>${slot.day} ${slot.slot}</strong>: ${slot.module} in ${slot.room}
                        ${slot.groups && slot.groups.length > 0 ? `<br/><span style='color:#444;'>Groups: ${slot.groups.join(', ')}</span>` : ''}
                    `;
                    slotsList.appendChild(slotItem);
                });
                lecturerDiv.appendChild(slotsList);
            }
            facultySection.appendChild(lecturerDiv);
        });
    } else {
        facultySection.innerHTML += `<div>No lecturer statistics available.</div>`;
    }
    resultsContainer.appendChild(facultySection);
    
    // Course Coverage Report
    const courseSection = document.createElement('div');
    courseSection.innerHTML = `
        <h2>Course Coverage Report</h2>
        <div class="report-grid"></div>
    `;
    resultsContainer.appendChild(courseSection);
}

// Check Authentication Status
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
    } else {
        authContainer.classList.remove('hidden');
        appContainer.classList.add('hidden');
    }
}

// Initialize
checkAuth(); 