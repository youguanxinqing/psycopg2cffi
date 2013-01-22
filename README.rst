An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.4.4.

You can  install ``psycopg2cffi`` from pypi::

    pip install psycopg2cffi

Or from source::

    python setup.py develop

Installation requirements are the same as for ``psycopg2`` - you must
have ``libpq`` headers, ``pg_config`` somewhere on your ``$PATH``.
Installation was tested on Ubuntu 12.04 and CentOS (RHEL 5.0).
It should be possible to make it work on Windows, but I did not even test it.

This module is only tested with python 2.6+ and PyPy 2.0 (and will 
definityly not work on PyPy 1.9).

To use this package with Django or SQLAlchemy invoke a compatability
hook (for example, from ``settings.py`` in case of django, or 
from a ``psycopg2.py`` file in site-packages of your virtual env)::

    from psycopg2cffi import compat
    compat.register()

This will map ``psycopg2cffi`` to ``psycopg2``.

To run tests, install ``pytest`` and run them with::

    py.test psycopg2cffi

Submit issues to https://github.com/chtd/psycopg2cffi/issues 

If you notice that ``psycopg2cffi`` under PyPy is noticably slower than 
``psycopg2`` under CPython, submit this to the issues too - it should 
not be the case.

This is a port of (Michael van Tellingen port 
https://github.com/mvantellingen/psycopg2-ctypes 
of Alex Gaynor's rpython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
python + ctypes) to cffi.

The main motivation for a port was speed - the writeup with benchmarks
is here: http://chtd.ru/blog/bystraya-rabota-s-postgres-pod-pypy/?lang=en

