"""
py2app build script for SEED2_0
"""
 
from setuptools import setup
 
APP = ['SEED2_0.py']
DATA_FILES = ["data"]
OPTIONS = {'argv_emulation': True,
           'iconfile': 'icon.icns',
           'packages': ['PIL','sklearn','pandas','pysindy']
    }
 
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
