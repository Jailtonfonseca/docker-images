from flask import current_app, Blueprint
from app import app, bcrypt
from flask import render_template, jsonify, request, flash, redirect, url_for
from . import template_manager
from . import docker_manager
from . import config_manager
from .forms import RegistrationForm, LoginForm
from .models import User
from flask_login import login_user, current_user, logout_user, login_required
import json # For pretty printing dicts in logs
import psutil

@app.route('/')
@login_required
def index():
    app.logger.info("Index route called.")
    templates_data = template_manager.get_all_templates()
    # Group templates by title to handle duplicates
    grouped_templates = {}
    if templates_data:
        for i, t in enumerate(templates_data):
            template_type = t.get('type')
            title = t.get('title')
            logo = t.get('logo')
            description = t.get('description')

            # Only include templates that have a title, logo, description, and a supported type (1 or 2)
            if title and logo and description and (template_type in [1, 2, '1', '2']):
                if title not in grouped_templates:
                    grouped_templates[title] = {
                        'title': title,
                        'logo': logo,
                        'description': description,
                        'templates': []
                    }

                # Use a unique ID for each template instance
                t['id'] = f"{title.replace(' ', '_').lower()}_{i}"
                grouped_templates[title]['templates'].append(t)

    app.logger.info(f"Displaying {len(grouped_templates)} grouped templates from cache.")
    return render_template("index.html", title="DockYard - Available Apps", grouped_templates=grouped_templates)

@app.route('/settings')
@login_required
def settings_page():
    app.logger.info("Settings page route called.")
    return render_template("settings.html", title="DockYard Settings")

@app.route('/app/<template_id>')
@login_required
def app_details(template_id):
    app.logger.info(f"App details route called for template_id: {template_id}")
    template = template_manager.get_template_by_id(template_id)
    if not template:
        app.logger.error(f"Template with id {template_id} not found.")
        return "Template not found", 404

    return render_template("app_details.html", title=template.get('title', 'App Details'), template=template)

@app.route('/dashboard')
@login_required
def dashboard():
    app.logger.info("Dashboard route called.")
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent

    # Temperature is more complex, so we'll omit it for now.
    # It often requires specific libraries and configuration per-system.

    return render_template("dashboard.html", title="System Dashboard", cpu_usage=cpu_usage, ram_usage=ram_usage)

@app.route('/templates_json')
def list_templates_json():
    app.logger.info("Templates JSON route called.")
    templates_data = template_manager.get_all_templates()
    if not templates_data:
        app.logger.warning("No template data in cache for JSON endpoint.")
        return jsonify({"error": "No templates found in cache."}), 404
    app.logger.info(f"Returning {len(templates_data)} templates from cache via JSON.")
    return jsonify(templates_data)

@app.route('/install_app', methods=['POST'])
@login_required
def install_app_route():
    app.logger.info("Install app route called.")
    data = request.get_json()
    if not data or 'template_id' not in data:
        app.logger.error("API Error: Missing template_id in request for /install_app.")
        return jsonify({"success": False, "message": "Missing template_id in request."}), 400

    template_id_to_install = data['template_id']
    app.logger.info(f"Attempting to install template with ID: '{template_id_to_install}'.")

    target_template = template_manager.get_template_by_id(template_id_to_install)

    if not target_template:
        app.logger.error(f"Installation Error: Template with ID '{template_id_to_install}' not found in cache.")
        return jsonify({"success": False, "message": f"Template '{template_id_to_install}' not found."}), 404

    app.logger.info(f"Found template for ID '{template_id_to_install}'. Template details: {json.dumps(target_template, indent=2)}")

    template_type = target_template.get('type')
    # Stricter check: Only proceed if type is explicitly 2 (integer or string '2')
    if template_type != 2 and template_type != '2':
        app.logger.error(f"Installation Error: Template '{target_template.get('title')}' is type '{template_type}', not type 2 (container). This type is not supported for direct container installation by this endpoint.")
        return jsonify({"success": False, "message": f"Template '{target_template.get('title')}' is type '{template_type}'. Only type 2 (container) templates can be installed via this method."}), 400

    app.logger.info(f"Proceeding with installation for template: {target_template.get('title')} (Type: {template_type})")
    success, message = docker_manager.install_container_from_template(target_template)

    if success:
        app.logger.info(f"Installation successful for '{target_template.get('title')}': {message}")
    else:
        app.logger.error(f"Installation failed for '{target_template.get('title')}': {message}")

    return jsonify({"success": success, "message": message})

@app.route('/api/settings/templates/sources', methods=['GET'])
def get_template_sources_api():
    app.logger.info("API GET /api/settings/templates/sources called.")
    user_sources = config_manager.get_user_template_sources()
    return jsonify({"urls": user_sources}), 200

@app.route('/api/settings/templates/sources', methods=['POST'])
def save_template_sources_api():
    app.logger.info("API POST /api/settings/templates/sources called.")
    data = request.get_json()

    if not data or 'urls' not in data:
        app.logger.warning("API POST /sources: Missing 'urls' in request payload.")
        return jsonify({"success": False, "message": "Missing 'urls' in request payload."}), 400

    urls_list = data['urls']
    if not isinstance(urls_list, list) or not all(isinstance(url, str) for url in urls_list):
        app.logger.warning("API POST /sources: 'urls' must be a list of strings.")
        return jsonify({"success": False, "message": "'urls' must be a list of strings."}), 400

    cleaned_urls_list = [url.strip() for url in urls_list if url.strip()]

    if config_manager.save_user_template_sources(cleaned_urls_list):
        app.logger.info("User template sources saved successfully. Triggering cache update.")
        try:
            template_manager.update_cached_templates()
            app.logger.info("Template cache update triggered successfully after saving sources.")
        except Exception as e:
            app.logger.error(f"Error triggering template cache update: {e}")
            return jsonify({"success": True, "message": "Template sources saved, but cache update failed. Please check logs."}), 500

        return jsonify({"success": True, "message": "Template sources saved and cache updated."}), 200
    else:
        app.logger.error("API POST /sources: Failed to save template sources using config_manager.")
        return jsonify({"success": False, "message": "Failed to save template sources."}), 500

@app.before_request
def check_for_users():
    # Allow access to static files and the registration page without a user check
    if request.endpoint and (request.endpoint.startswith('static') or request.endpoint in ['register', 'login']):
        return

    if not User.get_all_users():
        if request.endpoint != 'register':
            return redirect(url_for('register'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # If users already exist, redirect to login
    if User.get_all_users() and request.method == 'GET':
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        User.save_user(username=form.username.data, password_hash=hashed_password)
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_username(form.username.data)
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))
