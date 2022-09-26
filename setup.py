"""
A setuptools based setup module.
"""

from setuptools import setup, find_packages
from os import path
# import rabbitmqpubsub
import re

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md")) as f:
    long_description = f.read()


def find_version(*file_paths):
    """
    Reads out software version from provided path(s).
    """
    version_file = open("/".join(file_paths), 'r').read()
    lookup = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                       version_file, re.M)

    if lookup:
        return lookup.group(1)

    raise RuntimeError("Unable to find version string.")


setup(
    name="RabbitMQPubSub",
    version=find_version("rabbitmqpubsub", "rabbit_pubsub", "__init__.py"),
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
        "pika==1.3.0",
        "dateutils==0.6.12"
    ],
    dependency_links=[
    ],
    setup_requires=["pytest-runner"],
    tests_require=[
        "pytest",
        "mock",
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
    ],
)
