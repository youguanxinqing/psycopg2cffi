An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.4.4.

In order to satisfy ``cffi==0.4`` requirement, you currently
need to install cffi from source::

    pip install -e https://bitbucket.org/cffi/cffi#egg=cffi

To use this package with Django or SQLAlchemy create a psycopg2.py file
somewhere in your python path (e.g. the current working dir) and add::

    from psycopg2cffi import compat
    compat.register()

This will map psycopg2cffi to psycopg2.

This module is only tested with python 2.6+ and PyPy trunk (will be 2.0)

This is a port of (Michael van Tellingen port 
https://github.com/mvantellingen/psycopg2-ctypes 
of Alex Gaynor's rpython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
python + ctypes) to cffi.

To run tests, install pytest and run them with::

    py.test psycopg2cffi

Source code is hosted on github at https://github.com/chtd/psycopg2cffi.
Submit issues to https://github.com/chtd/psycopg2cffi/issues 
