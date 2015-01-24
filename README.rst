.. image:: https://travis-ci.org/chtd/psycopg2cffi.svg

An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.5.

You can  install ``psycopg2cffi`` from pypi::

    pip install psycopg2cffi

Or from source::

    python setup.py develop

Installation requirements are the same as for ``psycopg2`` - you must
have ``libpq`` headers, ``pg_config`` somewhere on your ``$PATH``.
Installation was tested on Ubuntu 12.04 and CentOS (RHEL 5.0).
It should be possible to make it work on Windows, but I did not even test it.

This module works under CPython 2.6+, CPython 3.2+, PyPy 2 and PyPy 3
(PyPy version should be at least 2.0, which is ancient history now).

To use this package with Django or SQLAlchemy invoke a compatability
hook (for example, from ``settings.py`` in case of django, or
from a ``psycopg2.py`` file in site-packages of your virtual env)::

    from psycopg2cffi import compat
    compat.register()

This will map ``psycopg2cffi`` to ``psycopg2``.

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

Development
-----------

To run tests, install ``pytest`` and run them with::

    py.test psycopg2cffi

You can also run Django tests. You need to checkout django source, add
psycopg2 compat as described above, and, from the root of the django checkout::

    PYTHONPATH=`pwd` ./tests/runtests.py \
        --settings=psycopg2cffi.tests.psycopg2_tests.testconfig

In case of problems with django tests, see official django docs
https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/#running-the-unit-tests


