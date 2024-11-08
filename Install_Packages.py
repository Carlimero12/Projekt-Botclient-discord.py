import subprocess
import sys
import pkg_resources

def install_main():
    required_packages = ["discord", "asyncio", "json5", "threading", "audioop-lts"]
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}

    for package in required_packages:
        if package not in installed_packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package])
