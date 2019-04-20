import os

from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='robogame_engine',
    version='1.0.0',
    packages=['robogame_engine'],
    include_package_data=True,
    license='BSD License',
    description='The package allows you to create RoboGames.',
    long_description=README,
    url='https://github.com/suguby/robogame_engine',
    author='Shandrinov Vadim',
    author_email='suguby@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'six==1.12.0', 'pygame==1.9.5'
    ]
)
