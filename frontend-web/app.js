/* ═══════════════════════════════════════════════════════════════════════════
   AI Agriculture Assistant — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════════════════ */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://aiagriiii-3.onrender.com'; // Render backend URL

// ─── State ──────────────────────────────────────────────────────────────────

let authToken = localStorage.getItem('agri_token') || '';
let currentUser = null;
let selectedFile = null;
let statesDistricts = {};

// ─── Utility Functions ──────────────────────────────────────────────────────

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3500);
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

async function apiFetch(endpoint, options = {}) {
    const headers = { ...options.headers };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    if (!(options.body instanceof FormData) && options.body) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            handleLogout();
            showToast('Session expired. Please log in again.', 'error');
            return null;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Something went wrong');
        }

        return data;
    } catch (error) {
        if (error.message === 'Failed to fetch') {
            showToast('Cannot connect to server. Is the backend running?', 'error');
        } else {
            showToast(error.message, 'error');
        }
        throw error;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTHENTICATION
// ═══════════════════════════════════════════════════════════════════════════

function showLogin() {
    document.getElementById('login-form').classList.add('active');
    document.getElementById('register-form').classList.remove('active');
}

function showRegister() {
    document.getElementById('login-form').classList.remove('active');
    document.getElementById('register-form').classList.add('active');
}

function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const eyeOpen = btn.querySelector('.eye-open');
    const eyeClosed = btn.querySelector('.eye-closed');

    if (input.type === 'password') {
        input.type = 'text';
        eyeOpen.style.display = 'none';
        eyeClosed.style.display = 'block';
    } else {
        input.type = 'password';
        eyeOpen.style.display = 'block';
        eyeClosed.style.display = 'none';
    }
}

async function handleLogin() {
    const phone = document.getElementById('login-phone').value.trim();
    const password = document.getElementById('login-password').value;

    if (!phone || !password) {
        showToast('Please enter phone number and password', 'error');
        return;
    }

    showLoading();
    try {
        const data = await apiFetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ phone, password }),
        });

        if (data && data.access_token) {
            authToken = data.access_token;
            localStorage.setItem('agri_token', authToken);
            showToast('Login successful! 🎉', 'success');
            await loadProfile();
            showAppScreen();
        }
    } catch (e) {
        // Error already shown via toast
    }
    hideLoading();
}

async function handleRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const password = document.getElementById('reg-password').value;
    const village = document.getElementById('reg-village').value.trim();
    const state = document.getElementById('reg-state').value.trim();
    const language = document.getElementById('reg-language').value;

    if (!name || !phone || !password) {
        showToast('Name, phone, and password are required', 'error');
        return;
    }

    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }

    showLoading();
    try {
        const data = await apiFetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, phone, password, village, state, language }),
        });

        if (data) {
            showToast('Account created! Please sign in.', 'success');
            showLogin();
            document.getElementById('login-phone').value = phone;
        }
    } catch (e) {
        // Error shown via toast
    }
    hideLoading();
}

function applyProfilePic() {
    const picData = localStorage.getItem('agri_profile_pic');
    const avatar = document.getElementById('user-avatar');
    const preview = document.getElementById('profile-pic-preview');
    if (picData) {
        avatar.style.backgroundImage = `url(${picData})`;
        avatar.textContent = '';
        if (preview) {
            preview.style.backgroundImage = `url(${picData})`;
            preview.textContent = '';
        }
    } else {
        avatar.style.backgroundImage = 'none';
        if (currentUser) {
            avatar.textContent = currentUser.name.charAt(0).toUpperCase();
            if (preview) {
                preview.style.backgroundImage = 'none';
                preview.textContent = currentUser.name.charAt(0).toUpperCase();
            }
        }
    }
}

