This module is not yet packaged properly, to use it you need to install
cffi trunk and have a working C compiler, as well as libffi.

An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.4.4.

To use this package with Django or SQLAlchemy create a psycopg2.py file
somewhere in your python path (e.g. the current working dir) and add::

    from psycopg2ct import compat
    compat.register()

This will map psycopg2ct to psycopg2.

This module is only tested with python 2.6+ and PyPy trunk (will be 2.0)

This is a port of (Michael van Tellingen port of Alex Gaynor's rpython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
python + ctypes) to cffi.
