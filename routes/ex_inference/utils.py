from database import ssh_crud

import os
import uuid
import base64
import configs


# DEPRECATED
def setup_server(environment: dict, name: str = "myvm"):
    
    # pull private key
    ssh_item = ssh_crud.get({"environment_id": environment["_id"]})
    ssh_key_path = f"{configs.TEMP_FOLDER}/{str(uuid.uuid1()).replace('-', '_')}.pem"
    
    with open(ssh_key_path, "wb") as temp_file:
        file_data = base64.b64decode(ssh_item["key_file"])
        temp_file.write(file_data)
    
    # run chmod on ssh file
    os.system(f"sudo chmod 400 ./{ssh_key_path}")
    print("--- setup private key ---")
    
    # setting dynamic path
    uninstall_path = configs.ansible.ANS_UNINSTALL_PATH.replace("<name>", name)
    install_path = configs.ansible.ANS_INSTALL_PATH.replace("<name>", name)
    inventory_path = configs.ansible.INVENTORY_PATH.replace("<name>", name)
    
    # add to ansible inventory
    with open(inventory_path, "w") as f:
        text = configs.ansible.docs.inventory_setup \
                .replace("<name>", name).replace("<ip_address>", environment["hostname"]) \
                .replace("<ssh_user>", environment["username"]).replace("<ssh_key_path>", ssh_key_path)
        f.write(text)
        
    # add to ansible install
    with open(install_path, "w") as f:
        text = configs.ansible.docs.install_setup.replace("<name>", name)
        f.write(text)
        
    # add to ansible uninstall
    with open(uninstall_path, "w") as f:
        text = configs.ansible.docs.unistall_setup.replace("<name>", name)
        f.write(text)
    
    # test ansible setup
    p = os.popen(f'ansible -i {inventory_path} {name} -m ping')
    print(p.read())
    print("\n\n")
    
    # setup ansible container
    p = os.popen(f"ansible-playbook {install_path} -i {inventory_path}")
    print(p.read())
    
    return True

