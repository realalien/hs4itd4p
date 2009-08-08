#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#                 BUGZILLA.PY -- INTERFACE TO BUGZILLA
#
#             Nick Barnes, Ravenbrook Limited, 2000-11-21
#
#
# 1. INTRODUCTION
#
# This module defines a Python interface to the Bugzilla database.  Its
# design is documented in [NB 2000-11-14c].  It accesses and updates
# data according to the Bugzilla schema [NB 2000-11-14a] and schema
# extensions [NB 2000-11-14b].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import os
import re
import string
import types

error = 'Bugzilla database error'

class bugzilla:

    schema_version = '5'
    # particular Bugzilla features.  Maybe should have a 'feature'
    # dictionary.
    features = {}
    bugzilla_version = None
    db = None
    cursor = None
    rid = None
    sid = None
    replication = None
    logger = None
    bugmail_commands = None
    cache = None

    # 2. BUGZILLA INTERFACE

    def __init__(self, db, config):
        self.db = db
        self.cache = {}
        self.bugmail_commands = []
        self.logger = config.logger
        self.cursor = self.db.cursor()
        self.rid = config.rid
        self.sid = config.sid
        self.bugzilla_directory = config.bugzilla_directory
        self.bugmail_command = config.bugmail_command
        self.check_mysql_version()
        self.check_bugzilla_version()
        self.update_p4dti_schema()

        # Make a configuration dictionary and pass it to set_config to
        # ensure that the copy of the configuration in the Bugzilla
        # database is up-to-date.
        c = {
            'replicator_user': config.replicator_address,
            'p4_server_description': config.p4_server_description,
            }
        if config.changelist_url is not None:
            c['changelist_url'] = config.changelist_url
        if config.job_url is not None:
            c['job_url'] = config.job_url
        self.set_config(c)

        # Fetch Bugzilla's configuration parameters (if they can be
        # found in the database).
        self.fetch_bugzilla_config()

        # Check whether the MySQL database character set
        # settings are appropriate for UTF8 replication.
        self.check_utf8_config()

    def log(self, id, args = ()):
        msg = catalog.msg(id, args)
        self.logger.log(msg)


    # 3. DATABASE INTERFACE
    #
    # The Python database interface [DBAPI 2.0] is very basic.  This
    # section bulds up some layers of abstraction, providing logging
    # (section 3.1), checking and conversion (section 3.2), quoting
    # (section 3.3).


    # 3.1. SQL wrappers
    #
    # These three methods directly wrap methods in the database
    # interface [DBAPI 2.0], logging the executed SQL commands and
    # the returned results.

    # execute(sql) executes the given SQL command and returns the number
    # of rows returned.

    def execute(self, sql, params=None):
        assert isinstance(sql, basestring)
        # "Executing SQL command '%s'."
        self.log(100, repr((sql, params)))
        self.cursor.execute(sql, params)
        rows = self.cursor.rowcount
        # "MySQL returned '%s'."
        self.log(101, repr(rows))
        return rows

    # fetchone() fetches one row from the current result set and returns
    # it as a sequence.

    def fetchone(self):
        row = self.cursor.fetchone()
        # "fetchone() returned '%s'."
        self.log(102, repr(row))
        return row

    # fetchall() fetches all the rows from the current result and
    # returns them as a sequence of sequences.

    def fetchall(self):
        rows = self.cursor.fetchall()
        # "fetchall() returned '%s'."
        self.log(103, repr(rows))
        return rows


    # 3.2. Select methods
    #
    # These methods select rows from the database, checking that the
    # results are as expected, and converting the results into various
    # data structures.
    #
    # In all of these select methods, the description argument is a
    # description of the data being selected; it's used in error
    # messages.

    # select_one_row(select, description) executes the SQL select
    # statement, checks that it returns exactly one row, and returns the
    # row as a sequence.

    def select_one_row(self, select, description):
        nrows = self.execute(select)
        if nrows == 0:
            # "Select '%s' of %s returns no rows."
            raise error, catalog.msg(106, (select, description))
        elif nrows > 1:
            # "Select '%s' of %s expecting one row but returns %d."
            raise error, catalog.msg(107, (select, description, nrows))
        elif self.cursor.description == None:
            # "Trying to fetch a row from non-select '%s'."
            raise error, catalog.msg(108, select)
        row = self.fetchone()
        if row == None:
            # "Select '%s' of %s returned an unfetchable row."
            raise error, catalog.msg(109, (select, description))
        else:
            return row

    # select_rows(select, description) executes the SQL select
    # statement, checks that it executed correctly, and returns all the
    # results as a sequence of sequences.

    def select_rows(self, select, description):
        self.execute(select)
        if self.cursor.description == None:
            # "Trying to fetch rows from non-select '%s'."
            raise error, catalog.msg(110, select)
        rows = self.fetchall()
        if rows == None:
            # "Select '%s' of %s returned unfetchable rows."
            raise error, catalog.msg(111, (select, description))
        else:
            return rows

    # select_at_most_one_row(select, description) executes the SQL
    # select statement, check that it returns at most one row, and
    # returns the row as a sequence, or None if there was no row.

    def select_at_most_one_row(self, select, description):
        rows = self.select_rows(select, description)
        if len(rows) == 0:
            return None
        elif len(rows) == 1:
            return rows[0]
        else:
            # "Select '%s' of %s expecting no more than one row but
            # returns %d."
            raise error, catalog.msg(112, (select, description, rows))

    # column_names() returns a list of the column names of the results
    # of the most recent select.  (It will raise a TypeError if the most
    # recent operation was not a select.)

    def column_names(self):
        return map(lambda d:d[0], self.cursor.description)

    # row_to_dictionary(row, columns, select, description) takes a row
    # from the results of the most recent select statement and returns
    # it as a dictionary mapping column name to value.  The columns
    # argument is a sequence of column names for the results of the
    # select statement; the select argument is the most recent SQL
    # select statement; and description is a description of the data
    # being selected.  (The select and description arguments are used in
    # error messages.)

    def row_to_dictionary(self, row, columns, select, description):
        if len(columns) != len(row):
            # "Select '%s' of %s returns %d columns but %d values."
            raise error, catalog.msg(113, (select, description,
                                           len(columns), len(row)))
        dict = {}
        for i in range(len(columns)):
            dict[columns[i]] = row[i]
        return dict

    # fetch_one_row_as_dictionary(select, description) executes the SQL
    # select statement, checks that it returns exactly one row, and
    # return that row as a dictionary mapping column name to value.

    def fetch_one_row_as_dictionary(self, select, description):
        row = self.select_one_row(select, description)
        columns = self.column_names()
        return self.row_to_dictionary(row, columns, select, description)

    # fetch_at_most_one_row_as_dictionary(select, description) executes
    # the SQL select statement, check that it returns at most one row,
    # and returns the row as a dictionary mapping column name to value,
    # or None if there was no row.

    def fetch_at_most_one_row_as_dictionary(self, select, description):
        row = self.select_at_most_one_row(select, description)
        if row == None:
            return None
        columns = self.column_names()
        return self.row_to_dictionary(row, columns, select, description)

    # fetch_rows_as_list_of_dictionaries(select, description) executes
    # the SQL select statement, and returns the results as a list of
    # dictionaries mapping column name to value.

    def fetch_rows_as_list_of_dictionaries(self, select, description):
        rows = self.select_rows(select, description)
        columns = self.column_names()
        def r2d(row, self=self, c=columns, s=select, d=description):
            return self.row_to_dictionary(row, c, s, d)
        return map(r2d, rows)

    # fetch_rows_as_list_of_sequences(select, description) executes the
    # SQL select statement, and returns the result as a list of
    # sequences.

    def fetch_rows_as_list_of_sequences(self, select, description):
        rows = self.select_rows(select, description)
        # select_rows may be any sequence type; we want a list.
        return list(rows)

    # fetch_simple_rows_as_dictionary(select, description) executes the
    # SQL select statement and returns a dictionary mapping the value in
    # the first column to the value in the second.

    def fetch_simple_rows_as_dictionary(self, select, description):
        rows = self.fetch_rows_as_list_of_sequences(select, description)
        dict = {}
        for row in rows:
            dict[row[0]] = row[1]
        return dict

    # Get the set of table names.
    def table_names(self):
        if not self.cache.has_key('table names'):
            tables = self.fetch_rows_as_list_of_sequences('show tables',
                                                          'list all tables')
            # Use table names only.
            self.cache['table names'] = map(lambda x:x[0], tables)
        return self.cache['table names']

    # 4. QUOTATION

    def quote_string(self, s):
        return "'%s'" % self.db.escape_string(s)
    #
    # We now use MySQLdb's parameter-passing mechanism for most
    # arguments; see [DBAPI 2.0]).  The remaining code here enables us
    # to write SQL expressions which aren't possible with the %s
    # parameter-passing, and which we need for particular fields.
    #
    # - now() in a datetime field when passing an empty string;
    # - encrypt(password) in an encrypted field when passed an empty string;
    # - encrypt(%s) in an encrypted field.

    # if_empty_then_now(value) is the quote method for timestamps
    # fields.

    def if_empty_then_now(self, value):
        if value == '':
            return 'now()'
        else:
            return ('%s', value)

    # cryptpassword(value) is the quote method for encrypted passwords.

    def cryptpassword(self, value):
        if value == '':
            return 'encrypt(password)'
        else:
            return ('encrypt(%s)', value)

    # quote_table maps (table name, field name) to the quote method for
    # that field.

    quote_table = {
        ('bugs', 'creation_ts'): if_empty_then_now,
        ('bugs', 'delta_ts'): if_empty_then_now,
        ('longdescs', 'bug_when'): if_empty_then_now,
        ('p4dti_bugs', 'migrated'): if_empty_then_now,
        ('p4dti_replications', 'end'): if_empty_then_now,
        ('profiles', 'cryptpassword'): cryptpassword,
        }

    # quote(table, field, value) quotes the value for inclusion in a SQL
    # command, for inclusion in the given field in the given table.

    def quote(self, table, field, value):
        quoter = self.quote_table.get((table, field))
        if quoter:
            return quoter(self, value)
        else:
            return ('%s', value)


    # 5. TYPES
    #
    #
    # 5.1. MySQL column types
    #
    # These functions allow us to interrogate the database schema and
    # determine column types.  A column type is returned from MySQL as a
    # row with these columns (note that we don't make use of 'Key' or
    # 'Extra'):
    #
    #   Field     The column name.
    #   Type      SQL type.
    #   Default   Default value or None.
    #   Null      'YES' if Null is allowed, '' if not.
    #   Key       How column is indexed ('PRI', 'UNI', 'MUL', or '').
    #   Extra     Column attributes (for example, auto_increment).
    #
    #
    # 5.2. P4DTI column types
    #
    # We decode the type into a dictionary with these keys:
    #
    #   field     The column name.
    #   type      The SQL type (enum/int/float/date/timestamp/text);
    #             'user' if it contains a Bugzilla user id; 'other' if
    #             we don't recognise it.
    #   length    Length (for text and integer fields).
    #   null      Null allowed? (0 or 1)
    #   default   The default value or None.
    #   values    Legal values (for enum fields).
    #   sql_type  The original SQL type.

    # user_fields is a dictionary mapping (table name, field name) to
    # to a suitable Perforce default value, for user fields only
    # (their database type is integer but we need to treat them
    # specially).

    user_fields = {
        ('bugs', 'assigned_to') : '$user',
        ('bugs', 'reporter'):     '$user',
        ('bugs', 'qa_contact'):   'None',
        }

    # convert_type(table, dict) converts dict, a MySQL column
    # description (section 5.1) for the specified table, into a P4DTI
    # column description (section 5.2) and returns it.

    def convert_type(self, table, dict):
        name = dict['Field']
        sql_type = dict['Type']
        column = {
            'field': name,
            'sql_type': sql_type,
            'default': dict['Default'],
            'null': dict['Null'] == 'YES',
            }

        # User fields.
        if self.user_fields.has_key((table, name)):
            column['type'] = 'user'
            column['default'] = self.user_fields[(table, name)]
            return column

        # Enumerated fields.
        match = re.match("^enum\('(.*)'\)$", sql_type)
        if match:
            enum_values = string.split(match.group(1), "','")
            column['type'] = 'enum'
            column['length'] = max(map(len, enum_values))
            column['values'] = enum_values
            return column

        # Integer fields.
        match = re.match("^(tinyint|smallint|mediumint|int|bigint)"
                         "\((.*)\)$", sql_type)
        if match:
            column['type'] = 'int'
            column['length'] = int(match.group(2))
            return column

        # Date fields.
        match = re.match("^datetime", sql_type)
        if match:
            column['type'] = 'date'
            # We don't support default dates.
            column['default'] = None
            return column

        # Timestamp fields.
        match = re.match("^timestamp", sql_type)
        if match:
            column['type'] = 'timestamp'
            # We don't support default timestamps.
            column['default'] = None
            return column

        # Sized text fields.
        match = re.match("^(char|varchar)\((.*)\)$", sql_type)
        if match:
            column['type'] = 'text'
            column['length'] = int(match.group(2))
            return column

        # Implicit-sized text fields.
        text_length = {
            'tinyblob': 0xff,
            'tinytext': 0xff,
            'blob': 0xffff,
            'text': 0xffff,
            'mediumblob': 0xffffff,
            'mediumtext': 0xffffff,
            'longblob': 0xffffffffL,
            'longtext': 0xffffffffL,
            }
        if text_length.has_key(sql_type):
            column['type'] = 'text'
            column['length'] = text_length[sql_type]
            return column

        # Floating-point fields.
        match = re.match("^(float|double|decimal)", sql_type)
        if match:
            column['type'] = 'float'
            return column

        # Field types we don't know how to handle includes date, time,
        # year, set(...).  We don't raise an exception here because we
        # might not look at this field so might not care that we don't
        # know what type it is.
        column['type'] = 'other'
        return column

    def get_columns(self, table):
        return self.fetch_rows_as_list_of_dictionaries(
            'describe %s;' % table, 'describe %s' % table)
    # get_types(table) returns a dictionary mapping name to type for all
    # the columns in the table.

    def get_types(self, table):
        results = self.get_columns(table)
        columns = {}
        for result in results:
            columns[result['Field']] = self.convert_type(table, result)
        # fake some fields for the 'bugs' table;
        if table == 'bugs':
            columns['longdesc'] = { 'field': 'longdesc',
                                    'type': 'text',
                                    'length': 0,
                                    'default': None,
                                    'null': 0, }

            # From Bugzilla 2.17.1, the products and components tables
            # are normalized.  We fake something resembling the old
            # schema, as 'product' and 'component' are really bug fields.
            #
            # When we drop support for Bugzilla 2.16.x and earlier, we
            # can do this differently.
            
            if self.features.has_key('normalized tables'):
                del columns['product_id']
                del columns['component_id']
                product_cols = self.get_columns('products')
                for c in product_cols:
                    if c['Field'] == 'name':
                        columns['product'] = self.convert_type('products', c)
                        columns['product']['field'] = 'product'
                component_cols = self.get_columns('components')
                for c in component_cols:
                    if c['Field'] == 'name':
                        columns['component'] = self.convert_type('components', c)
                        columns['component']['field'] = 'component'

            # From Bugzilla 2.19.3, we no longer have any enum columns,
            # but enum tables instead.
            if self.features.has_key('enum tables'):
                # Start off with a list of the built-in enum tables:

                #                field name      param for default value
                enum_tables =  [('bug_severity', 'defaultseverity'),
                                ('bug_status',   'defaultstatus'),
                                ('op_sys', 'defaultopsys'),
                                ('priority', 'defaultpriority'),
                                ('rep_platform', 'defaultplatform'),
                                ('resolution', None),
                                ]
                # From Bugzilla 3.0, also consider custom enum tables
                if self.features.has_key('custom fields'):
                    for (name,cf) in self.custom_fields().items():
                        if cf.get('type') == 2: # FIELD_TYPE_SINGLE_SELECT
                            enum_tables.append((name, None))
                # now get all the possible values
                for (col, defparam) in enum_tables:
                    default = self.params.get(defparam)
                    
                    values = self.fetch_rows_as_list_of_sequences('select value from %s where isactive=1 order by sortkey' % col,
                                                                  'get possible values of %s' % col)
                    values = map(lambda x:x[0], values)
                    if default not in values:
                        default = values[0]
                    columns[col]['length'] = max(map(lambda x:len(x),
                                                     values))
                    columns[col]['type'] = 'enum'
                    columns[col]['values'] = values
                    columns[col]['default'] = default
            # Non-enum custom fields already showed up in 'describe bugs'
        return columns


    # 6. BASIC OPERATIONS

    # table_present(tablename) returns 1 if the named table is present
    # in the database, 0 otherwise.

    def table_present(self, tablename):
        assert isinstance(tablename, types.StringType)
        rows = self.execute("show tables like %s;"
                            % self.quote_string(tablename))
        return rows == 1

    # insert_row(table, dict) inserts a row (specified as a dictionary
    # mapping column name to value) into the given table.

    def insert_row(self, table, dict):
        keys = []
        values = []
        params = []
        for (key,value) in dict.items():
            quoted = self.quote(table, key, value)
            if isinstance(quoted, tuple):
                params.append(quoted[1])
                quoted = quoted[0]
            keys.append(key)
            values.append(quoted)
        command = ("insert %s ( %s ) values ( %s );"
                   % (table, ','.join(keys), ','.join(values)))
        rows = self.execute(command, params)
        if rows != 1:
            # "Couldn't insert row in table '%s'."
            raise error, catalog.msg(116, table)

    # insert_row_rid_sid is the same as insert_row, but includes rid and
    # sid columns in the inserted row.

    def insert_row_rid_sid(self, table, dict):
        dict['rid'] = self.rid
        dict['sid'] = self.sid
        self.insert_row(table, dict)

    # update_row(table, dict, where) updates the rows in the given table
    # matching the "where" clause so that they have have the values
    # specified by the dictionary mapping column name to value.  An
    # error is raised if there is no row, or more than one row, matching
    # the "where" clause.

    def update_row(self, table, dict, where):
        updates = []
        params = []
        for (key,value) in dict.items():
            quoted = self.quote(table, key, value)
            if isinstance(quoted, tuple):
                params.append(quoted[1])
                quoted = quoted[0]
            updates.append("%s = %s" % (key, quoted))
        command = "update %s set %s where %s;" % (table,
                                                  ','.join(updates),
                                                  where)
        rows = self.execute(command, params)
        if rows != 1:
            # "Couldn't update row in table '%s' where %s."
            raise error, catalog.msg(117, (table, where))

    # update_row_rid_sid is the same as update_row, but includes rid and
    # sid columns in the "where" clause.

    def update_row_rid_sid(self, table, dict, where):
        self.update_row(table, dict, where +
                        (' and rid = %s and sid = %s' %
                         (self.quote_string(self.rid),
                          self.quote_string(self.sid))))

    # delete_rows(table, where) deletes all rows in the given table
    # matching the "where" clause.

    def delete_rows(self, table, where):
        self.execute('delete from %s where %s;' % (table, where))

    # delete_rows_rid_sid is the same as delete_rows, but includes rid
    # and sid columns in the "where" clause.

    def delete_rows_rid_sid(self, table, where):
        self.delete_rows(table, where +
                         (' and rid = %s and sid = %s' %
                          (self.quote_string(self.rid),
                           self.quote_string(self.sid))))


    # 7. BUGZILLA VERSIONS
    #
    # The methods in this section detect the Bugzilla version (by
    # analyzing the database schema) and handle these differences
    # between Bugzilla versions.
    # 
    # bugzilla_version_map is a list of triplets.  Each triplet is
    # (Bugzilla version, tables added, tables removed).  Using this
    # table we can work out the Bugzilla version by executing "show
    # tables" and then going through the versions until we find one
    # whose tables are not all present.  See [NB 2000-11-14a] for a
    # variorum edition of the schemas for many Bugzilla versions.

    bugzilla_version_map = [
        ('2.0', ['bugs',
                 'bugs_activity',
                 'cc',
                 'components',
                 'logincookies',
                 'profiles',
                 'versions',
                 ], []),

        ('2.2', ['products',
                 ], []),

        ('2.4', ['attachments',
                 'groups',
                 ], []),

        ('2.6', ['dependencies',
                 ], []),

        ('2.8', ['votes',
                 ], []),

        ('2.10', ['watch',
                  'longdescs',
                  'profiles_activity',
                  'namedqueries',
                  'fielddefs',
                  'keywords',
                  'keyworddefs',
                  'milestones',
                  'shadowlog',
                  ], []),

        ('2.12', ['duplicates',
                  ], []),

        ('2.14', ['tokens',
                  ], []),

        ('2.16', ['attachstatusdefs',
                  'attachstatuses',
                  ], []),

        ('2.17.1', ['bug_group_map',
                    'user_group_map',
                    'group_group_map',
                    'flags',
                    'flagtypes',
                    'flaginclusions',
                    'flagexclusions',
                    'quips',
                    ], ['attachstatusdefs',
                        'attachstatuses',
                        ]),
        ('2.17.3', ['group_control_map',
                    ], ['shadowlog',
                        ]),
        ('2.17.5', ['series',
                    'series_categories',
                    'series_data',
                    'user_series_map',
                    ], []),
        ('2.18', ['category_group_map',
                  ], ['user_series_map',
                      ]),
        ('2.19.1', ['classifications',
                    'whine_events',
                    'whine_queries',
                    'whine_schedules',
                    ], []),
        # the following tables actually added in 2.19.3
        ('2.20', ['bug_severity',
                  'bug_status',
                  'op_sys',
                  'priority',
                  'rep_platform',
                  'resolution',
                  'bz_schema',
                  'profile_setting',
                  'setting',
                  'setting_value',
                  'email_setting',
                  ], []),
        ('2.22', ['attach_data', # actually added in 2.21.1
                    ], []),
        ('3.0' , ['component_cc', # actually added in 2.23.3
                  'namedquery_group_map', # actually added in 2.23.3
                  'namedqueries_link_in_footer', # actually added in 2.23.3
                    ], []),
        ]

    # The list of Bugzilla versions supported by the P4DTI:
    bugzilla_versions_supported = ['2.20',
                                   '2.22',
                                   '3.0',
                                   ]
                                   
    # find_bugzilla_version() determines the Bugzilla version.  It
    # returns a pair: a string containing the Bugzilla version and a
    # list of names of tables which are present in the database but not
    # in the schema for that version of Bugzilla (this will mean either
    # that the Bugzilla has been modified or extended, or is a future
    # version).

    def find_bugzilla_version(self):
        tables = self.table_names()

        # Eliminate P4DTI table (these all start with "p4dti_").
        tables = filter(lambda x:x[:6] != 'p4dti_', tables)

        # Work out the version.
        best_version = None
        version_tables = []
        for (version, added, removed) in self.bugzilla_version_map:
            version_tables = version_tables + added
            for table in removed:
                version_tables.remove(table)
            # version_tables is now the list of tables in this version.
            extra = tables[:]
            missing = []
            for table in version_tables:
                if table in extra:
                    extra.remove(table)
                else:
                    missing.append(table)
            badness = len(missing) + len(extra)
            if ((best_version is None) or
                (badness < best_version[1])):
                best_version = (version, badness, extra, missing)
                if badness == 0: # exact match
                    break

        return best_version

    # check_bugzilla_version() finds the Bugzilla version (by inspecting
    # the database, using find_bugzilla_version above), checks that it
    # is supported by the P4DTI, and causes an error if not.

    def check_bugzilla_version(self):
        version, badness, extra, missing  = self.find_bugzilla_version()
        if missing:
            if extra:
                # "Bugzilla version %s detected, with these tables
                # missing: %s and these additional tables present: %s.
                # The P4DTI may fail to operate correctly."
                self.log(131, (version, missing, extra))
            else:
                # "Bugzilla version %s detected, with these tables
                # missing: %s.  The P4DTI may fail to operate correctly."
                self.log(132, (version, missing))
        else:
            if extra:
                # "Bugzilla version %s detected, with these additional
                # tables present: %s."
                self.log(124, (version, extra))
            else:
                # "Bugzilla version %s detected."
                self.log(125, version)
        if version not in self.bugzilla_versions_supported:
            # "Bugzilla version %s is not supported by the P4DTI."
            raise error, catalog.msg(123, version)
        if version >= '2.17':
            self.features['normalized tables'] = 1
        else:
            self.features['bitset groups'] = 1
        if version >= '2.17.3':
            self.features['group_control_map'] = 1
        if version >= '2.20':
            self.features['enum tables'] = 1
        if version >= '3.0':
            self.features['custom fields'] = 1
        self.bugzilla_version = version
        

    def mysql_unsupported(self, version):
        # "MySQL version %s is not supported by the P4DTI."
        raise error, catalog.msg(134, version)

    def mysql_deprecated_unicode(self, version):
        # "MySQL version %s detected.  Use of this
        # version is deprecated due to poor Unicode support."
        self.log(136, version)

    def mysql_supported(self, version):
        self.features['mysql_unicode'] = 1
        # "MySQL version %s detected."
        self.log(135, version)

    # The MySQL versions supported by the P4DTI:
    mysql_version_patterns = [(r'4\.0\.', mysql_deprecated_unicode),
                              (r'4\.1\.', mysql_supported),
                              (r'5\.0\.', mysql_supported),
                              (r'5\.1\.', mysql_supported),
                              ]

    # check_mysql_version() identifies the MySQL version and warns if
    # it is not supported.

    def check_mysql_version(self):
        version_row = self.select_at_most_one_row(
            "show variables like 'version'",
            "MySQL version string")
        if version_row:
            mysql_version_string = version_row[1]
            for (pattern, fn) in self.mysql_version_patterns:
                if re.match(pattern, mysql_version_string):
                    fn(self, mysql_version_string)
                    return
            self.mysql_unsupported(mysql_version_string)
        else:
            # "Could not determine MySQL version."
            raise error, catalog.msg(137)

    # check_utf8_config() attempts to determine whether the Bugzilla
    # database is set to UTF-8 encoding.
    #
    # We just check the character set of the longdescs table
    # and the longdescs.thetext column.

    def check_utf8_config(self):
        if (self.features.has_key('mysql_unicode') and
            self.params.get('utf8','0') == '1'):

            create_row = self.select_at_most_one_row(
                "show create table longdescs",
                "Get create table command to check character sets")

            table_charset = 'unknown'
            if create_row:
                create_command = create_row[1]
                # find the table character set
                m = re.search('DEFAULT CHARSET=([a-z0-9]+)', create_command)
                if m:
                    table_charset = m.group(1)
                    
            if table_charset != 'utf8':
                # "Bugzilla is configured to store text in UTF-8
                # encoding, but the Bugzilla database is not
                # configured for that encoding (table '%s' has
                # character set '%s').  Replication of non-ASCII text
                # data may be incorrect."
                self.log(138, ('longdescs', table_charset))
            else:
                # "Bugzilla table '%s' has character set '%s'."
                self.log(140, ('longdescs', table_charset))

                # table is UTF-8; check column character set
                column_charset = table_charset
                m = re.search('\\n *`thetext`(.*)\\n', create_command)
                if m:
                    m = re.search('character set ([a-z0-9]+)', m.group(1))
                    if m:
                        column_charset = m.group(1)
                else:
                    column_charset = 'not found'
                if column_charset != 'utf8':
                    # "Bugzilla is configured to store text in UTF-8
                    # encoding, but the Bugzilla database is not
                    # configured for that encoding (column '%s' has
                    # character set '%s').  Replication of non-ASCII
                    # text data may be incorrect."
                    self.log(139, ('longdescs.thetext',
                                   column_charset))
                else:
                    # "Bugzilla column '%s' has character set '%s'."
                    self.log(141, ('longdescs.thetext',
                                   column_charset))
                    self.features['unicode'] = 1
        

    # 8. P4DTI SCHEMA EXTENSIONS
    #
    # See [NB 2000-11-14b] for the definition of the schema extensions.
    #
    # The P4DTI schema extensions have gone through a number of
    # versions, described in detail in [NB 2000-11-14b, 5].  When the
    # P4DTI is upgraded, it must check to see if the schema extensions
    # belong to an old schema version; if so, they must be upgraded to
    # the new schema version.

    # p4dti_schema_extensions is a list of pairs (table, sql) giving the
    # name of a table in the P4DTI schema extensions and the SQL command
    # used to create it.

    p4dti_schema_extensions = [
        ('p4dti_bugs',
         "create table p4dti_bugs "
         "  ( bug_id mediumint not null primary key, "
         "    rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    jobname text not null, "
         "    migrated datetime, "
         "    index(bug_id) "
         "  );"),

        ('p4dti_bugs_activity',
         "create table p4dti_bugs_activity "
         "  ( bug_id mediumint not null, "
         "    who mediumint not null, "
         "    bug_when datetime not null, "
         "    fieldid mediumint not null, "
         "    oldvalue tinytext, "
         "    newvalue tinytext, "
         "    rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    index(bug_id), "
         "    index(bug_when) "
         "  );"),

        ('p4dti_changelists',
         "create table p4dti_changelists "
         "  ( changelist int not null, "
         "    rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    user mediumint not null, "
         "    flags int not null, "
         "    description longtext not null, "
         "    client text not null, "
         "    p4date text not null, "
         "    unique (changelist, rid, sid) "
         "  );"),

        ('p4dti_fixes',
         "create table p4dti_fixes "
         "  ( changelist int not null, "
         "    bug_id mediumint not null, "
         "    rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    user mediumint not null, "
         "    client text not null, "
         "    status text not null, "
         "    p4date text not null, "
         "    unique (bug_id, changelist, rid, sid), "
         "    index (bug_id) "
         "  );"),

        ('p4dti_filespecs',
         "create table p4dti_filespecs "
         "  ( bug_id mediumint not null, "
         "    rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    filespec longtext not null, "
         "    index(bug_id)"
         "  );"),

        ('p4dti_config',
         "create table p4dti_config "
         "  ( rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    config_key text not null, "
         "    config_value longtext, "
         "    index(rid, sid)"
         "  );"),

        ('p4dti_replications',
         "create table p4dti_replications "
         "  ( rid varchar(32) not null, "
         "    sid varchar(32) not null, "
         "    start datetime not null, "
         "    end datetime not null, "
         "    completed int not null, "
         "    id  int not null auto_increment, "
         "    unique (id), "
         "    unique (start, rid, sid, id), "
         "    index (rid, sid), "
         "    index (end) "
         "  );"),
        ]

    # schema_upgrade maps each old schema version to a pair of
    # a new schema version and a list of SQL commands transforming the
    # old version to the new. As explained in [NB 2000-11-14a, 5].

    schema_upgrade = {
        '0': ('1', ['alter table p4dti_bugs'
                    '  drop action',
                    'alter table p4dti_replications'
                    '  add id int not null auto_increment,'
                    '  drop index start,'
                    '  add unique (start, rid, sid, id),'
                    '  add unique (id)']),
        '1': ('3', ['alter table p4dti_bugs'
                    '  add migrated datetime,'
                    '  drop replication',
                    'alter table p4dti_changelists'
                    '  drop replication',
                    'alter table p4dti_fixes'
                    '  drop replication',
                    'alter table p4dti_filespecs'
                    '  drop replication']),
        # There was never a schema version 2 (it was used briefly on a
        # branch, but never merged into the master sources).
        '3': ('4', []),
        '4': ('5', ['alter table p4dti_replications'
                    '  add completed int not null default 0',
                    'update p4dti_replications'
                    '  set completed=1 where end >= start']),
        }

    schema_config = {
        'config_key': 'schema_version',
        'config_value': schema_version,
        'rid': '',
        'sid': '',
        }

    # update_p4dti_schema() ensures that the P4DTI schema extensions are
    # present in the Bugzilla database and up to date.

    def update_p4dti_schema(self):
        # Create missing tables.
        up_to_date = 0
        for table, sql in self.p4dti_schema_extensions:
            if not self.table_present(table):
                self.execute(sql)
                if self.cache.has_key('table names'):
                    del self.cache['table names']

                # When we create the p4dti_config table for the first
                # time, set the 'schema_version' configuration parameter
                # so that in future we'll be able to tell whether the
                # schema is up to date.
                if table == 'p4dti_config':
                    up_to_date = 1
                    self.insert_row('p4dti_config', self.schema_config)

        # If we just created the p4dti_config table, then we know there
        # was no previous P4DTI installation (since the p4dti_config
        # table has been there since before release 1.0.0), and so the
        # schema is now up to date.
        if up_to_date:
            return

        row = self.select_at_most_one_row(
            "select config_value from p4dti_config"
            " where config_key='schema_version';",
            "schema_version configuration parameter")
        if row:
            old_schema_version = row[0]
            if old_schema_version == self.schema_version:
                return
        else:
            # The database specifies no schema_version.  We call this
            # "schema version 0"; see [NB 2000-11-14b, 5.2].
            # Unfortunately there are two different varieties of schema
            # version 0.  Make sure that we have the canonical one.
            self.ensure_schema_version_0()
            old_schema_version = 0

        while old_schema_version != self.schema_version:
            if not self.schema_upgrade.has_key(old_schema_version):
                # "Unknown or future P4DTI/Bugzilla schema version %s
                # detected."
                raise error, catalog.msg(120, old_schema_version)

            (new_version, sql_commands) = self.schema_upgrade[old_schema_version]
            # "Old P4DTI/Bugzilla schema version %s detected; altering
            # tables to upgrade to schema version %s."
            self.log(119, (old_schema_version, new_version))
            for sql in sql_commands:
                self.execute(sql)
            old_schema_version = new_version

        # Update schema version in configuration.
        if row:
            self.update_row('p4dti_config', self.schema_config,
                            "config_key = 'schema_version'")
        else:
            self.insert_row('p4dti_config', self.schema_config)

    # drop_p4dti_tables() drops all the P4DTI schema extensions.  Not
    # used by the P4DTI, but useful when testing.

    def drop_p4dti_tables(self):
        for table, _ in self.p4dti_schema_extensions:
            if self.table_present(table):
                self.execute("drop table %s;" % table)

    # Ensure that schema version 0 is canonical.  We need to do this
    # because we had two different schema both with no schema version.
    # See [NB 2000-11-14a, 5.1] for details.

    def ensure_schema_version_0(self):
        # Do we have a schema from before release 1.0.2?
        replications_indexes = self.fetch_rows_as_list_of_dictionaries(
            "show index from p4dti_replications",
            "Getting indexes for the p4dti_replications table.")
        for i in replications_indexes:
            if i['Column_name'] == 'end':
                # We're in release 1.0.2 or later.
                return
        # "Your P4DTI/Bugzilla schema is prior to release 1.0.2.
        # Altering tables to upgrade schema to release 1.0.2."
        self.log(121)
        for alteration in [
            'alter table p4dti_bugs'
            '  add index(bug_id)',
            'alter table p4dti_fixes'
            '  drop index bug_id,'
            '  drop index changelist,'
            '  add unique (bug_id, changelist, rid, sid),'
            '  add index (bug_id)',
            'alter table p4dti_replications'
            '  drop index rid,'
            '  add unique (start, rid, sid),'
            '  add index (rid, sid),'
            '  add index (end)'
            ]:
            self.execute(alteration)


    # 9. BUGZILLA DATABASE OPERATIONS
    #
    # This section provides abstractions for operations on the Bugzilla
    # schema [NB 2000-11-14a] and the P4DTI schema extensions [NB
    # 2000-11-14b].
    #
    # Many of the update methods take a dict argument mapping column
    # name to value.  This means we can restrict our update to a part of
    # a record by passing a dictionary with only a few fields.


    # 9.1. Table "bugs"

    def bug_from_bug_id(self, bug_id):
        if not self.cache.has_key(('bugs', bug_id)):
            bug = self.fetch_one_row_as_dictionary(
                "select * from bugs where bug_id = %d;" % bug_id,
                "bug id %d" % bug_id)
            if self.features.has_key('normalized tables'):
                bug['product'] = self.product_name_from_id(bug['product_id'])
                bug['component'] = self.component_name_from_id(bug['component_id'])
                del bug['product_id']
                del bug['component_id']
            bug['groups'] = self.bug_groups(bug)
            bug['longdesc'] = self.bug_get_longdesc(bug)
            self.cache[('bugs', bug_id)] = bug
        return self.cache[('bugs', bug_id)]

    def all_bugs_since(self, date):
        # Find all bugs replicated by this replicator, and all
        # unreplicated bugs new, touched, or changed since the given
        # date.

        bug_ids = self.fetch_rows_as_list_of_sequences(
            ("select bugs.bug_id from bugs "
             "  left join p4dti_bugs using (bug_id) " # what replication
             "  where (bugs.delta_ts >= %s "          # (recently changed
             "         or bugs.creation_ts >= %s "    #  or recently created
             "         and p4dti_bugs.rid is null) "  #  and not replicated)
             "     or (p4dti_bugs.rid = %s "          # or replicated by me.
             "         and p4dti_bugs.sid = %s)" %
             (self.quote_string(date),
              self.quote_string(date),
              self.quote_string(self.rid),
              self.quote_string(self.sid))),
            "all bugs since '%s'" % date)
        return map(self.bug_from_bug_id, map(lambda b: b[0], bug_ids))

    def changed_bugs_since(self, date):
        # Find bugs new, touched, or changed (by someone other than
        # this replicator) since the given date, which are not
        # being replicated by any other replicator.

        # We exclude changes which have the same timestamp as the
        # current replication; they will get picked up by the next
        # replication. This avoids these changes being replicated by
        # two consecutive replications (which causes an overwrite).
        # See job000235.  NB 2001-03-01.  However, it causes
        # job000337.

        # We do this by combining the results of three SELECTs.
        # These results are disjoint.  We could almost certainly
        # do it in a smaller number of SELECTs.

        # First, bugs which have been created since the date (but not
        # by migration by me from a new Perforce job), which are not
        # being replicated by any other replicator.

        new_ids = self.fetch_rows_as_list_of_sequences(
            ("select bugs.bug_id from bugs "
             "  left join p4dti_bugs using (bug_id) " # what replication
             "  where bugs.creation_ts >= %s "        # recent timestamp
             "    and bugs.creation_ts < %s "         # NOT just now
             "    and (p4dti_bugs.rid is null "       # NOT replicated
             "         or (p4dti_bugs.rid = %s "      # or replicated by me.
             "             and p4dti_bugs.sid = %s "
             "             and p4dti_bugs.migrated is null))" %
                                                      # but not migrated by me.
             (self.quote_string(date),
              self.quote_string(self.replication),
              self.quote_string(self.rid),
              self.quote_string(self.sid))),
            "new bugs since '%s'" % date)

        # Next, bugs which are not new but have been touched since the
        # date, but not changed, (no matching rows in bugs_activity),
        # which are not being replicated by any other replicator.
        #
        # Note that we have to specifically exclude bugs which we have
        # just migrated, as the migration might set creation_ts.

        touched_ids = self.fetch_rows_as_list_of_sequences(
            ("select bugs.bug_id from bugs "
             "  left join p4dti_bugs using (bug_id) " # what replication
             "  left join bugs_activity "             # what activity
             "    on (bugs_activity.bug_when >= %s and " # since 'date'
             "        bugs_activity.bug_when < %s and " # and NOT just now
             "        bugs.bug_id = bugs_activity.bug_id) " # on this bug
             "  where bugs.delta_ts >= %s "           # since 'date'
             "    and bugs.delta_ts < %s "            # NOT just now
             "    and creation_ts < %s "              # NOT brand new
             "    and bugs_activity.fieldid is null"  # NO recent activity
             "    and (p4dti_bugs.rid is null "       # NOT replicated
             "         or (p4dti_bugs.rid = %s "      # or replicated by me.
             "             and p4dti_bugs.sid = %s)) "
             "    and (p4dti_bugs.migrated is null "  # NOT migrated lately
             "         or p4dti_bugs.migrated < %s) " %
             (self.quote_string(date),
              self.quote_string(self.replication),
              self.quote_string(date),
              self.quote_string(self.replication),
              self.quote_string(date),
              self.quote_string(self.rid),
              self.quote_string(self.sid),
              self.quote_string(date))),
            "bugs touched since '%s'" % date)

        # Next, bugs which have been changed since the date, by
        # someone other than me, which are not being replicated by
        # any other replicator.

        changed_ids = self.fetch_rows_as_list_of_sequences(
            ("select bugs.bug_id from bugs, bugs_activity ba "  # bug activity
             "left join p4dti_bugs using (bug_id) "        # what replication
             "left join p4dti_bugs_activity pba "   # what replication activity
             "  on (ba.bug_id = pba.bug_id and "    # by me
             "      ba.bug_when = pba.bug_when and "
             "      ba.who = pba.who and "
             "      ba.fieldid = pba.fieldid and "
             "      ba.removed = pba.oldvalue and "
             "      ba.added = pba.newvalue and "
             "      pba.rid = %s and "
             "      pba.sid = %s) "
             "  where ba.bug_when >= %s "        # recent bug activity
             "    and ba.bug_when < %s "         # but not too recent
             "    and bugs.bug_id = ba.bug_id "  # on this bug
             "    and pba.rid is null "          # NO recent activity by me
             "    and (p4dti_bugs.rid is null "  # NOT replicated
             "         or (p4dti_bugs.rid = %s " # or replicated by me
             "             and p4dti_bugs.sid =  %s))"
             "    and (bugs.creation_ts < %s or " # NOT new, or newly
             "         p4dti_bugs.migrated is not null) " # migrated
             "  group by bugs.bug_id " %         # each bug only once
             (self.quote_string(self.rid),
              self.quote_string(self.sid),
              self.quote_string(date),
              self.quote_string(self.replication),
              self.quote_string(self.rid),
              self.quote_string(self.sid),
              self.quote_string(date))),
            "changed bugs since '%s'" % date)

        bug_ids = new_ids + touched_ids + changed_ids
        return map(self.bug_from_bug_id, map(lambda b: b[0], bug_ids))

    def add_bug(self, bug):
        longdesc = bug['longdesc']
        del bug['longdesc']
        if not bug.has_key('creation_ts'):
            bug['creation_ts'] = '' # gets now()
        if self.features.has_key('normalized tables'):
            if bug.has_key('product'):
                bug['product_id'] = self.product_id_from_name(bug['product'])
                del bug['product']
            if bug.has_key('component'):
                bug['component_id'] = self.component_id_from_name(bug['component'])
                del bug['component']
        if self.features.has_key('bitset groups'):
            bug['groupset'] = self.groups_groupset(bug['groups'])
        else:
            groups = bug['groups']
        del bug['groups']
        for key in ['status_whiteboard','keywords']:
            if not bug.has_key(key):
                bug[key] = ''
        self.insert_row('bugs', bug)
        bug_id = int(self.select_one_row('select last_insert_id();',
                                         'id of bug just created')[0])
        bug['bug_id'] = bug_id
        self.add_longdesc(bug_id, bug['reporter'], longdesc)
        if not self.features.has_key('bitset groups'):
            self.add_bug_groups(bug_id, groups)
        self.bugmail(bug_id, bug['reporter'])
        return bug_id

    def update_bug(self, dict, bug, user):
        if dict:
            bug_id = bug['bug_id']
            if self.cache.has_key(('bugs', bug_id)):
                del self.cache[('bugs', bug_id)]
            changes = dict.copy()
            if changes.has_key('longdesc'):
                self.update_longdesc(bug_id, user,
                                     bug['longdesc'], changes['longdesc'])
                # don't put longdesc into bugs or bugs_activity tables
                del changes['longdesc']
            # This shouldn't happen, because we don't let
            # the replicator change these fields anyway.
            if self.features.has_key('normalized tables'):
                if changes.has_key('product'):
                    changes['product_id'] = self.product_id_from_name(changes['product'])
                    del changes['product']
                if changes.has_key('component'):
                    changes['component_id'] = self.component_id_from_name(changes['component'])
                    del bug['component']
            # if we wanted to update delta_ts, this is where
            # we would do it.  job000484.
            # changes['delta_ts'] = changes.get('delta_ts', '')
            if changes:
                self.update_row('bugs', changes, 'bug_id = %d' % bug_id)
                self.update_bugs_activity(user, bug_id, bug, changes)
            

    def delete_bug(self, bug_id):
        # all the tables which have per-bug information, and the
        # column name of the bug number in that table.
        column_names = {
            'attachments': 'bug_id',
            'bug_group_map': 'bug_id',
            'bugs': 'bug_id',
            'bugs_activity': 'bug_id',
            'cc': 'bug_id',
            'dependencies': 'blocked',
            'dependencies': 'dependson',
            'duplicates': 'dupe',
            'duplicates': 'dupeof',
            'flags': 'bug_id',
            'keywords': 'bug_id',
            'longdescs': 'bug_id',
            'votes': 'bug_id',
            'p4dti_bugs': 'bug_id',
            'p4dti_bugs_activity': 'bug_id',
            'p4dti_fixes': 'bug_id',
            'p4dti_filespecs': 'bug_id',
            }
        tables = self.table_names()
        for (table, column) in column_names.items():
            if table in tables:
                self.delete_rows(table, '%s = %d' % (column, bug_id))
        if self.cache.has_key(('bugs', bug_id)):
            del self.cache[('bugs', bug_id)]


    # 9.2. Table "bugs_activity"

    # Some fields don't get recorded in bugs_activity

    fields_not_in_bugs_activity = ['longdesc',
                                   'delta_ts']

    # After making a change to a bugs record, we have to record the
    # change in the bugs_activity and p4dti_bugs_activity tables.

    def update_bugs_activity(self, user, bug_id, bug, changes):
        activity = {}
        activity['bug_id'] = bug_id
        activity['who'] = user
        activity['bug_when'] = self.now()
        p4dti_activity = activity.copy()
        for key, newvalue in changes.items():
            if key not in self.fields_not_in_bugs_activity:
                if self.user_fields.has_key(('bugs', key)):
                    u = self.users()
                    oldvalue = u.get(bug[key],{}).get('login_name','')
                    newvalue = u.get(newvalue,{}).get('login_name','')
                else:
                    oldvalue = str(bug[key])
                    newvalue = str(newvalue)
                fieldid = self.fieldid(key)
                if fieldid is not None:
                    activity['fieldid'] = fieldid
                    p4dti_activity['fieldid'] = fieldid
                    activity['removed'] = oldvalue
                    activity['added'] = newvalue
                    p4dti_activity['oldvalue'] = oldvalue
                    p4dti_activity['newvalue'] = newvalue
                    self.insert_row('bugs_activity', activity)
                    self.insert_row_rid_sid('p4dti_bugs_activity',
                                            p4dti_activity)


    # 9.3. Table "cc"

    # We don't interact with this table any more.

    # 9.4. Table "components"

    def components_of_product(self, product):
        if not self.cache.has_key(('components', product)):
            if self.features.has_key('normalized tables'):
                rows = self.fetch_rows_as_list_of_dictionaries (
                    "select components.* from components, products"
                    " where components.product_id = products.id"
                    " and products.name = %s"
                    % self.quote_string(product),
                    "components of product '%s'" % product)
                name_column = 'name'
            else:
                rows = self.fetch_rows_as_list_of_dictionaries (
                    "select * from components where program=%s"
                    % self.quote_string(product),
                    "components of product '%s'" % product)
                name_column = 'value'
            components={}
            for row in rows:
                components[row[name_column]] = row
            self.cache[('components', product)] = components
        return self.cache[('components', product)]

    def components(self):
        if not self.cache.has_key('components'):
            cs = self.fetch_rows_as_list_of_dictionaries(
                "select * from components",
                "all components")
            components = {}
            for c in cs:
                components[c['id']] = c
            self.cache['components'] = components
        return self.cache['components']

    def component_name_from_id(self, component_id):
        return self.components()[component_id]['name']

    def component_id_from_name(self, component_name):
        for c in self.components().values():
            if c['name'] == component_name:
                return c['id']

    # 9.5. Table "dependencies"

    # We don't interact with this table any more.

    # 9.6. Table "fielddefs"

    def fielddefs(self):
        if not self.cache.has_key('fielddefs'):
            fielddefs = self.fetch_rows_as_list_of_dictionaries(
                'select * from fielddefs', 'all fielddefs')
            by_name = {}
            for fielddef in fielddefs:
                # Bugzilla 2.23.3 changes fielddefs.fieldid to fielddefs.id
                if not(fielddef.has_key('fieldid')):
                    fielddef['fieldid'] = fielddef['id']
                    del fielddef['id']
                by_name[fielddef['name']] = fielddef
            self.cache['fielddefs'] = by_name
        return self.cache['fielddefs']

    # return the fieldid of the field with this name,
    # or None if this field does not have a fieldid.

    def fieldid(self, name):
        by_name = self.fielddefs()
        if not by_name.has_key(name):
            return None
        return by_name[name]['fieldid']

    def field_description(self, name):
        by_name = self.fielddefs()
        if not by_name.has_key(name):
            return None
        return by_name[name]['description']

    def custom_fields(self):
        if not self.cache.has_key('custom_fields'):
            cf = {}
            by_name = self.fielddefs()
            for fielddef in by_name.values():
                if fielddef.get('custom', 0):
                    cf[fielddef['name']] = fielddef
            self.cache['custom_fields'] = cf
        return self.cache['custom_fields']

    # 9.7. Table "groups"

    def group_control_map_product(self, product):
        if not self.cache.has_key(('group_control_map', product)):
            group_rows = self.fetch_rows_as_list_of_dictionaries(
                "select group_control_map.entry,"
                "       group_control_map.canedit,"
                "       group_control_map.membercontrol,"
                "       group_control_map.othercontrol,"
                "       groups.name " 
                " from groups, group_control_map, products"
                " where group_control_map.group_id = groups.id"
                " and group_control_map.product_id = products.id"
                " and products.name = %s" % self.quote_string(product),
                "group controls for product %s" % product)
            groups = {}
            for g in group_rows:
                groups[g['name']] = g
            self.cache[('group_control_map', product)] = groups
        return self.cache[('group_control_map', product)]

    # A list of the groups required to create a bug in this
    # product.

    def product_creator_groups(self, product):
        if not self.cache.has_key(('product_creator_groups', product)):
            if self.features.has_key('group_control_map'):
                groups = []
                for (name, g) in self.group_control_map_product(product).items():
                    if g['entry']:
                        groups.append(name)
            else:
                group_row = self.select_at_most_one_row(
                    "select groups.name from groups "
                    "  where name = %s and "
                    "        isbuggroup = 1" % self.quote_string(product),
                    "group for product %s" % product)
                if group_row:
                    groups = [group_row[0]]
                else:
                    groups = []
            self.cache[('product_creator_groups', product)] = groups
        return self.cache[('product_creator_groups', product)]

    # A list of the groups required to edit a bug in this product.

    def product_editor_groups(self, product):
        if not self.cache.has_key(('product_editor_groups', product)):
            if self.features.has_key('group_control_map'):
                groups = []
                for (name, g) in self.group_control_map_product(product).items():
                    if g['canedit']:
                        groups.append(name)
            else:
                groups = []
            self.cache[('product_editor_groups', product)] = groups
        return self.cache[('product_editor_groups', product)]

    # A list of the groups into which a new bug in a product is
    # automatically assigned.

    def new_bug_groups(self, product, user_groups):
        if self.features.has_key('group_control_map'):
            groups = []
            for (name, g) in self.group_control_map_product(product).items():
                if name in user_groups:
                    control = g['membercontrol']
                else:
                    control = g['othercontrol']
                if control == 3: # control value is 'MANDATORY'
                    groups.append(name)
            return groups
        else:
            return []

    # All the groups.
    def groups(self):
        if not self.cache.has_key('groups'):
            groups = {}
            gs = self.fetch_rows_as_list_of_dictionaries(
                'select * from groups', 'all groups')
            for g in gs:
                groups[g['name']] = g
            self.cache['groups'] = groups
        return self.cache['groups']

    # The group names corresponding to this groupset.
    def groupset_groups(self, groupset):
        groups = []
        if groupset:
            gs = self.groups()
            for (name, group) in gs.items():
                if group['bit'] & groupset:
                    groups.append(name)
        return groups

    # The group names corresponding to this groupset.
    def groups_groupset(self, groups):
        groupset = 0L
        if groups:
            gs = self.groups()
            for (name, group) in gs.items():
                if name in groups:
                    groupset += group['bit']
        return groupset

    # The names of groups which this bug is in.
    def bug_groups(self, bug):
        bug_id = bug['bug_id']
        if not self.cache.has_key(('bug_groups', bug_id)):
            if self.features.has_key('bitset groups'):
                groups = self.groupset_groups(bug['groupset'])
            else:
                groups = self.fetch_rows_as_list_of_sequences(
                    "select groups.name from groups, bug_group_map"
                    " where groups.id = bug_group_map.group_id"
                    " and bug_group_map.bug_id = %d" % bug_id,
                    "groups for bug %d" % bug_id)
                groups = map(lambda g: g[0], groups)
            self.cache[('bug_groups', bug_id)] = groups
        return self.cache[('bug_groups', bug_id)]

    # The names of groups which this user is in.
    def user_groups(self, user_id):
        if not self.cache.has_key(('user_groups', user_id)):
            if self.features.has_key('bitset groups'):
                groupset = self.select_one_row("select groupset from profiles where"
                                               " userid = %d;" % user_id,
                                               "groupset for user %d" % user_id)[0]
                groups = self.groupset_groups(groupset)
            else:
                groups = self.fetch_rows_as_list_of_sequences(
                    "select groups.name from groups, user_group_map"
                    " where groups.id = user_group_map.group_id"
                    " and user_group_map.user_id = %d"
                    " group by groups.name" % user_id,
                    "groups for user %d" % user_id)
                groups = map(lambda g: g[0], groups)
            self.cache[('user_groups', user_id)] = groups
        return self.cache[('user_groups', user_id)]

    # Put the user in the named groups.
    def add_user_groups(self, userid, groups):
        if self.cache.has_key(('user_groups', userid)):
            del self.cache[('user_groups', userid)]
        if groups:
            gs = self.groups()
            row = {'user_id': userid,
                   'isbless': 0,
                   'isderived': 0,
                   }
            for (name, group) in gs.items():
                if name in groups:
                    row['group_id'] = group['id']
                    self.insert_row('user_group_map', row)

    # Put the bug in the named groups.
    def add_bug_groups(self, bug_id, groups):
        if self.cache.has_key(('bug_groups', bug_id)):
            del self.cache[('bug_groups', bug_id)]
        if groups:
            gs = self.groups()
            row = {'bug_id': bug_id,
                   }
            for (name, group) in gs.items():
                if name in groups:
                    row['group_id'] = group['id']
                    self.insert_row('bug_group_map', row)

    # 9.8. Table "longdescs"

    # Regular expression to match a non-empty blank line, i.e. a line
    # containing space and/or tab characters but nothing else.
    # See job000375.
    blank_line_re = re.compile('^[ \t]+$', re.M)

    def bug_get_longdesc(self, bug):
        bug_id = bug['bug_id']
        longdescs = self.fetch_rows_as_list_of_dictionaries(
            "select profiles.login_name, profiles.realname, "
            "       longdescs.bug_when, longdescs.thetext "
            "  from longdescs, profiles "
            " where profiles.userid = longdescs.who "
            "   and longdescs.bug_id = %d"
            " order by longdescs.bug_when" % bug_id,
            "long descriptions for bug %d" % bug_id)
        longdesc = ""
        first = 1
        for record in longdescs:
            thetext = record['thetext']
            # replace blank lines with empty lines.  job000375.
            thetext = self.blank_line_re.sub('', thetext)
            if first:
                longdesc = thetext
                first = 0
            else:
                longdesc = (longdesc +
                            ("\n\n------- %s <%s> at %s -------\n" %
                             (record['realname'],
                              record['login_name'],
                              record['bug_when']))
                            + thetext)
        longdesc = (longdesc + "\n\n"
                    "------- Append additional comments below -------")
        return longdesc

    def add_longdesc(self, bug_id, user, comment):
        longdesc = {}
        longdesc['bug_id'] = bug_id
        longdesc['who'] = user
        # Empty "bug_when" defaults to now(); see section 4.
        longdesc['bug_when'] = ''
        longdesc['thetext'] = string.strip(comment)
        self.insert_row('longdescs', longdesc)

    def update_longdesc(self, bug_id, user, old, new):
        new_comment = string.strip(new[len(old):])
        self.add_longdesc(bug_id, user, new_comment)


    # 9.9. Table "products"

    def products(self):
        if not self.cache.has_key('products'):
            rows = self.fetch_rows_as_list_of_dictionaries(
                "select * from products;",
                "list of products")
            products={}
            if self.features.has_key('normalized tables'):
                name_column = 'name'
            else:
                name_column = 'product'
            for row in rows:
                products[row[name_column]] = row
            self.cache['products'] = products
        return self.cache['products']

    def product_name_from_id(self, product_id):
        for (name, p) in self.products().items():
            if p['id'] == product_id:
                return name

    def product_id_from_name(self, product_name):
        products = self.products()
        return products[product_name]['id']

    # 9.10. Table "profiles"

    def users(self):
        if not self.cache.has_key('users'):
            us = self.fetch_rows_as_list_of_dictionaries (
                "select * from profiles;",
                "all user records")
            users = {}
            for u in us:
                users[u['userid']] = u
            self.cache['users'] = users
        return self.cache['users']

    def add_user(self, dict):
        # The quote_table will make sure that the password is encrypted
        # before being written to the database.
        dict['cryptpassword'] = dict['password']
        del dict['password']
        if self.features.has_key('bitset groups'):
            dict['groupset'] = self.groups_groupset(dict['groups'])
        else:
            groups = dict['groups']
        del dict['groups']
        self.insert_row('profiles', dict)
        u = self.fetch_one_row_as_dictionary('select * from profiles'
                                             ' where userid = last_insert_id();',
                                             'user just created')
        userid = u['userid']
        if self.cache.has_key('users'):
            self.cache['users'][userid] = u
        if not self.features.has_key('bitset groups'):
            self.add_user_groups(userid, groups)
        return userid

    def user_id_and_email_list(self):
        users = []
        us = self.users()
        for (id, user) in self.users().items():
            users.append((id, user['login_name']))
        if self.params.get('emailsuffix'):
            def add_suffix(u, suffix=self.params['emailsuffix']):
                return u[0], u[1] + suffix
            users = map(add_suffix, users)
        return users

    def user_is_disabled(self, user):
        return self.users()[user]['disabledtext'] != ''

    def email_from_userid(self, user):
        return self.users()[user]['login_name']

    def userid_from_email(self, email):
        for (id, user) in self.users().items():
            if user['login_name'] == email:
                return id
        return None

    def real_name_from_userid(self, user):
        return self.users()[user]['realname']

    # 9.11. Table "versions"

    def versions_of_product(self, product):
        if not self.cache.has_key(('versions', product)):
            if self.features.has_key('normalized tables'):
                rows = self.fetch_rows_as_list_of_sequences (
                    "select value from versions, products"
                    " where versions.product_id = products.id"
                    " and products.name = %s"
                    % self.quote_string(product),
                    "versions of product '%s'" % product)
            else:
                rows = self.fetch_rows_as_list_of_sequences (
                    "select value from versions where program=%s"
                    % self.quote_string(product),
                    "versions of product '%s'" % product)
            self.cache[('versions', product)] = map(lambda x:x[0], rows)
        return self.cache[('versions', product)]


    # 10. P4DTI DATABASE OPERATIONS
    #
    # This section provides abstractions for operations on the P4DTI
    # schema extensions [NB 2000-11-14b].


    # 10.1. Table "p4dti_bugs"

    def bug_p4dti_bug(self, bug):
        bug_id = bug['bug_id']
        p4dti_bug = self.fetch_at_most_one_row_as_dictionary(
            ("select * from p4dti_bugs "
             "  where bug_id = %d" % bug_id),
            'p4dti_bug %d' % bug_id)
        return p4dti_bug

    def add_p4dti_bug(self, dict, created):
        if created:
            # Empty "migrated" defaults to now(); see section 4.
            dict['migrated'] = ''
        self.insert_row_rid_sid('p4dti_bugs', dict)

    def update_p4dti_bug(self, dict, bug_id):
        if dict:
            self.update_row_rid_sid('p4dti_bugs', dict,
                                    'bug_id = %d' % bug_id)

    # 10.2. Table "p4dti_bugs_activity"
    #
    # The p4dti_bugs_activity table is updated by the P4DTI whenever the
    # bugs_activity is updated.  See section 9.2.


    # 10.3. Table "p4dti_bugzilla_parameters"

    # Bugzilla's configuration parameters are wanted over here, for
    # example so that we can fix job000352.

    def fetch_bugzilla_config(self):
        # Check that the p4dti_bugzilla_parameters table exists.  Its
        # presense depends on a new configuration step; its absense is
        # not an error as most users do not need the information
        # stored in it.
        if not self.table_present("p4dti_bugzilla_parameters"):
            # "The Bugzilla configuration parameters are missing from
            # the Bugzilla database.  This means that the P4DTI won't
            # support Bugzilla features like 'emailsuffix'.  If you need
            # these features, edit your Bugzilla configuration
            # parameters and restart the P4DTI.  See section 5.3.3 of
            # the P4DTI Administrator's Guide."
            self.log(129)
            self.params = {}
        else:
            self.params = self.fetch_simple_rows_as_dictionary(
                "select parameter_name, parameter_value "
                "from p4dti_bugzilla_parameters;",
                "bugzilla parameters")
            if self.params['p4dti'] == '0':
                # "Bugzilla configuration parameter 'p4dti' is turned
                # off.  You won't see Perforce fixes in Bugzilla until
                # you turn it on.  See section 5.3.3 of the P4DTI
                # Administrator's Guide."
                self.log(130)
            if self.params.get('utf8','0') == '0':
                # "Bugzilla is not configured to store text in UTF-8
                # encoding.  Replication of non-ASCII text data from
                # Bugzilla may be incorrect."
                self.log(133)


    # 10.4. Table "p4dti_changelists"

    def changelists(self, number):
        return self.fetch_rows_as_list_of_dictionaries(
            "select * from p4dti_changelists "
            "  where changelist = %d and "
            "        rid = %s and "
            "        sid = %s;" % (number,
                                   self.quote_string(self.rid),
                                   self.quote_string(self.sid)),
            "changelist %d" % number)

    def add_changelist(self, dict):
        self.insert_row_rid_sid('p4dti_changelists', dict)

    def update_changelist(self, dict, number):
        if dict:
            self.update_row_rid_sid('p4dti_changelists', dict,
                                    'changelist = %d' % number)


    # 10.5. Table "p4dti_config"

    # Configuration parameters which we pass through the database
    # to Bugzilla.

    def get_config(self):
	return self.fetch_simple_rows_as_dictionary(
                   "select config_key, config_value from p4dti_config "
                   "where rid = %s and sid = %s;"
                   % (self.quote_string(self.rid),
                      self.quote_string(self.sid)),
                   'p4dti configuration')

    def add_config(self, key, value):
        self.insert_row_rid_sid('p4dti_config',
                                {'config_key'  : key,
                                 'config_value': value})

    def update_config(self, key, value):
        self.update_row_rid_sid('p4dti_config',
                                {'config_value': value},
                                ('config_key = %s'
                                 % self.quote_string(key)))

    def delete_config(self, key):
        self.delete_rows_rid_sid('p4dti_config',
                                 ('config_key = %s'
                                  % self.quote_string(key)))

    def set_config(self, dict):
        old_config = self.get_config()
        for key, value in dict.items():
            if old_config.has_key(key):
                if old_config[key] != value:
                    self.update_config(key, value)
                del old_config[key]
            else:
                self.add_config(key, value)
        for key in old_config.keys():
            self.delete_config(key)


    # 10.6. Table "p4dti_filespecs"

    def filespecs_from_bug_id(self, bug_id):
        return self.fetch_rows_as_list_of_dictionaries (
            ("select * from p4dti_filespecs "
             "  where rid = %s and "
             "        sid = %s and "
             "        bug_id = %d" % (self.quote_string(self.rid),
                                      self.quote_string(self.sid),
                                      bug_id)),
            "fixes for bug %d" % bug_id)

    def add_filespec(self, filespec):
        self.insert_row_rid_sid('p4dti_filespecs', filespec)

    def delete_filespec(self, filespec):
        self.delete_rows_rid_sid(
            'p4dti_filespecs',
            ('bug_id = %d and filespec = %s'
             % (filespec['bug_id'],
                self.quote_string(filespec['filespec']))))

    # 10.7. Table "p4dti_fixes"

    def fixes_from_bug_id(self, bug_id):
        return self.fetch_rows_as_list_of_dictionaries (
            ("select * from p4dti_fixes "
             "  where rid = %s and "
             "        sid = %s and "
             "        bug_id = %d" % (self.quote_string(self.rid),
                                      self.quote_string(self.sid),
                                      bug_id)),
            "fixes for bug %d" % bug_id)

    def add_fix(self, fix):
        self.insert_row_rid_sid('p4dti_fixes', fix)

    def update_fix(self, dict, bug_id, changelist):
        if dict:
            self.update_row_rid_sid('p4dti_fixes', dict,
                                    ('bug_id = %d and changelist = %d'
                                     % (bug_id, changelist)))

    def delete_fix(self, fix):
        self.delete_rows_rid_sid('p4dti_fixes',
                                 ('bug_id = %d and changelist = %d '
                                  % (fix['bug_id'], fix['changelist'])))

    # 10.8. Table "p4dti_replications"

    def now(self):
        return self.select_one_row('select now();', 'now')[0]

    # If there are no replications, in the replications table, insert a
    # record whose 'end' is the date given by start_date.  That is,
    # pretend that we last did a replication on start_date.  This
    # ensures that (a) when you run the replicator for the first time,
    # all issues changed since the start date get replicated (see
    # job000355), and (b) the replications table is never empty and we
    # always have a valid self.replication (see job000221).

    def first_replication(self, start_date):
        date = self.latest_complete_replication_no_checking()
        if date == None:
            self.insert_row_rid_sid('p4dti_replications',
                                    { 'start': start_date,
                                      'end': start_date,
                                      'completed': 1 })
            self.replication = start_date
        else:
            self.replication = date

    def new_replication(self):
        self.replication = self.now()
        self.insert_row_rid_sid('p4dti_replications',
                                { 'start': self.replication,
                                  'end': '1980-01-01 00:00:00',
                                  'completed': 0 } )
        return self.replication

    def end_replication(self):
        assert self.replication != None
        self.update_row_rid_sid('p4dti_replications', {'end': '',
                                                       'completed': 1},
                                'start = %s and completed = 0'
                                % self.quote_string(self.replication))

        # clean out old complete replication records from the
        # p4dti_replications table (job000236).
        self.delete_rows_rid_sid('p4dti_replications',
                                 'completed=1 and '
                                 'end < date_sub(now(), '
                                 'INTERVAL 1 HOUR)')

    def latest_complete_replication_no_checking(self):
        return self.select_one_row(
            "select max(start) from p4dti_replications where "
            " rid = %s and "
            " sid=  %s and "
            " completed = 1;"
            % (self.quote_string(self.rid),
               self.quote_string(self.sid)),
            "select latest complete replication")[0]

    # Start time of last complete replication.
    def latest_complete_replication(self):
        start = self.latest_complete_replication_no_checking()
        if start == None:
            # "Nothing in p4dti_replications table: database corrupted?"
            raise error, catalog.msg(122)
        return start


    # 11. BUG MAIL

    def bugmail_invocation(self, script_name):
            if os.name == 'posix':
                return('perl -T ./%s' % script_name,
                       '> /dev/null')
            elif os.name == 'nt':
                return ('perl -T %s' % script_name,
                        '> nul')

    def bugmail(self, bug_id, user):
        if self.bugzilla_directory == None:
            return
        (prefix, suffix) = self.bugmail_invocation(self.bugmail_command)
        self.bugmail_commands.append(string.join([prefix,
                                                  str(bug_id),
                                                  self.email_from_userid(user),
                                                  suffix,
                                                  ],
                                                 ' '))

    def clear_bugmail_commands(self):
        self.bugmail_commands = []

    def invoke_bugmail_commands(self):
        if self.bugmail_commands:
            # "Running %d deferred commands..."
            self.log(128, len(self.bugmail_commands))
            cwd = os.getcwd()
            try:
                os.chdir(self.bugzilla_directory)
                for command in self.bugmail_commands:
                    # "Running command '%s'."
                    self.log(104, command)
                    os.system(command)
            finally:
                os.chdir(cwd)


    # 12. LOCKING

    tables_to_lock = [
        ('attachments', 'write', []),
        ('bug_group_map', 'write', []),
        ('bugs', 'write', []),
        ('bugs_activity', 'write', [('ba', 'read'),]),
        ('cc', 'write', []),
        ('dependencies', 'write', []),
        ('duplicates', 'write', []),
        ('flags', 'write', []),
        ('keywords', 'write', []),
        ('longdescs', 'write', []),
        ('votes', 'write', []),

        ('p4dti_bugs', 'write', []),
        ('p4dti_bugs_activity', 'write', [('pba', 'read'),]),
        ('p4dti_changelists', 'write', []),
        ('p4dti_filespecs', 'write', []),
        ('p4dti_fixes', 'write', []),
        ('p4dti_replications', 'write', []),

        ('components', 'read', []),
        ('fielddefs', 'read', []),
        ('group_control_map', 'read', []),
        ('groups', 'read', []),
        ('products', 'read', []),
        ('profiles', 'read', []),
        ('user_group_map', 'read', []),
        ('versions', 'read', []),
        ]

    def lock_tables(self):
        tables = self.table_names()
        locks = []
        for (table, mode, aliases) in self.tables_to_lock:
            if table in tables:
                locks.append('%s %s' % (table, mode))
                for (alias, mode) in aliases:
                    locks.append('%s as %s %s' % (table, alias, mode))
        self.execute("lock tables %s;" % string.join(locks, ", "))

    def unlock_tables(self):
        self.execute("unlock tables;")

    def clear_caches(self):
        self.clear_bugmail_commands()
        self.cache = {}

    def invoke_deferred_commands(self):
        self.invoke_bugmail_commands()


