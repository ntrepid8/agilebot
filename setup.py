__author__ = 'ntrepid8'
from setuptools import setup, find_packages
import os

# get version
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
with open(os.path.join(__location__, 'agilebot/VERSION.txt')) as f:
    version = f.read()

setup(
    name='agilebot',
    version=version,
    author='Josh Austin',
    author_email='josh.austin@gmail.com',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={'': ['*.txt']},
    entry_points={
        'console_scripts': [
            'agilebot=agilebot.__main__:main'
        ]
    },
    install_requires=[
        'py-trello'
    ]
)
