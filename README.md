# DockYard - Your Docker Application Facilitator

DockYard is a simple web application that helps you discover and install Docker applications from predefined template lists. It's designed to be a lightweight alternative or companion to tools like Portainer for quick deployments.

## Features

*   Browse Docker applications from multiple template sources.
*   View application details: title, description, logo.
*   Install container-based applications directly through the Docker API (Type 2 templates).
*   Configurable template source URLs.
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
```bash
docker --version
```
If Docker is installed, you'll see its version. If not, you'll likely get a "command not found" error, and you should proceed to the next step.

**2. Install Docker Engine**

It's highly recommended to follow the **official Docker installation guide** for your specific Linux distribution to ensure you get the latest and most secure version:
*   **Official Docker Installation Docs:** [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

Below are example commands for some common distributions. **Please prefer the official documentation linked above.**

*   **For Debian/Ubuntu-based systems:**
    ```bash
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
    ```

*   **For Fedora-based systems:**
    ```bash
    # Uninstall old versions (if necessary)
    # sudo dnf remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-selinux docker-engine-selinux docker-engine

    # Set up the Docker repository
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

    # Install Docker Engine
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    ```

**3. Manage Docker as a non-root user (Recommended)**

To run Docker commands without needing `sudo` every time:

```bash
# Create the 'docker' group (it might already exist)
sudo groupadd docker

# Add your user to the 'docker' group
sudo usermod -aG docker $USER
```
**Important:** You'll need to log out and log back in for this group change to take effect. Alternatively, you can activate the changes for the current terminal session by running `newgrp docker` (you might need to open a new terminal).

**4. Start and Enable Docker Service**

Ensure the Docker service is running and enabled to start on boot:

```bash
# Start the Docker service
sudo systemctl start docker

# Enable Docker to start on system boot
sudo systemctl enable docker

# Check the Docker service status (optional)
sudo systemctl status docker
```
You should see that the service is active (running).

**5. Obtain the DockYard Application Code**

If you haven't already, get the DockYard source code. If this is a Git repository:
```bash
# Replace with the actual repository URL if applicable
# git clone https://your-git-repository-url/dockyard.git
# cd dockyard
```
For now, assuming you have the source code in your current directory.

**6. Build the DockYard Docker Image**

Navigate to the root directory of the DockYard project (where the `Dockerfile` is located) and run:
```bash
docker build -t dockyard .
```
This command builds the Docker image for DockYard and tags it as `dockyard`.

**7. Run the DockYard Container**

Once the image is built, you can run DockYard using the following command:

```bash
docker run -d --rm \
    -p 5001:5001 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e TEMPLATE_SOURCES_URL="https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json" \
    -e SECRET_KEY="change_this_to_a_very_strong_secret_key" \
    --name dockyard-app \
    dockyard
```

**Explanation of the `docker run` command:**
*   `-d`: Run in detached mode (in the background).
*   `--rm`: Automatically remove the container when it exits (useful for testing and keeping things clean).
*   `-p 5001:5001`: Map port 5001 on your host to port 5001 in the container (DockYard listens on this port).
*   `-v /var/run/docker.sock:/var/run/docker.sock`: **Crucial!** This mounts the host's Docker socket into the DockYard container, allowing DockYard to manage other Docker containers on your system.
*   `-e TEMPLATE_SOURCES_URL=...`: Sets the URL (or comma-separated URLs) for the application templates.
*   `-e SECRET_KEY=...`: **Important!** Change this to a strong, unique secret key for your instance.
*   `--name dockyard-app`: Assigns a recognizable name to your running container.
*   `dockyard`: The name of the Docker image to run (which you built in the previous step).

*(For users on macOS or Windows, please refer to the official Docker Desktop documentation for installation, then proceed from step 5, adapting paths and commands as necessary.)*

### Accessing DockYard

Once the DockYard container is running, open your web browser and navigate to:
\`http://localhost:5001\`

You should see the DockYard interface listing available applications.

### Configuring Template Sources

DockYard fetches application templates from URLs specified in the \`TEMPLATE_SOURCES_URL\` environment variable. You can customize this when running the container by modifying the \`-e TEMPLATE_SOURCES_URL=...\` part of the \`docker run\` command.

The \`TEMPLATE_SOURCES_URL\` should be a comma-separated list of URLs pointing to Portainer v2 compatible template JSON files.

**Example with multiple template sources:**
\`\`\`bash
docker run -d --rm \
    -p 5001:5001 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e TEMPLATE_SOURCES_URL="https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json,https://another.example.com/templates.json" \
    -e SECRET_KEY="your_strong_secret_key" \
    --name dockyard-app \
    dockyard
\`\`\`
If \`TEMPLATE_SOURCES_URL\` is not provided, it defaults to the one specified in the Dockerfile (or `config.py`).

## How It Works

DockYard consists of:
*   A Flask web application (Python).
*   A template manager that fetches, parses, and caches JSON template files.
*   A Docker manager that interacts with the Docker daemon to pull images and run containers.
*   An APScheduler instance for periodic background updates of templates.

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

## Future Development (Ideas)

*   Support for Docker Compose (Stack) templates (Portainer type 1).
*   User authentication.
*   More detailed container status and management.
*   Periodic background updates for templates.
*   AI-powered discovery of new template sources (as per original request).

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit a pull request.
