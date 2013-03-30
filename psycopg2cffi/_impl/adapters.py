from __future__ import unicode_literals

import datetime
import decimal
import math
import six
from six.moves import xrange

from psycopg2cffi._impl.libpq import libpq, ffi
from psycopg2cffi._impl.encodings import encodings
from psycopg2cffi._impl.exceptions import ProgrammingError
from psycopg2cffi._config import PG_VERSION
from psycopg2cffi.tz import LOCAL as TZ_LOCAL


adapters = {}


def ascii_to_bytes(s):
    ''' Convert ascii string to bytes
    '''
    if isinstance(s, six.text_type):
        return s.encode('ascii')
    else:
        assert isinstance(s, six.binary_type)
        return s


def bytes_to_ascii(b):
    ''' Convert ascii bytestring to string
    '''
    assert isinstance(b, six.binary_type)
    return b.decode('ascii')


# TODO - return bytes

class _BaseAdapter(object):
    def __init__(self, wrapped_object):
        self._wrapped = wrapped_object
        self._conn = None

    def __str__(self):
        return self.getquoted()

    @property
    def adapted(self):
        return self._wrapped


class ISQLQuote(_BaseAdapter):
    def getquoted(self):
        pass


class AsIs(_BaseAdapter):
    def getquoted(self):
        return ascii_to_bytes(self._wrapped)


class Binary(_BaseAdapter):
    def prepare(self, connection):
        self._conn = connection

    def __conform__(self, proto):
        return self

    def getquoted(self):
        if self._wrapped is None:
            return b'NULL'

        to_length = ffi.new('size_t *')
        _wrapped = ffi.new('unsigned char[]', self._wrapped)
        if self._conn:
            data_pointer = libpq.PQescapeByteaConn(
                self._conn._pgconn, _wrapped, len(self._wrapped), to_length)
        else:
            data_pointer = libpq.PQescapeBytea(
                _wrapped, len(self._wrapped), to_length)

        data = ffi.string(data_pointer)[:to_length[0] - 1]
        libpq.PQfreemem(data_pointer)

        if self._conn and self._conn._equote:
            return b''.join([b"E'", data,  b"'::bytea"])

        return b''.join([b"'", data,  b"'::bytea"])


class Boolean(_BaseAdapter):
    def getquoted(self):
        return b'true' if self._wrapped else b'false'


class DateTime(_BaseAdapter):
    def getquoted(self):
        obj = self._wrapped
        if isinstance(obj, datetime.timedelta):
            # TODO: microseconds
            return "'%d days %d.0 seconds'::interval" % (
                int(obj.days), int(obj.seconds))
        else:
            iso = obj.isoformat()
            if isinstance(obj, datetime.datetime):
                format = 'timestamp'
                if getattr(obj, 'tzinfo', None):
                    format = 'timestamptz'
            elif isinstance(obj, datetime.time):
                format = 'time'
            else:
                format = 'date'
            return "'%s'::%s" % (str(iso), format)


def Date(year, month, day):
    date = datetime.date(year, month, day)
    return DateTime(date)


def DateFromTicks(ticks):
    date = datetime.datetime.fromtimestamp(ticks).date()
    return DateTime(date)


class Decimal(_BaseAdapter):
    def getquoted(self):
        if self._wrapped.is_finite():
            value = str(self._wrapped)

            # Prepend a space in front of negative numbers
            if value.startswith('-'):
                value = ' ' + value
            return ascii_to_bytes(value)
        return b"'NaN'::numeric"


class Float(ISQLQuote):
    def getquoted(self):
        n = float(self._wrapped)
        if math.isnan(n):
            return b"'NaN'::float"
        elif math.isinf(n):
            if n > 0:
                return b"'Infinity'::float"
            else:
                return b"'-Infinity'::float"
        else:
            value = repr(self._wrapped)

            # Prepend a space in front of negative numbers
            if value.startswith('-'):
                value = ' ' + value
            return ascii_to_bytes(value)


class Int(_BaseAdapter):
    def getquoted(self):
        value = str(self._wrapped)

        # Prepend a space in front of negative numbers
        if value.startswith('-'):
            value = ' ' + value
        return ascii_to_bytes(value)


