import logging
from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config.from_object(Config)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
# Ensure Flask's logger is also used or configured
if not app.debug: # Don't use basicConfig in debug mode if Flask's own setup is better
    app.logger.setLevel(logging.INFO)
else:
    app.logger.setLevel(logging.DEBUG) # More verbose in debug

app.logger.info("DockYard application starting up...")

# Import routes and models after app is created
from app import routes
# from app import models # if you add models later

# Import template_manager and initialize cache/scheduler
from app import template_manager

def initialize_templates_and_scheduler(flask_app):
    with flask_app.app_context():
        flask_app.logger.info("Attempting initial template cache population...")
        template_manager.update_cached_templates() # Populate cache at startup

        scheduler = BackgroundScheduler(daemon=True)
        # Run job every X hours, e.g., every 4 hours. Configurable via app.config if needed.
        job_hours = flask_app.config.get('TEMPLATE_UPDATE_INTERVAL_HOURS', 4)
        scheduler.add_job(
            func=template_manager.update_cached_templates,
            trigger='interval',
            hours=job_hours,
            id='update_templates_job', # Give the job an ID
            replace_existing=True      # Replace if a job with this ID already exists
        )
        try:
            scheduler.start()
            flask_app.logger.info(f"APScheduler started. Template update job scheduled every {job_hours} hours.")
        except Exception as e:
            # This can happen if scheduler is started multiple times in some Flask dev server reloads
            flask_app.logger.error(f"APScheduler could not be started (maybe already running?): {e}")

        # It's good practice to shut down the scheduler when the app exits
        import atexit
        atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

# Call initialization function
initialize_templates_and_scheduler(app)

app.logger.info("DockYard application startup complete.")
