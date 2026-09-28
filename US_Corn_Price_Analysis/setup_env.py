import subprocess
import sys
import os

def install_requirements():
    requirements_file = 'requirements.txt'
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        return

    print("--- 1. Upgrading pip ---")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        pass

    print("--- 2. Installing Dependencies ---")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("\nSUCCESS: Environment Ready.")
    except subprocess.CalledProcessError:
        print("\nERROR: Installation failed.")

if __name__ == "__main__":
    install_requirements()