from __future__ import unicode_literals

import sys
from collections import namedtuple
from functools import wraps
from io import TextIOBase
import weakref
import six
from six.moves import xrange

from psycopg2cffi import tz
from psycopg2cffi._impl import consts
from psycopg2cffi._impl import exceptions
from psycopg2cffi._impl.libpq import libpq, ffi
from psycopg2cffi._impl import typecasts
from psycopg2cffi._impl import util
from psycopg2cffi._impl.adapters import _getquoted
from psycopg2cffi._impl.exceptions import InterfaceError, ProgrammingError


is_32bits = sys.maxsize < 2**32


def check_closed(func):
    """Check if the connection is closed and raise an error"""
    @wraps(func)
    def check_closed_(self, *args, **kwargs):
        if self.closed:
            raise InterfaceError("connection already closed")
        return func(self, *args, **kwargs)
    return check_closed_


def check_no_tuples(func):
    """Check if there are tuples available. This is only the case when the
    postgresql status was PGRES_TUPLES_OK

    """
    @wraps(func)
    def check_no_tuples_(self, *args, **kwargs):
        if self._no_tuples and self._name is None:
            raise ProgrammingError("no results to fetch")
        return func(self, *args, **kwargs)
    return check_no_tuples_


def check_async(func):
    @wraps(func)
    def check_async_(self, *args, **kwargs):
        if self._conn._async:
            raise exceptions.ProgrammingError(
                '%s cannot be used in asynchronous mode' % func.__name__)
        return func(self, *args, **kwargs)
    return check_async_


# Used for Cursor.description
Column = namedtuple('Column', ['name', 'type_code', 'display_size',
    'internal_size', 'precision', 'scale', 'null_ok'])


