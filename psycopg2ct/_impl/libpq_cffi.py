''' CFFI interface to libpq the library '''

from cffi import FFI

ffi = FFI()
ffi.cdef('''
typedef ... PGconn;
typedef ... PGresult;
typedef ... PGcancel;

typedef struct pgNotify
{
    char       *relname;        /* notification condition name */
    int        be_pid;            /* process ID of notifying server process */
    char       *extra;            /* notification parameter */
    ...;
} PGnotify;

extern PGconn *PQconnectStart(const char *conninfo);
''')
ffi.verify('#include <libpq-fe.h>', 
        libraries=['pq'],
        include_dirs=['/usr/include/postgresql/'])
