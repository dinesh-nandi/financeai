/**
 * FinanceAI - Authentication Module
 * Handles email/password and Web3 wallet auth, JWT storage, and route protection
 */

// API base URL (relative so it works on any host/port)
const API_BASE_URL = '/api';

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.getAttribute('content')) return meta.getAttribute('content');
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Check if user is authenticated
function isAuthenticated() {
    const token = localStorage.getItem('token');
    return token !== null && token !== '';
}

// Get current user data
function getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

// Update UI with user name
function getDisplayName(user) {
    if (!user) return 'User';
    var u = user.username || user.name || '';
    if (!u) return 'User';
    if (u.indexOf('wallet_0x') === 0) return '0x' + u.slice(9, 15) + '...' + u.slice(-4);
    return u;
}
function userNeedsUsername(user) {
    var u = (user && (user.username || user.name)) || '';
    return u.indexOf('wallet_') === 0;
}
function updateUserName() {
    const userNameElement = document.getElementById('user-name');
    if (userNameElement) {
        const user = getCurrentUser();
        userNameElement.textContent = 'Welcome, ' + getDisplayName(user);
    }
}

/**
 * Show modal to set display username (e.g. after wallet login when name is unknown).
 * @param {Object} options - { onSuccess: function(), onSkip: function(), title: string }
 * @returns {Promise<boolean>} Resolves true if username was set, false if skipped/closed.
 */
function showSetUsernameModal(options) {
    options = options || {};
    var onSuccess = options.onSuccess || function() {};
    var onSkip = options.onSkip || function() {};
    var title = options.title || 'Choose a display name';

    return new Promise(function(resolve) {
        var existing = document.getElementById('set-username-modal');
        if (existing) existing.remove();

        var overlay = document.createElement('div');
        overlay.id = 'set-username-modal';
        overlay.className = 'auth-modal-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-label', 'Set username');

        var box = document.createElement('div');
        box.className = 'auth-modal-box';

        var titleEl = document.createElement('h3');
        titleEl.className = 'auth-modal-title';
        titleEl.textContent = title;

        var desc = document.createElement('p');
        desc.className = 'auth-modal-desc';
        desc.textContent = 'Your wallet doesn\'t have a display name. Pick a username (letters, numbers, underscores, 3–30 characters).';

        var input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input';
        input.placeholder = 'e.g. trader_jane';
        input.autocomplete = 'username';
        input.maxLength = 30;

        var errEl = document.createElement('p');
        errEl.className = 'auth-modal-error';
        errEl.style.display = 'none';
        errEl.style.color = 'var(--accent-red, #ef4444)';
        errEl.style.fontSize = '13px';
        errEl.style.marginTop = '6px';

        var btnRow = document.createElement('div');
        btnRow.style.display = 'flex';
        btnRow.style.gap = '10px';
        btnRow.style.marginTop = '16px';

        var submitBtn = document.createElement('button');
        submitBtn.type = 'button';
        submitBtn.className = 'btn btn-primary';
        submitBtn.textContent = 'Save username';

        var skipBtn = document.createElement('button');
        skipBtn.type = 'button';
        skipBtn.className = 'btn btn-secondary';
        skipBtn.textContent = 'Skip for now';

        function closeModal() {
            overlay.remove();
        }

        submitBtn.addEventListener('click', function() {
            var username = (input.value || '').trim();
            if (username.length < 3) {
                errEl.textContent = 'Username must be at least 3 characters.';
                errEl.style.display = 'block';
                return;
            }
            if (username.length > 30) {
                errEl.textContent = 'Username must be 30 characters or fewer.';
                errEl.style.display = 'block';
                return;
            }
            if (!/^[a-zA-Z0-9_]+$/.test(username)) {
                errEl.textContent = 'Use only letters, numbers, and underscores.';
                errEl.style.display = 'block';
                return;
            }
            errEl.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving…';

            var headers = { 'Content-Type': 'application/json' };
            var token = localStorage.getItem('token');
            if (token) headers['Authorization'] = 'Bearer ' + token;
            var csrf = getCsrfToken();
            if (csrf) headers['X-CSRFToken'] = csrf;

            fetch(API_BASE_URL + '/auth/profile/', {
                method: 'PATCH',
                headers: headers,
                body: JSON.stringify({ username: username }),
                credentials: 'same-origin'
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data && data.status === 'success' && data.data) {
                    var user = getCurrentUser();
                    if (user) {
                        user.username = data.data.username;
                        user.name = data.data.username;
                        localStorage.setItem('user', JSON.stringify(user));
                    }
                    updateUserName();
                    closeModal();
                    onSuccess();
                    resolve(true);
                } else {
                    errEl.textContent = (data && data.message) || 'Could not save username.';
                    errEl.style.display = 'block';
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Save username';
                }
            }).catch(function() {
                errEl.textContent = 'Network error. Try again.';
                errEl.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save username';
            });
        });

        skipBtn.addEventListener('click', function() {
            closeModal();
            onSkip();
            resolve(false);
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeModal();
                onSkip();
                resolve(false);
            }
        });

        btnRow.appendChild(submitBtn);
        btnRow.appendChild(skipBtn);
        box.appendChild(titleEl);
        box.appendChild(desc);
        box.appendChild(input);
        box.appendChild(errEl);
        box.appendChild(btnRow);
        overlay.appendChild(box);
        document.body.appendChild(overlay);
        input.focus();
    });
}

