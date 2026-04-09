from flask import Flask
from models import db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.company import company_bp
from routes.student import student_bp
import os

# --- TROUBLESHOOTING ---
# If you see "ModuleNotFoundError: No module named 'flask'", 
# run the following command in your terminal:
# pip install -r requirements.txt

def create_app():
    """
    Application Factory to initialize the Placement Portal.
    This structure ensures the app is modular and avoids circular imports.
    """
    app = Flask(__name__)
    
    # --- Configuration ---
    # Secret key is required for session security and flashing messages.
    app.config['SECRET_KEY'] = 'placement_portal_2026_secure_key'
    
    # Database path for SQLite.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- File Storage Setup ---
    # Defining the directory where student resumes will be stored.
    upload_path = os.path.join(app.root_path, 'static', 'resumes')
    app.config['UPLOAD_FOLDER'] = upload_path
    
    # Create the directory if it doesn't exist to prevent errors during upload.
    os.makedirs(upload_path, exist_ok=True)

    # --- Extensions Initialization ---
    db.init_app(app)

    # --- Route Registration ---
    # Dividing the application into Blueprints based on user roles.
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(student_bp, url_prefix='/student')

    # --- Database & Admin Setup ---
    with app.app_context():
        # Automatically create database tables based on models defined in models.py.
        db.create_all()
        # Create the initial superuser for the system.
        seed_admin()

    return app

def seed_admin():
    """
    Creates a default admin account if none exists.
    Login: admin@placement.com | Password: admin123
    """
    from models import User
    from werkzeug.security import generate_password_hash
    
    if not User.query.filter_by(role='admin').first():
        admin = User(
            name='Placement Admin',
            email='admin@placement.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Initial Admin Seeded: admin@placement.com")

if __name__ == '__main__':
    # Start the Flask development server.
    app = create_app()
    app.run(debug=True)