# A. REFERENCES
#
# [DBAPI 2.0] "Python Database API Specification 2.0";
# <http://www.python.org/topics/database/DatabaseAPI-2.0.html>.
#
# [NB 2000-11-14a] "Bugzilla database schema"; Nick Barnes; Ravenbrook
# Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/tool/cgi/bugzilla-schema/>.
#
# [NB 2000-11-14b] "Bugzilla database schema extensions for integration
# with Perforce"; Nick Barnes; Ravenbrook Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/bugzilla-p4dti-schema/>.
#
# [NB 2000-11-14c] "Python interface to Bugzilla: design"; Nick Barnes;
# Ravenbrook Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/python-bugzilla-interface/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-05 NB Fixes for job job000089 and job000118.  We update
# bugs_activity and have a new table p4dti_bugs_activity which
# duplicates bugs_activity rows added by this replicator.  A complicated
# select then identifies bugs which have been changed other than by the
# replicator.  Locking added.  Fixes, filespecs, and changelists now
# work.
#
# 2000-12-07 RB Abolished "config" in favour of explicit parameters so
# that this is callable from the configurator (which doesn't have a
# config when it needs to call).
#
# 2000-12-08 NB Add p4dti_config table and code to manipulate it.  This
# gets configuration from the replicator to Bugzilla.
#
# 2000-12-13 NB Stop replicating historical bugs, and add code to find
# bugs which have been 'touched'.  Put output through the logger.  Add
# indices to the tables.
#
# 2000-12-15 NB Added verbosity control.
#
# 2001-01-11 NB Added MySQL type parsing code so that we can do
# replicated_fields.  Also take code to make the MySQL connection out to
# configure_bugzilla.py so we only make one connection when starting up.
#
# 2001-01-12 NB Added longdesc support.
#
# 2001-01-15 NB Defaults for date types don't work.
#
# 2001-01-22 NB Fix job000184, if database isn't called 'bugs'.
#
# 2001-01-26 NB Added processmail support and tidied up our response to
# a zero-row select.
#
# 2001-02-08 NB Added some checking.
#
# 2001-02-20 GDR Removed unused 'dict' argument from
# delete_rows_rid_sid, to fix job000222.
#
# 2001-02-23 NB Made error messages more regular (job000227).
#
# 2001-03-01 NB Fixes for job000235, job000236, job000238.
#
# 2001-03-02 NB Fix for job000241 (convert_type for other MySQL
# versions).
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-12 GDR Use new message classes when logging debug messages.
# Fixed bug in error reporting for
# fetch_at_most_one_row_as_dictionary().
#
# 2001-03-13 GDR Removed verbose parameter (made redundant by
# log_level).  Removed action field from table p4dti_bugs (since
# conflict resolution is now always immediate).
#
# 2001-03-15 GDR Get configuration from module.
#
# 2001-03-29 NB Fix for job000283 (non-uniqueness in p4dti_replications
# index).
#
# 2001-04-10 NB Fix for job000291 (new message; add to catalog).
#
# 2001-04-23 NB Initial code to add bugs to Bugzilla.
#
# 2001-05-09 NB Now able to add bugs to Bugzilla.  Also fixed job000262.
#
# 2001-06-26 NB Add functions for deleting a bug (needed when creating a
# new bug from a new Perforce job fails half-way).  Also added a
# 'migrate' field to the p4dti_bugs table, so we can tell whether and
# when a bug was migrated from Perforce.
#
# 2001-06-27 NB split all_bugs_since into all_bugs_since and
# changed_bugs_since, to correctly pick up or ignore migrated bugs
# accordingly.  This also fixes an obscure bug which could sometimes
# miss bugs, and thinking about it revealed job000339.
#
# 2001-06-27 NB change logic of all_issues_since: it needs to return all
# issues replicated by this replicator regardless of their timestamps.
#
# 2001-07-09 NB Only set creation_ts on a new bug if it's not already
# set.
#
# 2001-07-09 NB Added job_url config item.
#
# 2001-07-13 NB Workaround for MySQL bug (left join with non-null
# datetime field)
#
# 2001-07-16 NB Old schema versions get upgraded.  Made schema_version a
# string (so we can have schema_version='1.2.3.4' if we need it).
# Delete config entries from the p4dti_config table if necessary.
#
# 2001-07-16 GDR Ensured that there's always a row in the replications
# table.  On the first replication, this pretends that the last
# replication was on the start_date.  all_bugs_since() says "fieldid is
# null" rather than "bug_when is null" to work around bug in MySQL.
#
# 2001-07-19 NB Always strip longdesc records on the way in or out of
# the database.
#
# 2001-07-19 NB Because we were setting creation_ts on migration, to a
# time in the (usually recent) past, the SQL to find recently touched
# bugs was always returning newly migrated bugs as well, and generating
# conflicts (job000016 means that they show up as changed in Perforce
# too).
#
# 2001-07-25 NB job000375: non-empty blank lines must be cleared when
# reading from Bugzilla, or Perforce will do it for us and confuse the
# replicator.
#
# 2001-09-10 NB Added auto-quoting for integral types.  See job000262.
#
# 2001-09-19 NB Bugzilla 2.14 (job000390).
#
# 2001-10-18 NB Exclude from "new and touched" those bugs which have a
# bugs_activity row whose bug_when is more recent than the since
# argument to changed_bugs_since (job000406).
#
# 2001-10-25 NB Accept any sequence type from MySQLdb, where previously
# we sometimes required a list type (job000411).
#
# 2001-10-26 NB Fix for job000410: only attempt to record field changes
# in bugs_activity if the field has a fieldid.
#
# 2001-11-01 NB Add user_is_disabled() method, to determine whether a
# user is disabled.
#
# 2001-11-26 NDL Read p4dti_bugzilla_parameters table into params
# dictionary.
#
# 2001-11-27 GDR Handle Bugzilla 2.14 change to profiles table.
#
# 2002-01-24 GDR Support Bugzilla emailsuffix parameter.  Better
# warning messages.
#
# 2002-02-01 GDR Removed unused method incomplete_replications.
#
# 2002-02-04 GDR Organized code into sections, added comments and
# references to design.
#
# 2002-03-28 NB We would like to always update delta_ts when we update
# a bug.  job000484.
#
# 2002-04-03 NB User fields in the bugs database need a sensible
# default value for Perforce.  qa_contact should default to None (0)
# because that's the same as the Bugzilla default.  The other user
# fields should default to $user.
#
# 2002-04-19 NB job000512: has_key can't take multiple arguments
# instead of a tuple.
#
# 2002-05-06 Ram Fix Processmail and system command interface for Win2000
#
# 2002-07-23 NB Add Bugzilla 2.16 support.
#
# 2002-10-29 NB Move directory-changing commands around in processmail
# so that it stands a chance of working on Windows.  Also send the
# output to nul.
#
# 2003-05-23 NB Remove support for older versions of Bugzilla.
#
# 2003-05-30 NB When getting a bug record, always find the current rid
# and sid even if they aren't ours.
#
# 2003-09-24 NB Improved Bugzilla version detection.
#
# 2003-11-04 NB Add tables for recognizing the schema of Bugzilla 2.17.5.
#
# 2004-05-28 NB Bugzilla 2.17.7 support: processmail replaced by
# bugmail.pl; detect and permit 2.17.5 schema; Handle either product
# and component names (before Bugzilla 2.17) or IDs (after); Handle
# group memberships either as bitsets (before Bugzilla 2.17) or as
# table entries (after); Support membership of a single bug in
# multiple groups; Handle group_control_map table for per-product
# group controls (from Bugzilla 2.17.5); Cache results of some
# database queries to speed operation with new or old schemas; More
# table locking now that there are more tables; Clean up better when
# deleting a bug; Correct values in bugs_activity entries when
# changing user columns.
#
# 2005-10-04 NB Bugzilla 2.19.3 has enumeration tables.  We pretend
# that these are actual enums, so that the rest of the code doesn't
# have to change.
#
#
# C. COPYRIGHT AND LICENSE
#
# This file is copyright (c) 2001 Perforce Software, Inc.  All rights
# reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1.  Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
# 2.  Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDERS AND CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
#
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/bugzilla.py#8 $
