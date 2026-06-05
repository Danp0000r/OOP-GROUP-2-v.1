import json
import os
import importlib.util
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_login import LoginManager

from database.db import db
from services.compatibility.compatibility_service import CompatibilityService

login_manager = LoginManager()


def create_app():

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.debug = app.config['DEBUG']

    # ensure instance folder exists inside the project
    instance_dir = os.path.join(app.root_path, "instance")
    os.makedirs(instance_dir, exist_ok=True)

    # Secret Key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')

    # Main Database (stored in instance/)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'users.db').replace('\\', '/')

    # Components Database (stored in instance/)
    app.config['SQLALCHEMY_BINDS'] = {
        'components': 'sqlite:///' + os.path.join(instance_dir, 'components.db').replace('\\', '/')
    }

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Database
    db.init_app(app)

    # Initialize Login Manager
    login_manager.init_app(app)

    # Register Jinja filters
    def from_json_filter(value):
        if isinstance(value, (list, dict)):
            return value
        if value is None:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []
    app.jinja_env.filters['from_json'] = from_json_filter

    # Import Models (ensure these are registered with SQLAlchemy before create_all)
    from models.user import User
    from models.build import Build
    from models.activity import Activity
    from models.component import Component
    from models.link import Link
    from models.cpu import CPU
    from models.gpu import GPU
    from models.ram import RAM
    from models.motherboard import Motherboard
    from models.psu import PSU
    from models.storage import Storage
    from models.cooling import Cooling
    from models.case import Case

    # Create all database tables
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Context processor to inject user into all templates
    @app.context_processor
    def inject_user():
        from models.user import User
        user = None
        if session.get('user_id'):
            try:
                user = User.query.get(int(session['user_id']))
            except (ValueError, TypeError):
                pass
        return dict(user=user)

    # Register blueprints
    from routes.main_routes import main_bp
    from routes.auth_routes import auth_bp
    from routes.build_routes import build_bp
    from routes.component_routes import component_bp
    from routes.admin_routes import admin_bp
    from routes.questionnaire_routes import questionnaire_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(build_bp)
    app.register_blueprint(component_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questionnaire_bp)

    # Register CLI commands for database updates
    update_db_path = os.path.join(os.path.dirname(__file__), "data reset", "update_db.py")
    spec = importlib.util.spec_from_file_location("data_reset_update_db", update_db_path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load database update module from {update_db_path}")
    update_db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(update_db_module)
    update_db_module.register_cli_commands(app)

    # Serve and persist Nexus3D positions JSON in the instance folder.
    @app.route('/nexus3d_positions.json', methods=['GET', 'POST'])
    def nexus3d_positions():
        file_name = 'nexus3d_positions.json'
        path = os.path.join(instance_dir, file_name)
        if request.method == 'GET':
            try:
                if os.path.exists(path):
                    return send_from_directory(instance_dir, file_name)
                return jsonify({'savedPositions': {}})
            except Exception:
                return jsonify({'savedPositions': {}})

        # POST: persist positions (admin-only)
        if not session.get('is_admin'):
            return jsonify({'error': 'Admin access required.'}), 403
        try:
            data = request.get_json(force=True)
            # Write JSON payload to instance file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data or {}, f, indent=2, ensure_ascii=False)
            return jsonify({'message': 'Positions saved.'})
        except Exception as e:
            return jsonify({'error': 'Failed to save positions.', 'detail': str(e)}), 500

    return app
