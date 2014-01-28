"""A mighty handle for performing MySQL database operations."""

import mysql.connector
#from mysql.connector import errorcode

DB_NAME = 'routeme'

class DBHandle(object):

    """"Usage:

    >>> dbh = DBHandle()
    >>> for pid, place in dbh('SELECT id, place FROM Place'):
    ...     print pid, place
    """

    def __init__(self, database='routeme', user='root', password=None):

        self._conn = mysql.connector.connect(database=database, user=user,
            password=password, charset='utf8')
        self.cursor = self._conn.cursor()


    def __call__(self, operation, params=None, commit=True, multi=False):

        operation = operation.strip()
        if params is None:
            sw = operation.startswith
            self.cursor.execute(operation)
            if sw('UPDATE') or sw('ALTER') or sw('DELETE'):
                if commit:
                    return self._conn.commit()
            else:
                result = self.cursor.fetchall()
                return result
        else:
            if multi:
                self.cursor.executemany(operation, params)
            else:
                self.cursor.execute(operation, params)
            if commit:
                return self._conn.commit()

    def __del__(self):

        self._conn.commit()
        self.cursor.close()
        self._conn.close()
