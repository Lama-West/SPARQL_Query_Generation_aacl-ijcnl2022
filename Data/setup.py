# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='SPARQL_NTM_Data',
    version='0.1.0',
    author='Anonymous',
    author_email='anonymous',
    description='Knowledge Base-aware SPARQL Query Translation from Natural Language - Data Repository',
    long_description=readme,
    long_description_content_type="text/markdown",
    url='anonymous',
    license=license,
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=('docs', 'raw_data', 'out_data', 'data_sources')),
    python_requires=">=3.7",
)