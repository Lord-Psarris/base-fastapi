import json
import os 

import configs

# create temp directory and file
os.makedirs(f'{configs.TEMP_FOLDER}', exist_ok=True)
with open(f'{configs.TEMP_FOLDER}/cleanupOrders.json', 'w') as f:
    f.write('{"userToClean": {}}')


def generate_py_extensions_to_clean(filename: str):
    """Generates PyTorch extensions to clean for a given filename."""
    return [f"{filename}.py", f"{filename}.pt", f"{filename}.pth", f"{filename}.onnx"]


def generate_tf_1_extensions_to_clean(filename: str):
    """Generates TensorFlow v1 extensions to clean."""
    return [f"{filename}.pb", f"{filename}.pbtxt"]

framework_handler = {
    "tensorflow": generate_tf_1_extensions_to_clean,
    "pytorch": generate_py_extensions_to_clean
}

framework_lookup = {
    "pb": "tensorflow",
    "py": "pytorch"
}

def clean_files(user_id: str):
    json_content = {}
    with open(f"{configs.TEMP_FOLDER}/cleanupOrders.json", "r") as json_file:
        json_content = json.load(json_file)

    # Getting common name for all tmp files
    tmp_filename = json_content["userToClean"].get(user_id, None)

    if not tmp_filename:
        return

    filename_no_extension = tmp_filename.split(".")[0]
    file_extension = tmp_filename.split(".")[-1]
    framework = framework_lookup[file_extension]

    files_to_delete = [f"{filename_no_extension}.bin", f"{filename_no_extension}.xml", f"{filename_no_extension}.zip"] + framework_handler[framework](filename=filename_no_extension)

    for filename in files_to_delete:
        try:
            os.remove(f"{configs.TEMP_FOLDER}/{filename}")
        except Exception as e:
            print(e)

    # Deleting entry for this user after cleaning
    del json_content["userToClean"][user_id]

    json_formatted = json.dumps(json_content)

    with open(f"{configs.TEMP_FOLDER}/cleanupOrders.json", "w") as json_file:
        json_file.write(json_formatted)

def queue_file_to_delete_after(tmp_file_name: str, user_id: str):
    json_content = {}
    with open(f"{configs.TEMP_FOLDER}/cleanupOrders.json", "r") as json_file:
        json_content = json.load(json_file)

    # Creating entry for file to delete
    json_content["userToClean"][user_id] = tmp_file_name

    json_formatted = json.dumps(json_content)

    with open(f"{configs.TEMP_FOLDER}/cleanupOrders.json", "w") as json_file:
        json_file.write(json_formatted)
