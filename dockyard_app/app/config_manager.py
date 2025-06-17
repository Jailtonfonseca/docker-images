import json
import os
from flask import current_app

# Define the path for user-defined template sources
# This path should be targeted by a Docker volume for persistence
APP_DATA_DIR = '/app_data'
USER_TEMPLATE_SOURCES_FILENAME = 'user_template_sources.json'
USER_TEMPLATE_SOURCES_PATH = os.path.join(APP_DATA_DIR, USER_TEMPLATE_SOURCES_FILENAME)

def _ensure_data_dir_exists():
    """Ensures the APP_DATA_DIR exists."""
    if not os.path.exists(APP_DATA_DIR):
        try:
            os.makedirs(APP_DATA_DIR)
            current_app.logger.info(f"Created data directory: {APP_DATA_DIR}")
        except OSError as e:
            current_app.logger.error(f"Error creating data directory {APP_DATA_DIR}: {e}")
            # Depending on the error, this could be critical
            raise # Re-raise the exception if directory creation fails

def get_user_template_sources():
    """
    Reads the user-defined template sources from the JSON file.
    Returns a list of URLs, or an empty list if the file doesn't exist or is invalid.
    """
    _ensure_data_dir_exists() # Ensure directory exists before trying to read

    if not os.path.exists(USER_TEMPLATE_SOURCES_PATH):
        current_app.logger.info(f"User template sources file not found: {USER_TEMPLATE_SOURCES_PATH}. Returning empty list.")
        return []

    try:
        with open(USER_TEMPLATE_SOURCES_PATH, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and all(isinstance(url, str) for url in data):
                current_app.logger.info(f"Loaded {len(data)} user template sources from {USER_TEMPLATE_SOURCES_PATH}.")
                return data
            else:
                current_app.logger.warning(f"Invalid format in {USER_TEMPLATE_SOURCES_PATH}. Expected a list of strings. Returning empty list.")
                return []
    except json.JSONDecodeError:
        current_app.logger.error(f"Error decoding JSON from {USER_TEMPLATE_SOURCES_PATH}. Returning empty list.")
        return []
    except IOError as e:
        current_app.logger.error(f"IOError reading from {USER_TEMPLATE_SOURCES_PATH}: {e}. Returning empty list.")
        return []

def save_user_template_sources(urls_list):
    """
    Saves the given list of URLs to the JSON file.
    Returns True on success, False on failure.
    """
    _ensure_data_dir_exists() # Ensure directory exists before trying to write

    if not isinstance(urls_list, list) or not all(isinstance(url, str) for url in urls_list):
        current_app.logger.error("Invalid data type for save_user_template_sources: Expected a list of strings.")
        return False

    try:
        with open(USER_TEMPLATE_SOURCES_PATH, 'w') as f:
            json.dump(urls_list, f, indent=4)
        current_app.logger.info(f"Saved {len(urls_list)} user template sources to {USER_TEMPLATE_SOURCES_PATH}.")
        return True
    except IOError as e:
        current_app.logger.error(f"IOError writing to {USER_TEMPLATE_SOURCES_PATH}: {e}")
        return False
    except Exception as e: # Catch any other unexpected errors
        current_app.logger.error(f"Unexpected error saving to {USER_TEMPLATE_SOURCES_PATH}: {e}")
        return False
