from setuptools import setup

from pip.req import parse_requirements

#http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
install_reqs = parse_requirements('./requirements.txt')
# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='wos-client',
    version='0.1',
    description='Client for searching the Web of Science API.',
    license='MIT',
    packages=['wos'],
    zip_safe=False,
    install_requires=reqs,
)