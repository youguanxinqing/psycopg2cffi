# setup.py

import os

from setuptools import setup


# read the version number from the package
f = open(os.path.join(os.path.dirname(__file__), 'psycopg2cffi/__init__.py'))
try:
    for line in f:
        if line.startswith('__version__'):
            PSYCOPG_VERSION = line.split('=')[1].replace('"', '').replace("'", '').strip()
            break
    else:
        raise ValueError('__version__ not found in psycopg2cffi package')
finally:
    f.close()


README = []
with open('README.rst', 'r') as fh:
    README = fh.readlines()


setup(
    name='psycopg2cffi',
    author='Konstantin Lopuhin',
    author_email='konstantin.lopuhin@chtd.ru',
    license='LGPL',
    url='http://github.com/chtd/psycopg2cffi',
    version=PSYCOPG_VERSION,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: SQL',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
    ],
    platforms=['any'],
    description=README[0].strip(),
    long_description=''.join(README),
    test_suite='psycopg2cffi.tests.suite',

    py_modules=['_build_libpq'],  # FIXME - only for config
    packages=['psycopg2cffi', 'psycopg2cffi._impl', 'psycopg2cffi.tests'],
    setup_requires=['cffi>=1.0.dev0'],
    cffi_modules=['_build_libpq:ffi'],
    install_requires=[
        'six',
        'cffi>=1.0.dev0',  # TODO - cffi-runtime
        ],
)