// Protect routes - redirect to login if not authenticated
function protectRoute() {
    if (!isAuthenticated()) {
        window.location.href = '/login/';
        return false;
    }
    updateUserName();
    return true;
}

// Login function (email + password -> JWT)
async function login(email, password) {
    try {
        email = (email || '').trim().toLowerCase();
        if (!email || !password) {
            return { success: false, error: 'Email and password are required.' };
        }
        const headers = { 'Content-Type': 'application/json' };
        const csrf = getCsrfToken();
        if (csrf) headers['X-CSRFToken'] = csrf;
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ email: email, password: password }),
            credentials: 'same-origin'
        });
        const rawText = await response.text();
        let data;
        try {
            data = rawText ? JSON.parse(rawText) : {};
        } catch (_) {
            return { success: false, error: 'Server returned an invalid response. Please try again.' };
        }

        if (!response.ok) {
            const msg = (data && data.message) || 'Invalid email or password.';
            return { success: false, error: msg };
        }
        if (data.status !== 'success' || !data.data) {
            return { success: false, error: (data && data.message) || 'Invalid response from server.' };
        }

        const { access, refresh, user } = data.data;
        localStorage.setItem('token', access);
        if (refresh) localStorage.setItem('refresh', refresh);
        const userForStorage = {
            id: user.id,
            name: (user.first_name && user.last_name) ? `${user.first_name} ${user.last_name}`.trim() : (user.username || ''),
            email: user.email || '',
            username: user.username || '',
            riskAppetite: user.profile && user.profile.risk_appetite,
            experienceLevel: user.profile && user.profile.experience_level
        };
        localStorage.setItem('user', JSON.stringify(userForStorage));
        return { success: true, user: userForStorage };
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: 'Network error. Please check your connection and try again.' };
    }
}

// Register function (name, email, password, risk, experience -> JWT)
async function register(name, email, password, riskAppetite, experienceLevel) {
    try {
        email = (email || '').trim().toLowerCase();
        if (!email || !password) {
            return { success: false, error: 'Email and password are required.' };
        }
        const parts = (name || '').trim().split(/\s+/);
        const firstName = parts[0] || '';
        const lastName = parts.slice(1).join(' ') || '';
        const username = (email || '').split('@')[0] || 'user' + Date.now();

        const headers = { 'Content-Type': 'application/json' };
        const csrf = getCsrfToken();
        if (csrf) headers['X-CSRFToken'] = csrf;

        const response = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                first_name: firstName,
                last_name: lastName,
                risk_appetite: riskAppetite || 'moderate',
                experience_level: experienceLevel || 'beginner'
            }),
            credentials: 'same-origin'
        });

        const rawText = await response.text();
        let data;
        try {
            data = rawText ? JSON.parse(rawText) : {};
        } catch (_) {
            return { success: false, error: 'Server returned an invalid response. Please try again.' };
        }

        if (!response.ok) {
            const msg = (data && (data.message || (data.detail && (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))))) || 'Registration failed.';
            return { success: false, error: msg };
        }
        if (data.status !== 'success' || !data.data) {
            return { success: false, error: (data && data.message) || 'Invalid response from server.' };
        }

        const { access, refresh, user } = data.data;
        localStorage.setItem('token', access);
        if (refresh) localStorage.setItem('refresh', refresh);
        const userForStorage = {
            id: user.id,
            name: ((user.first_name || '') + ' ' + (user.last_name || '')).trim() || (user.username || ''),
            email: user.email || '',
            username: user.username || '',
            riskAppetite: user.profile && user.profile.risk_appetite,
            experienceLevel: user.profile && user.profile.experience_level
        };
        localStorage.setItem('user', JSON.stringify(userForStorage));
        return { success: true, user: userForStorage };
    } catch (error) {
        console.error('Registration error:', error);
        return { success: false, error: 'Network error. Please check your connection and try again.' };
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login/';
}

// Get auth headers for API requests
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {})
    };
}

// Make authenticated API request
async function apiRequest(endpoint, options = {}) {
    const path = (endpoint.startsWith('/') ? endpoint : '/' + endpoint);
    const url = API_BASE_URL + path.replace(/^\/api/, '');
    const headers = getAuthHeaders();
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
        const csrf = getCsrfToken();
        if (csrf) headers['X-CSRFToken'] = csrf;
    }
    const config = {
        ...options,
        method: options.method || 'GET',
        headers: {
            ...headers,
            ...options.headers
        },
        credentials: options.credentials ?? 'same-origin'
    };
    
    try {
        const response = await fetch(url, config);
        
        if (response.status === 401) {
            // Token expired or invalid
            logout();
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', function() {
    // Update user name if authenticated
    if (isAuthenticated()) {
        updateUserName();
        // If wallet user without a real username, prompt to set one
        var user = getCurrentUser();
        if (userNeedsUsername(user)) {
            showSetUsernameModal({
                title: 'Choose a display name',
                onSuccess: function() { updateUserName(); },
                onSkip: function() {}
            });
        }
    }

    // Add logout functionality to any logout buttons
    const logoutButtons = document.querySelectorAll('[onclick="logout()"]');
    logoutButtons.forEach(btn => {
        btn.addEventListener('click', logout);
    });
});

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        isAuthenticated,
        getCurrentUser,
        login,
        register,
        logout,
        apiRequest,
        protectRoute,
        showSetUsernameModal,
        userNeedsUsername,
        updateUserName
    };
}
