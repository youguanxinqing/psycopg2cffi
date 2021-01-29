.. image:: https://travis-ci.org/chtd/psycopg2cffi.svg?branch=master
    :target: https://travis-ci.org/chtd/psycopg2cffi

.. contents::

An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.5.

Installation
------------

You can  install ``psycopg2cffi`` from PyPI::

    pip install psycopg2cffi

Or from source::

    python setup.py install

Installation requirements are the same as for ``psycopg2`` - you must
have ``libpq`` headers, ``pg_config`` somewhere on your ``$PATH``,
Python development headers (``python-dev`` or similar), and ``ffi-dev``
for ``cffi``.
Installation was tested on Ubuntu 12.04, Ubuntu 14.04, CentOS (RHEL 5.0),
OS X 10.8 - 10.10.
It should be possible to make it work on Windows, but I did not test it.

This module works under CPython 2.7+, CPython 3.5+, PyPy 2 and PyPy 3
(PyPy version should be at least 2.0, which is ancient history now).

To use this package with Django or SQLAlchemy invoke a compatibility
hook (for example, from ``settings.py`` in case of Django, or
from a ``psycopg2.py`` file in site-packages of your virtual env)::

    from psycopg2cffi import compat
    compat.register()

This will map ``psycopg2cffi`` to ``psycopg2``, so now any code that
does ``import psycopg2`` will use ``psycopg2cffi``.

Submit issues to https://github.com/chtd/psycopg2cffi/issues

If you notice that ``psycopg2cffi`` under PyPy is noticeably slower than
``psycopg2`` under CPython, submit this to the issues too - it should
not be the case.

This is a port of (Michael van Tellingen port
https://github.com/mvantellingen/psycopg2-ctypes
of Alex Gaynor's RPython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
Python + ctypes) to cffi.

The main motivation for a port was speed - the writeup with benchmarks
is here: http://chtd.ru/blog/bystraya-rabota-s-postgres-pod-pypy/?lang=en

Development
-----------

To run tests, install ``pytest`` and run them with::

    py.test psycopg2cffi

Note that for ``cffi>=1.0`` you need to run ``python setup.py develop``
to rebuild ``_libpq.so`` (if you changed bindings).
And for ``cffi<1.0`` (only PyPy 2.5 and below) you need to run
``python setup.py install`` once to generate ``psycopg2cffi/_config.py``,
otherwise each import will run config and notify tests will fail.

You can also run Django tests. You need to checkout Django source, add
psycopg2 compat as described above, and, from the root of the Django checkout::

    PYTHONPATH=`pwd` ./tests/runtests.py \
        --settings=psycopg2cffi.tests.psycopg2_tests.testconfig

In case of problems with Django tests, see official Django docs
https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/#running-the-unit-tests

Release notes
-------------

2.9.0 (27 Jan 2021)
+++++++++++++++++++

New features:

- Add execute_batch and execute_values to psycopg2cffi.extras by @fake-name in #98
- psycopg2cffi.extras: add fetch argument to execute_values() by @intelfx in #119

Bug fixes:

- Fix for async keyword argument when creating a connection by @donalm in #104
- Allow adapters to be passed as arguments of cursor's execute() by @amigrave in #107
- Fix installation with old cffi by dand-oss in #116

Test changes:

- Dropped support for python 2.6, 3.3, 3.4 by @thedrow in #109
- Added support for python 3.8 by @thedrow in #108

2.8.1 (31 July 2018)
++++++++++++++++++++

Release date added

2.8.0 (31 July 2018)
++++++++++++++++++++

Python 3.7 support by unimariJo (#92) and farrokhi (#101).
``async_`` should be used instead of ``async`` in public APIs
(but the change is backwards compatible,
``async`` is still supported as an alias).


2.7.7 (13 November 2017)
++++++++++++++++++++++++

Bugfixes:

- Support installation under Postgres 10 by jimbattin (#90)


2.7.6 (11 August 2017)
++++++++++++++++++++++

Bugfixes:

- Named cursors fix (affects newer Django) by danchr (#81)
- Python 3 fixes in extras by avanov (#83)
- Null check added in fast parser utils by malthe (#79)


2.7.5 (31 October 2016)
+++++++++++++++++++++++

Windows wheels support added by ryoyoko (#69).

Bugfixes:

- Non-ascii notice messages fixed by asterite3 (#72)
- AsIs with non-text/bytes fixed by jinty (#64)
- Silent failures in copy_from and copy_to fixed by gobbledygook88 (#62)
- Infinite recursion error fixed in errorcodes.lookup (#68)
- Typos in README fixed by PavloKapyshin (#66)


2.7.4 (01 April 2016)
+++++++++++++++++++++

Fix a regression with error handling when establishing the connection (#61)


2.7.3 (29 February 2016)
++++++++++++++++++++++++

Fix a bug with non-ascii error messages (#56)


2.7.2 (06 August 2015)
++++++++++++++++++++++

Fixes for FreeBSD support by Andrew Coleman


2.7.1 (20 June 2015)
++++++++++++++++++++

JSONB support


2.7.0 (21 May 2015)
+++++++++++++++++++

Use cffi 1.0, which makes installation more robust, and import is faster.
cffi<1.0 is used now only for PyPy 2.5 or below.


2.6.1 (08 Feb 2015)
+++++++++++++++++++

Fixing things that were broken in 2.6.0:

- Fix issue #31 - bigint on 32-bit
- Fix issue #32 - register_type and unicode


2.6.0 (24 Jan 2015)
+++++++++++++++++++

- Python 3 support
- A bit faster reading of int, long, float, double fields

2.5.1 (14 May 2014)
+++++++++++++++++++

- Small bugfixes

2.5.0 (3 Sep 2013)
++++++++++++++++++

- Bugfixes and a lot of compatibility work by Daniele Varrazzo


Older releases lack release notes, first release of psycopg2cffi around Nov 2012.
