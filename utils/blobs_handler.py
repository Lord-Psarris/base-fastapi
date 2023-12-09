import requests


def upload_file_to_azure(file_data: bytes, container_name: str = 'measureuploads', folder: str = '', overwrite_existing: bool = False):
    """
    Uploads to Blob using in-memory data from objects such as TemporarySpooledFiles.
    """
    params = {
        "overwrite": overwrite_existing,
        "container": container_name,
        "folder": folder,
    }
    files = {
        "file": file_data
    }
    response = requests.post('https://flapmax-blob-storage.wonderfulfield-8a109abc.eastus.azurecontainerapps.io/upload-file',
                             params=params, files=files, headers={"accept": "application/json"})
    response.raise_for_status()

    return response.json()
