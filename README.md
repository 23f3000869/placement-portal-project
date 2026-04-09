# Placement Portal Application

## Setup & Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Default Admin Login
- Email: admin@placement.com
- Password: admin123

## Project Structure
placement_portal/
├── app.py              # App factory, entry point
├── models.py           # SQLAlchemy DB models
├── requirements.txt
├── routes/
│   ├── auth.py         # Login, Register, Logout
│   ├── admin.py        # Admin dashboard & management
│   ├── company.py      # Company features
│   └── student.py      # Student features
├── templates/
│   ├── base.html
│   ├── auth/           # login.html, register.html
│   ├── admin/          # dashboard, companies, students, drives, applications
│   ├── company/        # dashboard, create_drive, edit_drive, applications, profile
│   └── student/        # dashboard, applications, profile
└── static/
    ├── css/style.css
    └── resumes/        # Uploaded student resumes
