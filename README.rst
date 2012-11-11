An implementation of the psycopg2 module using cffi.
The module is currently compatible with Psycopg 2.4.4.

In order to satisfy ``cffi==0.4`` requirement, you currently
need to install cffi from source::

    pip install -e hg+https://bitbucket.org/cffi/cffi#egg=cffi

After that you can install ``psycopg2cffi`` from pypi::

    pip install psycopg2cffi

Or from source::

    python setup.py develop

To use this package with Django or SQLAlchemy create
somewhere in your python path (e.g. the site-packages of your virtual env)
a ``psycopg2.py`` file with the following::

    from psycopg2cffi import compat
    compat.register()

This will map psycopg2cffi to psycopg2.

This module is only tested with python 2.6+ and PyPy trunk (will be 2.0
release, right now you can get a nighlty build for Linux or OS X from 
http://buildbot.pypy.org/nightly/trunk/).

This is a port of (Michael van Tellingen port 
https://github.com/mvantellingen/psycopg2-ctypes 
of Alex Gaynor's rpython port
(https://bitbucket.org/alex_gaynor/pypy-postgresql/overview) of psycopg2 to
python + ctypes) to cffi.

To run tests, install pytest and run them with::

    py.test psycopg2cffi

Submit issues to https://github.com/chtd/psycopg2cffi/issues 
