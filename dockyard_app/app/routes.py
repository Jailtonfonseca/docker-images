from app import app
from flask import render_template, jsonify, request
from . import template_manager # template_manager now handles caching
from . import docker_manager

@app.route('/')
def index():
    app.logger.info("Index route called.")
    # get_all_templates() now returns from cache or fetches if empty
    templates_data = template_manager.get_all_templates()
    processed_templates = []
    if templates_data:
        for t in templates_data:
            template_type = t.get('type')
            title = t.get('title')
            if title and (template_type == 1 or template_type == 2):
                processed_templates.append({
                    'id': title.replace(' ', '_').lower(),
                    'title': title,
                    'description': t.get('description', 'No description available.'),
                    'logo': t.get('logo', ''),
                    'type': template_type,
                })
    app.logger.info(f"Displaying {len(processed_templates)} templates from cache.")
    return render_template("index.html", title="DockYard - Available Apps", templates=processed_templates)

@app.route('/templates_json')
def list_templates_json():
    app.logger.info("Templates JSON route called.")
    templates_data = template_manager.get_all_templates() # Returns from cache
    if not templates_data:
        app.logger.warning("No template data in cache for JSON endpoint.")
        return jsonify({"error": "No templates found in cache."}), 404
    app.logger.info(f"Returning {len(templates_data)} templates from cache via JSON.")
    return jsonify(templates_data)

@app.route('/install_app', methods=['POST'])
def install_app_route():
    app.logger.info("Install app route called.")
    data = request.get_json()
    if not data or 'template_id' not in data:
        return jsonify({"success": False, "message": "Missing template_id in request."}), 400

    template_id_to_install = data['template_id']
    app.logger.info(f"Attempting to install template with ID: {template_id_to_install} using cached data.")

    # Fetch the specific template details from cache using its ID
    target_template = template_manager.get_template_by_id(template_id_to_install)

    if not target_template:
        app.logger.error(f"Template with ID '{template_id_to_install}' not found in cache.")
        return jsonify({"success": False, "message": f"Template '{template_id_to_install}' not found."}), 404

    if target_template.get('type') != 2: # Check type from cached template
        app.logger.warning(f"Template '{template_id_to_install}' found, but it's not a type 2 (container) template. Type: {target_template.get('type')}")
        return jsonify({"success": False, "message": f"Installation for this template type ({target_template.get('type')}) is not yet supported."}), 400

    app.logger.info(f"Found template in cache: {target_template.get('title')}. Proceeding with installation.")
    success, message = docker_manager.install_container_from_template(target_template)

    if success:
        app.logger.info(f"Installation successful: {message}")
    else:
        app.logger.error(f"Installation failed: {message}")

    return jsonify({"success": success, "message": message})
