from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Company, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__)


# ── Auth guard ──────────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_students     = User.query.filter_by(role='student').count()
    total_companies    = Company.query.filter_by(approval_status='approved').count()
    total_drives       = PlacementDrive.query.count()
    pending_companies  = Company.query.filter_by(approval_status='pending').count()
    pending_drives     = PlacementDrive.query.filter_by(status='pending').count()
    total_applications = Application.query.count()
    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        total_applications=total_applications,
    )


# ── Companies ────────────────────────────────────────────────────────────────
@admin_bp.route('/companies')
@admin_required
def companies():
    search = request.args.get('search', '').strip()
    query  = Company.query.join(User)
    if search:
        query = query.filter(
            db.or_(
                Company.company_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )
    companies = query.order_by(Company.created_at.desc()).all()
    return render_template('admin/companies.html', companies=companies, search=search)


@admin_bp.route('/companies/<int:company_id>/approve', methods=['POST'])
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'approved'
    db.session.commit()
    flash(f'"{company.company_name}" has been approved.', 'success')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/companies/<int:company_id>/reject', methods=['POST'])
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'rejected'
    db.session.commit()
    flash(f'"{company.company_name}" has been rejected.', 'warning')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/companies/<int:company_id>/blacklist', methods=['POST'])
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.user.is_blacklisted = not company.user.is_blacklisted
    db.session.commit()
    state = 'blacklisted' if company.user.is_blacklisted else 'unblacklisted'
    flash(f'"{company.company_name}" {state}.', 'info')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/companies/<int:company_id>/delete', methods=['POST'])
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    user = company.user
    db.session.delete(user)   # cascade removes Company + Drives + Applications
    db.session.commit()
    flash('Company and all associated data deleted.', 'info')
    return redirect(url_for('admin.companies'))


# ── Students ─────────────────────────────────────────────────────────────────
@admin_bp.route('/students')
@admin_required
def students():
    search = request.args.get('search', '').strip()
    query  = User.query.filter_by(role='student')
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),    # username = roll no
                User.email.ilike(f'%{search}%'),
            )
        )
    students = query.order_by(User.created_at.desc()).all()
    return render_template('admin/students.html', students=students, search=search)


@admin_bp.route('/search')
@admin_required
def search():
    """Dedicated search endpoint — GET /admin/search?q=<term>"""
    q       = request.args.get('q', '').strip()
    results = []
    if q:
        results = User.query.filter(
            User.role == 'student',
            db.or_(
                User.name.ilike(f'%{q}%'),
                User.username.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%'),
            )
        ).all()
    return render_template('admin/students.html', students=results, search=q)


@admin_bp.route('/students/<int:student_id>/blacklist', methods=['POST'])
@admin_required
def blacklist_student(student_id):
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    state = 'blacklisted' if student.is_blacklisted else 'unblacklisted'
    flash(f'"{student.name}" {state}.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    db.session.delete(student)   # cascade removes Applications
    db.session.commit()
    flash('Student deleted.', 'info')
    return redirect(url_for('admin.students'))


# ── Drives ────────────────────────────────────────────────────────────────────
@admin_bp.route('/drives')
@admin_required
def drives():
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives)


@admin_bp.route('/drives/<int:drive_id>/approve', methods=['POST'])
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" approved and is now live.', 'success')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drives/<int:drive_id>/reject', methods=['POST'])
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" rejected.', 'warning')
    return redirect(url_for('admin.drives'))


# ── All Applications (read-only overview) ────────────────────────────────────
@admin_bp.route('/applications')
@admin_required
def applications():
    applications = Application.query.order_by(Application.applied_on.desc()).all()
    return render_template('admin/applications.html', applications=applications)
