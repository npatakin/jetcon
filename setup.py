from setuptools import setup, find_packages     # type: ignore


with open('requirements.txt') as reqs:
    required = reqs.read().splitlines()

setup(
    name='jetcon',
    version='0.1',
    author='Dmitry Senushkin',
    packages=find_packages(),
    install_requires=required
)
