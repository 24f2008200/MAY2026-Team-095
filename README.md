# Smart Society

## Apartment Association Issue Tracking & Maintenance Management System

A centralized platform connecting **residents, management, and maintenance staff** for efficient complaint management, maintenance tracking, communication, and feedback.

---

## 📌 Project Overview

Smart Society is a web-based Apartment Association Management System that streamlines complaint handling, maintenance operations, communication, and reporting within residential communities.

The platform provides dedicated dashboards for:

- Residents
- Administrators / Management
- Maintenance Staff

---

## 🛠️ Technology Stack

| Component       | Technology            |
| --------------- | --------------------- |
| Backend         | Python, Flask         |
| Database        | PostgreSQL            |
| ORM             | Flask-SQLAlchemy      |
| Authentication  | JWT                   |
| Frontend        | HTML, CSS, JavaScript |
| Version Control | Git                   |

---

## 📂 Project Structure

```text
MAY2026-Team-095/
│
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   ├── .env.example
│   ├── .gitignore
│   ├── app.py
│   ├── requirements.txt
│   └── runtime.txt
│
└── frontend/
    ├── assets/
    │   └── css/
    ├── images/
    ├── js/
    ├── static/
    ├── README.md
    ├── index.html
    └── requirements.txt
```

### Backend Directory

| File/Folder        | Description                      |
| ------------------ | -------------------------------- |
| `app/`             | Core Flask application modules   |
| `migrations/`      | Database migration scripts       |
| `tests/`           | Unit and integration tests       |
| `.env.example`     | Sample environment configuration |
| `app.py`           | Application entry point          |
| `requirements.txt` | Python dependencies              |
| `runtime.txt`      | Runtime configuration            |

### Frontend Directory

| File/Folder        | Description                           |
| ------------------ | ------------------------------------- |
| `assets/css/`      | Stylesheets                           |
| `images/`          | Project images and icons              |
| `js/`              | JavaScript files                      |
| `static/`          | Static resources                      |
| `index.html`       | Main application page                 |
| `requirements.txt` | Frontend dependencies |

---

## 📋 Prerequisites

Before running the project, ensure the following are installed:

- Python 3.10 or higher
- PostgreSQL
- Git
- Modern web browser (Chrome, Edge, Firefox, Safari)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MAY2026-Team-095
```

---

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```powershell
.\venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Configuration

Create a `.env` file in the backend directory using `.env.example` as a reference.

Example:

```env
DATABASE_URL=<your-database-url>
SECRET_KEY=<your-secret-key>
JWT_SECRET_KEY=<your-jwt-secret-key>
MAIL_SERVER=<mail-server>
MAIL_PORT=<mail-port>
MAIL_USERNAME=<mail-username>
MAIL_PASSWORD=<mail-password>
MAIL_USE_TLS=True
MAIL_DEFAULT_SENDER=<default-email>
```

---

## 🗄️ Database Setup

Run database migrations:

```bash
flask db upgrade
```

---

## ▶️ Running the Backend

From the backend directory:

```bash
python app.py
```

Backend will be available at:

```text
http://127.0.0.1:5000
```

---

## 🌐 Running the Frontend

Open a new terminal:

```bash
cd frontend
```

Start a local server:

```bash
python -m http.server 5500
```

Open:

```text
http://localhost:5500
```

---

## ✨ Features

### Resident Module

- Register and login
- Raise complaints with details
- Track complaint status
- View complaint history
- Communicate with management and staff
- Provide feedback and ratings

### Administrator Module

- Manage residents and staff
- Approve resident registrations
- Manage complaint categories
- Assign complaints to staff
- Monitor complaint progress
- Generate and print reports

### Maintenance Staff Module

- View assigned complaints
- Update work status
- Track pending and completed tasks
- Communicate with residents and administrators
- Receive ratings and feedback

---

## 🧪 Testing

Run backend tests:

```bash
cd backend
pytest
```

---

## 🐛 Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running.
- Check the `DATABASE_URL` value.
- Ensure database credentials are correct.

### Backend Not Starting

```bash
pip install -r requirements.txt
```

Verify the virtual environment is activated.

### Frontend Cannot Reach Backend

- Ensure backend is running on port 5000.
- Verify API URLs configured in frontend JavaScript files.
- Check browser console for network errors.

---

## 📌 Project Highlights

- Role-based dashboards
- Complaint lifecycle management
- Maintenance task tracking
- Feedback and rating system
- Report generation and printing
- Centralized communication platform

---

## 👨‍💻 Team

**MAY2026-Team-095**

Smart Society – Apartment Association Issue Tracking & Maintenance Management System

---

## 📄 License

This project was developed as part of an academic software engineering project and is intended for educational purposes.
