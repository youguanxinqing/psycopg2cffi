An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.4.4.

You can  install ``psycopg2cffi`` from pypi::

    pip install psycopg2cffi

Or from source::

    python setup.py develop

To use this package with Django or SQLAlchemy create
somewhere in your python path (e.g. the site-packages of your virtual env)
a ``psycopg2.py`` file with the following::

    from psycopg2cffi import compat
    compat.register()

This will map psycopg2cffi to psycopg2.

This module is only tested with python 2.6+ and PyPy 2.0 (and will 
definityly not work on 1.9).

This is a port of (Michael van Tellingen port 
https://github.com/mvantellingen/psycopg2-ctypes 
of Alex Gaynor's rpython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
python + ctypes) to cffi.

To run tests, install pytest and run them with::

    py.test psycopg2cffi

Submit issues to https://github.com/chtd/psycopg2cffi/issues 

If you notice that ``psycopg2cffi`` under PyPy is noticably slower than 
``psycopg2`` under CPython, submit this to the issues too - it should 
not be the case.
