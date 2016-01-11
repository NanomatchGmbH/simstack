try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Implementation of the UNICORE REST api in python',
    'author': ['Florian Muenchbach','Timo Strunk']
    'url': 'momentan noch keine',
    'download_url': 'still nothing',
    'author_email': 'well',
    'version': '0.1',
    'install_requires': ['nose','enum34'],
    'packages': ['pyura'],
    'scripts': [],
    'name': 'pyura'
}

setup(**config)
