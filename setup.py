from setuptools import setup

setup(
    name='wos-client',
    version='0.1',
    description='Client for searching the Web of Science API.',
    license='MIT',
    packages=['wos'],
    zip_safe=False,
    install_requires=['suds'],
)
