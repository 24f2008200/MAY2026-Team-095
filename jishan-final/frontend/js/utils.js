// Frontend and API are served by the same Flask/Render service. Keeping this
// same-origin also prevents a new deployment from reconnecting to an older
// Render backend. Developers can still override it before this script loads.
const API_BASE = window.SMART_SOCIETY_API_BASE || window.location.origin;


/* ==========================================================================
   FILE URLS
   ========================================================================== */

function resolveFileUrl(path) {
    if (!path) return '';

    const value = String(path).trim();

    if (
        value.startsWith('http://') ||
        value.startsWith('https://')
    ) {
        return value;
    }

    return `${API_BASE}${value}`;
}


/* ==========================================================================
   API ERROR MESSAGES
   ========================================================================== */

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
    password: 'Password',
    remarks: 'Remarks',
    staff_id: 'Staff member',
    rating: 'Rating',
    comment: 'Comment'
};


function formatFieldValidationMessage(field, value) {
    const label =
        API_FIELD_LABELS[field] ||
        String(field || '')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());

    const raw = Array.isArray(value)
        ? value.filter(Boolean).join(' ')
        : String(value ?? '').trim();

    if (!raw) {
        return '';
    }

    const betweenMatch = raw.match(
        /length must be between\s+(\d+)\s+and\s+(\d+)/i
    );

    if (betweenMatch) {
        return `${label} must be between ${betweenMatch[1]} and ${betweenMatch[2]} characters.`;
    }

    const minMatch = raw.match(
        /shorter than minimum length\s+(\d+)|length must be at least\s+(\d+)/i
    );

    if (minMatch) {
        const min = minMatch[1] || minMatch[2];

        return `${label} must be at least ${min} characters.`;
    }

    const maxMatch = raw.match(
        /longer than maximum length\s+(\d+)|length must be at most\s+(\d+)/i
    );

    if (maxMatch) {
        const max = maxMatch[1] || maxMatch[2];

        return `${label} must be at most ${max} characters.`;
    }

    if (
        raw.toLowerCase().startsWith(
            label.toLowerCase()
        )
    ) {
        return raw;
    }

    return `${label}: ${raw}`;
}


function extractFieldErrors(container) {
    if (
        !container ||
        typeof container !== 'object' ||
        Array.isArray(container)
    ) {
        return '';
    }

    return Object.entries(container)
        .map(([field, value]) =>
            formatFieldValidationMessage(field, value)
        )
        .filter(Boolean)
        .join(' ');
}


function extractApiMessage(errorData) {
    if (
        !errorData ||
        typeof errorData !== 'object'
    ) {
        return '';
    }

    const errorsMessage =
        extractFieldErrors(errorData.errors);

    if (errorsMessage) {
        return errorsMessage;
    }

    if (
        errorData.message &&
        typeof errorData.message === 'object'
    ) {
        const nestedMessage =
            extractFieldErrors(
                errorData.message
            );

        if (nestedMessage) {
            return nestedMessage;
        }
    }

    if (
        typeof errorData.message === 'string' &&
        errorData.message.trim()
    ) {
        return errorData.message.trim();
    }

    if (
        typeof errorData.detail === 'string' &&
        errorData.detail.trim()
    ) {
        return errorData.detail.trim();
    }

    return '';
}


