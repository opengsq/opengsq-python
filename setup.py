import os

from setuptools import find_packages, setup

current_dir = os.path.abspath(os.path.dirname(__file__))
version_contents = {}

with open(os.path.join(current_dir, 'opengsq', 'version.py'), encoding='utf-8') as f:
    exec(f.read(), version_contents)

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        install_requires = f.read().splitlines()
except FileNotFoundError:
    with open(os.path.join(current_dir, 'opengsq.egg-info', 'requires.txt'), 'r', encoding='utf-8') as f:
        install_requires = f.read().splitlines()

setup(
    name='opengsq',
    version=version_contents['__version__'],
    description='🐍 OpenGSQ - Python library for querying game servers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    entry_points={'console_scripts': ['opengsq=opengsq.cli:main']},
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.7',
    url='https://github.com/opengsq/opengsq-python',
    project_urls={
        'Bug Tracker': 'https://github.com/opengsq/opengsq-python/issues',
        'Source Code': 'https://github.com/opengsq/opengsq-python',
        'Documentation': 'https://python.opengsq.com/',
    },
    license='MIT',
    author='OpenGSQ',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
