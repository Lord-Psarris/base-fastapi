from utils.host_handler import download_fmax_docker_image


def install_docker_centos(ssh_client):
    """
    Installs Docker Engine for a CentOS client.
    """
    status = "Failed"

    uninstall_old_docker = ssh_client.run_command("""sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine""")
    for line in uninstall_old_docker.stdout:
        print(line)

    install_utils = ssh_client.run_command("sudo yum install -y yum-utils")
    for line in install_utils.stdout:
        print(line)

    setup_repository = ssh_client.run_command("""sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
    """)
    for line in setup_repository.stdout:
        print(line)

    # Installing Docker Engine
    install_docker = ssh_client.run_command("sudo yum -y install docker-ce docker-ce-cli containerd.io")
    for line in install_docker.stdout:
        print(line)

    start_docker = ssh_client.run_command("sudo systemctl start docker")
    for line in start_docker.stdout:
        print(line)

    # Verify the installation was successful
    verify_installation = ssh_client.run_command("sudo docker run hello-world")
    for line in verify_installation.stdout:
        if "This message shows that your installation appears to be working correctly." in line:
            print("Great success.")
            status = "Success"

    return status


def open_port_centos(ssh_client, port=4000):
    """
    Opens a port on a CentOS 7 client.
    """
    status = "Failed"

    # Starting firewall service
    ssh_client.run_command("sudo systemctl start firewalld")

    # Opening Port
    open_port = ssh_client.run_command(f"sudo firewall-cmd --permanent --add-port={port}/tcp")
    for line in open_port.stdout:
        print(line)
        if "success" in line:
            status = "Success"

    # If port was opened, reload service to enable new setting
    if status == "Success":
        status = "Failed"
        reload_config = ssh_client.run_command("sudo firewall-cmd --reload")
        for line in reload_config.stdout:
            print(line)
            if "success" in line:
                status = "Success"


    return status


def run_setup_centos(ssh_client):
    """
    Runs the setup process for a CentOS 7 client.
    """
    status = "Failed"
    has_docker = True

    # Check if Docker is installed
    docker_info = ssh_client.run_command("yum list installed docker-ce")
    for line in docker_info.stderr:
        if "No matching Packages to list" in line:
            has_docker = False

    # Install Docker if not installed
    if not has_docker:
        print("Installing Docker")
        result = install_docker_centos(ssh_client)
        if result == "Failed":
            return "Docker Installation Failed"

    # Install measure-remote image from Dockerhub
    install_success = False


    install_success = download_fmax_docker_image(ssh_client)
    print("Install Success: ", install_success)

    # Open port 4000 for REST API
    if install_success:
        result = open_port_centos(ssh_client, 4000)
        if result == "Success":
            status = "Success"

    return status

