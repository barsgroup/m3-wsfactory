import os
from distutils.core import setup


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fd:
        return fd.read()

setup(
    name='m3_wsfactory',
    version='0.1.0',
    packages=['m3_wsfactory', 'm3_wsfactory.smev', 'm3_wsfactory.smev.smev256',
              'm3_wsfactory.management', 'm3_wsfactory.management.commands',
              'm3_wsfactory.migrations'],
    package_dir={'': 'src'},
    package_data={'': ['schema/*', 'templates/ui-js/*']},
    url='http://bitbucket.org/timic/m3_wsfactory',
    license=read_file("LICENSE"),
    description=read_file("DESCRIPTION"),
    author='Timur Salyakhutdinov',
    author_email='t.salyakhutdinov@gmail.com',
    requires=['lxml', 'spyne', 'django==1.4'],
)