async function loadProfile() {
    try {
        const data = await apiFetch('/auth/profile');
        if (data) {
            currentUser = data;
            document.getElementById('user-greeting').textContent = `Hello, ${data.name}`;
            applyProfilePic();

            const hour = new Date().getHours();
            let greeting = 'Good Evening';
            if (hour < 12) greeting = 'Good Morning';
            else if (hour < 17) greeting = 'Good Afternoon';
            
            const welcomeMsg = document.getElementById('welcome-msg');
            if (welcomeMsg) welcomeMsg.textContent = `${greeting}, ${data.name}! 🌅`;

            // Populate profile form
            document.getElementById('prof-name').value = data.name || '';
            document.getElementById('prof-phone').value = data.phone || '';
            document.getElementById('prof-village').value = data.village || '';
            document.getElementById('prof-district').value = data.district || '';
            document.getElementById('prof-state').value = data.state || '';
            if (data.language) {
                document.getElementById('prof-language').value = data.language;
            }
        }
    } catch (e) {
        // silently fail
    }
}

async function handleProfileUpdate() {
    const name = document.getElementById('prof-name').value.trim();
    const village = document.getElementById('prof-village').value.trim();
    const district = document.getElementById('prof-district').value.trim();
    const state = document.getElementById('prof-state').value.trim();
    const language = document.getElementById('prof-language').value;

    if (!name) {
        showToast('Name is required', 'error');
        return;
    }

    showLoading();
    try {
        const data = await apiFetch('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify({ name, village, district, state, language }),
        });

        if (data) {
            showToast('Profile updated successfully! 🎉', 'success');
            await loadProfile();
        }
    } catch (e) {
        // Error shown via toast
    }
    hideLoading();
}

function handleProfilePicSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
        showToast('Please select a JPG or PNG image', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const base64Str = e.target.result;
        localStorage.setItem('agri_profile_pic', base64Str);
        applyProfilePic();
        showToast('Profile picture updated!', 'success');
    };
    reader.readAsDataURL(file);
}

function handleLogout() {
    authToken = '';
    currentUser = null;
    localStorage.removeItem('agri_token');
    document.getElementById('auth-screen').classList.add('active');
    document.getElementById('app-screen').classList.remove('active');
    showToast('Logged out successfully', 'info');
}

function showAppScreen() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
    initializeWeatherDropdowns();
    navigate('dashboard');
}

// ═══════════════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════

const pageTitles = {
    dashboard: 'Dashboard',
    disease: 'Disease Detection',
    weather: 'Weather Alerts',
    fertilizer: 'Fertilizer Recommendation',
    market: 'Market Prices',
    chat: 'AI Chat Assistant',
    profile: 'My Profile',
};

function navigate(page) {
    // Update active page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');

    // Update nav items
    document.querySelectorAll('.nav-item[data-page]').forEach(n => n.classList.remove('active'));
    const activeNav = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (activeNav) activeNav.classList.add('active');

    // Update title
    document.getElementById('page-title').textContent = pageTitles[page] || page;

    closeSidebar();

    // Auto-fetch data for certain pages
    if (page === 'market') fetchMarketPrices();
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (backdrop) backdrop.classList.remove('active');
    document.body.classList.remove('sidebar-open');
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const isOpen = sidebar.classList.toggle('open');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (backdrop) backdrop.classList.toggle('active', isOpen);
    document.body.classList.toggle('sidebar-open', isOpen);
}

// ═══════════════════════════════════════════════════════════════════════════
// DISEASE DETECTION
// ═══════════════════════════════════════════════════════════════════════════

function handleImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
        showToast('Please select a JPG or PNG image', 'error');
        return;
    }

    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('preview-image');
        preview.src = e.target.result;
        preview.style.display = 'block';
        document.getElementById('upload-placeholder').style.display = 'none';
        document.getElementById('predict-btn').disabled = false;
    };
    reader.readAsDataURL(file);
}

async function handlePredict() {
    if (!selectedFile) {
        showToast('Please upload an image first', 'error');
        return;
    }

    showLoading();
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const data = await apiFetch('/predict', {
            method: 'POST',
            body: formData,
        });

        if (data) {
            displayPredictionResult(data);
            loadPredictionHistory();
        }
    } catch (e) {
        // Error shown via toast
    }
    hideLoading();
}

