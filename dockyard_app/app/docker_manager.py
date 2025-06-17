import docker
from flask import current_app

def get_docker_client():
    """Initializes and returns a Docker client."""
    try:
        # If running inside a container with /var/run/docker.sock mounted
        client = docker.from_env()
        # Verify connection
        client.ping()
        current_app.logger.info("Successfully connected to Docker daemon.")
        return client
    except docker.errors.DockerException as e:
        current_app.logger.error(f"Failed to connect to Docker daemon: {e}")
        current_app.logger.error("Ensure Docker is running and the socket is accessible if DockYard is in a container (e.g., -v /var/run/docker.sock:/var/run/docker.sock).")
        return None
    except Exception as e: # Catch any other unexpected errors during client initialization
        current_app.logger.error(f"An unexpected error occurred while initializing Docker client: {e}")
        return None

def parse_ports(port_mappings_str_list):
    """
    Parses port mappings from Portainer template format (e.g., "80:8080/tcp")
    into Docker SDK format { 'container_port/protocol': host_port }.
    Example: ["80:8080/tcp", "443:8443/tcp"]
    Becomes: {'8080/tcp': 80, '8443/tcp': 443}
    If only container port is given (e.g., "8080/tcp"), it will be published to a random host port.
    Example: ["8080/tcp"] becomes {'8080/tcp': None}
    """
    port_bindings = {}
    if not port_mappings_str_list:
        return port_bindings
    for port_map_str in port_mappings_str_list:
        try:
            # Format is host:container/protocol or container/protocol
            parts = port_map_str.split(':')
            if len(parts) == 2: # host:container/protocol
                host_port_str, container_port_proto = parts
                container_port, protocol = container_port_proto.split('/')
                port_bindings[f"{container_port}/{protocol}"] = int(host_port_str)
            elif len(parts) == 1: # container/protocol
                container_port_proto = parts[0]
                container_port, protocol = container_port_proto.split('/')
                port_bindings[f"{container_port}/{protocol}"] = None # Publish to random host port
            else:
                current_app.logger.warning(f"Invalid port format: {port_map_str}")
        except ValueError as e:
            current_app.logger.warning(f"Error parsing port string '{port_map_str}': {e}")
        except Exception as e: # Catch any other parsing errors
            current_app.logger.warning(f"Unexpected error parsing port string '{port_map_str}': {e}")
    return port_bindings


def parse_volumes(volume_mappings_list):
    """
    Parses volume mappings from Portainer template format.
    Example: [{"bind": "/mnt/host", "container": "/data", "readonly": false}]
    Becomes: {'/mnt/host': {'bind': '/data', 'mode': 'rw'}}
    If only container path is given, it's an anonymous volume.
    Example: [{"container": "/data"}] becomes: {'/data': {}} (Docker SDK handles anonymous volume creation)
    This needs to be adapted if Portainer templates use a simpler string format like "host_path:container_path:mode".
    The example template (Qballjos) uses the object format.
    """
    volume_bindings = {}
    if not volume_mappings_list:
        return volume_bindings
    for vol in volume_mappings_list:
        if isinstance(vol, dict) and 'container' in vol:
            container_path = vol['container']
            if 'bind' in vol: # Host-mounted volume
                host_path = vol['bind']
                mode = 'ro' if vol.get('readonly', False) else 'rw'
                volume_bindings[host_path] = {'bind': container_path, 'mode': mode}
            else: # Anonymous or named volume (if 'bind' is missing but it's a named volume)
                  # For simplicity, we'll treat it as an anonymous volume request for the container path
                  # Docker SDK handles {'/path/in/container': {}} as creating an anonymous volume.
                  # If it's a named volume, the `name` field would be present in Portainer templates usually.
                  # For now, we'll assume simple anonymous if no bind path.
                volume_bindings[container_path] = {} # Let Docker create an anonymous volume for this path
        else:
            current_app.logger.warning(f"Skipping unrecognized volume format: {vol}")
    return volume_bindings

def parse_env(env_vars_list):
    """
    Parses environment variables from Portainer template format.
    Each item in list is a dict: {"name": "VAR_NAME", "label": "Label", "description": "", "default": "value", "value": "actual_user_value_if_set"}
    We primarily care about 'name' and 'default' (or 'value' if set, but templates usually provide 'default').
    Returns a list of "NAME=VALUE" strings.
    """
    env_list_for_sdk = []
    if not env_vars_list:
        return env_list_for_sdk
    for env_var in env_vars_list:
        if isinstance(env_var, dict) and 'name' in env_var:
            name = env_var['name']
            # Portainer templates might have 'value' if user pre-filled, otherwise 'default'
            value = env_var.get('value', env_var.get('default', ''))
            env_list_for_sdk.append(f"{name}={value}")
        else:
            current_app.logger.warning(f"Skipping unrecognized environment variable format: {env_var}")
    return env_list_for_sdk

# Main function to install a container based on parsed template details.
# Handles image pulling, container creation, and error reporting.
def install_container_from_template(template_details):
    """
    Pulls a Docker image and runs a container based on template details.
    'template_details' is expected to be a dictionary for a single template.
    """
    client = get_docker_client()
    if not client:
        return False, "Docker client not available."

    try:
        image_name = template_details.get('image')
        if not image_name:
            return False, "Missing image name in template."

        container_name = template_details.get('title', image_name.split(':')[0]).lower().replace(' ', '_') # Basic name generation

        # Check for existing container with the same name
        try:
            existing_container = client.containers.get(container_name)
            if existing_container:
                return False, f"A container named '{container_name}' already exists."
        except docker.errors.NotFound:
            pass # Good, container does not exist

        current_app.logger.info(f"Pulling image: {image_name}")
        client.images.pull(image_name)
        current_app.logger.info(f"Image pulled: {image_name}")

        ports_raw = template_details.get('ports', []) # Assuming structure like ["80:8080/tcp"]
        port_bindings = parse_ports(ports_raw)

        volumes_raw = template_details.get('volumes', []) # Assuming structure like [{"bind": "/host", "container": "/container"}]
        volume_bindings = parse_volumes(volumes_raw)

        env_raw = template_details.get('env', []) # Assuming structure like [{"name": "NAME", "default": "value"}]
        environment_vars = parse_env(env_raw)

        restart_policy_name = template_details.get('restart_policy') # e.g. "always", "on-failure"
        restart_policy = {"Name": restart_policy_name} if restart_policy_name else {"Name": "unless-stopped"}


        current_app.logger.info(f"Creating container '{container_name}' from image '{image_name}' with ports: {port_bindings}, volumes: {volume_bindings}, env: {environment_vars}, restart_policy: {restart_policy}")

        container = client.containers.run(
            image=image_name,
            name=container_name,
            ports=port_bindings,
            volumes=volume_bindings,
            environment=environment_vars,
            restart_policy=restart_policy,
            detach=True  # Run in detached mode
        )
        current_app.logger.info(f"Container '{container.name}' (ID: {container.id}) started successfully.")
        return True, f"Container '{container_name}' started successfully."

    except docker.errors.ImageNotFound:
        current_app.logger.error(f"Image not found: {image_name}")
        return False, f"Image not found: {image_name}"
    except docker.errors.APIError as e:
        current_app.logger.error(f"Docker API error: {e}")
        return False, f"Docker API error: {e.response.text if e.response else str(e)}"
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during container installation: {e}")
        return False, f"An unexpected error occurred: {str(e)}"
