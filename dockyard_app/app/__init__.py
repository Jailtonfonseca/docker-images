import logging
import os # Import os for path manipulation
from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler

# Determine the correct path to the template folder
# The app is in dockyard_app/app/, templates are in dockyard_app/templates/
# So, from app/__init__.py, the path to templates is '../templates'
# A more robust way is to calculate it from the application root path.
# app_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# template_dir = os.path.join(app_root_path, 'templates')
# For simplicity and common Flask patterns, '../templates' relative to the blueprint/app location is fine.

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
if not app.debug:
    app.logger.setLevel(logging.INFO)
else:
    app.logger.setLevel(logging.DEBUG)

app.logger.info("DockYard application starting up...")
app.logger.info(f"Flask template_folder set to: {app.template_folder}")
app.logger.info(f"Flask static_folder set to: {app.static_folder}")


from app import routes
from app import template_manager

def initialize_templates_and_scheduler(flask_app):
    with flask_app.app_context():
        flask_app.logger.info("Attempting initial template cache population...")
        template_manager.update_cached_templates()

        scheduler = BackgroundScheduler(daemon=True)
        job_hours = flask_app.config.get('TEMPLATE_UPDATE_INTERVAL_HOURS', 4)
        scheduler.add_job(
            func=template_manager.update_cached_templates,
            trigger='interval',
            hours=job_hours,
            id='update_templates_job',
            replace_existing=True
        )
        try:
            scheduler.start()
            flask_app.logger.info(f"APScheduler started. Template update job scheduled every {job_hours} hours.")
        except Exception as e:
            flask_app.logger.error(f"APScheduler could not be started (maybe already running?): {e}")

        import atexit
        atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

initialize_templates_and_scheduler(app)

app.logger.info("DockYard application startup complete.")
