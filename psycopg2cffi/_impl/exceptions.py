class OperationError(Exception):
    pass


class Warning(StandardError):
    pass


class Error(StandardError):
    pgerror = None
    pgcode = None
    cursor = None

    def __reduce__(self):
        t = super(Error, self).__reduce__()
        if not isinstance(t, tuple):
            return t
        # note: in c implementation reduce returns a 2-items tuple;
        # in python a 3-items tuple. Maybe the c exception doesn't have a dict?
        if len(t) != 3:
            return t

        d = t[2].copy()
        d.pop('cursor', None)
        return (t[0], t[1], d)

    def __setstate__(self, state):
        print "setstate"
        self.pgerror = state.get('pgerror')
        self.pgcode = state.get('pgcode')


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


class QueryCanceledError(OperationalError):
    pass


class TransactionRollbackError(OperationalError):
    pass
