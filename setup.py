from setuptools import setup


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='COVID-19 Evolution',
    version='0.1',
    install_requires=requirements
)
