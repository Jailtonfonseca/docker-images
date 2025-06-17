import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # Add other configurations here, like template URLs
    TEMPLATE_SOURCES_URL = os.environ.get('TEMPLATE_SOURCES_URL') or "https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json"

    # Scheduler settings
    TEMPLATE_UPDATE_INTERVAL_HOURS = int(os.environ.get('TEMPLATE_UPDATE_INTERVAL_HOURS', 4))
