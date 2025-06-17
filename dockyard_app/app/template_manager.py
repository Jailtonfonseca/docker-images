import requests
import json
from flask import current_app
from . import config_manager
import logging # Import logging for fallback

_cached_templates = []
_is_updating = False

def fetch_templates_from_url(url):
    """Fetches template data from a single URL."""
    logger = current_app.logger if current_app else logging.getLogger(__name__)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'templates' in data and isinstance(data['templates'], list):
            return data['templates']
        else:
            logger.error(f"Unexpected JSON structure from {url}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching template from {url}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {url}: {e}")
        return []
    except Exception as e: # Catch any other unexpected errors during fetch
        logger.error(f"Unexpected error fetching or decoding from {url}: {e}")
        return []


def update_cached_templates():
    """Fetches and updates the cached templates.
    Prioritizes user-defined URLs, then falls back to environment config.
    De-duplicates templates based on their title (case-insensitive, ignoring whitespace).
    """
    global _cached_templates
    global _is_updating

    logger = current_app.logger if current_app else logging.getLogger(__name__)
    if not current_app and not hasattr(logger, 'handlers') or not logger.handlers: # Check if logger has handlers
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    if _is_updating:
        logger.info("Template update already in progress. Skipping.")
        return

    _is_updating = True
    logger.info("Starting template cache update (with de-duplication)...")

    source_urls = []
    user_defined_sources = config_manager.get_user_template_sources()

    if user_defined_sources:
        logger.info(f"Using {len(user_defined_sources)} user-defined template source(s).")
        source_urls = user_defined_sources
    else:
        logger.info("No user-defined template sources found or list is empty. Falling back to environment configuration.")
        if current_app:
            template_sources_str = current_app.config.get('TEMPLATE_SOURCES_URL', '')
            if template_sources_str:
                source_urls = [url.strip() for url in template_sources_str.split(',') if url.strip()]
                logger.info(f"Using {len(source_urls)} template source(s) from environment configuration.")
            else:
                logger.warning("TEMPLATE_SOURCES_URL is not configured in environment. No sources to fetch.")
        else:
            logger.warning("Flask current_app not available, cannot read TEMPLATE_SOURCES_URL from env. No sources to fetch.")

    if not source_urls:
        logger.warning("No template source URLs configured. Cache will be empty.")
        _cached_templates = []
        _is_updating = False
        return

    new_templates_data = []
    processed_titles = set() # Set to keep track of processed template titles for de-duplication

    for url in source_urls:
        logger.info(f"Fetching templates from: {url} for cache update.")
        templates_from_current_url = fetch_templates_from_url(url)

        if templates_from_current_url:
            for template in templates_from_current_url:
                title = template.get('title')
                if not title or not isinstance(title, str): # Skip templates without a valid string title
                    logger.warning(f"Template missing title or title is not a string, skipping: {template}")
                    continue

                normalized_title = title.lower().strip()

                if normalized_title not in processed_titles:
                    new_templates_data.append(template) # Add the original template object
                    processed_titles.add(normalized_title)
                    logger.debug(f"Added template '{title}' (Normalized: '{normalized_title}').")
                else:
                    logger.debug(f"Duplicate template title '{title}' (Normalized: '{normalized_title}') found. Skipping.")
        else:
            logger.warning(f"No templates found or error fetching from {url} during cache update.")

    _cached_templates = new_templates_data
    _is_updating = False
    logger.info(f"Template cache updated. Total unique templates: {len(_cached_templates)} (after de-duplication).")

def get_all_templates():
    """Returns all templates, primarily from cache. Fetches if cache is empty."""
    logger = current_app.logger if current_app else logging.getLogger(__name__)
    if not current_app and (not hasattr(logger, 'handlers') or not logger.handlers): # Check if logger has handlers
        logging.basicConfig(level=logging.INFO) # Ensure logger is configured
        logger = logging.getLogger(__name__)

    if not _cached_templates and not _is_updating:
        logger.info("Cache is empty, attempting initial fetch...")
        update_cached_templates()
    return _cached_templates

def get_template_by_id(template_id_str):
    """Gets a single template by its ID from the cache.
    ID is expected to be title.replace(' ', '_').lower().
    """
    # This function should still work as expected, as it operates on the de-duplicated _cached_templates.
    # The ID generation in routes.py uses title, so if titles are unique in cache, IDs will be too.
    all_templates = get_all_templates()
    for t in all_templates:
        # ID generation must match how it's done in routes.py for display
        title = t.get('title', '') # Ensure title exists
        current_template_id = title.replace(' ', '_').lower()
        if current_template_id == template_id_str:
            return t
    return None
