import sys
import os
from appdirs import user_data_dir
import requests

GITHUB_URL = "https://github.com/guysoft/backupfriend-client"
GITHUB_API = "https://api.github.com/repos/guysoft/backupfriend-client"

def ensure_dir(d, chmod=0o777):
    """
    Ensures a folder exists.
    Returns True if the folder already exists
    """
    if not os.path.exists(d):
        os.makedirs(d, chmod)
        os.chmod(d, chmod)
        return False
    return True


def get_data_path():
    appname = "BackupFriend"
    appauthor = "Guy Sheffer (GuySoft)"

    if "linux" in sys.platform:
        DATA_PATH = os.path.expanduser(os.path.join("~", ".backupfriend"))
    else:
        DATA_PATH = user_data_dir(appname, appauthor)
    return DATA_PATH


def resource_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    print("getting base path")
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    print(base_path)
    return base_path


def get_latest_version():
    """
    Get latest version, none if no version found
    """
    try:
        response = requests.get(GITHUB_API + "/tags")
        data = response.json()[0]
        if "name" in data:
            return data["name"]
    except Exception:
        return
    return
