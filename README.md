# DockYard - Your Docker Application Facilitator

DockYard is a simple web application that helps you discover and install Docker applications from predefined template lists. It's designed to be a lightweight alternative or companion to tools like Portainer for quick deployments.

## Features

*   Browse Docker applications from multiple template sources.
*   View application details: title, description, logo.
*   Install container-based applications directly through the Docker API (Type 2 templates).
*   Configurable template source URLs via environment variable **and** through the application UI.
*   User-defined template URLs are persisted if a Docker volume is used.
*   Containerized for easy deployment.
*   Periodic background updates for templates.

## Getting Started

This guide will help you get DockYard running on your system.

### Prerequisites

*   A Linux system (this guide focuses on Linux, but Docker can be installed on macOS and Windows too).
*   Basic familiarity with the command line.

### Linux Installation Guide

Follow these steps to install Docker and run DockYard on your Linux system.

**1. Check if Docker is Installed**

Open your terminal and run:
\`\`\`bash
docker --version
\`\`\`
If Docker is installed, you'll see its version. If not, you'll likely get a "command not found" error, and you should proceed to the next step.

**2. Install Docker Engine**

It's highly recommended to follow the **official Docker installation guide** for your specific Linux distribution to ensure you get the latest and most secure version:
*   **Official Docker Installation Docs:** [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

Below are example commands for some common distributions. **Please prefer the official documentation linked above.**

*   **For Debian/Ubuntu-based systems:**
    \`\`\`bash
    # Update package lists
    sudo apt-get update
    # Install prerequisite packages
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    # Add Docker's stable repository
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    # Update package lists again (after adding new repo)
    sudo apt-get update
    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    \`\`\`

*   **For Fedora-based systems:**
    \`\`\`bash
    # Uninstall old versions (if necessary)
    # sudo dnf remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-selinux docker-engine-selinux docker-engine
    # Set up the Docker repository
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    # Install Docker Engine
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    \`\`\`

**3. Manage Docker as a non-root user (Recommended)**

To run Docker commands without needing \`sudo\` every time:
\`\`\`bash
# Create the 'docker' group (it might already exist)
sudo groupadd docker
# Add your user to the 'docker' group
sudo usermod -aG docker $USER
\`\`\`
**Important:** You'll need to log out and log back in for this group change to take effect. Alternatively, you can activate the changes for the current terminal session by running \`newgrp docker\` (you might need to open a new terminal).

**4. Start and Enable Docker Service**

Ensure the Docker service is running and enabled to start on boot:
\`\`\`bash
# Start the Docker service
sudo systemctl start docker
# Enable Docker to start on system boot
sudo systemctl enable docker
# Check the Docker service status (optional)
sudo systemctl status docker
\`\`\`
You should see that the service is active (running).

**5. Obtain the DockYard Application Code**

Clone the repository from GitHub and navigate into the cloned directory:
\`\`\`bash
git clone https://github.com/Jailtonfonseca/docker-images.git
cd docker-images
\`\`\`
All subsequent commands assume you are in the \`docker-images\` directory.

**6. Build the DockYard Docker Image**

Inside the \`docker-images\` directory (which contains the \`Dockerfile\` for DockYard), run:
\`\`\`bash
docker build -t dockyard .
\`\`\`
This command builds the Docker image for DockYard and tags it as \`dockyard\`.

**7. Run the DockYard Container**

Once the image is built (while still in the \`docker-images\` directory), you can run DockYard. **To persist your custom template URLs added via the UI, it is crucial to mount a volume to `/app_data` inside the container.**

Here's an example using a named volume called \`dockyard_data\`:
\`\`\`bash
docker volume create dockyard_data

docker run -d --rm \
    -p 5001:5001 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v dockyard_data:/app_data \
    -e TEMPLATE_SOURCES_URL="https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json" \
    # IMPORTANT: Always change the SECRET_KEY below to a unique, strong random string!
    # Do NOT use this example value in a production environment.
    -e SECRET_KEY="YOUR_UNIQUE_STRONG_SECRET_KEY_HERE" \
    --name dockyard-app \
    dockyard
\`\`\`
Alternatively, you can use a bind mount to a specific path on your host:
\`\`\`bash
# Example: mkdir -p /path/on/your/host/dockyard_config
# docker run -d --rm \
#     ... (other options) ... \
#     -v /path/on/your/host/dockyard_config:/app_data \
#     ... (rest of options) ...
\`\`\`

**Explanation of the \`docker run\` command (key options):**
*   \`-v dockyard_data:/app_data\`: This mounts a Docker named volume \`dockyard_data\` to the \`/app_data\` directory inside the container. This is where DockYard stores user-defined template URLs (in \`user_template_sources.json\`). **This is essential for persistence.**
*   (Other options like -d, --rm, -p, -v /var/run/docker.sock, -e TEMPLATE_SOURCES_URL, -e SECRET_KEY, --name, dockyard remain as previously explained)

*(For users on macOS or Windows, please refer to the official Docker Desktop documentation for installation, then proceed from step 5, adapting paths and commands as necessary. Ensure you are in the correct directory after cloning and understand how volume mounting works on your system.)*

### Accessing DockYard

Once the DockYard container is running, open your web browser and navigate to:
\`http://localhost:5001\`

You should see the DockYard interface. Look for a "Settings" link (usually in the header) to manage your template sources.

### Configuring Template Sources

DockYard offers two ways to configure template source URLs:

1.  **Via Environment Variable (Initial Default/Fallback):**
    You can set the \`TEMPLATE_SOURCES_URL\` environment variable when running the container (as shown in the \`docker run\` command). This can be a single URL or a comma-separated list of URLs. This serves as the initial default or a fallback.

2.  **Via the Application UI (Recommended for User Customization):**
    *   Navigate to the "Settings" page within the DockYard application (usually accessible from a link in the header).
    *   Here, you can add, view, or modify a list of template source URLs.
    *   **Persistence:** These UI-configured URLs are stored in a file named \`user_template_sources.json\` inside the container's \`/app_data\` directory. To ensure these settings persist across container restarts or updates, you **must** mount a Docker volume to the \`/app_data\` path inside the container (see Step 7 for an example using \`-v dockyard_data:/app_data\`).
    *   **Precedence:** If user-defined URLs are configured through the UI and saved, they will take precedence over (i.e., replace) the URLs specified in the \`TEMPLATE_SOURCES_URL\` environment variable. If the list of user-defined URLs is empty, DockYard will fall back to using the URLs from the environment variable.

## How It Works
DockYard consists of:
*   A Flask web application (Python).
*   A template manager (\`template_manager.py\`) that fetches, parses, and caches JSON template files.
*   A configuration manager (\`config_manager.py\`) that handles storage of user-defined template URLs.
*   A Docker manager (\`docker_manager.py\`) that interacts with the Docker daemon to pull images and run containers.
*   An APScheduler instance for periodic background updates of templates.

## Manual Testing Guide

To manually test the core functionalities of DockYard:

1.  **Build the Docker Image:** (As per step 6 above)
    \`\`\`bash
    docker build -t dockyard .
    \`\`\`
    *Expected: Successful build without errors.*

2.  **Run the DockYard Container (Without Volume for Initial UI Test):**
    For initial UI functionality tests where persistence isn't the primary focus:
    \`\`\`bash
    docker run -d --rm \
        -p 5001:5001 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -e SECRET_KEY="test-secret-for-testing" \
        --name dockyard-test \
        dockyard
    \`\`\`
    *Expected: Container runs. Check logs (\`docker logs dockyard-test\`) for startup messages.*

3.  **Access Web UI:**
    *   Open \`http://localhost:5001\` in your browser.
    *   *Expected: Web page loads and displays applications from the default template source(s).*

4.  **Test Container Installation (Type 2):**
    *   Choose a simple **Type 2 (container)** application from the list (e.g., Nginx, if available in the loaded templates) and click "Install".
        *   **Note:** The installation button currently only supports Type 2 templates. If you attempt to install a template of a different type (e.g., Type 1 for stacks, or if a template's 'type' field is missing or incorrect), you should receive an error message from the application indicating that only Type 2 templates are supported for direct installation.
    *   *Expected (for a valid Type 2 template):*
        *   UI provides feedback on installation progress/success/failure.
        *   If successful, verify the new container is running (\`docker ps\`).
        *   If it exposes ports, test accessing the application.

5.  **Test Duplicate Installation:**
    *   Try installing the same application again.
    *   *Expected: UI shows an error message indicating the container already exists.*

6.  **Test Settings Page UI (Template URL Management):**
    *   Navigate to the "Settings" page (link in the header).
    *   *Expected:* Page loads, textarea for URLs is shown. Initially, it should be empty or reflect \`user_template_sources.json\` if persistence was used before.
    *   Enter a new, valid template URL (e.g., \`https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json\` if not already the default, or another known valid Portainer template JSON URL).
    *   Click "Save Settings".
    *   *Expected:* Success message. The textarea and "Currently Active" list update.
    *   Navigate back to the Home page.
    *   *Expected:* The list of applications should now reflect templates from the newly added source(s). (If the new source is the same as the old one, the list might not change visually but the logs should show it re-fetched).

7.  **Test Clearing User-Defined Sources:**
    *   Go back to "Settings". Clear all URLs from the textarea. Click "Save Settings".
    *   *Expected:* Success message. Textarea is empty. "Currently Active" list indicates fallback to environment defaults.
    *   Navigate to Home.
    *   *Expected:* Application list reverts to using templates from \`TEMPLATE_SOURCES_URL\` defined at container startup.

8.  **Test Persistence of User-Defined Template Sources (Requires Volume Mount):**
    *   Stop the current DockYard container: \`docker stop dockyard-test\` (it will be removed due to \`--rm\`).
    *   Create a named volume: \`docker volume create my_dockyard_user_data\`
    *   Run DockYard again, this time mounting the volume:
        \`\`\`bash
        docker run -d --rm \
            -p 5001:5001 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v my_dockyard_user_data:/app_data \
            -e SECRET_KEY="test-secret-for-testing" \
            -e TEMPLATE_SOURCES_URL="<some_default_env_url>" \
            --name dockyard-test-persistent \
            dockyard
        \`\`\`
    *   Go to "Settings", add one or more unique template URLs, and save. Verify they are active and templates load.
    *   Stop the container: \`docker stop dockyard-test-persistent\`.
    *   Run the container *again* with the *same volume mount*:
        \`\`\`bash
        docker run -d --rm \
            -p 5001:5001 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v my_dockyard_user_data:/app_data \
            -e SECRET_KEY="test-secret-for-testing" \
            -e TEMPLATE_SOURCES_URL="<some_other_default_env_url>" \
            --name dockyard-test-persistent2 \
            dockyard
        \`\`\`
    *   Go to "Settings".
    *   *Expected:* The URLs you saved in the previous run (with \`dockyard-test-persistent\`) should still be present in the textarea and active, because they were read from the \`my_dockyard_user_data\` volume. The \`TEMPLATE_SOURCES_URL\` from this second run should be ignored if persisted URLs exist.
    *   Verify templates from these persisted URLs are shown on the Home page.

9.  **Cleanup:**
    *   Stop the DockYard test container(s): \`docker stop dockyard-test dockyard-test-persistent dockyard-test-persistent2\` (if not run with \`--rm\`, otherwise they are already gone if stopped).
    *   Remove any containers installed by DockYard during testing.
    *   Optionally, remove the test volume: \`docker volume rm my_dockyard_user_data\`.

This guide helps ensure the main features are working as intended.

## Future Development (Ideas)

*   Support for Docker Compose (Stack) templates (Portainer type 1).
*   User authentication.
*   More detailed container status and management.
*   Periodic background updates for templates.
*   AI-powered discovery of new template sources (as per original request).

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit a pull request.
