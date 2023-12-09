from fastapi.exceptions import HTTPException
import aiofiles
import tarfile
import shutil
import docker
import uuid
import io
import os


AZURE_DATABASE = os.environ.get('AZURE_DATABASE')
AZURE_HOST = os.environ.get('AZURE_HOST')
AZURE_PASSWORD = os.environ.get('AZURE_PASSWORD')
AZURE_USER = os.environ.get('AZURE_USER')
AZURE_PORT = os.environ.get('AZURE_PORT')

#—————————————————————————————————————————————————————————————————————————#
# SECTION Classes
#—————————————————————————————————————————————————————————————————————————#


class DockerVPNManager:
    """
    Manages docker operations for remote-host VPN support.
    """
    openvpn_sessions = {}

    def __init__(self):
        self.client = docker.from_env()

    @staticmethod
    def _send_auth_to_openvpn_client(container, source_dir: str, dst_dir: str):
        """
        Copies a given OpenVPN session's auth files to the target location.

        :param docker.Container container: The container instance to copy to.
        :param str source_dir: An absolute path to use as the source.
        :param str dst_dir: The target location for the container. 
        """
        tar_name = 'vpn.tar.gz'
        stream = io.BytesIO()

        # Creating tar file containing certificates / keys
        with tarfile.open(f'{source_dir}/{tar_name}', mode='w:gz') as archive:
            archive.add(source_dir, arcname='.')

        # Writing tar file into a stream to send to OpenVPN client
        with tarfile.open(fileobj=stream, mode='w|') as stream_tar, open(f'{source_dir}/{tar_name}', 'rb') as tar:
            info = stream_tar.gettarinfo(fileobj=tar)
            info.name = os.path.basename(source_dir)
            stream_tar.addfile(info, tar)

        try:
            container.put_archive(dst_dir, stream.getvalue())
        except Exception as e:
            print("Put archive exception: ", e)

    async def create_openvpn_session(self, files):
        """
        Creates a session for a remote-host OpenVPN connection.

        A session is a way to track the container instances for a 
        specific VPN-enabled connection request, as well as any 
        related authentication files for the VPN.

        :param dict files: A dict containing filenames as keys and byte values.
        :rtype str: session_id
        """
        session_id: str = str(uuid.uuid4())

        session_id = session_id.replace("-", "")

        session_path = self.get_session_directory(session_id)

        auth_files = {}
        for filename, file_data in files.items():
            async with aiofiles.open(f"{session_path}/{filename}", "wb") as vpn_file:
                await vpn_file.write(file_data)
                auth_files[filename] = file_data

        # Initializing session entry into openvpn sessions
        self.openvpn_sessions[session_id] = {
            "vpn-client-container": None,
            "remote-api-container": None,
            "session_id": session_id
        }

        return session_id, auth_files

    def start_openvpn(self, session_id):
        """
        Starts an OpenVPN container for a given session.

        :param str session_id: The ID of the session.
        :rtype docker.Container: vpn_container
        """
        session_path = self.get_session_directory(session_id)
        
        vpn_container = self.client.containers.create("fmax-dock-reg-priv.flapmax.com/flapmax/openvpn-client:latest",
                                                      cap_add="NET_ADMIN", devices=["/dev/net/tun:/dev/net/tun"], environment=["KILL_SWITCH=off"])

        self._send_auth_to_openvpn_client(
            vpn_container, session_path, '/data/vpn')

        self.openvpn_sessions[session_id]["vpn-client-container"] = vpn_container

        vpn_container.start()

        success = False
        streamed_logs = vpn_container.logs(stream=True)
        bytes_str = "Initialization Sequence Completed".encode()

        for line in streamed_logs:
            if bytes_str in line:
                success = True
                break
            else:
                continue

        if not success:
            raise HTTPException(
                status_code=400, detail="OpenVPN tunnel failed. Check credentials.")

        return vpn_container

    def start_remote_api(self, session_id):
        """
        Starts a remote API container for a given session.

        This API grants access to initialization and inference
        functions on the remote host for this session.

        :param str session_id: The ID of the session.
        :rtype docker.Container: remote_api_container
        """
        vpn_container = self.openvpn_sessions[session_id]['vpn-client-container']

        # Setting ENV values for database connection in measure-vpn-remote
        env_dict = {
            "AZURE_DATABASE": AZURE_DATABASE,
            "AZURE_HOST": AZURE_HOST,
            "AZURE_PASSWORD": AZURE_PASSWORD,
            "AZURE_USER": AZURE_USER,
            "AZURE_PORT": AZURE_PORT
        }

        # Starts the VPN Remote container and attaches it to the OpenVPN client network
        # To route traffic through VPN
        remote_api_container = self.client.containers.create("fmax-dock-reg-priv.flapmax.com/flapmax/measure-vpn-remote:latest",
                                                             network_mode=f'container:{vpn_container.id}', environment=env_dict)

        self.openvpn_sessions[session_id]["remote-api-container"] = remote_api_container

        remote_api_container.start()

        return remote_api_container

    def get_session_ip(self, session_id):
        """
        Gets the IP address for a session's VPN container.

        :param str session_id: The ID of the session.
        """
        vpn_container = self.openvpn_sessions[session_id]['vpn-client-container']

        vpn_container.reload()

        attrs = vpn_container.attrs

        ip_address = attrs["NetworkSettings"]["IPAddress"]

        return ip_address

    def stop_session(self, session_id):
        """
        Stops the containers for a given session.

        :param str session_id: The ID of the session.
        :rtype int: exit_code
        """
        session = self.openvpn_sessions[session_id]

        try:
            session["remote-api-container"].stop()
        except Exception as e:
            print(e)

        try:
            session["vpn-client-container"].stop()
        except Exception as e:
            print(e)

        session_path = self.get_session_directory(session_id)
        shutil.rmtree(session_path)

        return 0

    @staticmethod
    def get_session_directory(session_id: str) -> str:
        session_path =  f'__remote/sessions/{session_id}'
        
        os.makedirs('__remote/sessions', exist_ok=True)
        os.makedirs(session_path, exist_ok=True)

        return session_path