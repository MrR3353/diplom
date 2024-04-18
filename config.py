import os
from pathlib import Path

BASE_PATH = Path(os.getcwd())
# BASE_PATH = Path(os.path.join(BASE_PATH, 'folder'))
VCS_FOLDER = Path(os.path.join(BASE_PATH, '.vcs'))
DATA_FOLDER = Path(os.path.join(VCS_FOLDER, 'data'))
HEAD_PATH = Path(os.path.join(VCS_FOLDER, 'HEAD'))
GITIGNORE = '.gitignore'
