import requests
import json
from flask import current_app
from . import config_manager # Import config_manager to get user-defined URLs

_cached_templates = []
_is_updating = False

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
            # Use current_app.logger if available, otherwise print
            logger = current_app.logger if current_app else logging.getLogger(__name__)
            logger.error(f"Unexpected JSON structure from {url}")
            return []
    except requests.exceptions.RequestException as e:
        logger = current_app.logger if current_app else logging.getLogger(__name__)
        logger.error(f"Error fetching template from {url}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger = current_app.logger if current_app else logging.getLogger(__name__)
        logger.error(f"Error decoding JSON from {url}: {e}")
        return []
    # Add a basic logging import for cases where current_app might not be available (e.g. direct script call for testing)
    except NameError: # if current_app is not defined (e.g. no Flask context)
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.error(f"Flask current_app not available. Error fetching/decoding from {url}: {e}")
        return []


def update_cached_templates():
    """Fetches and updates the cached templates.
    Prioritizes user-defined URLs, then falls back to environment config.
    """
    global _cached_templates
    global _is_updating

    # Ensure logger is available even if current_app is not (e.g., during threaded execution startup)
    logger = current_app.logger if current_app else logging.getLogger(__name__)
    if not current_app and not hasattr(logger, 'info'): # Basic setup if no Flask logger
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)


    if _is_updating:
        logger.info("Template update already in progress. Skipping.")
        return

    _is_updating = True
    logger.info("Starting template cache update...")

    source_urls = []
    user_defined_sources = config_manager.get_user_template_sources()

    if user_defined_sources:
        logger.info(f"Using {len(user_defined_sources)} user-defined template source(s).")
        source_urls = user_defined_sources
    else:
        logger.info("No user-defined template sources found or list is empty. Falling back to environment configuration.")
        # Fallback to environment variable if current_app and its config are available
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
        logger.warning("No template source URLs configured (neither user-defined nor environment). Cache will be empty.")
        _cached_templates = []
        _is_updating = False
        return

    new_templates_data = []
    for url in source_urls:
        logger.info(f"Fetching templates from: {url} for cache update.")
        templates = fetch_templates_from_url(url) # This function now also uses a logger
        if templates:
            new_templates_data.extend(templates)
        else:
            logger.warning(f"No templates found or error fetching from {url} during cache update.")

    _cached_templates = new_templates_data
    _is_updating = False
    logger.info(f"Template cache updated. Total templates: {len(_cached_templates)}")

def get_all_templates():
    """Returns all templates, primarily from cache. Fetches if cache is empty."""
    logger = current_app.logger if current_app else logging.getLogger(__name__)
    if not _cached_templates and not _is_updating:
        logger.info("Cache is empty, attempting initial fetch...")
        update_cached_templates()
    return _cached_templates

def get_template_by_id(template_id_str):
    """Gets a single template by its unique ID from the cache."""
    all_templates = get_all_templates()
    for i, t in enumerate(all_templates):
        title = t.get('title')
        if title:
            # Recreate the unique ID using the same logic as in the index route
            current_id = f"{title.replace(' ', '_').lower()}_{i}"
            if current_id == template_id_str:
                # Add the unique id to the template dict before returning
                # so it's available for the caller.
                t['id'] = current_id
                return t
    return None

# Add a basic logging import at module level for the logger fallback in fetch_templates_from_url
import logging