class Cursor(object):
    """These objects represent a database cursor, which is used to manage
    the context of a fetch operation.

    Cursors created from the same connection are not isolated, i.e., any
    changes done to the database by a cursor are immediately visible by the
    other cursors. Cursors created from different connections can or can not
    be isolated, depending on how the transaction support is implemented
    (see also the connection's .rollback() and .commit() methods).

    """

    def __init__(self, connection, name, row_factory=None):

        self._conn = connection

        #: This read/write attribute specifies the number of rows to fetch at
        #: a time with .fetchmany(). It defaults to 1 meaning to fetch a
        #: single row at a time.
        #:
        #: Implementations must observe this value with respect to the
        #: .fetchmany() method, but are free to interact with the database a
        #: single row at a time. It may also be used in the implementation of
        #: .executemany().
        self.arraysize = 1

        #: Read/write attribute specifying the number of rows to fetch from
        #: the backend at each network roundtrip during iteration on a named
        #: cursor. The default is 2000
        self.itersize = 2000

        self.tzinfo_factory = tz.FixedOffsetTimezone
        self.row_factory = row_factory

        self._closed = False
        self._description = None
        self._lastrowid = 0
        self._name = name.replace('"', '""') if name is not None else name
        self._withhold = False
        self._scrollable = None
        self._no_tuples = True
        self._rowcount = -1
        self._rownumber = 0
        self._query = None
        self._statusmessage = None
        self._typecasts = {}
        self._pgres = ffi.NULL
        self._copyfile = None
        self._copysize = None

    def __del__(self):
        if self._pgres:
            libpq.PQclear(self._pgres)
            self._pgres = ffi.NULL

    def __enter__(self):
        return self

    def __exit__(self, type, name, tb):
        self.close()

    @property
    def closed(self):
        return self._closed or self._conn.closed

    @property
    def description(self):
        """This read-only attribute is a sequence of 7-item sequences.

        Each of these sequences contains information describing one result
        column:

          (name,
           type_code,
           display_size,
           internal_size,
           precision,
           scale,
           null_ok)

        The first two items (name and type_code) are mandatory, the other
        five are optional and are set to None if no meaningful values can be
        provided.

        This attribute will be None for operations that do not return rows or
        if the cursor has not had an operation invoked via the .execute*()
        method yet.

        The type_code can be interpreted by comparing it to the Type Objects
        specified in the section below.

        """
        return self._description

    @property
    def rowcount(self):
        """This read-only attribute specifies the number of rows that the
        last .execute*() produced (for DQL statements like 'select') or
        affected (for DML statements like 'update' or 'insert').

        The attribute is -1 in case no .execute*() has been performed on the
        cursor or the rowcount of the last operation is cannot be determined
        by the interface.

        Note: Future versions of the DB API specification could redefine the
        latter case to have the object return None instead of -1.

        """
        return self._rowcount

    @check_closed
    def callproc(self, procname, parameters=None):
        if parameters is None:
            length = 0
        else:
            length = len(parameters)
        sql = "SELECT * FROM %s(%s)" % (
            procname,
            ", ".join(["%s"] * length)
        )
        self.execute(sql, parameters)
        return parameters

    def close(self):
        """Close the cursor now (rather than whenever __del__ is called).

        The cursor will be unusable from this point forward; an Error
        (or subclass) exception will be raised if any operation is attempted
        with the cursor.

        """
        if self._closed:
            return

        if self._name is not None:
            self._pq_execute('CLOSE "%s"' % self._name)

        self._closed = True

    @check_closed
    def execute(self, query, parameters=None):
        """Prepare and execute a database operation (query or command).

        Parameters may be provided as sequence or mapping and will be bound to
        variables in the operation.  Variables are specified in a
        database-specific notation (see the module's paramstyle attribute for
        details).

        A reference to the operation will be retained by the cursor.  If the
        same operation object is passed in again, then the cursor can optimize
        its behavior.  This is most effective for algorithms where the same
        operation is used, but different parameters are bound to it
        (many times).

        For maximum efficiency when reusing an operation, it is best to use
        the .setinputsizes() method to specify the parameter types and sizes
        ahead of time.  It is legal for a parameter to not match the
        predefined information; the implementation should compensate,
        possibly with a loss of efficiency.

        The parameters may also be specified as list of tuples to e.g. insert
        multiple rows in a single operation, but this kind of usage is
        deprecated: .executemany() should be used instead.

        Return values are not defined.

        """
        self._description = None
        conn = self._conn

        if self._name:
            if self._query:
                raise ProgrammingError(
                    "can't call .execute() on named cursors more than once")
            if self._conn.autocommit and not self._withhold:
                raise ProgrammingError(
                    "can't use a named cursor outside of transactions")

        if isinstance(query, six.text_type):
            query = query.encode(self._conn._py_enc)

        if parameters is not None:
            self._query = _combine_cmd_params(query, parameters, conn)
        else:
            self._query = query

        scroll = ""
        if self._scrollable is not None:
            scroll = self._scrollable and "SCROLL " or "NO SCROLL "

        conn._begin_transaction()
        self._clear_pgres()

        if self._name:
            self._query = \
                util.ascii_to_bytes(
                        'DECLARE "%s" %sCURSOR %s HOLD FOR ' % (
                            self._name, scroll,
                            "WITH" if self._withhold else "WITHOUT")) \
                + self._query

        self._pq_execute(self._query, conn._async)

    @check_closed
    @check_async
    def executemany(self, query, paramlist):
        """Prepare a database operation (query or command) and then execute
        it against all parameter sequences or mappings found in the sequence
        seq_of_parameters.

        Modules are free to implement this method using multiple calls to the
        .execute() method or by using array operations to have the database
        process the sequence as a whole in one call.

        Use of this method for an operation which produces one or more result
        sets constitutes undefined behavior, and the implementation is
        permitted (but not required) to raise an exception when it detects
        that a result set has been created by an invocation of the operation.

        The same comments as for .execute() also apply accordingly to this
        method.

        Return values are not defined.

        """
        self._rowcount = -1
        rowcount = 0
        for params in paramlist:
            self.execute(query, params)
            if self.rowcount == -1:
                rowcount = -1
            else:
                rowcount += self.rowcount
        self._rowcount = rowcount

    @check_closed
    @check_no_tuples
    def fetchone(self):
        """Fetch the next row of a query result set, returning a single
        sequence, or None when no more data is available. [6]


        An Error (or subclass) exception is raised if the previous call to
        .execute*() did not produce any result set or no call was issued yet.

        """
        if self._name is not None:
            self._pq_execute(
                'FETCH FORWARD 1 FROM "%s"' % self._name)

        if self._rownumber >= self._rowcount:
            return None

        return self._build_row()

    @check_closed
    @check_no_tuples
    def fetchmany(self, size=None):
        """Fetch the next set of rows of a query result, returning a
        sequence of sequences (e.g. a list of tuples). An empty sequence is
        returned when no more rows are available.

        The number of rows to fetch per call is specified by the parameter.
        If it is not given, the cursor's arraysize determines the number of
        rows to be fetched. The method should try to fetch as many rows as
        indicated by the size parameter. If this is not possible due to the
        specified number of rows not being available, fewer rows may be
        returned.

        An Error (or subclass) exception is raised if the previous call to
        .execute*() did not produce any result set or no call was issued yet.

        Note there are performance considerations involved with the size
        parameter.  For optimal performance, it is usually best to use the
        arraysize attribute.  If the size parameter is used, then it is best
        for it to retain the same value from one .fetchmany() call to the
        next.

        """
        if size is None:
            size = self.arraysize

        if self._name is not None:
            self._clear_pgres()
            self._pq_execute(
                'FETCH FORWARD %d FROM "%s"' % (size, self._name))

        if size > self._rowcount - self._rownumber or size < 0:
            size = self._rowcount - self._rownumber

        if size <= 0:
            return []

        return [self._build_row() for _ in xrange(size)]

    @check_closed
    @check_no_tuples
    def fetchall(self):
        """Fetch all (remaining) rows of a query result, returning them as a
        sequence of sequences (e.g. a list of tuples).

        Note that the cursor's arraysize attribute can affect the performance
        of this operation.

        An Error (or subclass) exception is raised if the previous call to
        .execute*() did not produce any result set or no call was issued yet.

        """
        if self._name is not None:
            self._pq_execute('FETCH FORWARD ALL FROM "%s"' % self._name)

        size = self._rowcount - self._rownumber
        if size <= 0:
            return []

        return [self._build_row() for _ in xrange(size)]

    def nextset(self):
        """This method will make the cursor skip to the next available set,
        discarding any remaining rows from the current set.

        If there are no more sets, the method returns None. Otherwise, it
        returns a true value and subsequent calls to the fetch methods will
        return rows from the next result set.

        An Error (or subclass) exception is raised if the previous call to
        .execute*() did not produce any result set or no call was issued yet.

        Note: this method is not supported

        """
        raise NotImplementedError()

    def cast(self, oid, s):
        """Convert a value from a PostgreSQL string to a Python object.

        Use the most specific of the typecasters registered by register_type().

        This is not part of the dbapi 2 standard, but a psycopg2 extension.

        """
        cast = self._get_cast(oid)
        if isinstance(s, six.text_type):
            s = s.encode(self._conn._py_enc)
        return cast.cast(s, self, None)

    def mogrify(self, query, vars=None):
        """Return the the querystring with the vars binded.

        This is not part of the dbapi 2 standard, but a psycopg2 extension.

        """
        if isinstance(query, six.text_type):
            query = query.encode(self._conn._py_enc)

        return _combine_cmd_params(query, vars, self._conn)

    @check_closed
    @check_async
    def copy_from(self, file, table, sep='\t', null='\\N', size=8192,
                  columns=None):
        """Reads data from a file-like object appending them to a database
        table (COPY table FROM file syntax).

        The source file must have both read() and readline() method.

        TODO: Improve error handling

        """
        if columns:
            columns_str = '(%s)' % ','.join([column for column in columns])
        else:
            columns_str = ''

        query = util.ascii_to_bytes(
                "COPY %s%s FROM stdin WITH DELIMITER AS " % (
                    table, columns_str)) + \
                util.quote_string(self._conn, sep) + b' NULL AS ' + \
                util.quote_string(self._conn, null)

        self._copysize = size
        self._copyfile = file
        try:
            self._pq_execute(query)
        finally:
            self._copyfile = None
            self._copysize = None

    @check_closed
    @check_async
    def copy_to(self, file, table, sep='\t', null='\\N', columns=None):
        """Writes the content of a table to a file-like object (COPY table
        TO file syntax).

        The target file must have a write() method.

        TODO: Improve error handling

        """
        if columns:
            columns_str = '(%s)' % ','.join([column for column in columns])
        else:
            columns_str = ''

        query = util.ascii_to_bytes(
                "COPY %s%s TO stdout WITH DELIMITER AS " % (
                    table, columns_str)) + \
                util.quote_string(self._conn, sep) + b' NULL AS ' + \
                util.quote_string(self._conn, null)

        self._copyfile = file
        try:
            self._pq_execute(query)
        finally:
            self._copyfile = None

    @check_closed
    @check_async
    def copy_expert(self, sql, file, size=8192):
        if not sql:
            return

        if not hasattr(file, 'read') and not hasattr(file, 'write'):
            raise TypeError("file must be a readable file-like object for"
                " COPY FROM; a writeable file-like object for COPY TO.")

        self._copysize = size
        self._copyfile = file
        try:
            self._pq_execute(sql)
        finally:
            self._copyfile = None
            self._copysize = None

    @check_closed
    def setinputsizes(self, sizes):
        """This can be used before a call to .execute*() to predefine memory
        areas for the operation's parameters.

        sizes is specified as a sequence -- one item for each input
        parameter.  The item should be a Type Object that corresponds to the
        input that will be used, or it should be an integer specifying the
        maximum length of a string parameter.  If the item is None, then no
        predefined memory area will be reserved for that column (this is
        useful to avoid predefined areas for large inputs).

        This method would be used before the .execute*() method is invoked.

        Implementations are free to have this method do nothing and users are
        free to not use it.

        """
        pass

    @check_closed
    def setoutputsize(self, size, column=None):
        """Set a column buffer size for fetches of large columns (e.g.
        LONGs, BLOBs, etc.).

        The column is specified as an index into the result sequence.  Not
        specifying the column will set the default size for all large columns
        in the cursor.

        This method would be used before the .execute*() method is invoked.

        Implementations are free to have this method do nothing and users are
        free to not use it.

        """
        pass

    @property
    def rownumber(self):
        """This read-only attribute should provide the current 0-based index
        of the cursor in the result set or None if the index cannot be
        determined.

        The index can be seen as index of the cursor in a sequence (the
        result set). The next fetch operation will fetch the row indexed by
        .rownumber in that sequence.

        This is an optional DB API extension.

        """
        return self._rownumber

    @property
    def connection(self):
        """This read-only attribute return a reference to the Connection
        object on which the cursor was created.

        The attribute simplifies writing polymorph code in multi-connection
        environments.

        This is an optional DB API extension.

        """
        return self._conn

    @check_closed
    def __iter__(self):
        """Return self to make cursors compatible to the iteration protocol

        This is an optional DB API extension.

        """
        while 1:
            rows = self.fetchmany(self.itersize)
            if not rows:
                return
            real_rownumber = self._rownumber
            try:
                self._rownumber = 0
                for row in rows:
                    self._rownumber += 1
                    yield row
            finally:
                self._rownumber = real_rownumber

    @property
    def lastrowid(self):
        """This read-only attribute provides the OID of the last row inserted
        by the cursor.

        If the table wasn't created with OID support or the last operation is
        not a single record insert, the attribute is set to None.

        This is a Psycopg extension to the DB API 2.0

        """
        return self._lastrowid

    @property
    def name(self):
        """Name of the cursor if it was created with a name

        This is a Psycopg extension to the DB API 2.0

        """
        return self._name

    @property
    def query(self):
        return self._query

    @property
    def statusmessage(self):
        """Read-only attribute containing the message returned by the last
        command.

        This is a Psycopg extension to the DB API 2.0

        """
        return self._statusmessage

    @property
    def withhold(self):
        return self._withhold

    @withhold.setter
    def withhold(self, value):
        if not self._name:
            raise ProgrammingError(
                "trying to set .withhold on unnamed cursor")

        self._withhold = bool(value)

    @property
    def scrollable(self):
        return self._scrollable

    @scrollable.setter
    def scrollable(self, value):
        if not self._name:
            raise ProgrammingError(
                "trying to set .scrollable on unnamed cursor")

        self._scrollable = bool(value) if value is not None else None

    @check_closed
    def scroll(self, value, mode='relative'):
        if not self._name:
            if mode == 'relative':
                new_pos = self._rownumber + value
            elif mode == 'absolute':
                new_pos = value
            else:
                raise ProgrammingError(
                    "scroll mode must be 'relative' or 'absolute'")

            if not 0 <= new_pos < self._rowcount:
                raise ProgrammingError("scroll destination out of bounds")

            self._rownumber = new_pos
        else:
            if self._conn._async_cursor is not None:
                raise ProgrammingError(
                    "cannot be used while an asynchronous query is underway")

            if self._mark != self._conn._mark and not self._withhold:
                raise ProgrammingError("named cursor isn't valid anymore")

            # This should also raise a ProgrammingError if the mode is
            # not absolute or relative. But mimic psycopg for now.
            if mode == 'absolute':
                cmd = 'MOVE ABSOLUTE %d FROM "%s"' % (value, self._name)
            else:
                cmd = 'MOVE %d FROM "%s"' % (value, self._name)
            self._pq_execute(cmd)

    def _clear_pgres(self):
        if self._pgres:
            libpq.PQclear(self._pgres)
            self._pgres = ffi.NULL

    def _pq_execute(self, query, async_conn=False):
        """Execute the query"""
        with self._conn._lock:
            pgconn = self._conn._pgconn

            # Check the status of the connection
            if libpq.PQstatus(pgconn) != libpq.CONNECTION_OK:
                raise self._conn._create_exception(cursor=self)

            if not async_conn:
                with self._conn._lock:
                    if not self._conn._have_wait_callback():
                        self._pgres = libpq.PQexec(
                                pgconn, util.ascii_to_bytes(query))
                    else:
                        self._pgres = self._conn._execute_green(query)
                    if not self._pgres:
                        raise self._conn._create_exception(cursor=self)
                    self._conn._process_notifies()
                self._pq_fetch()

            else:
                with self._conn._lock:
                    ret = libpq.PQsendQuery(pgconn, query)
                    if not ret:

                        # XXX: check if this is correct, seems like a hack.
                        # but the test_async_after_async expects it.
                        if self._conn._async_cursor:
                            raise ProgrammingError(
                                'cannot be used while an asynchronous query is underway')

                        raise self._conn._create_exception(cursor=self)

                    ret = libpq.PQflush(pgconn)
                    if ret == 0:
                        async_status = consts.ASYNC_READ
                    elif ret == 1:
                        async_status = consts.ASYNC_WRITE
                    else:
                        raise ValueError()  # XXX

                self._conn._async_status = async_status
                self._conn._async_cursor = weakref.ref(self)

    def _pq_fetch(self):
        pgstatus = libpq.PQresultStatus(self._pgres)
        if pgstatus != libpq.PGRES_FATAL_ERROR:
            self._statusmessage = util.bytes_to_ascii(
                    ffi.string(libpq.PQcmdStatus(self._pgres)))
        else:
            self._statusmessage = None

        self._no_tuples = True
        self._rownumber = 0

        if pgstatus == libpq.PGRES_COMMAND_OK:
            rowcount = ffi.string(libpq.PQcmdTuples(self._pgres))
            if not rowcount or not rowcount[0]:
                self._rowcount = -1
            else:
                self._rowcount = int(rowcount)
            self._lastrowid = libpq.PQoidValue(self._pgres)
            self._clear_pgres()

        elif pgstatus == libpq.PGRES_TUPLES_OK:
            self._rowcount = libpq.PQntuples(self._pgres)
            return self._pq_fetch_tuples()

        elif pgstatus == libpq.PGRES_COPY_IN:
            return self._pq_fetch_copy_in()

        elif pgstatus == libpq.PGRES_COPY_OUT:
            return self._pq_fetch_copy_out()

        elif pgstatus == libpq.PGRES_EMPTY_QUERY:
            self._clear_pgres()
            raise ProgrammingError("can't execute an empty query")

        else:
            raise self._conn._create_exception(cursor=self)

    def _pq_fetch_tuples(self):
        with self._conn._lock:
            self._nfields = libpq.PQnfields(self._pgres)
            self._no_tuples = False
            description = []
            casts = []
            fast_parsers = []
            for i in xrange(self._nfields):
                ftype = libpq.PQftype(self._pgres, i)
                fsize = libpq.PQfsize(self._pgres, i)
                fmod = libpq.PQfmod(self._pgres, i)
                if fmod > 0:
                    fmod -= 4   # TODO: sizeof(int)

                if fsize == -1:
                    if ftype == 1700:   # NUMERIC
                        isize = fmod >> 16
                    else:
                        isize = fmod
                else:
                    isize = fsize

                if ftype == 1700:
                    prec = (fmod >> 16) & 0xFFFF
                    scale = fmod & 0xFFFF
                else:
                    prec = scale = None

                casts.append(self._get_cast(ftype))
                description.append(Column(
                    name=ffi.string(libpq.PQfname(self._pgres, i))\
                            .decode(self._conn._py_enc),
                    type_code=ftype,
                    display_size=None,
                    internal_size=isize,
                    precision=prec,
                    scale=scale,
                    null_ok=None,
                ))

                fast_parser = None
                if is_32bits:
                    # disable all fast parsers to avoid portability problems
                    pass
                elif ftype == 21 or ftype == 23:
                    fast_parser = libpq.PQEgetint, ffi.new("int32_t*")
                elif ftype == 20:
                    fast_parser = libpq.PQEgetlong, ffi.new("int64_t*")
                elif ftype == 700:
                    fast_parser = libpq.PQEgetfloat, ffi.new("float*")
                elif ftype == 701:
                    fast_parser = libpq.PQEgetdouble, ffi.new("double*")
                fast_parsers.append(fast_parser)


            self._description = tuple(description)
            self._casts = casts
            self._fast_parsers = fast_parsers

    def _pq_fetch_copy_in(self):
        pgconn = self._conn._pgconn
        size = self._copysize
        error = 0
        while True:
            data = self._copyfile.read(size)
            if isinstance(self._copyfile, TextIOBase):
                data = data.encode(self._conn._py_enc)

            if not data:
                break

            res = libpq.PQputCopyData(pgconn, data, len(data))
            if res <= 0:
                error = 2
                break

        errmsg = ffi.NULL
        if error == 2:
            errmsg = 'error in PQputCopyData() call'

        libpq.PQputCopyEnd(pgconn, errmsg)
        self._clear_pgres()
        util.pq_clear_async(self._conn)

    def _pq_fetch_copy_out(self):
        is_text = isinstance(self._copyfile, TextIOBase)
        pgconn = self._conn._pgconn
        while True:
            buf = ffi.new('char **')
            length = libpq.PQgetCopyData(pgconn, buf, 0)

            if length > 0:
                if buf[0] == ffi.NULL:
                    return
                value = ffi.buffer(buf[0], length)
                if is_text:
                    value = typecasts.parse_unicode(value[:], length, self)

                self._copyfile.write(value)
            elif length == -2:
                raise self._conn._create_exception(cursor=self)
            else:
                break

        self._clear_pgres()
        util.pq_clear_async(self._conn)

    def _build_row(self):
        row_num = self._rownumber

        # Create the row
        if self.row_factory:
            row = self.row_factory(self)
            is_tuple = False
        else:
            row = [None] * self._nfields
            is_tuple = True

        # Fill it
        n = self._nfields
        for i in xrange(n):
            if libpq.PQgetisnull(self._pgres, row_num, i):
                row[i] = None
            else:
                fast_parser = self._fast_parsers[i]
                if fast_parser is not None:
                    p = fast_parser[1]
                    error = fast_parser[0](p, self._pgres, row_num, i)
                    row[i] = None if error else p[0]
                else:
                    length = libpq.PQgetlength(self._pgres, row_num, i)
                    val = ffi.buffer(libpq.PQgetvalue(
                        self._pgres, row_num, i), length)[:]
                    row[i] = typecasts.typecast(
                            self._casts[i], val, length, self)

        self._rownumber += 1

        if is_tuple:
            return tuple(row)
        return row

    def _get_cast(self, oid):
        try:
            return self._typecasts[oid]
        except KeyError:
            try:
                return self._conn._typecasts[oid]
            except KeyError:
                try:
                    return typecasts.string_types[oid]
                except KeyError:
                    return typecasts.string_types[705]


