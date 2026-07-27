# Smart Society Complaint Resolution System

Smart Society is a responsive, web-based platform designed to bridge the gap between residential management, maintenance personnel, and residents. It provides an intuitive workflow for logging, tracking, and resolving facility issues in real-time.

## Features

*   **Role-Based Dashboards:** Distinct interfaces configured specifically for Administrators, Residents, and Maintenance Staff.
*   **Ticket Lifecycle Management:** Full CRUD capabilities for facility issues—from ticket creation and status updating (Open, Assigned, In Progress, Resolved) to closure.
*   **Dynamic Assignation:** Admin console functionality to assign jobs directly to available technical staff.
*   **Integrated Messaging:** Built-in chat functionalities to easily communicate progress and log specific issues.
*   **Session Persistence:** Fully utilizes LocalStorage to cache and retrieve session data and task lists, removing the immediate need for a robust database during prototyping.

## Tech Stack

This repository is built using purely frontend web technologies, making deployment rapid and lightweight:
*   **HTML5**
*   **CSS / UI:** [Tailwind CSS](https://tailwindcss.com/) (imported via CDN) for responsive structural layout. Custom standardizations in `assets/css/styles.css`.
*   **Interactivity:** Vanilla JavaScript coupled with [Vue.js 3](https://vuejs.org/) (via CDN) to manage reactive UI states.

## Getting Started

Because the application is strictly client-side, no heavy server infrastructure or dependency installations are required to run it locally.

1. Clone or download this repository to your local machine.
2. Open `index.html` directly in any modern web browser.
3. You can also host it via any minimal local server (such as Python's `http.server` or the VSCode `Live Server` extension) for a simulated web environment.

## Demo Credentials

You can test the platform utilizing the following pre-configured user credentials:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` |
| **Resident** | `resident` | `resident123` |
| **Maintenance Staff** | `maintenance` | `maintenance123` |

*Note: You can add and configure new maintenance staff credentials directly from the Administrator dashboard.*
