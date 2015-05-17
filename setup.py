# setup.py

import os
import sys

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


if '_cffi_backend' in sys.builtin_module_names:   # pypy
    import _cffi_backend
    new_cffi = _cffi_backend.__version__ >= "1"
else:
    new_cffi = True   # assume at least 1.0.0 will be installed


setup_kwargs = dict(
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
    packages=['psycopg2cffi', 'psycopg2cffi._impl', 'psycopg2cffi.tests'],
    install_requires=['six'],
)

if new_cffi:
    setup_kwargs.update(dict(
        setup_requires=[
            'cffi>=1.0',
            ],
        cffi_modules=['psycopg2cffi/_impl/_build_libpq.py:ffi'],
        install_requires=setup_kwargs['install_requires'] + [
            'cffi>=1.0',
            ],
        ))
else:
    try:
        import cffi
    except ImportError:
        ext_modules = []
    else:
        from psycopg2cffi._impl.libpq import ffi
        ext_modules = [ffi.verifier.get_extension()]
    setup_kwargs.update(dict(
        install_requires=setup_kwargs['install_requires'] + [
            'cffi<1.0',
            ],
        setup_requires=[
            'cffi<1.0',
            ],
        ext_package='psycopg2cffi',
        ext_modules=ext_modules,
        ))

setup(**setup_kwargs)
