"""
A setuptools based setup module.
"""

from setuptools import setup, find_packages
from os import path
import rabbitmqpubsub.rabbit_pubsub 

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md")) as f:
    long_description = f.read()


setup(
    name="RabbitMQPubSub",
    version=rabbitmqpubsub.rabbit_pubsub.__version__,
    description="Python package for connecting to rabbit publish-subscribe or remote procedure call implementation with pika library",
    long_description=long_description,
    url="",
    packages=find_packages(exclude=["doc"]),
    include_package_data=True,
    namespace_packages=["rabbitmqpubsub"],
    author="Nebojsa Mrkic",
    author_email="mrkic.nebojsa@gmail.com",
    license="Apache 2.0",
    install_requires=[
        "overrides>=1.8",
        "pika==1.1.0"
    ],
    dependency_links=[
    ],
    setup_requires=["pytest-runner"],
    tests_require=[
        "pytest",
        "mock",
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
)
