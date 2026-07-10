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
        window.location.href = window.location.pathname.includes('/static/') ? '../index.html' : 'index.html';
        return null;
    }
    if (requiredRole && user.role !== requiredRole) {
        if (user.role === 'Admin') window.location.href = 'dashboard-admin.html';
        else if (user.role === 'Staff') window.location.href = 'dashboard-staff.html';
        else window.location.href = 'dashboard-resident.html';
        return null;
    }
    return user;
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
    window.location.href = (window.location.pathname.includes('/static/') ? '' : 'static/') + 'complaint-details.html?id=' + id + (returnPage ? '&return=' + encodeURIComponent(returnPage) : '');
}

// Withdraw complaint
function withdrawComplaint(id) {
    const comp = store.complaints.find(c => c.id === id);
    if (comp && ['Open','Reopened'].includes(comp.status)) {
        comp.status = 'Closed';
        comp.history.push({ date: getFormattedDate(), action: 'Withdrawn by Resident' });
        showToast('Request has been withdrawn.');
        setTimeout(() => window.history.back(), 800);
    }
}

function updateUnreadBadge() {
    if (!window.store || !window.store.notifications) return;
    const count = window.store.notifications.filter(n => !n.read).length;
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

document.addEventListener('DOMContentLoaded', function() {
    updateUnreadBadge();
    
    document.addEventListener('click', function(e) {
        const dropdown = document.getElementById('notificationDropdown');
        const bellBtn = e.target.closest('[onclick*="toggleNotifications"]');
        if (dropdown && !bellBtn && !e.target.closest('#notificationDropdown')) {
            dropdown.classList.add('hidden');
        }
    });
});

function toggleNotifications() {
    let dropdown = document.getElementById('notificationDropdown');
    
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'notificationDropdown';
        dropdown.className = 'absolute top-12 right-0 mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-xl z-50 hidden overflow-hidden';
        dropdown.innerHTML = `
            <div class="bg-slate-50 px-4 py-3 border-b border-slate-200 flex justify-between items-center">
                <h3 class="font-bold text-sm text-slate-800">Alerts</h3>
                <button onclick="markAllRead()" class="text-xs text-indigo-600 font-medium hover:text-indigo-800 transition">Mark all read</button>
            </div>
            <div id="notifDropdownList" class="max-h-80 overflow-y-auto"></div>
        `;
        
        const headerBtnContainer = document.querySelector('[onclick*="toggleNotifications"]').closest('.relative');
        if(headerBtnContainer) {
            headerBtnContainer.appendChild(dropdown);
        }
    }

    dropdown.classList.toggle('hidden');
    if (!dropdown.classList.contains('hidden')) {
        loadNotificationDropdown();
    }
}

window.markAllRead = function() {
    if(window.store && window.store.notifications) {
        window.store.notifications.forEach(n => n.read = true);
        updateUnreadBadge();
        loadNotificationDropdown();
    }
};

function loadNotificationDropdown() {
    const list = document.getElementById('notifDropdownList');
    if (!list) return;
    const recent = window.store.notifications.slice(0, 5);
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
                    <p class="text-xs text-slate-600 mt-1 line-clamp-2">${notif.text || ''}</p>
                    <p class="text-[11px] text-slate-500 mt-1.5">${notif.time || 'Just now'}</p>
                </div>
            </div>
        </div>`;
    }).join('');
}

function renderNav() {
    const nav = document.getElementById('navTabs');
    if (!nav) return;
    const user = getCurrentUser();
    if (!user) return;
         
    let links = [];
    if (user.role === 'Admin') {
        links = [
            { href: 'dashboard-admin.html', label: 'Portal', icon: 'fa-chart-pie' },
            { href: 'admin-staff.html', label: 'Staff', icon: 'fa-users' },
            { href: 'messages.html', label: 'Messages', icon: 'fa-comments' }
        ];
    } else if (user.role === 'Staff') {
        links = [
            { href: 'dashboard-staff.html', label: 'Portal', icon: 'fa-clipboard-list' },
            { href: 'staff-history.html', label: 'Past Jobs', icon: 'fa-check-double' },
            { href: 'support-contact.html', label: 'Support', icon: 'fa-headset' }
        ];
    } else { // Resident
        links = [
            { href: 'dashboard-resident.html', label: 'Portal', icon: 'fa-home' },
            { href: 'support-contact.html', label: 'Support', icon: 'fa-headset' }
        ];
    }
    
    // Determine which page we are currently on to assign the 'active' blue styling
    const currentPath = window.location.pathname.split('/').pop();
         
    nav.innerHTML = links.map(l => {
        const isActive = currentPath === l.href;
        const activeClasses = isActive 
            ? 'border-indigo-600 text-indigo-700' 
            : 'border-transparent text-slate-500 hover:text-slate-900';
            
        return `
            <a href="${l.href}" class="nav-link py-2 px-3 text-xs font-bold ${activeClasses} border-b-2 flex items-center transition">
                <i class="fas ${l.icon} mr-1.5 text-base"></i> ${l.label}
            </a>
        `;
    }).join('');
}