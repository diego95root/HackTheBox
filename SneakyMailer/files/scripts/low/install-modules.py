import pty
import requests
import subprocess
import re
import threading
import os
import tempfile
import time


username = "pypi"
password = "soufianeelhaoui"

active_threads = 0
max_threads = 5


def get_modules_file() -> tuple:
    response = requests.get("http://pypi.sneakycorp.htb:8080/packages/", auth=(username, password))
    return tuple(map(lambda module: module[1:-3], re.findall(r">.+<\/a", response.text)))


def uninstall_module(file_name: str):
    subprocess.run(f"/home/low/venv/bin/pip uninstall {file_name.replace('.tar.gz', '')}", shell=True)
    os.remove(f"/var/www/pypi.sneakycorp.htb/packages/{file_name}")


def install_module(file_name: str):
    with tempfile.TemporaryDirectory() as temporary_folder:
        # Decompress the tar
        subprocess.run(f"/usr/bin/tar -C {temporary_folder} -zxf /var/www/pypi.sneakycorp.htb/packages/{file_name}", shell=True)
        # Run the installation process
        subprocess.run(f"/usr/bin/screen -d -m /opt/scripts/low/install-module.sh {temporary_folder}/{file_name.replace('.tar.gz', '')}/setup.py &", shell=True)
        time.sleep(3)


def process_module(file_name: str):
    global active_threads
    try:
        install_module(file_name)
    except:
        pass
    try:
        uninstall_module(file_name)
    except:
        pass
    active_threads -= 1
    exit(0)


def main():
    global active_threads
    while True:
        modules_files = get_modules_file()
        for file_name in modules_files:
            while active_threads > max_threads:
                pass
            threading.Thread(target=process_module, args=(file_name,)).start()
            # process_module(file_name)
            active_threads += 1
        time.sleep(5)
    while active_threads > 0:
        pass


if __name__ == "__main__":
    main()


