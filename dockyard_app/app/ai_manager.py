import google.generativeai as genai
from flask import current_app
import os
import json

def configure_ai():
    """Configures the generative AI model."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        current_app.logger.error("GOOGLE_API_KEY is not set. AI features will be disabled.")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        current_app.logger.error(f"Failed to configure Google AI: {e}")
        return None

def generate_compose_file(template_data):
    """
    Generates a Docker Compose YAML file from template data using an AI model.
    """
    model = configure_ai()
    if not model:
        return None, "AI model is not configured. Please set the GOOGLE_API_KEY."

    # Constructing a detailed prompt for the AI
    prompt = f"""
    Based on the following JSON template for a Docker application, please generate a complete and valid `docker-compose.yml` file.

    Template Details:
    {json.dumps(template_data, indent=2)}

    Please ensure the following:
    1. The output is only the `docker-compose.yml` content, without any extra explanations or markdown formatting like ```yaml.
    2. The service name should be derived from the application's title, formatted as a lowercase string with underscores instead of spaces.
    3. Use the 'image' field for the image name and tag.
    4. Map the 'ports' correctly in the `ports` section.
    5. Map the 'volumes' correctly in the `volumes` section.
    6. Convert the 'env' variables correctly into the `environment` section.
    7. Set the 'restart_policy' as specified, or use 'unless-stopped' if not provided.

    Generate the `docker-compose.yml` file now.
    """

    try:
        current_app.logger.info("Generating Docker Compose file with AI...")
        response = model.generate_content(prompt)
        # Assuming the response text contains the YAML content directly
        compose_content = response.text
        current_app.logger.info("Successfully generated Docker Compose file.")
        return compose_content, None
    except Exception as e:
        current_app.logger.error(f"Error generating Docker Compose file with AI: {e}")
        return None, f"An error occurred while communicating with the AI model: {str(e)}"