from utils.host_handler import download_fmax_docker_image


def run_setup_ubuntu(ssh_client, cpu_name):
    """
    Runs the setup processes for an Ubuntu 18.04+ client.
    """
    status = "failed"
    has_docker = True

    # Check if Docker is installed
    docker_info = ssh_client.run_command("dpkg -s docker-ce")
    for line in docker_info.stderr:
        if "package 'docker-ce' is not installed" in line:
            has_docker = False
            break

    # Install Docker if not installed
    if not has_docker:
        print("Installing docker")
        result = install_docker_ubuntu(ssh_client)
        
        print("Install Docker result", result)
        if result == "failed":
            return "Docker Installation Failed"

    # Install measure-remote image from Dockerhub
    install_success = download_fmax_docker_image(ssh_client)

    # Open port 4000 for REST API
    if install_success:
        open_port = ssh_client.run_command("sudo ufw allow 4000/tcp")
        for line in open_port.stdout:
            if "Rules updated" in line or "Skipping adding existing rule" in line:
                status = "success"

    return status


def install_docker_ubuntu(ssh_client):
    """
    Installs Docker Engine for an Ubuntu client using x86_64 / amd64 processor architecture.
    """
    # Initialize status which will be updated to success upon running Hello World from Docker
    status = "failed"

    # Running through the Docker Engine install steps (https://docs.docker.com/engine/install/ubuntu/)
    remove_packages = ssh_client.run_command("sudo apt-get remove docker docker-engine docker.io containerd runc")
    for line in remove_packages.stdout:
        print("Remove packages: ", line)

    update_index = ssh_client.run_command("sudo apt-get update")
    for line in update_index.stdout:
        print(line)

    install_dependencies = ssh_client.run_command("sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release")
    for line in install_dependencies.stdout:
        print(line)

    add_docker_gpg_key = ssh_client.run_command("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg")
    for line in add_docker_gpg_key.stdout:
        print(line)

    setup_stable_repository = ssh_client.run_command("""echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   """)
    for line in setup_stable_repository.stdout:
        print(line)

    update_index = ssh_client.run_command("sudo apt-get update")
    for line in update_index.stdout:
        print(line)

    # Installing Docker Engine
    install_docker = ssh_client.run_command("sudo apt-get install -y docker-ce docker-ce-cli containerd.io")
    for line in install_docker.stdout:
        print(line)

    # Verify the installation was successful
    verify_installation = ssh_client.run_command("sudo docker run hello-world")
    for line in verify_installation.stdout:
        if "This message shows that your installation appears to be working correctly." in line:
            print("Great success.")
            status = "success"

    return status
