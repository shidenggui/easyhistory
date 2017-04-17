# coding:utf8
from setuptools import setup

import easyhistory

long_desc = """
easyhistory
===============

* easy to use rqalpha history data

Installation
--------------

pip install easytrader

Upgrade
---------------

    pip install easytrader --upgrade
"""

setup(
    name='easyhistory',
    version=easyhistory.__version__,
    description='A utility for rqalpha history',
    long_description=long_desc,
    author='shidenggui',
    author_email='longlyshidenggui@gmail.com',
    license='BSD',
    url='https://github.com/shidenggui/easyhistory',
    keywords='China stock trade',
    install_requires=[
            'rqalpha',
            'requests',
            'six',
            'easyutils',
    ],
    classifiers=['Development Status :: 4 - Beta',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'License :: OSI Approved :: BSD License'],
    packages=['easyhistory'],
    package_data={},
)