def _combine_cmd_params(cmd, params, conn):
    """Combine the command string and params"""

    if isinstance(cmd, six.text_type):
        cmd = cmd.encode(conn._py_enc)

    # Return when no argument binding is required.  Note that this method is
    # not called from .execute() if `params` is None.
    if b'%' not in cmd:
        return cmd

    idx = 0
    next_start = 0
    param_num = 0
    n_arg_values = 0
    arg_values = None
    named_args_format = None
    parts = []

    cmd_length = len(cmd)
    while idx < cmd_length:

        # Escape
        if cmd[idx:idx+2] == b'%%':
            parts.append(cmd[next_start:idx])
            parts.append(b'%')
            idx += 1
            next_start = idx + 1

        # Named parameters
        elif cmd[idx:idx+2] == b'%(':

            # Validate that we don't mix formats
            if named_args_format is False:
                raise ValueError("argument formats can't be mixed")
            elif named_args_format is None:
                named_args_format = True

            # Check for incomplate placeholder
            max_lookahead = cmd.find(b'%', idx + 2)
            end = cmd.find(b')', idx + 2, max_lookahead)
            if end < 0:
                raise ProgrammingError(
                    "incomplete placeholder: '%(' without ')'")

            key = cmd[idx + 2:end].decode(conn._py_enc)
            if arg_values is None:
                arg_values = {}
            if key not in arg_values:
                arg_values[key] = _getquoted(params[key], conn)
            parts.append(cmd[next_start:idx])
            if six.PY3 and isinstance(arg_values[key], six.text_type):
                arg_values[key] = arg_values[key].encode(conn._py_enc)
            parts.append(arg_values[key])
            n_arg_values += 1
            next_start = end + 2

            _check_format_char(cmd[end + 1], idx)

        # Indexed parameters
        elif cmd[idx:idx+1] == b'%':

            # Validate that we don't mix formats
            if named_args_format is True:
                raise ValueError("argument formats can't be mixed")
            elif named_args_format is None:
                named_args_format = False

            _check_format_char(cmd[idx + 1], idx)

            value = _getquoted(params[param_num], conn)
            if six.PY3 and isinstance(value, six.text_type):
                value = value.encode(conn._py_enc)
            n_arg_values += 1
            parts.append(cmd[next_start:idx])
            parts.append(value)
            next_start = idx + 2

            param_num += 1
            idx += 1

        idx += 1

    parts.append(cmd[next_start:cmd_length])

    if named_args_format is False:
        if n_arg_values != len(params):
            raise TypeError(
                "not all arguments converted during string formatting")

    return b''.join(parts)


_s_ord = ord(b's')

def _check_format_char(format_char_ord, pos):
    """Raise an exception when the format_char is unsupported"""
    if not six.PY3:
        format_char_ord = ord(format_char_ord)
    if format_char_ord != _s_ord:
        raise ValueError(
            "unsupported format character 0x%x at index %d" %
            (format_char_ord, pos))


