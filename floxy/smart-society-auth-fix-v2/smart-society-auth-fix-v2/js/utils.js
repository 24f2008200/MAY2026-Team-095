const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:5000'
    : 'https://smart-society-backend-2dqe.onrender.com';

// Uploaded file URLs come back from the backend as relative paths
// (e.g. "/uploads/abc123_photo.jpg"). They need the API origin prefixed
// to be loadable from the frontend, which is served from a different
// origin/port than the API.
function resolveFileUrl(path) {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    return `${API_BASE}${path}`;
}

const API_FIELD_LABELS = {
    name: 'Name',
    first_name: 'First name',
    last_name: 'Last name',
    email: 'Email address',
    mobile_number: 'Mobile number',
    mobile: 'Mobile number',
    flat_number: 'Flat number',
    flat: 'Flat number',
    building: 'Building',
    password: 'Password'
};

function formatFieldValidationMessage(field, value) {
    const label = API_FIELD_LABELS[field] || String(field || '')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
    const raw = Array.isArray(value) ? value.filter(Boolean).join(' ') : String(value || '').trim();
    if (!raw) return '';

    const betweenMatch = raw.match(/length must be between\s+(\d+)\s+and\s+(\d+)/i);
    if (betweenMatch) {
        return `${label} must be between ${betweenMatch[1]} and ${betweenMatch[2]} characters.`;
    }

    const minMatch = raw.match(/shorter than minimum length\s+(\d+)|length must be at least\s+(\d+)/i);
    if (minMatch) {
        const min = minMatch[1] || minMatch[2];
        return `${label} must be at least ${min} characters.`;
    }

    const maxMatch = raw.match(/longer than maximum length\s+(\d+)|length must be at most\s+(\d+)/i);
    if (maxMatch) {
        const max = maxMatch[1] || maxMatch[2];
        return `${label} must be at most ${max} characters.`;
    }

    // If the server already names the field, don't repeat it.
    if (raw.toLowerCase().startsWith(label.toLowerCase())) return raw;
    return `${label}: ${raw}`;
}

function extractFieldErrors(container) {
    if (!container || typeof container !== 'object' || Array.isArray(container)) return '';
    const messages = Object.entries(container)
        .map(([field, value]) => formatFieldValidationMessage(field, value))
        .filter(Boolean);
    return messages.join(' ');
}

function extractApiMessage(errorData) {
    if (!errorData || typeof errorData !== 'object') return '';

    const errorsMessage = extractFieldErrors(errorData.errors);
    if (errorsMessage) return errorsMessage;

    if (errorData.message && typeof errorData.message === 'object') {
        const message = extractFieldErrors(errorData.message);
        if (message) return message;
    }

    if (typeof errorData.message === 'string' && errorData.message.trim()) {
        return errorData.message.trim();
    }

    if (typeof errorData.detail === 'string' && errorData.detail.trim()) {
        return errorData.detail.trim();
    }

    return '';
}

function friendlyHttpMessage(status, serverMessage = '') {
    // Never expose raw HTTP codes (e.g. "Request failed with status 409")
    // to end users. Prefer a useful server message when one exists.
    if (serverMessage && !/^request failed with status\s+\d+/i.test(serverMessage)) {
        return serverMessage;
    }

    switch (status) {
        case 400:
            return 'Please check the information you entered and try again.';
        case 401:
            return 'Authentication failed. Please check your details and try again.';
        case 403:
            return 'You do not have permission to perform this action.';
        case 404:
            return 'The requested information could not be found.';
        case 409:
            return 'This information is already in use. Please review your details and try again.';
        case 422:
            return 'Some of the information entered is invalid. Please review it and try again.';
        case 429:
            return 'Too many attempts. Please wait a moment and try again.';
        default:
            return status >= 500
                ? 'The server is temporarily unavailable. Please try again later.'
                : 'Something went wrong. Please try again.';
    }
}

async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('smartSocietyToken');
    const headers = { ...(options.headers || {}) };
    const suppressErrorToast = Boolean(options.suppressErrorToast);

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        method: options.method || 'GET',
        headers,
        body: options.body instanceof FormData ? options.body : (options.body ? JSON.stringify(options.body) : null)
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);

        if (response.status === 401 && token) {
            clearCurrentUser();
            window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html';
            const sessionError = new Error('Your session has expired. Please sign in again.');
            sessionError.status = 401;
            throw sessionError;
        }

        if (!response.ok) {
            let errorData = {};
            const responseText = await response.text().catch(() => '');
            if (responseText) {
                try {
                    errorData = JSON.parse(responseText);
                } catch {
                    // Some backends/proxies return plain text or an HTML error page.
                    // Do not surface that raw content to the user.
                    errorData = {};
                }
            }

            const serverMessage = extractApiMessage(errorData);
            const error = new Error(friendlyHttpMessage(response.status, serverMessage));
            error.status = response.status;
            error.data = errorData;
            throw error;
        }

        if (response.status === 204) return null;

        const text = await response.text();
        if (!text) return null;
        try {
            return JSON.parse(text);
        } catch {
            return text;
        }
    } catch (err) {
        let normalizedError = err;

        if (err instanceof TypeError || err.message === 'Failed to fetch' || /networkerror|network request failed/i.test(err.message || '')) {
            normalizedError = new Error('Unable to connect to the server. Please check your connection and try again.');
            normalizedError.status = 0;
        }

        if (!suppressErrorToast && typeof showToast === 'function') {
            showToast(normalizedError.message || 'Something went wrong. Please try again.', 'error');
        }

        throw normalizedError;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    if (!toast || !toastMsg) return;

    toast.className = 'fixed bottom-6 right-6 z-50 flex items-center px-4 py-3 rounded-md shadow-lg border ' +
        (type === 'error' ? 'bg-white border-rose-200 text-rose-800' : 'bg-slate-900 border-slate-800 text-white');
    toastMsg.textContent = message;
    toast.classList.remove('hidden');
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => { toast.classList.add('hidden'); }, 3500);
}

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('smartSocietyUser'));
    } catch {
        return null;
    }
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

    if (requiredRole && String(user.role || '').toUpperCase() !== requiredRole.toUpperCase()) {
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
            if (requiredRole && String(response.user.role || '').toUpperCase() !== requiredRole.toUpperCase()) {
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

    const role = String(user.role || '').toUpperCase();
    if (role === 'ADMIN') window.location.href = 'dashboard-admin.html';
    else if (role === 'STAFF') window.location.href = 'dashboard-staff.html';
    else window.location.href = 'dashboard-resident.html';
}

function viewComplaint(id, returnPage) {
    window.location.href = (window.location.pathname.includes('/static/') ? '' : 'static/') +
        'complaint-details.html?id=' + encodeURIComponent(id) +
        (returnPage ? '&return=' + encodeURIComponent(returnPage) : '');
}
