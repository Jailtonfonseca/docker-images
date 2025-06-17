import docker
from flask import current_app
import json # For pretty printing dicts in logs

def get_docker_client():
    """Initializes and returns a Docker client."""
    try:
        client = docker.from_env()
        client.ping()
        current_app.logger.info("Successfully connected to Docker daemon.")
        return client
    except docker.errors.DockerException as e:
        current_app.logger.error(f"Failed to connect to Docker daemon: {e}")
        current_app.logger.error("Ensure Docker is running and the socket is accessible if DockYard is in a container (e.g., -v /var/run/docker.sock:/var/run/docker.sock).")
        return None
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred while initializing Docker client: {e}")
        return None

def parse_ports(port_mappings_str_list):
    current_app.logger.debug(f"Parsing ports from: {port_mappings_str_list}")
    port_bindings = {}
    if not port_mappings_str_list:
        return port_bindings
    for port_map_str in port_mappings_str_list:
        try:
            parts = port_map_str.split(':')
            if len(parts) == 2:
                host_port_str, container_port_proto = parts
                container_port, protocol = container_port_proto.split('/')
                port_bindings[f"{container_port.strip()}/{protocol.strip()}"] = int(host_port_str.strip())
            elif len(parts) == 1:
                container_port_proto = parts[0]
                container_port, protocol = container_port_proto.split('/')
                port_bindings[f"{container_port.strip()}/{protocol.strip()}"] = None
            else:
                current_app.logger.warning(f"Invalid port format during parsing: {port_map_str}")
        except ValueError as e:
            current_app.logger.warning(f"Error parsing port string '{port_map_str}': {e}")
        except Exception as e:
            current_app.logger.warning(f"Unexpected error parsing port string '{port_map_str}': {e}")
    current_app.logger.debug(f"Parsed port_bindings: {port_bindings}")
    return port_bindings

def parse_volumes(volume_mappings_list):
    current_app.logger.debug(f"Parsing volumes from: {volume_mappings_list}")
    volume_bindings = {}
    if not volume_mappings_list:
        return volume_bindings
    for vol in volume_mappings_list:
        if isinstance(vol, dict) and 'container' in vol:
            container_path = vol['container']
            if 'bind' in vol:
                host_path = vol['bind']
                mode = 'ro' if vol.get('readonly', False) else 'rw'
                volume_bindings[host_path] = {'bind': container_path, 'mode': mode}
            else:
                volume_bindings[container_path] = {}
        else:
            current_app.logger.warning(f"Skipping unrecognized volume format during parsing: {vol}")
    current_app.logger.debug(f"Parsed volume_bindings: {volume_bindings}")
    return volume_bindings

def parse_env(env_vars_list):
    current_app.logger.debug(f"Parsing environment variables from: {env_vars_list}")
    env_list_for_sdk = []
    if not env_vars_list:
        return env_list_for_sdk
    for env_var in env_vars_list:
        if isinstance(env_var, dict) and 'name' in env_var:
            name = env_var['name']
            value = env_var.get('value', env_var.get('default', ''))
            env_list_for_sdk.append(f"{name}={value}")
        else:
            current_app.logger.warning(f"Skipping unrecognized environment variable format during parsing: {env_var}")
    current_app.logger.debug(f"Parsed environment variables for SDK: {env_list_for_sdk}")
    return env_list_for_sdk

def install_container_from_template(template_details):
    current_app.logger.info(f"Attempting to install container from template. Full details received: {json.dumps(template_details, indent=2)}")
    client = get_docker_client()
    if not client:
        return False, "Docker client not available."

    try:
        image_name = template_details.get('image')
        if not image_name:
            current_app.logger.error("Installation Error: Missing 'image' name in template.")
            return False, "Missing image name in template."
        current_app.logger.info(f"Target image: {image_name}")

        # Generate a default name if 'name' is not in template (Portainer templates usually use 'title')
        container_name_from_title = (template_details.get('title') or image_name.split(':')[0]).lower().replace(' ', '_').replace('/', '_')
        container_name = template_details.get('name', container_name_from_title) # Use 'name' if present, else from title
        current_app.logger.info(f"Target container name: {container_name}")

        try:
            existing_container = client.containers.get(container_name)
            if existing_container:
                current_app.logger.error(f"Installation Error: A container named '{container_name}' already exists.")
                return False, f"A container named '{container_name}' already exists."
        except docker.errors.NotFound:
            current_app.logger.info(f"Container '{container_name}' does not exist yet. Proceeding.")
            pass

        current_app.logger.info(f"Pulling image: {image_name}...")
        client.images.pull(image_name)
        current_app.logger.info(f"Image pulled successfully: {image_name}")

        ports_raw = template_details.get('ports', [])
        port_bindings = parse_ports(ports_raw)

        volumes_raw = template_details.get('volumes', [])
        volume_bindings = parse_volumes(volumes_raw)

        env_raw = template_details.get('env', [])
        environment_vars = parse_env(env_raw)

        restart_policy_name = template_details.get('restart_policy')
        restart_policy = {"Name": restart_policy_name} if restart_policy_name else {"Name": "unless-stopped"}
        current_app.logger.info(f"Restart policy: {restart_policy}")

        current_app.logger.info(f"Preparing to run container '{container_name}':")
        current_app.logger.info(f"  Image: {image_name}")
        current_app.logger.info(f"  Ports: {json.dumps(port_bindings)}")
        current_app.logger.info(f"  Volumes: {json.dumps(volume_bindings)}")
        current_app.logger.info(f"  Env: {environment_vars}") # Already a list of strings
        current_app.logger.info(f"  Restart Policy: {json.dumps(restart_policy)}")

        container = client.containers.run(
            image=image_name,
            name=container_name,
            ports=port_bindings,
            volumes=volume_bindings,
            environment=environment_vars,
            restart_policy=restart_policy,
            detach=True
        )
        current_app.logger.info(f"Container '{container.name}' (ID: {container.id}) started successfully.")
        return True, f"Container '{container_name}' started successfully."

    except docker.errors.ImageNotFound:
        current_app.logger.error(f"Docker Error: Image not found: {image_name}")
        return False, f"Image not found: {image_name}"
    except docker.errors.APIError as e:
        current_app.logger.error(f"Docker API Error during installation: {e}")
        current_app.logger.error(f"Docker API Error Response: {e.response.text if hasattr(e, 'response') and e.response else 'N/A'}")
        return False, f"Docker API error: {str(e)}"
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during container installation: {e}", exc_info=True)
        return False, f"An unexpected error occurred: {str(e)}"