class List(_BaseAdapter):

    def prepare(self, connection):
        self._conn = connection

    def getquoted(self):
        length = len(self._wrapped)
        if length == 0:
            return b"'{}'"

        quoted = [None] * length
        for i in xrange(length):
            obj = self._wrapped[i]
            quoted[i] = _getquoted(obj, self._conn)
        return b''.join([b'ARRAY[', b', '.join(quoted), b']'])


class Long(_BaseAdapter):
    def getquoted(self):
        value = str(self._wrapped)

        # Prepend a space in front of negative numbers
        if value.startswith('-'):
            value = ' ' + value
        return ascii_to_bytes(value)


def Time(hour, minutes, seconds, tzinfo=None):
    time = datetime.time(hour, minutes, seconds, tzinfo=tzinfo)
    return DateTime(time)


def TimeFromTicks(ticks):
    time = datetime.datetime.fromtimestamp(ticks).time()
    return DateTime(time)


def Timestamp(year, month, day, hour, minutes, seconds, tzinfo=None):
    dt = datetime.datetime(
        year, month, day, hour, minutes, seconds, tzinfo=tzinfo)
    return DateTime(dt)


def TimestampFromTicks(ticks):
    dt = datetime.datetime.fromtimestamp(ticks, TZ_LOCAL)
    return DateTime(dt)


class QuotedString(_BaseAdapter):
    def __init__(self, obj):
        super(QuotedString, self).__init__(obj)
        self.encoding = "latin-1"

    def prepare(self, conn):
        self._conn = conn
        self.encoding = conn.encoding

    def getquoted(self):

        obj = self._wrapped
        if isinstance(obj, six.text_type):
            encoding = encodings[self.encoding]
            obj = obj.encode(encoding)
        else:
            assert isinstance(obj, six.binary_type)
        string = obj
        length = len(string)

        to_length = (length * 2) + 1
        to = ffi.new('char []', to_length)

        if not self._conn:
            libpq.PQescapeString(to, string, length)
            return b''.join([b"'", ffi.string(to), b"'"])

        if PG_VERSION < 0x090000:
            err = ffi.new('int *')
            libpq.PQescapeStringConn(
                self._conn._pgconn, to, string, length, err)
            if self._conn and self._conn._equote:
                return b''.join([b"E'", ffi.string(to), b"'"])
            return b''.join([b"'", ffi.string(to), b"'"])

        data_pointer = libpq.PQescapeLiteral(
            self._conn._pgconn, string, length)
        data = ffi.string(data_pointer)
        libpq.PQfreemem(data_pointer)
        return data


def adapt(value, proto=ISQLQuote, alt=None):
    """Return the adapter for the given value"""
    obj_type = type(value)
    try:
        return adapters[(obj_type, proto)](value)
    except KeyError:
        for subtype in obj_type.mro()[1:]:
            try:
                return adapters[(subtype, proto)](value)
            except KeyError:
                pass

    conform = getattr(value, '__conform__', None)
    if conform is not None:
        return conform(proto)
    raise ProgrammingError("can't adapt type '%s'" % obj_type.__name__)


def _getquoted(param, conn):
    """Helper method"""
    if param is None:
        return 'NULL'
    adapter = adapt(param)
    try:
        adapter.prepare(conn)
    except AttributeError:
        pass
    return adapter.getquoted()


built_in_adapters = {
    bool: Boolean,
    str: QuotedString,
    list: List,
    bytearray: Binary,
    int: Int,
    float: Float,
    datetime.date: DateTime, # DateFromPY
    datetime.datetime: DateTime, # TimestampFromPy
    datetime.time: DateTime, # TimeFromPy
    datetime.timedelta: DateTime, # IntervalFromPy
    decimal.Decimal: Decimal,
}

try: built_in_adapters[memoryview] = Binary
except NameError: pass # Python 2.6

try: built_in_adapters[buffer] = Binary
except NameError: pass # Python 3

try: built_in_adapters[unicode] = QuotedString
except NameError: pass # Python 3

try: built_in_adapters[long] = Long
except NameError: pass # Python 3 - Int handles all numbers fine

if six.PY3:
    built_in_adapters[bytes] = Binary


for k, v in built_in_adapters.items():
    adapters[(k, ISQLQuote)] = v
