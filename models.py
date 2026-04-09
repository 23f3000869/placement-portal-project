from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """
    Base entity for ALL roles (admin, company, student).
    Student profile fields live here directly (single-table architecture).
    """
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    # username stores student roll-no / student ID for student role; company/admin leave it as email
    username      = db.Column(db.String(80), unique=True, nullable=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)   # admin / company / student
    name          = db.Column(db.String(100), nullable=False)
    is_active     = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Student-specific profile fields (null for company / admin) ──
    phone     = db.Column(db.String(20),  nullable=True)
    branch    = db.Column(db.String(100), nullable=True)
    cgpa      = db.Column(db.Float,       nullable=True)
    resume_path = db.Column(db.String(300), nullable=True)  # relative path inside static/resumes/

    # ── Relationships ──
    company      = db.relationship('Company',     backref='user', uselist=False, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')


class Company(db.Model):
    __tablename__ = 'company'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name    = db.Column(db.String(150), nullable=False)
    hr_contact      = db.Column(db.String(100))
    website         = db.Column(db.String(200))
    description     = db.Column(db.Text)
    approval_status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade='all, delete-orphan')


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title   = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text)
    eligibility = db.Column(db.Text)                  # eligibility criteria string
    package     = db.Column(db.String(50))
    deadline    = db.Column(db.Date)                  # application deadline
    status      = db.Column(db.String(20), default='pending')  # pending / approved / closed / rejected
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'application'
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)   # references User.id
    drive_id   = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    status     = db.Column(db.String(20), default='applied')  # applied / shortlisted / selected / rejected

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )
