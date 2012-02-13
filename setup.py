#!/usr/bin/env python

from setuptools import setup, find_packages
from nova_dns import __version__


setup(name='nova-dns',
      version=__version__,
      license='GNU LGPL v2.1',
      description='cloud computing dns toolkit',
      author='Savin Nikita (GridDynamics Openstack Core Team, (c) GridDynamics)',
      author_email='openstack@griddynamics.com',
      url='http://www.griddynamics.com/openstack',
      packages=find_packages(exclude=['bin', 'smoketests', 'tests']),
      scripts=['bin/nova-dns'],
      py_modules=[],
      test_suite='tests'
)

