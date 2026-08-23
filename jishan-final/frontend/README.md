# Smart Society Complaint Resolution System

Smart Society is a responsive, web-based platform designed to bridge the gap between residential management, maintenance personnel, and residents. It provides an intuitive workflow for logging, tracking, and resolving facility issues in real-time.

## Features

*   **Role-Based Dashboards:** Distinct interfaces configured specifically for Administrators, Residents, and Maintenance Staff.
*   **Ticket Lifecycle Management:** Full CRUD capabilities for facility issues—from ticket creation and status updating (Open, Assigned, In Progress, Resolved) to closure.
*   **Dynamic Assignation:** Admin console functionality to assign jobs directly to available technical staff.
*   **Integrated Messaging:** Built-in chat functionalities to easily communicate progress and log specific issues.
*   **Session Persistence:** Fully utilizes LocalStorage to cache and retrieve session data and task lists, removing the immediate need for a robust database during prototyping.

## Tech Stack

The user interface uses HTML, Tailwind CSS, Vue 3 and vanilla JavaScript. It
connects to the Flask API in `../backend`; on Render, both are served by the
same web service so no old or cross-account backend URL is required.

## Getting Started

Run the Flask app from `../backend` and open `http://127.0.0.1:5000/`.
Deployment instructions and free-tier limitations are documented in
`../DEPLOYMENT.md`.

The deployment administrator is created from the `ADMIN_EMAIL` and
`ADMIN_PASSWORD` environment variables. Realistic seeded people and complaints
populate the dashboards, but no shared demo passwords are published.
