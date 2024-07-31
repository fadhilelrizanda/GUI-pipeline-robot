from PyInstaller.utils.hooks import copy_metadata

# Copy metadata for the 'python-dotenv' package to ensure it is included.
datas = copy_metadata('dotenv')