function friendlyHttpMessage(
    status,
    serverMessage = ''
) {
    if (
        serverMessage &&
        !/^request failed with status\s+\d+/i.test(
            serverMessage
        )
    ) {
        return serverMessage;
    }

    switch (status) {
        case 400:
            return 'Please check the information you entered and try again.';

        case 401:
            return 'Your session is invalid or has expired. Please sign in again.';

        case 403:
            return 'You do not have permission to perform this action.';

        case 404:
            return 'The requested information could not be found.';

        case 409:
            return 'This action conflicts with the current record state. Please refresh and try again.';

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


/* ==========================================================================
   AUTH / USER STORAGE
   ========================================================================== */

function getCurrentUser() {
    try {
        const stored =
            localStorage.getItem(
                'smartSocietyUser'
            );

        return stored
            ? JSON.parse(stored)
            : null;

    } catch (err) {
        console.error(
            'Failed to read stored user:',
            err
        );

        return null;
    }
}


function setCurrentUser(user, token) {
    if (user) {
        localStorage.setItem(
            'smartSocietyUser',
            JSON.stringify(user)
        );
    }

    if (token) {
        localStorage.setItem(
            'smartSocietyToken',
            token
        );
    }
}


function clearCurrentUser() {
    localStorage.removeItem(
        'smartSocietyUser'
    );

    localStorage.removeItem(
        'smartSocietyToken'
    );
}


function normalizeRole(user) {
    return String(
        user?.role || ''
    )
        .trim()
        .toUpperCase();
}


/* ==========================================================================
   URL HELPERS
   ========================================================================== */

function currentPageName() {
    return (
        window.location.pathname
            .split('/')
            .pop() || ''
    ).toLowerCase();
}


function loginPageUrl() {
    return window.location.pathname.includes(
        '/static/'
    )
        ? '../index.html'
        : 'index.html';
}


function homeForRole(role) {
    const normalized =
        String(role || '')
            .trim()
            .toUpperCase();

    if (normalized === 'ADMIN') {
        return 'dashboard-admin.html';
    }

    if (normalized === 'STAFF') {
        return 'dashboard-staff.html';
    }

    if (normalized === 'RESIDENT') {
        return 'dashboard-resident.html';
    }

    return loginPageUrl();
}


/* ==========================================================================
   API
   ========================================================================== */

async function apiCall(
    endpoint,
    options = {}
) {
    const token =
        localStorage.getItem(
            'smartSocietyToken'
        );

    const headers = {
        ...(options.headers || {})
    };

    const suppressErrorToast =
        Boolean(
            options.suppressErrorToast
        );

    if (token) {
        headers.Authorization =
            `Bearer ${token}`;
    }

    if (
        !(options.body instanceof FormData) &&
        !headers['Content-Type']
    ) {
        headers['Content-Type'] =
            'application/json';
    }

    const config = {
        method:
            options.method || 'GET',

        headers
    };

    if (
        options.body !== undefined &&
        options.body !== null
    ) {
        config.body =
            options.body instanceof FormData
                ? options.body
                : JSON.stringify(
                    options.body
                );
    }

    try {
        const response =
            await fetch(
                `${API_BASE}${endpoint}`,
                config
            );

        if (
            response.status === 401 &&
            token
        ) {
            clearCurrentUser();

            window.location.replace(
                loginPageUrl()
            );

            const error =
                new Error(
                    'Your session has expired. Please sign in again.'
                );

            error.status = 401;

            throw error;
        }

        if (!response.ok) {
            let errorData = {};

            const responseText =
                await response
                    .text()
                    .catch(() => '');

            if (responseText) {
                try {
                    errorData =
                        JSON.parse(
                            responseText
                        );
                } catch (err) {
                    errorData = {};
                }
            }

            const serverMessage =
                extractApiMessage(
                    errorData
                );

            const error =
                new Error(
                    friendlyHttpMessage(
                        response.status,
                        serverMessage
                    )
                );

            error.status =
                response.status;

            error.data =
                errorData;

            throw error;
        }

        if (
            response.status === 204
        ) {
            return null;
        }

        const text =
            await response.text();

        if (!text) {
            return null;
        }

        try {
            return JSON.parse(text);
        } catch (err) {
            return text;
        }

    } catch (err) {
        let normalizedError = err;

        if (
            err instanceof TypeError ||
            err.message ===
                'Failed to fetch' ||
            /networkerror|network request failed/i.test(
                err.message || ''
            )
        ) {
            normalizedError =
                new Error(
                    'Unable to connect to the server. Please check your connection and try again.'
                );

            normalizedError.status = 0;
        }

        if (
            !suppressErrorToast &&
            typeof showToast ===
                'function'
        ) {
            showToast(
                normalizedError.message ||
                    'Something went wrong. Please try again.',
                'error'
            );
        }

        throw normalizedError;
    }
}


/* ==========================================================================
   COMPLAINT STATUS RULES
   ========================================================================== */

const COMPLAINT_ACTIVE_STATUSES =
    Object.freeze([
        'OPEN',
        'REOPENED',
        'ASSIGNED',
        'IN_PROGRESS'
    ]);


const COMPLAINT_REOPENABLE_STATUSES =
    Object.freeze([
        'RESOLVED',
        'CLOSED'
    ]);


function sameId(left, right) {
    if (
        left === null ||
        left === undefined ||
        right === null ||
        right === undefined
    ) {
        return false;
    }

    return String(left) ===
        String(right);
}


function isComplaintOwner(
    user,
    complaint
) {
    return (
        normalizeRole(user) ===
            'RESIDENT' &&
        sameId(
            complaint?.resident_id,
            user?.id
        )
    );
}


function isAssignedStaff(
    user,
    complaint
) {
    return (
        normalizeRole(user) ===
            'STAFF' &&
        sameId(
            complaint?.assigned_staff_id,
            user?.id
        )
    );
}


function canAssignComplaint(
    user,
    complaint
) {
    return (
        normalizeRole(user) ===
            'ADMIN' &&
        COMPLAINT_ACTIVE_STATUSES.includes(
            String(
                complaint?.status || ''
            ).toUpperCase()
        )
    );
}


function canStaffWorkComplaint(
    user,
    complaint
) {
    return (
        isAssignedStaff(
            user,
            complaint
        ) &&
        [
            'ASSIGNED',
            'IN_PROGRESS'
        ].includes(
            String(
                complaint?.status || ''
            ).toUpperCase()
        )
    );
}


function canCloseComplaint(
    user,
    complaint
) {
    const status =
        String(
            complaint?.status || ''
        ).toUpperCase();

    if (
        ![
            ...COMPLAINT_ACTIVE_STATUSES,
            'RESOLVED'
        ].includes(status)
    ) {
        return false;
    }

    const role =
        normalizeRole(user);

    if (role === 'ADMIN') {
        return true;
    }

    return (
        role === 'RESIDENT' &&
        isComplaintOwner(
            user,
            complaint
        )
    );
}


/* ==========================================================================
   TIMEZONE-SAFE DATE PARSING

   IMPORTANT:

   Backend/SQLite timestamps such as:

   2026-08-22 04:30:00
   2026-08-22T04:30:00
   2026-08-22T04:30:00.123456

   do not contain a timezone.

   Your backend stores these as UTC, therefore this function explicitly
   interprets them as UTC.

   This means it behaves correctly whether the browser is in:
   - Canada
   - India
   - USA
   - UK
   - or any other timezone.
   ========================================================================== */

function parseServerTimestamp(timestamp) {
    if (
        timestamp === null ||
        timestamp === undefined ||
        timestamp === ''
    ) {
        return null;
    }

    let value =
        String(timestamp)
            .trim()
            .replace(' ', 'T');


    /*
     * Python can produce microseconds:
     *
     * .123456
     *
     * JavaScript normally uses milliseconds:
     *
     * .123
     *
     * Trim extra fractional digits for consistent
     * browser support.
     */
    value = value.replace(
        /\.(\d{3})\d+/,
        '.$1'
    );


    /*
     * Detect timezone information:
     *
     * Z
     * +00:00
     * -04:00
     * +0530
     */
    const hasTimezone =
        /(?:Z|[+-]\d{2}:?\d{2})$/i.test(
            value
        );


    /*
     * If no timezone is supplied,
     * interpret the server timestamp as UTC.
     */
    if (!hasTimezone) {
        value += 'Z';
    }


    const parsed =
        new Date(value);


    if (
        Number.isNaN(
            parsed.getTime()
        )
    ) {
        console.warn(
            'Invalid server timestamp:',
            timestamp
        );

        return null;
    }


    return parsed;
}


/* ==========================================================================
   REOPEN WINDOW
   ========================================================================== */

function isWithinReopenWindow(
    complaint
) {
    if (!complaint) {
        return false;
    }


    const status =
        String(
            complaint.status || ''
        ).toUpperCase();


    let timestamp = null;


    /*
     * For CLOSED tickets use closed_at.
     *
     * resolved_at remains a fallback for
     * old database records where closed_at
     * may not exist.
     */
    if (status === 'CLOSED') {
        timestamp =
            complaint.closed_at ||
            complaint.resolved_at;
    }


    /*
     * For RESOLVED tickets use resolved_at.
     */
    else if (
        status === 'RESOLVED'
    ) {
        timestamp =
            complaint.resolved_at;
    }


    /*
     * Any other state cannot be reopened.
     */
    else {
        return false;
    }


    const referenceTime =
        parseServerTimestamp(
            timestamp
        );


    if (!referenceTime) {
        return false;
    }


    const now =
        Date.now();


    const elapsed =
        now -
        referenceTime.getTime();


    const SEVEN_DAYS_MS =
        7 *
        24 *
        60 *
        60 *
        1000;


    /*
     * Allow tiny clock differences between
     * server and client devices.
     */
    const CLOCK_SKEW_ALLOWANCE_MS =
        5 *
        60 *
        1000;


    /*
     * Valid from closure/resolution until
     * exactly 7 days later.
     *
     * After this window the button disappears.
     */
    return (
        elapsed >=
            -CLOCK_SKEW_ALLOWANCE_MS &&
        elapsed <=
            SEVEN_DAYS_MS
    );
}


function canReopenComplaint(
    user,
    complaint
) {
    if (
        !user ||
        !complaint
    ) {
        return false;
    }


    const status =
        String(
            complaint.status || ''
        ).toUpperCase();


    return (
        isComplaintOwner(
            user,
            complaint
        ) &&

        COMPLAINT_REOPENABLE_STATUSES.includes(
            status
        ) &&

        /*
         * Once feedback/review has been submitted,
         * reopening is no longer allowed.
         */
        !complaint.feedback &&

        isWithinReopenWindow(
            complaint
        )
    );
}


function canSubmitComplaintFeedback(
    user,
    complaint
) {
    if (
        !user ||
        !complaint
    ) {
        return false;
    }


    const status =
        String(
            complaint.status || ''
        ).toUpperCase();


    return (
        isComplaintOwner(
            user,
            complaint
        ) &&

        COMPLAINT_REOPENABLE_STATUSES.includes(
            status
        ) &&

        !complaint.feedback
    );
}


function canCommentOnComplaint(
    user,
    complaint
) {
    if (
        !user ||
        !complaint
    ) {
        return false;
    }


    const status =
        String(
            complaint.status || ''
        ).toUpperCase();


    if (
        !COMPLAINT_ACTIVE_STATUSES.includes(
            status
        )
    ) {
        return false;
    }


    const role =
        normalizeRole(user);


    if (role === 'ADMIN') {
        return true;
    }


    if (role === 'RESIDENT') {
        return isComplaintOwner(
            user,
            complaint
        );
    }


    if (role === 'STAFF') {
        return canStaffWorkComplaint(
            user,
            complaint
        );
    }


    return false;
}


function canUploadComplaintAttachment(
    user,
    complaint
) {
    return canCommentOnComplaint(
        user,
        complaint
    );
}


/* ==========================================================================
   PAGE ACCESS / PAGE LOCK
   ========================================================================== */

const PAGE_ACCESS_POLICY =
    Object.freeze({

        'dashboard-admin.html':
            'ADMIN',

        'admin-staff.html':
            'ADMIN',

        'admin-approvals.html':
            'ADMIN',

        'admin-reports.html':
            'ADMIN',

        'assign-complaint.html':
            'ADMIN',

        'dashboard-staff.html':
            'STAFF',

        'staff-history.html':
            'STAFF',

        'update-status.html':
            'STAFF',

        'dashboard-resident.html':
            'RESIDENT',

        'raise-complaint.html':
            'RESIDENT',

        /*
         * These pages support multiple roles.
         * null means login required but no single
         * role restriction.
         */
        'complaint-details.html':
            null,

        'messages.html':
            null,

        'support-contact.html':
            null
    });


function ensurePageLockStyle() {
    if (
        document.getElementById(
            'smart-auth-lock-style'
        )
    ) {
        return;
    }


    const style =
        document.createElement(
            'style'
        );


    style.id =
        'smart-auth-lock-style';


    style.textContent = `
        html.smart-auth-lock #app {
            visibility: hidden !important;
        }

        [v-cloak] {
            display: none !important;
        }
    `;


    document.head.appendChild(
        style
    );
}


function lockProtectedPage() {
    const page =
        currentPageName();


    if (
        !Object.prototype
            .hasOwnProperty.call(
                PAGE_ACCESS_POLICY,
                page
            )
    ) {
        return;
    }


    ensurePageLockStyle();


    document.documentElement
        .classList.add(
            'smart-auth-lock'
        );


    const user =
        getCurrentUser();


    const token =
        localStorage.getItem(
            'smartSocietyToken'
        );


    const requiredRole =
        PAGE_ACCESS_POLICY[page];


    if (
        !user ||
        !token
    ) {
        window.location.replace(
            loginPageUrl()
        );

        return;
    }


    if (
        requiredRole &&
        normalizeRole(user) !==
            requiredRole
    ) {
        window.location.replace(
            homeForRole(
                user.role
            )
        );
    }
}


function unlockProtectedPage() {
    document.documentElement
        .classList.remove(
            'smart-auth-lock'
        );
}


function requireAuth(
    requiredRole
) {
    const user =
        getCurrentUser();


    const token =
        localStorage.getItem(
            'smartSocietyToken'
        );


    if (
        !user ||
        !token
    ) {
        window.location.replace(
            loginPageUrl()
        );

        return null;
    }


    if (
        requiredRole &&
        normalizeRole(user) !==
            String(
                requiredRole
            ).toUpperCase()
    ) {
        window.location.replace(
            homeForRole(
                user.role
            )
        );

        return null;
    }


    return user;
}


/* ==========================================================================
   SERVER SESSION VERIFICATION
   ========================================================================== */

async function refreshUserProfile(
    userRef,
    requiredRole
) {
    try {
        const response =
            await apiCall(
                '/auth/profile',
                {
                    suppressErrorToast:
                        true
                }
            );


        if (
            !response ||
            !response.user
        ) {
            clearCurrentUser();

            window.location.replace(
                loginPageUrl()
            );

            return null;
        }


        const serverUser =
            response.user;


        if (
            requiredRole &&
            normalizeRole(
                serverUser
            ) !==
                String(
                    requiredRole
                ).toUpperCase()
        ) {
            setCurrentUser(
                serverUser
            );


            window.location.replace(
                homeForRole(
                    serverUser.role
                )
            );


            return null;
        }


        setCurrentUser(
            serverUser
        );


        if (userRef) {
            userRef.value =
                serverUser;
        }


        unlockProtectedPage();


        return serverUser;

    } catch (err) {
        console.error(
            'Session verification failed:',
            err
        );


        /*
         * Do NOT unlock protected content
         * when server verification fails.
         */
        return null;
    }
}


/* ==========================================================================
   UI HELPERS
   ========================================================================== */

function showToast(
    message,
    type = 'success'
) {
    const toast =
        document.getElementById(
            'toast'
        );


    const toastMsg =
        document.getElementById(
            'toastMsg'
        );


    if (
        !toast ||
        !toastMsg
    ) {
        return;
    }


    toast.className =
        'fixed bottom-6 right-6 z-50 flex items-center px-4 py-3 rounded-md shadow-lg border ' +
        (
            type === 'error'
                ? 'bg-white border-rose-200 text-rose-800'
                : 'bg-slate-900 border-slate-800 text-white'
        );


    toastMsg.textContent =
        message;


    toast.classList.remove(
        'hidden'
    );


    clearTimeout(
        window.toastTimer
    );


    window.toastTimer =
        setTimeout(
            () => {
                toast.classList.add(
                    'hidden'
                );
            },
            3500
        );
}


/* ==========================================================================
   NAVIGATION
   ========================================================================== */

function logout() {
    clearCurrentUser();

    window.location.replace(
        loginPageUrl()
    );
}


function goHome() {
    const user =
        getCurrentUser();


    if (!user) {
        window.location.replace(
            loginPageUrl()
        );

        return;
    }


    window.location.href =
        homeForRole(
            user.role
        );
}


function viewComplaint(
    id,
    returnPage
) {
    const prefix =
        window.location.pathname.includes(
            '/static/'
        )
            ? ''
            : 'static/';


    let url =
        `${prefix}complaint-details.html?id=${encodeURIComponent(id)}`;


    if (returnPage) {
        url +=
            `&return=${encodeURIComponent(returnPage)}`;
    }


    window.location.href =
        url;
}


/* ==========================================================================
   APPLY PAGE PROTECTION IMMEDIATELY
   ========================================================================== */

lockProtectedPage();
