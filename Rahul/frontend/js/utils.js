const API_BASE = 'http://127.0.0.1:5000';

async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('smartSocietyToken');
    const headers = options.headers || {};

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        method: options.method || 'GET',
        headers: headers,
        body: options.body instanceof FormData ? options.body : (options.body ? JSON.stringify(options.body) : null)
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);

        if (response.status === 401) {
            clearCurrentUser();
            window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html';
            throw new Error('Session expired. Please login again.');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
            let message = errorData.detail || `Request failed with status ${response.status}`;
            
            // Handle marshmallow validation errors
            if (errorData.errors) {
                const errors = Object.values(errorData.errors).flat();
                message = errors.join(' ');
            }
            
            // Handle flask-restx field-level validation errors
            if (errorData.message && typeof errorData.message === 'object') {
                const fieldErrors = Object.values(errorData.message).flat();
                message = fieldErrors.join(' ');
            }
            
            // Override with specific friendly messages based on HTTP status
            if (response.status === 400) {
                message = errorData.message || errorData.detail || message;
            } else if (response.status === 401) {
                message = 'Your session has expired. Please log in again.';
            } else if (response.status === 403) {
                message = 'You do not have permission to perform this action.';
            } else if (response.status === 404) {
                message = 'The requested resource was not found.';
            } else if (response.status >= 500) {
                message = 'Server error. Please try again later.';
            }
            throw new Error(message);
        }

        if (response.status === 204) return null;
        return await response.json();
    } catch (err) {
        let message = err.message;
        if (message === 'Failed to fetch') {
            message = 'Unable to connect to the server. Please check your connection.';
        } else if (err instanceof TypeError || message.includes('NetworkError') || message.includes('network')) {
            message = 'Network error. Please check your connection and try again.';
        }
        showToast(message, 'error');
        throw err;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    if (!toast) return;
    toast.className = 'fixed bottom-6 right-6 z-50 flex items-center px-4 py-3 rounded-md shadow-lg border ' + (type === 'error' ? 'bg-white border-rose-200 text-rose-800' : 'bg-slate-900 border-slate-800 text-white');
    toastMsg.textContent = message;
    toast.classList.remove('hidden');
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => { toast.classList.add('hidden'); }, 3500);
}

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('smartSocietyUser'));
    } catch { return null; }
}

function setCurrentUser(user, token) {
    localStorage.setItem('smartSocietyUser', JSON.stringify(user));
    if (token) localStorage.setItem('smartSocietyToken', token);
}

function clearCurrentUser() {
    localStorage.removeItem('smartSocietyUser');
    localStorage.removeItem('smartSocietyToken');
}

function requireAuth(requiredRole) {
    const user = getCurrentUser();
    const token = localStorage.getItem('smartSocietyToken');

    if (!user || !token) {
        window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html';
        return null;
    }
    if (requiredRole && user.role.toUpperCase() !== requiredRole.toUpperCase()) {
        goHome();
        return null;
    }
    return user;
}

// Re-validates the session against the server (GET /auth/profile) and
// refreshes the cached user with authoritative data (role, flat_number,
// etc). Fire-and-forget: keeps the cached user as a fast first paint,
// then upgrades it once the server responds. apiCall() already redirects
// to login on a 401, so no separate expiry handling is needed here.
async function refreshUserProfile(userRef, requiredRole) {
    try {
        const response = await apiCall('/auth/profile');
        if (response && response.user) {
            if (requiredRole && response.user.role.toUpperCase() !== requiredRole.toUpperCase()) {
                goHome();
                return;
            }
            setCurrentUser(response.user);
            if (userRef) userRef.value = response.user;
        }
    } catch (err) {
        // Network/server error - keep working off the cached user.
    }
}

function logout() {
    clearCurrentUser();
    window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html';
}

function goHome() {
    const user = getCurrentUser();
    if (!user) { 
        window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html'; 
        return; 
    }
    const role = user.role.toUpperCase();
    if (role === 'ADMIN') window.location.href = 'dashboard-admin.html';
    else if (role === 'STAFF') window.location.href = 'dashboard-staff.html';
    else window.location.href = 'dashboard-resident.html';
}

function viewComplaint(id, returnPage) {
    window.location.href = (window.location.pathname.includes('/static/') ? '' : 'static/') + 'complaint-details.html?id=' + id + (returnPage ? '&return=' + encodeURIComponent(returnPage) : '');
}