// js/utils.js

// Toast
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

// Get current user from localStorage
function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('smartSocietyUser'));
    } catch { return null; }
}

function setCurrentUser(user) {
    localStorage.setItem('smartSocietyUser', JSON.stringify(user));
}

function clearCurrentUser() {
    localStorage.removeItem('smartSocietyUser');
}

// Require authentication and optional role
function requireAuth(requiredRole) {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = 'index.html';
        return null;
    }
    if (requiredRole && user.role !== requiredRole) {
        // Redirect to appropriate home
        if (user.role === 'Admin') window.location.href = 'dashboard-admin.html';
        else if (user.role === 'Staff') window.location.href = 'dashboard-staff.html';
        else window.location.href = 'dashboard-resident.html';
        return null;
    }
    return user;
}

function logout() {
    clearCurrentUser();
    window.location.href = 'index.html';
}

function goHome() {
    const user = getCurrentUser();
    if (!user) { window.location.href = 'index.html'; return; }
    if (user.role === 'Admin') window.location.href = 'dashboard-admin.html';
    else if (user.role === 'Staff') window.location.href = 'dashboard-staff.html';
    else window.location.href = 'dashboard-resident.html';
}

function getFormattedDate() {
    const now = new Date();
    const d = now.getDate().toString().padStart(2, '0');
    const m = now.toLocaleString('en-us', { month: 'short' });
    const y = now.getFullYear();
    const h = now.getHours().toString().padStart(2, '0');
    const min = now.getMinutes().toString().padStart(2, '0');
    return `${d} ${m} ${y}, ${h}:${min}`;
}

// View complaint (redirects to details)
function viewComplaint(id, returnPage) {
    window.location.href = 'complaint-details.html?id=' + id + (returnPage ? '&return=' + encodeURIComponent(returnPage) : '');
}

// Withdraw complaint (called from details)
function withdrawComplaint(id) {
    const comp = store.complaints.find(c => c.id === id);
    if (comp && ['Open','Reopened'].includes(comp.status)) {
        comp.status = 'Closed';
        comp.history.push({ date: getFormattedDate(), action: 'Withdrawn by Resident' });
        showToast('Request has been withdrawn.');
        setTimeout(() => window.history.back(), 800);
    }
}

// Update unread badge on all pages
function updateUnreadBadge() {
    const count = store.notifications.filter(n => !n.read).length;
    const badge = document.getElementById('unreadBadge');
    const countEl = document.getElementById('unreadCount');
    if (badge) {
        if (count > 0) {
            badge.classList.remove('hidden');
            if (countEl) {
                countEl.textContent = count;
                countEl.classList.remove('hidden');
            }
        } else {
            badge.classList.add('hidden');
            if (countEl) countEl.classList.add('hidden');
        }
    }
}

// Initialize unread badge on page load (call after DOM ready)
document.addEventListener('DOMContentLoaded', function() {
    updateUnreadBadge();
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const dropdown = document.getElementById('notificationDropdown');
        const bellBtn = e.target.closest('[onclick*="toggleNotifications"]');
        if (dropdown && !bellBtn && !e.target.closest('#notificationDropdown')) {
            dropdown.classList.add('hidden');
        }
    });
});

// Toggle notification dropdown
function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    if (!dropdown) return;
    dropdown.classList.toggle('hidden');
    if (!dropdown.classList.contains('hidden')) {
        loadNotificationDropdown();
    }
}

// Load recent notifications into dropdown
function loadNotificationDropdown() {
    const list = document.getElementById('notifDropdownList');
    if (!list) return;
    const recent = store.notifications.slice(0, 5);
    if (recent.length === 0) {
        list.innerHTML = '<div class="px-4 py-6 text-center text-slate-500 text-sm"><i class="fas fa-inbox text-2xl opacity-50 block mb-2"></i> No notifications</div>';
        return;
    }
    list.innerHTML = recent.map(notif => {
        const icon = notif.type === 'alert' ? 'fa-exclamation-circle text-rose-500' : 'fa-info-circle text-blue-500';
        return `<div class="px-4 py-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0">
            <div class="flex gap-3">
                <i class="fas ${icon} text-lg flex-shrink-0 mt-0.5"></i>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-bold text-slate-900 line-clamp-2">${notif.title || 'Notification'}</p>
                    <p class="text-xs text-slate-600 mt-1 line-clamp-2">${notif.message || ''}</p>
                    <p class="text-[11px] text-slate-500 mt-1.5">${new Date(notif.date).toLocaleString().split(',')[1] || notif.date}</p>
                </div>
            </div>
        </div>`;
    }).join('');
}