from _libpq import ffi, lib as libpq


# imported from postgres/src/include/postgres_ext.h

"""
libpq.PG_DIAG_SEVERITY        = ord('S')
libpq.PG_DIAG_SQLSTATE        = ord('C')
libpq.PG_DIAG_MESSAGE_PRIMARY = ord('M')
libpq.PG_DIAG_MESSAGE_DETAIL  = ord('D')
libpq.PG_DIAG_MESSAGE_HINT    = ord('H')
libpq.PG_DIAG_STATEMENT_POSITION = ord('P')
libpq.PG_DIAG_INTERNAL_POSITION = ord('p')
libpq.PG_DIAG_INTERNAL_QUERY  = ord('q')
libpq.PG_DIAG_CONTEXT         = ord('W')
libpq.PG_DIAG_SCHEMA_NAME     = ord('s')
libpq.PG_DIAG_TABLE_NAME      = ord('t')
libpq.PG_DIAG_COLUMN_NAME     = ord('c')
libpq.PG_DIAG_DATATYPE_NAME   = ord('d')
libpq.PG_DIAG_CONSTRAINT_NAME = ord('n')
libpq.PG_DIAG_SOURCE_FILE     = ord('F')
libpq.PG_DIAG_SOURCE_LINE     = ord('L')
libpq.PG_DIAG_SOURCE_FUNCTION = ord('R')
"""
