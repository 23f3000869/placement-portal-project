from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, Company, PlacementDrive, Application
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import date
import os

student_bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Auth guard ──────────────────────────────────────────────────────────────
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            flash('Student access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def get_current_student():
    """Returns the current logged-in student as a User object."""
    return User.query.filter_by(id=session.get('user_id'), role='student').first()


# ── Dashboard ────────────────────────────────────────────────────────────────
@student_bp.route('/dashboard')
@student_required
def dashboard():
    student = get_current_student()
    # Only show approved drives from approved companies
    approved_drives = (
        PlacementDrive.query
        .join(Company)
        .filter(
            PlacementDrive.status == 'approved',
            Company.approval_status == 'approved',
        )
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )
    applied_drive_ids = {
        a.drive_id for a in Application.query.filter_by(student_id=student.id).all()
    }
    applications = (
        Application.query
        .filter_by(student_id=student.id)
        .order_by(Application.applied_on.desc())
        .all()
    )
    return render_template('student/dashboard.html',
        student=student,
        approved_drives=approved_drives,
        applied_drive_ids=applied_drive_ids,
        applications=applications,
    )


# ── Apply for a drive ─────────────────────────────────────────────────────────
@student_bp.route('/drives/<int:drive_id>/apply', methods=['POST'])
@student_required
def apply_drive(drive_id):
    student = get_current_student()
    drive   = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != 'approved':
        flash('This drive is not open for applications.', 'danger')
        return redirect(url_for('student.dashboard'))

    # Deadline check
    if drive.deadline and date.today() > drive.deadline:
        flash('The application deadline for this drive has passed.', 'danger')
        return redirect(url_for('student.dashboard'))

    # UNIQUE constraint guard (also enforced at DB level)
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied to this drive.', 'warning')
        return redirect(url_for('student.dashboard'))

    application = Application(student_id=student.id, drive_id=drive_id)
    db.session.add(application)
    db.session.commit()
    flash(f'Applied to "{drive.job_title}" successfully!', 'success')
    return redirect(url_for('student.dashboard'))


# ── My Applications ───────────────────────────────────────────────────────────
@student_bp.route('/applications')
@student_required
def my_applications():
    student      = get_current_student()
    applications = (
        Application.query
        .filter_by(student_id=student.id)
        .order_by(Application.applied_on.desc())
        .all()
    )
    return render_template('student/applications.html', applications=applications, student=student)


# ── Profile ───────────────────────────────────────────────────────────────────
@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student = get_current_student()   # student IS the User object now
    if request.method == 'POST':
        student.name     = request.form.get('name',       '').strip() or student.name
        student.username = request.form.get('student_id', '').strip() or student.username
        student.branch   = request.form.get('branch',     '').strip() or None
        student.phone    = request.form.get('phone',      '').strip() or None
        cgpa_str         = request.form.get('cgpa',       '').strip()
        student.cgpa     = float(cgpa_str) if cgpa_str else student.cgpa

        # ── Resume upload ──────────────────────────────────────────────────
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"resume_{student.id}_{file.filename}")
                upload_dir = current_app.config['UPLOAD_FOLDER']
                file.save(os.path.join(upload_dir, filename))
                student.resume_path = filename   # stored in User.resume_path

        db.session.commit()
        session['name'] = student.name   # keep navbar name in sync
        flash('Profile updated.', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student, user=student)
