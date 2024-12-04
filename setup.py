from setuptools import setup, find_packages

setup(
    name='my_database_lib',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,  
    package_data={
        '': ['Plant_Parenthood2.db'], 
    },
    install_requires=[],  
    description='A library for interacting with the Plant Parenthood Database',
    author='Coralee Rogers-Vickers, Dylan Nicks, Comfort Donkor, Christopher Vasquez',
    author_email='coraorog@unc.edu'
)