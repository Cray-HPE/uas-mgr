#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# coding: utf-8

import sys
from setuptools import setup, find_packages
from swagger_server import version

NAME = "cray-uas-mgr"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=version,
    description="Cray User Access Service",
    author_email="",
    url="",
    keywords=["Swagger", "Cray User Access Service"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['swagger_server=swagger_server.__main__:main']},
    long_description="""\
    User Access Service. This service is responsible for the management of User Access Node lifecycles.
    """
)

