# -*- coding: utf-8 -*-
import os
from distutils.core import setup


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fd:
        return fd.read()

setup(
    name='m3_wsfactory',
    version='0.2.3',
    packages=[
        'm3_wsfactory',
        'm3_wsfactory.migrations',
        'm3_wsfactory.ui',
    ],
    package_dir={'': 'src'},
    package_data={'': ['schema/*', 'templates/ui-js/*']},
    url='http://bitbucket.org/timic/m3_wsfactory',
    license=read_file("LICENSE"),
    description=read_file("DESCRIPTION"),
    author='Timur Salyakhutdinov',
    author_email='t.salyakhutdinov@gmail.com',
    install_requires=['lxml', 'spyne', 'django==1.4.15'],
)
