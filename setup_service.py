#!/usr/bin/env python3
import os
import sys
import subprocess

"""
Creates a systemd service for website_monitor
"""

if input("This script is intended for use on Linux with systemd. Any other usecase was not tested and might harm your computer. Continue? (y/n) >") != "y":
    print("Aborted.")
    sys.exit(0)

if os.geteuid() != 0:
    print("Error: This script must be run as root (use sudo)")
    sys.exit(1)

print(f"Running as user {os.getenv("USER")}")
SERVICE_NAME = input("Enter service name (default:website_monitor): ")
if SERVICE_NAME == "":
    SERVICE_NAME = "website_monitor"
if input(f"Confirm service name: ") != SERVICE_NAME:
    print("Name doesn't match: Aborting...")
    sys.exit(1)
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "website_monitor.py")
REQUIREMENTS_CHECK_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "check_requirements.py")
# USER = os.getenv("USER")
USER = input(f"The service os owned by root by default, but it has limited access to user-installed python packages. Pick user that has requirements installed.\nWhich user do you want to own the service (make sure it has correct python packages installed)? >> ")
if input("Confirm username >> ") != USER:
    print("Name doesn't match: Aborting...")
    sys.exit(1)
# # This is for importing user packages 
user_site_packages = os.path.expanduser(f'/home/{USER}/.local/lib/python3.13/site-packages')
if user_site_packages not in sys.path:
    sys.path.append(user_site_packages)


SERVICE_CONTENT = f"""[Unit]
Description=Monitor website status and content
After=network.target
Wants=network.target

[Service]
Type=simple
User={USER}
WorkingDirectory={os.path.dirname(SCRIPT_PATH)}
ExecStart={sys.executable} {SCRIPT_PATH}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
"""

def create_service():
    """Create and enable the systemd service"""
    if os.geteuid() != 0:
        print("Error: This script must be run as root (use sudo)")
        sys.exit(1)
    
    try:
        with open(SERVICE_FILE, "w") as f:
            f.write(SERVICE_CONTENT)
        print(f"✓ Service file created at {SERVICE_FILE}")
        
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)
        print(f"✓ Service '{SERVICE_NAME}' enabled")
        print(f"\nStart service: sudo systemctl start {SERVICE_NAME}")
        print(f"Check status: sudo systemctl status {SERVICE_NAME}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_service()