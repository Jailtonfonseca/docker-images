# DockYard - Your Docker Application Facilitator

DockYard is a simple web application that helps you discover and install Docker applications from predefined template lists. It's designed to be a lightweight alternative or companion to tools like Portainer for quick deployments.

## Features

*   Browse Docker applications from multiple template sources.
*   View application details: title, description, logo.
*   Install container-based applications directly through the Docker API.
*   Configurable template source URLs.
*   Containerized for easy deployment.

## Getting Started

### Prerequisites

*   Docker installed and running on your system.

### Building DockYard (Optional)

If you want to build the DockYard image yourself:

1.  Clone this repository (if applicable, or ensure you have the source code).
2.  Navigate to the project root directory (where the Dockerfile is).
3.  Build the Docker image:
    \`\`\`bash
    docker build -t dockyard .
    \`\`\`

### Running DockYard

To run the DockYard container:

\`\`\`bash
docker run -d \
    -p 5001:5001 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --name dockyard \
    dockyard
    # Image name might be different if you tagged it differently or pulled from a registry
\`\`\`

**Explanation of options:**

*   \`-d\`: Run the container in detached mode.
*   \`-p 5001:5001\`: Map port 5001 on your host to port 5001 in the container (where the DockYard app runs).
*   \`-v /var/run/docker.sock:/var/run/docker.sock\`: **Crucial!** This mounts the host's Docker socket into the DockYard container, allowing it to manage other Docker containers.
*   \`--name dockyard\`: Assign a name to the container for easy management.
*   \`dockyard\`: The name of the image to run.

### Configuring Template Sources

DockYard fetches application templates from URLs specified in the \`TEMPLATE_SOURCES_URL\` environment variable. You can customize this when running the container.

The \`TEMPLATE_SOURCES_URL\` should be a comma-separated list of URLs pointing to Portainer v2 compatible template JSON files.

**Example with a custom template source:**

\`\`\`bash
docker run -d \
    -p 5001:5001 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e TEMPLATE_SOURCES_URL="https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json,https://another.example.com/templates.json" \
    --name dockyard \
    dockyard
\`\`\`

If \`TEMPLATE_SOURCES_URL\` is not provided, it defaults to: \`https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json\`.

### Accessing DockYard

Once running, open your web browser and navigate to \`http://localhost:5001\`.

## How It Works

DockYard consists of:

*   A Flask web application (Python).
*   A template manager that fetches and parses JSON template files.
*   A Docker manager that interacts with the Docker daemon to pull images and run containers.

## Future Development (Ideas)

*   Support for Docker Compose (Stack) templates (Portainer type 1).
*   User authentication.
*   More detailed container status and management.
*   Periodic background updates for templates.
*   AI-powered discovery of new template sources (as per original request).

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit a pull request.

## Manual Testing Guide

To manually test the core functionalities of DockYard:

1.  **Build the Docker Image:**
    \`\`\`bash
    docker build -t dockyard .
    \`\`\`
    *Expected: Successful build without errors.*

2.  **Run the DockYard Container:**
    *   Use the default template source:
        \`\`\`bash
        docker run -d --rm \
            -p 5001:5001 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -e SECRET_KEY="test-secret" \
            --name dockyard-test \
            dockyard
        \`\`\`
        *(Using \`--rm\` for easier cleanup after testing)*
    *   *Expected: Container runs. Check logs (\`docker logs dockyard-test\`) for startup, initial template fetch, and scheduler messages.*

3.  **Access Web UI:**
    *   Open \`http://localhost:5001\` in your browser.
    *   *Expected: Web page loads and displays applications from the default template source.*

4.  **Test Container Installation (Type 2):**
    *   Choose a simple container application (e.g., Nginx, if available) and click "Install".
    *   *Expected:*
        *   UI provides feedback on installation progress/success/failure.
        *   If successful, verify the new container is running (\`docker ps\`).
        *   If it exposes ports, test accessing the application.

5.  **Test Duplicate Installation:**
    *   Try installing the same application again.
    *   *Expected: UI shows an error message indicating the container already exists.*

6.  **Test with Custom Template Sources:**
    *   Stop the current test container (\`docker stop dockyard-test\`).
    *   Run DockYard with the \`TEMPLATE_SOURCES_URL\` environment variable:
        \`\`\`bash
        docker run -d --rm \
            -p 5001:5001 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -e TEMPLATE_SOURCES_URL="https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json,https://another-valid.url/templates.json" \
            -e SECRET_KEY="test-secret" \
            --name dockyard-test \
            dockyard
        \`\`\`
        *(Replace \`https://another-valid.url/templates.json\` with an actual valid template URL if you have one for testing).*
    *   *Expected: Applications from all specified valid URLs are listed.*

7.  **Check Periodic Update (Optional):**
    *   To test scheduled updates quickly, you can set a short interval when running:
        \`\`\`bash
        # Example: Set update interval to 1 hour (or less for quicker check)
        docker run -d --rm \
            -p 5001:5001 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -e TEMPLATE_UPDATE_INTERVAL_HOURS="1" \
            -e SECRET_KEY="test-secret" \
            --name dockyard-test \
            dockyard
        \`\`\`
    *   Leave DockYard running and check logs after the interval.
    *   *Expected: Logs show messages about periodic cache updates.*

8.  **Cleanup:**
    *   Stop the DockYard test container: \`docker stop dockyard-test\` (if not run with \`--rm\`).
    *   Stop any containers installed by DockYard during testing.

This guide helps ensure the main features are working as intended.
