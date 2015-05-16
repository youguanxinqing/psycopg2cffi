from _libpq import ffi, lib as libpq


# imported from postgres/src/include/postgres_ext.h

class libpq_const:
    PG_DIAG_SEVERITY        = ord('S')
    PG_DIAG_SQLSTATE        = ord('C')
    PG_DIAG_MESSAGE_PRIMARY = ord('M')
    PG_DIAG_MESSAGE_DETAIL  = ord('D')
    PG_DIAG_MESSAGE_HINT    = ord('H')
    PG_DIAG_STATEMENT_POSITION = ord('P')
    PG_DIAG_INTERNAL_POSITION = ord('p')
    PG_DIAG_INTERNAL_QUERY  = ord('q')
    PG_DIAG_CONTEXT         = ord('W')
    PG_DIAG_SCHEMA_NAME     = ord('s')
    PG_DIAG_TABLE_NAME      = ord('t')
    PG_DIAG_COLUMN_NAME     = ord('c')
    PG_DIAG_DATATYPE_NAME   = ord('d')
    PG_DIAG_CONSTRAINT_NAME = ord('n')
    PG_DIAG_SOURCE_FILE     = ord('F')
    PG_DIAG_SOURCE_LINE     = ord('L')
    PG_DIAG_SOURCE_FUNCTION = ord('R')
