from setuptools import setup

setup(
    name='Golem-App',
    version='0.1.0',
    url='https://github.com/golemfactory/golem/golem_app/python',
    maintainer='The Golem team',
    maintainer_email='tech@golem.network',
    packages=[
        'golem_app',
    ],
    python_requires='>=3.5',
    install_requires=[
        'grpclib==0.2.4',
        'protobuf==3.7.1',
    ],
)
