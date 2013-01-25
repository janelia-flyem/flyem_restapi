#from distutils.core import setup
from setuptools import setup, find_packages

setup(name = "flyem_restapi",
    version = "1.0",
    url = "https://github.com/janelia-flyem/flyem_restapi.git",
    description = "Rest API for interfacing with FlyEM database",
    long_description = "Provides routines for accessing and modifying information in the FlyEM database",
    author = "FlyEM",
    author_email = 'plazas@janelia.hhmi.org',
    license = 'LICENSE.txt',
    packages = ['restful_core'],
    package_data = { },
    install_requires = [ ],
    scripts = ["flyem_restapi"]
)
