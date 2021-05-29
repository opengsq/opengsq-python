import os

from setuptools import find_packages, setup

version_contents = {}
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'opengsq', 'version.py'), encoding='utf-8') as f:
    exec(f.read(), version_contents)

with open('README.md', 'r') as file:
    long_description = file.read()

setup(
    name='opengsq',
    version=version_contents['VERSION'],
    description='🐍 OpenGSQ - Python library for querying game servers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    scripts=['bin/opengsq'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    url='https://github.com/opengsq/opengsq-python',
    author='OpenGSQ',
    license='MIT',
)