function displayPredictionResult(data) {
    const resultSection = document.getElementById('prediction-result');
    resultSection.style.display = 'block';

    const pred = data.prediction;
    const rec = data.recommendation;

    document.getElementById('result-confidence').textContent = `${pred.confidence}%`;
    document.getElementById('result-disease').textContent = pred.disease;

    let detailsHTML = '';
    if (rec) {
        if (rec.description) detailsHTML += `<h4>📋 Description</h4><p>${rec.description}</p>`;
        if (rec.cause) detailsHTML += `<h4>🔍 Cause</h4><p>${rec.cause}</p>`;
        if (rec.symptoms) detailsHTML += `<h4>🩺 Symptoms</h4><p>${rec.symptoms}</p>`;
        if (rec.organic_treatment) detailsHTML += `<h4>🌿 Organic Treatment</h4><p>${rec.organic_treatment}</p>`;
        if (rec.chemical_treatment) detailsHTML += `<h4>🧪 Chemical Treatment</h4><p>${rec.chemical_treatment}</p>`;
        if (rec.prevention) detailsHTML += `<h4>🛡️ Prevention</h4><p>${rec.prevention}</p>`;
    } else {
        detailsHTML = '<p style="color:var(--text-muted)">No detailed recommendation available for this disease.</p>';
    }

    document.getElementById('result-details').innerHTML = detailsHTML;

    // Scroll to result
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function loadPredictionHistory() {
    try {
        const data = await apiFetch('/predict/history');
        if (data && data.length > 0) {
            const container = document.getElementById('prediction-history');
            container.innerHTML = data.map(p => `
                <div class="history-item">
                    <div class="disease-name">${p.disease}</div>
                    <div class="confidence">Confidence: ${p.confidence}%</div>
                    <div class="date">${new Date(p.created_at).toLocaleDateString()}</div>
                </div>
            `).join('');
        }
    } catch (e) {
        // silently fail
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// WEATHER
// ═══════════════════════════════════════════════════════════════════════════

async function initializeWeatherDropdowns() {
    try {
        const response = await fetch('states_districts.json');
        statesDistricts = await response.json();
        
        const stateSelect = document.getElementById('weather-state');
        stateSelect.innerHTML = '<option value="">-- Choose State --</option>';
        
        Object.keys(statesDistricts.states).sort().forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
        
        // Set default state to Andhra Pradesh
        stateSelect.value = 'Andhra Pradesh';
        updateWeatherDistricts();
    } catch (error) {
        console.error('Error loading states/districts:', error);
    }
}

function updateWeatherDistricts() {
    const stateSelect = document.getElementById('weather-state');
    const districtSelect = document.getElementById('weather-district');
    const selectedState = stateSelect.value;
    
    districtSelect.innerHTML = '<option value="">-- Choose District --</option>';
    
    if (selectedState && statesDistricts.states[selectedState]) {
        [...statesDistricts.states[selectedState]].sort().forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            districtSelect.appendChild(option);
        });
        
        // Set first district as default
        if (districtSelect.options.length > 1) {
            districtSelect.value = districtSelect.options[1].value;
        }
    }
}

async function fetchWeather() {
    const district = document.getElementById('weather-district').value.trim();
    if (!district) {
        showToast('Please select a district', 'error');
        return;
    }

    showLoading();
    try {
        const data = await apiFetch(`/weather?city=${encodeURIComponent(district)}`);
        if (data) {
            displayWeather(data);
        }
    } catch (e) {
        // Error shown via toast
    }
    hideLoading();
}

let weatherOverviewChartInstance = null;

function displayWeather(data) {
    document.getElementById('weather-dashboard').style.display = 'block';

    const curr = data.current;
    
    // Top Card Update
    document.getElementById('weather-temp-val').textContent = Math.round(curr.temperature);
    document.getElementById('weather-desc-main').textContent = curr.description.charAt(0).toUpperCase() + curr.description.slice(1);
    document.getElementById('weather-feels-like').textContent = `Feels like ${Math.round(curr.temperature + 2)}°`;
    document.getElementById('weather-humidity-dash').textContent = `${curr.humidity}%`;
    document.getElementById('weather-wind-dash').textContent = `${curr.wind_speed} km/h`;
    
    // Mock Data for Dashboard
    const now = new Date();
    document.getElementById('weather-current-time').textContent = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let rainProb = curr.rain_probability != null ? Math.round(curr.rain_probability * 100) : 0;
    let high = Math.round(curr.temperature + 5);
    document.getElementById('weather-summary-text').textContent = `There will be ${curr.description}. The high will be ${high}°.`;
    
    document.getElementById('weather-aqi').textContent = Math.floor(Math.random() * 50 + 20); // mock aqi
    document.getElementById('weather-visibility').textContent = (Math.random() * 5 + 5).toFixed(1) + ' km'; // mock visibility
    document.getElementById('weather-pressure').textContent = Math.floor(Math.random() * 30 + 1000) + ' mb'; // mock pressure

    // Update Map
    const district = document.getElementById('weather-district').value.trim();
    if (district) {
        const gMapUrl = `https://maps.google.com/maps?q=${encodeURIComponent(district + ' agriculture farmlands')}&t=k&z=11&ie=UTF8&iwloc=&output=embed`;
        document.getElementById('weather-map-iframe').src = gMapUrl;
    }

    // Alerts
    if(data.alerts && data.alerts.length > 0) {
        document.getElementById('weather-alerts-container').style.display = 'block';
        const alertsContainer = document.getElementById('weather-alerts');
        alertsContainer.innerHTML = data.alerts.map(alert => `
            <div class="alert-card severity-${alert.severity}">
                <div class="alert-type">${alert.alert_type.toUpperCase()}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        `).join('');
    } else {
        document.getElementById('weather-alerts-container').style.display = 'none';
    }

    // Generate Mock Hourly Data (based on current temp)
    const hourlyTemps = [];
    const hourlyLabels = [];
    const metricsHtml = [];
    let tempCursor = curr.temperature;
    
    for(let i=0; i<8; i++) {
        let hr = new Date(now.getTime() + i*2*60*60*1000);
        let hrStr = hr.toLocaleTimeString([], {hour: 'numeric', hour12: true});
        if(i===0) hrStr = "Now";
        hourlyLabels.push(hrStr);
        
        if(i>0) tempCursor += (Math.random() * 4 - 2); // Random walk
        hourlyTemps.push(Math.round(tempCursor));
        
        let rain = Math.max(0, rainProb + (Math.random() * 20 - 10));
        
        metricsHtml.push(`
            <div class="metric-col">
                <span class="time">${hrStr}</span>
                <span class="icon">☁️</span>
                <span class="val">${Math.round(rain)}%</span>
            </div>
        `);
    }
    
    document.getElementById('weather-hourly-metrics').innerHTML = metricsHtml.join('');
    
    // Generate simple graph
    const minTemp = Math.min(...hourlyTemps);
    const maxTemp = Math.max(...hourlyTemps);
    const tempRange = (maxTemp - minTemp) || 1;
    
    let graphHtml = '';
    for(let i=0; i<8; i++) {
        let heightPct = ((hourlyTemps[i] - minTemp + 2) / (tempRange + 4)) * 100;
        if(heightPct > 100) heightPct = 100;
        
        graphHtml += `
            <div class="graph-bar-wrapper">
                <div class="graph-val">${hourlyTemps[i]}°</div>
                <div class="graph-bar" style="height: ${heightPct}%"></div>
            </div>
        `;
    }
    document.getElementById('weather-simple-graph').innerHTML = graphHtml;

    // Populate 7-day forecast mock
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    let scrollHtml = '';
    for(let i=0; i<7; i++) {
        let d = new Date(now.getTime() + i*24*60*60*1000);
        let dayName = i===0 ? 'Today' : days[d.getDay()];
        let dHigh = Math.round(curr.temperature + (Math.random() * 6 - 2));
        let dLow = Math.round(dHigh - 8 - Math.random() * 4);
        let icon = dHigh > 35 ? '☀️' : (rainProb > 40 ? '🌧️' : '⛅');
        scrollHtml += `
            <div class="day-card ${i===0 ? 'active' : ''}">
                <div class="day-name">${dayName}</div>
                <div class="day-icon">${icon}</div>
                <div class="day-temp">${dHigh}°</div>
                <div class="day-temp-low">${dLow}°</div>
            </div>
        `;
    }
    document.getElementById('weather-7day-scroll').innerHTML = scrollHtml;

    // Populate Calendar mock
    let calHtml = '';
    const daysInMonth = 30; // approx
    for(let i=1; i<=daysInMonth; i++) {
        let isToday = i === now.getDate();
        let cHigh = Math.round(curr.temperature + (Math.random() * 8 - 4));
        let cLow = cHigh - 10;
        let icon = cHigh > 35 ? '☀️' : (cHigh < 25 ? '🌧️' : '⛅');
        calHtml += `
            <div class="cal-day ${isToday ? 'today' : ''}">
                <div class="cal-date">${i}</div>
                <div class="cal-icon">${icon}</div>
                <div class="cal-temps"><span class="cal-high">${cHigh}°</span><span class="cal-low">${cLow}°</span></div>
            </div>
        `;
    }
    document.getElementById('weather-calendar-grid').innerHTML = calHtml;
    
    // Reset view
    document.getElementById('wtab-overview').style.display = 'block';
    document.getElementById('wtab-monthly').style.display = 'none';
    document.getElementById('weather-7day-scroll').style.display = 'flex';
    document.querySelector('.w-tab[data-wtab="overview"]').classList.add('active');
}

// Tab Switching
document.addEventListener('click', function(e) {
    if(e.target.classList.contains('w-tab')) {
        document.querySelectorAll('.w-tab').forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        if(e.target.getAttribute('data-wtab') === 'overview') {
            document.getElementById('wtab-overview').style.display = 'block';
            document.getElementById('wtab-monthly').style.display = 'none';
            document.getElementById('weather-7day-scroll').style.display = 'flex';
        } else {
            showToast('Showing ' + e.target.textContent + ' data');
        }
    }
});

function toggleWeatherMonthly() {
    document.getElementById('wtab-overview').style.display = 'none';
    document.getElementById('wtab-monthly').style.display = 'block';
    document.querySelectorAll('.w-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('weather-7day-scroll').style.display = 'none';
}

// ═══════════════════════════════════════════════════════════════════════════
// FERTILIZER
// ═══════════════════════════════════════════════════════════════════════════

async function fetchFertilizer() {
    const crop = document.getElementById('fert-crop').value;
    const soil_type = document.getElementById('fert-soil').value;
    const nitrogen = document.getElementById('fert-nitrogen').value || null;
    const phosphorus = document.getElementById('fert-phosphorus').value || null;
    const potassium = document.getElementById('fert-potassium').value || null;
    const moisture = document.getElementById('fert-moisture').value || null;
    const temperature = document.getElementById('fert-temp').value || null;

    showLoading();
    try {
        const body = { crop, soil_type };
        if (nitrogen) body.nitrogen = parseFloat(nitrogen);
        if (phosphorus) body.phosphorus = parseFloat(phosphorus);
        if (potassium) body.potassium = parseFloat(potassium);
        if (moisture) body.moisture = parseFloat(moisture);
        if (temperature) body.temperature = parseFloat(temperature);

        const data = await apiFetch('/fertilizer/recommend', {
            method: 'POST',
            body: JSON.stringify(body),
        });

        if (data) displayFertilizerResult(data);
    } catch (e) {
        // Error shown via toast
    }
    hideLoading();
}

function displayFertilizerResult(data) {
    document.getElementById('fertilizer-result').style.display = 'block';

    const container = document.getElementById('fert-recommendation');
    container.innerHTML = `
        <div class="fert-name">${data.recommended_fertilizer}</div>
        <div class="fert-detail-item">
            <h4>🌾 Crop</h4>
            <p>${data.crop} (${data.soil_type} soil)</p>
        </div>
        <div class="fert-detail-item">
            <h4>📦 Quantity</h4>
            <p>${data.quantity}</p>
        </div>
        <div class="fert-detail-item">
            <h4>📅 Application Schedule</h4>
            <p>${data.schedule}</p>
        </div>
        <div class="fert-detail-item">
            <h4>💡 Tips & Best Practices</h4>
            <ul class="fert-tips">
                ${data.tips.map(tip => `<li>${tip}</li>`).join('')}
            </ul>
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ═══════════════════════════════════════════════════════════════════════════
// MARKET PRICES
// ═══════════════════════════════════════════════════════════════════════════

async function fetchMarketPrices() {
    const crop = document.getElementById('market-crop-filter').value;
    const market = document.getElementById('market-name-filter').value;

    let query = '';
    if (crop) query += `crop=${encodeURIComponent(crop)}&`;
    if (market) query += `market=${encodeURIComponent(market)}&`;

    try {
        const data = await apiFetch(`/market-prices?${query}limit=100`);
        if (data) displayMarketPrices(data, crop, market);
    } catch (e) {
        // Error shown via toast
    }
}

function displayMarketPrices(data, filterCrop, filterMarket) {
    // Table
    const tbody = document.getElementById('market-tbody');
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No price data available</td></tr>';
    } else {
        tbody.innerHTML = data.map(p => `
            <tr>
                <td>${p.crop}</td>
                <td>${p.market}</td>
                <td class="price-cell">₹${p.price.toLocaleString()}</td>
                <td>${p.unit}</td>
                <td>${new Date(p.date).toLocaleDateString()}</td>
            </tr>
        `).join('');
    }

    // Trend cards — group by crop+market and show latest
    const groups = {};
    data.forEach(p => {
        const key = `${p.crop}-${p.market}`;
        if (!groups[key]) groups[key] = [];
        groups[key].push(p);
    });

    const trendsContainer = document.getElementById('market-trends');
    let trendsHTML = '';

    Object.values(groups).forEach(prices => {
        prices.sort((a, b) => new Date(b.date) - new Date(a.date));
        const latest = prices[0];
        const prev = prices.length > 1 ? prices[1] : null;
        let trend = 'stable';
        let changeText = '→ Stable';

        if (prev) {
            const change = ((latest.price - prev.price) / prev.price) * 100;
            if (change > 1) {
                trend = 'up';
                changeText = `↑ +${change.toFixed(1)}%`;
            } else if (change < -1) {
                trend = 'down';
                changeText = `↓ ${change.toFixed(1)}%`;
            }
        }

        trendsHTML += `
            <div class="trend-card">
                <div class="trend-crop">${latest.crop}</div>
                <div class="trend-market">${latest.market}</div>
                <div class="trend-price" style="color:var(--${trend === 'up' ? 'success' : trend === 'down' ? 'danger' : 'text-secondary'})">
                    ₹${latest.price.toLocaleString()}
                </div>
                <div class="trend-change ${trend}">${changeText}</div>
            </div>
        `;
    });

    trendsContainer.innerHTML = trendsHTML;

    // Compute Pie Chart Data
    const cropTotals = {};
    const cropCounts = {};
    const dateTotals = {};
    const dateCounts = {};

    data.forEach(p => {
        // For Pie Chart (by crop)
        if (!cropTotals[p.crop]) {
            cropTotals[p.crop] = 0;
            cropCounts[p.crop] = 0;
        }
        cropTotals[p.crop] += p.price;
        cropCounts[p.crop] += 1;

        // For Line Chart (by date)
        const d = new Date(p.date).toLocaleDateString();
        if (!dateTotals[d]) {
            dateTotals[d] = 0;
            dateCounts[d] = 0;
        }
        dateTotals[d] += p.price;
        dateCounts[d] += 1;
    });

    // Prepare Pie Chart
    const chartLabels = [];
    const chartData = [];
    const chartColors = [];
    const colors = ['#28a745', '#ffc107', '#17a2b8', '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c'];
    let colorIdx = 0;

    Object.keys(cropTotals).forEach(crop => {
        chartLabels.push(crop);
        chartData.push(Math.round(cropTotals[crop] / cropCounts[crop]));
        chartColors.push(colors[colorIdx % colors.length]);
        colorIdx++;
    });

    // Prepare Line Chart
    const sortedDates = Object.keys(dateTotals).sort((a,b) => new Date(a) - new Date(b));
    const lineLabels = sortedDates;
    const lineData = sortedDates.map(d => Math.round(dateTotals[d] / dateCounts[d]));

    const wrapper = document.getElementById('market-charts-wrapper');
    
    if (chartLabels.length > 0) {
        wrapper.style.display = 'grid';

        // Render Line Chart
        const ctxLine = document.getElementById('marketLineChart');
        if (window.marketLineChartInstance) window.marketLineChartInstance.destroy();
        window.marketLineChartInstance = new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: lineLabels,
                datasets: [{
                    label: 'Average Price Trend (₹)',
                    data: lineData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#e2e8f0' } },
                    title: { display: true, text: 'Price Trend Over Time', color: '#e2e8f0', font: { size: 16 } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#2a2e3f' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: '#2a2e3f' } }
                }
            }
        });

        // Render Pie Chart
        const ctxPie = document.getElementById('marketPieChart');
        if (window.marketPieChartInstance) window.marketPieChartInstance.destroy();
        window.marketPieChartInstance = new Chart(ctxPie, {
            type: 'pie',
            data: {
                labels: chartLabels,
                datasets: [{
                    data: chartData,
                    backgroundColor: chartColors,
                    borderWidth: 1,
                    borderColor: '#1a1d27'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#e2e8f0' } },
                    title: { display: true, text: 'Average Prices by Crop (₹)', color: '#e2e8f0', font: { size: 16 } }
                }
            }
        });
    } else {
        wrapper.style.display = 'none';
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// AI CHAT
// ═══════════════════════════════════════════════════════════════════════════

function sendSuggestion(text) {
    document.getElementById('chat-input').value = text;
    sendChat();
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const language = document.getElementById('chat-language').value;

    // Add user message bubble
    addChatMessage(message, 'user');
    input.value = '';

    try {
        const data = await apiFetch('/chat', {
            method: 'POST',
            body: JSON.stringify({ message, language }),
        });

        if (data) {
            addChatMessage(data.answer, 'bot');
        }
    } catch (e) {
        addChatMessage('Sorry, I couldn\'t process your question. Please check your connection and try again.', 'bot');
    }
}

function addChatMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const avatar = sender === 'bot' ? '🤖' : (currentUser ? currentUser.name.charAt(0) : '👤');

    // Convert markdown-like bold to HTML
    const formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${sender}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-bubble"><p>${formatted}</p></div>
    `;

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

async function init() {
    // Check for existing token
    if (authToken) {
        try {
            await loadProfile();
            if (currentUser) {
                showAppScreen();
                return;
            }
        } catch (e) {
            // Token expired / invalid
            authToken = '';
            localStorage.removeItem('agri_token');
        }
    }

    // Show auth screen
    document.getElementById('auth-screen').classList.add('active');
}

// Run on page load
document.addEventListener('DOMContentLoaded', () => {
    init();

    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            }
        });
    }, observerOptions);

    // Observe static animated elements
    document.querySelectorAll('.animate-on-scroll, .animate-pop, .animate-slide').forEach(el => {
        observer.observe(el);
    });

    // Make observer globally available for dynamically generated elements
    window.animationObserver = observer;
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
});

window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) closeSidebar();
});
