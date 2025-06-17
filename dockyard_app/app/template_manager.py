import requests
import json
from flask import current_app, g # g for application context global

# This will hold our cached templates
# Using g (application context global) might be problematic with APScheduler if the job runs
# outside of an active app context. A simple module-level global is safer for APScheduler.
_cached_templates = []
_is_updating = False # Simple flag to prevent concurrent updates by scheduler

def fetch_templates_from_url(url):
    """Fetches template data from a single URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'templates' in data and isinstance(data['templates'], list):
            return data['templates']
        else:
            current_app.logger.error(f"Unexpected JSON structure from {url}")
            return []
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching template from {url}: {e}")
        return []
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Error decoding JSON from {url}: {e}")
        return []

def update_cached_templates():
    """Fetches and updates the cached templates from all configured source URLs."""
    global _cached_templates
    global _is_updating

    # This check is important if the scheduler runs in a separate thread
    # and we want to ensure current_app is available or pass config explicitly.
    # For APScheduler integrated with Flask, current_app should be available if configured correctly.
    if not current_app:
        # This case should ideally not happen if scheduler is setup with app context.
        # If it does, we might need to pass app instance or config to the job.
        print("Error: update_cached_templates called without active Flask app context.") # Use print as logger might not be available
        return

    if _is_updating:
        current_app.logger.info("Template update already in progress. Skipping.")
        return

    _is_updating = True
    current_app.logger.info("Starting periodic template cache update...")

    template_sources_str = current_app.config.get('TEMPLATE_SOURCES_URL', '')
    if not template_sources_str:
        current_app.logger.warning("TEMPLATE_SOURCES_URL is not configured. Cache will be empty.")
        _cached_templates = []
        _is_updating = False
        return

    source_urls = [url.strip() for url in template_sources_str.split(',') if url.strip()]
    new_templates_data = []

    for url in source_urls:
        current_app.logger.info(f"Fetching templates from: {url} for cache update.")
        templates = fetch_templates_from_url(url)
        if templates:
            new_templates_data.extend(templates)
        else:
            current_app.logger.warning(f"No templates found or error fetching from {url} during cache update.")

    _cached_templates = new_templates_data
    _is_updating = False
    current_app.logger.info(f"Template cache updated. Total templates: {len(_cached_templates)}")

def get_all_templates():
    """Returns all templates, primarily from cache. Fetches if cache is empty."""
    # This function is called by routes. It should now return from cache.
    # Initial fetch if cache is empty can be triggered here or by scheduler at startup.
    if not _cached_templates and not _is_updating : # Fetch if empty and no update is running
        current_app.logger.info("Cache is empty, attempting initial fetch...")
        # In a scheduled environment, we might want the first fetch to be blocking
        # or rely on the scheduler to populate it soon after startup.
        # For simplicity, let's make it blocking for the first call if empty.
        update_cached_templates() # This will populate _cached_templates
    return _cached_templates

def get_template_by_id(template_id_str):
    """Gets a single template by its ID from the cache."""
    all_templates = get_all_templates() # Ensures cache is populated
    for t in all_templates:
        current_template_id = (t.get('title') or '').replace(' ', '_').lower()
        if current_template_id == template_id_str:
            return t
    return None
