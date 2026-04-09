from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Company, PlacementDrive, Application
from functools import wraps
from datetime import datetime

company_bp = Blueprint('company', __name__)


# ── Auth guard ──────────────────────────────────────────────────────────────
def company_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'company':
            flash('Company access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def get_current_company():
    return Company.query.filter_by(user_id=session.get('user_id')).first()


# ── Dashboard ────────────────────────────────────────────────────────────────
@company_bp.route('/dashboard')
@company_required
def dashboard():
    company = get_current_company()
    drives  = PlacementDrive.query.filter_by(company_id=company.id).order_by(PlacementDrive.created_at.desc()).all()
    drives_with_counts = [
        (d, Application.query.filter_by(drive_id=d.id).count())
        for d in drives
    ]
    return render_template('company/dashboard.html', company=company, drives_with_counts=drives_with_counts)


# ── Drives ────────────────────────────────────────────────────────────────────
@company_bp.route('/drives/create', methods=['GET', 'POST'])
@company_required
def create_drive():
    company = get_current_company()
    if company.approval_status != 'approved':
        flash('Your company must be approved before creating placement drives.', 'danger')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        job_title   = request.form.get('job_title', '').strip()
        description = request.form.get('job_description', '').strip()
        eligibility = request.form.get('eligibility_criteria', '').strip()
        package     = request.form.get('package', '').strip()
        dl_str      = request.form.get('application_deadline', '').strip()
        deadline    = datetime.strptime(dl_str, '%Y-%m-%d').date() if dl_str else None

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=description,
            eligibility=eligibility,
            package=package,
            deadline=deadline,
            status='pending',
        )
        db.session.add(drive)
        db.session.commit()
        flash('Placement drive submitted for admin approval.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/create_drive.html', company=company)


@company_bp.route('/drives/<int:drive_id>/edit', methods=['GET', 'POST'])
@company_required
def edit_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    if request.method == 'POST':
        drive.job_title       = request.form.get('job_title', '').strip()
        drive.job_description = request.form.get('job_description', '').strip()
        drive.eligibility     = request.form.get('eligibility_criteria', '').strip()
        drive.package         = request.form.get('package', '').strip()
        dl_str                = request.form.get('application_deadline', '').strip()
        drive.deadline        = datetime.strptime(dl_str, '%Y-%m-%d').date() if dl_str else None
        db.session.commit()
        flash('Drive updated.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/edit_drive.html', drive=drive)


@company_bp.route('/drives/<int:drive_id>/close', methods=['POST'])
@company_required
def close_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    drive.status = 'closed'
    db.session.commit()
    flash('Drive has been closed.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drives/<int:drive_id>/delete', methods=['POST'])
@company_required
def delete_drive(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('company.dashboard'))


# ── Applications ─────────────────────────────────────────────────────────────
@company_bp.route('/drives/<int:drive_id>/applications')
@company_required
def drive_applications(drive_id):
    company = get_current_company()
    drive   = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    applications = Application.query.filter_by(drive_id=drive_id).order_by(Application.applied_on.desc()).all()
    return render_template('company/applications.html', drive=drive, applications=applications)


@company_bp.route('/applications/<int:app_id>/update', methods=['POST'])
@company_required
def update_application(app_id):
    company    = get_current_company()
    app_record = Application.query.get_or_404(app_id)
    # Ownership guard — application must belong to this company's drive
    if app_record.drive.company_id != company.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('company.dashboard'))
    new_status = request.form.get('status')
    if new_status in ('applied', 'shortlisted', 'selected', 'rejected'):
        app_record.status = new_status
        db.session.commit()
        flash('Application status updated.', 'success')
    return redirect(request.referrer or url_for('company.dashboard'))


# ── Profile ───────────────────────────────────────────────────────────────────
@company_bp.route('/profile', methods=['GET', 'POST'])
@company_required
def profile():
    company = get_current_company()
    if request.method == 'POST':
        company.company_name = request.form.get('company_name', '').strip()
        company.hr_contact   = request.form.get('hr_contact',   '').strip()
        company.website      = request.form.get('website',      '').strip()
        company.description  = request.form.get('description',  '').strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('company.profile'))
    return render_template('company/profile.html', company=company)
