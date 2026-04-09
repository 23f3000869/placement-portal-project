from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Company

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}.dashboard"))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html')

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return render_template('auth/login.html')

        # Company accounts must be approved before they can log in
        if user.role == 'company':
            company = Company.query.filter_by(user_id=user.id).first()
            if company and company.approval_status != 'approved':
                flash('Your company account is pending admin approval.', 'warning')
                return render_template('auth/login.html')

        session['user_id'] = user.id
        session['role']    = user.role
        session['name']    = user.name
        return redirect(url_for(f"{user.role}.dashboard"))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role     = request.form.get('role')
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if role not in ('company', 'student'):
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')

        if not name or not email or not password:
            flash('All required fields must be filled in.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_active=True,
        )

        if role == 'student':
            # Student roll-no maps to username field
            student_roll = request.form.get('student_id', '').strip()
            user.username = student_roll if student_roll else None
            user.branch   = request.form.get('branch',  '').strip() or None
            user.phone    = request.form.get('phone',   '').strip() or None
            cgpa_str      = request.form.get('cgpa',    '').strip()
            user.cgpa     = float(cgpa_str) if cgpa_str else None
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please sign in.', 'success')

        elif role == 'company':
            company_name = request.form.get('company_name', '').strip()
            if not company_name:
                flash('Company name is required.', 'danger')
                return render_template('auth/register.html')
            hr_contact = request.form.get('hr_contact', '').strip()
            website    = request.form.get('website',    '').strip()
            db.session.add(user)
            db.session.flush()   # get user.id before Company FK
            company = Company(
                user_id=user.id,
                company_name=company_name,
                hr_contact=hr_contact,
                website=website,
            )
            db.session.add(company)
            db.session.commit()
            flash('Registration submitted. Await admin approval before logging in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
