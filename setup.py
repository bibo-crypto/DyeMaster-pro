from distutils.core import setup
import py2exe

setup(
    windows=['main.py'],
    options={
        'py2exe': {
            'bundle_files': 1,
            'compressed': True,
            'includes': [],
            'excludes': [],
            'dll_excludes': [],
        }
    },
    zipfile=None,
)