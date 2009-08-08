#                Perforce Defect Tracking Integration Project
#                 <http://www.ravenbrook.com/project/p4dti/>
#
#           MYSQLDB_SUPPORT.PY -- CHECK RELEASE OF MYSQLDB MODULE
#
#                 Nick Barnes, Ravenbrook Limited, 2001-10-24
#
#
# 1. INTRODUCTION
#
# This module provides a function connect().  That function takes a
# P4DTI configuration, attempts to determine the release of the MySQLdb
# library, checks whether the release is supported by the P4DTI, and
# returns a database connection.
#
# It also notifies the P4DTI administrator as follows:
#
# - If the MySQLdb release is supported by the P4DTI, it generates an
#   informative message.
#
# - If the MySQLdb release is known to be incompatible with the P4DTI,
#   it raises a fatal exception.
#
# - If the MySQLdb release is unsupported, but not known to be
#   incompatible, it generates a warning message.
# 
# - If the MySQLdb release is supported, but deprecated, it generates
#   a warning message.
#
# See job000317, job000413, job000411 for problems addressed by
# identifying the MySQLdb release.
#
# When support for other MySQLdb releases is added or changed, the table
# 'MySQLdb_support' in section 5 must be modified.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import types
import MySQLdb
import catalog

error = "MySQLdb module support error"


# 2.  IDENTIFYING MYSQLDB RELEASE
#
# This section provides a function what_release() which attempts to
# identify a MySQLdb release.
#
# Functions in this section take a MySQLdb module as argument M.  This
# is to allow us to test this section without having to install and
# uninstall MySQLdb releases.


# 2.1.  Distinguish between release 0.3.0 and release 0.3.1

# Also distinguish those releases from unknown other releases which
# resemble those releases.
#
# Release 0.3.0 has MySQLdb.type_conv[MySQLdb.FIELD_TYPE.LONG] == int.
# Release 0.3.1 has MySQLdb.type_conv[MySQLdb.FIELD_TYPE.LONG] == long.

def distinguish_030_031(M):
    if hasattr(M, 'type_conv'):
        converter = M.type_conv[M.FIELD_TYPE.LONG]
        if converter == int:
            return '0.3.0'
        elif converter == long:
            return '0.3.1'
        else:
            return None
    else:
        return None


# 2.2. Map __version__ strings to release names
#
# This table maps the MySQLdb __version__ string to either a string
# (in which case it's the MySQLdb release name) or a function, which
# should be called with the MySQLdb module as an argument and which
# returns the MySQLdb release name, or None if it can't tell.

MySQLdb_versions = {
    '1.21':    '0.2.0',
    '1.24':    '0.2.1',
    '1.29':    '0.2.2',
    '1.32':    distinguish_030_031,
    '1.33':    '0.3.2',
    '1.34':    '0.3.3',
    '1.39':    '0.3.4',
    '1.40':    '0.3.5',
    '0.9.0':   '0.9.0',
    '0.9.1g2': '0.9.1c1',
    '0.9.1':   '0.9.1',
    '0.9.2':   '0.9.2',
    '0.9.3a1': '0.9.3a1',
    '0.9.3b1': '0.9.3b1',
    '1.0.0':   '1.0.0',
    '1.0.1':   '1.0.1',
    '1.2.0':   '1.2.0',
    '1.2.1':   '1.2.1',
    '1.2.1_p2':'1.2.1p2',
    '1.2.2':   '1.2.2',
    }


# 2.3. Determine the MySQLdb release

# Returns a pair (version, release), where version is the MySQLdb
# module's version string and release is the identified MySQLdb
# release.

def what_release(M):
    version = getattr(M, '__version__', 'No __version__')
    release = MySQLdb_versions.get(version, None)
    if isinstance(release, types.FunctionType):
        release = release(M)
    if release is None:
        release = 'Unknown'
    return version, release


# 3. SUPPORT NOTIFICATION
#
# These functions notify the P4DTI administrator about whether their
# release of MySQLdb is supported, unsupported (not known not to work),
# or broken (known not to work).  If it's known not to work with the
# P4DTI then the function raises an error.

def supported(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This release is supported by the P4DTI."
    config.logger.log(catalog.msg(1007, (version, release)))

def deprecated(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This release is supported by the P4DTI, but deprecated.
    # Future versions of the P4DTI may not support this release."
    config.logger.log(catalog.msg(1022, (version, release)))

def deprecated_unicode(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This release is supported by the P4DTI, but deprecated.
    # Operation with Unicode text may be incorrect.
    # Future versions of the P4DTI may not support this release."
    config.logger.log(catalog.msg(1024, (version, release)))

def unsupported(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This release is not supported by the P4DTI, but may work."
    msg = catalog.msg(1006, (version, release))
    config.logger.log(msg)

def unsupported_old(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This old release is not supported by the P4DTI, and may not
    # provide functions on which the P4DTI relies."
    config.logger.log(catalog.msg(1023, (version, release)))

def broken(version, release, config):
    # "MySQLdb version '%s' (release '%s') detected.
    # This release is incompatible with the P4DTI."
    raise error, catalog.msg(1005, (version, release))


# 4. TURN OFF TYPE CONVERSION
#
# These functions turn off MySQLdb's type conversion for dates and
# times.  The P4DTI needs the raw date/time string from the MySQL
# database.  However, if you have the mx.DateTime modules installed,
# then MySQL will convert dates and times into DateTime objects.
#
# These functions are needed because type conversion is handled
# differently in different MySQLdb releases.
#
# Each of these functions returns a dictionary of extra keyword
# arguments to be passed to MySQLdb.connect.

MySQLdb_date_time_types = [
    MySQLdb.FIELD_TYPE.DATETIME,
    MySQLdb.FIELD_TYPE.DATE,
    MySQLdb.FIELD_TYPE.TIME,
    MySQLdb.FIELD_TYPE.TIMESTAMP,
    ]


# 4.1. Releases with type_conv
#
# In releases prior to 0.9.0, type conversion is handled by the two
# dictionaries MySQLdb.type_conv (MySQL to Python) and
# MySQLdb.quote_conv (Python to MySQL).  So turn off type conversion by
# deleting entries from MySQLdb.type_conv.  No extra arguments are
# returned.  See [Dustman 2000-11-30].

def type_conv(release):
    for t in MySQLdb_date_time_types:
        if MySQLdb.type_conv.has_key(t):
            del MySQLdb.type_conv[t]
    return {}

# 4.2. Specifying UTF8 connection
# 
# In releases prior to 1.2.0, we specify UTF8 by saying unicode='utf8'.
# In release 1.2.0, we say use_unicode=True, and hope for the best.
# In release 1.2.1 and later, we specify UTF8 by saying charset='utf8'.

def unicode_arguments(release):
    if release < '1.2.0':
        return {'unicode': 'utf8'}
    elif release == '1.2.0':
        return {'use_unicode': True, }
    elif release >= '1.2.1':
        return {'charset': 'utf8'}

# 4.3. Releases needing a conv argument
#
# In release 0.9.0 and later, you must construct a dictionary to perform
# both kinds of type conversion and pass it as the 'conv' argument to
# MySQLdb.connect.  See [Dustman 2001-05-11, 3.1].

def conv_argument(release):
    import MySQLdb.converters
    conv = MySQLdb.converters.conversions.copy()
    for t in MySQLdb_date_time_types:
        if conv.has_key(t):
            del conv[t]
    args = unicode_arguments(release)
    args['conv'] = conv
    return args

# 4.4. Guess what to do
#
# When we encounter an unrecognized release, we do our best to support
# it by taking a guess as to what to do by seeing if MySQLdb.type_conv
# exists, and calling one of the two functions above, according.

def guess(release):
    if hasattr(MySQLdb, 'type_conv'):
        return type_conv(release)
    else:
        return conv_argument(release)


# 5. SUPPORT TABLE
#
# This table maps the MySQLdb release name (as determined by the
# what_release, section 2.3) to a pair of functions that we call when
# we identify that release.
# 
# The first function takes three arguments: the MySQLdb.__version__
# string, the MySQLdb release name (or None if undetermined), and the
# P4DTI configuration (which must be set up to have a logger).  This
# function must report on whether the MySQLdb release is supported,
# and raise an error if it is known not to work.
#
# The second function takes no arguments.  It must turn off type
# conversion for date and time values, and return a dictionary of
# keyword arguments to be passed to MySQLdb.connect in addition to the
# basic five arguments.
#
# This table will be updated as we test against and support more MySQLdb
# releases.

MySQLdb_support = {
    # These old versions lack an escape_string method; see job000317.
    '0.2.0': (broken, None),
    '0.2.1': (broken, None),

    # Older versions are all unsupported.
    '0.2.2': (unsupported_old, type_conv),
    '0.3.0': (unsupported_old, type_conv),
    '0.3.1': (unsupported_old, type_conv),
    '0.3.2': (unsupported_old, type_conv),
    '0.3.3': (unsupported_old, type_conv),
    '0.3.4': (unsupported_old, type_conv),
    '0.3.5': (unsupported_old, type_conv),
    '0.9.0': (unsupported_old, conv_argument),
    '0.9.1c1': (unsupported_old, conv_argument),
    '0.9.1': (unsupported_old, conv_argument),
    '0.9.2': (unsupported_old, conv_argument),
    '0.9.3a1': (unsupported_old, conv_argument),
    '0.9.3b1': (unsupported_old, conv_argument),

    # Versions prior to the changed Unicode support in 1.2.1 (2006-04-02)
    # are deprecated.
    '1.0.0': (deprecated_unicode, conv_argument),
    '1.0.1': (deprecated_unicode, conv_argument),
    '1.2.0': (deprecated_unicode, conv_argument),

    # Newer versions are 'supported' if we've tested against them,
    # 'unsupported' if not tested against but believed to work.
    '1.2.1': (supported, conv_argument),
    '1.2.1p2': (supported, conv_argument),
    '1.2.2': (supported, conv_argument),
    }

# 6. CONNECT TO MYSQL

def connect(config):
    version, release = what_release(MySQLdb)
    support, args = MySQLdb_support.get(release, (unsupported, guess))
    support(version, release, config)
    connect_args = {
        'host': config.dbms_host,
        'port': config.dbms_port,
        'db': config.dbms_database,
        'user': config.dbms_user,
        'passwd': config.dbms_password,
        }
    assert args
    connect_args.update(args(release))
    return apply(MySQLdb.connect, [], connect_args)


# A. REFERENCES
#
# [Dustman 2000-11-30] "MySQLdb: a Python interface for MySQL" (release
# 0.3.5); Andy Dustman; 2000-11-30;
# <http://www.ravenbrook.com/project/p4dti/import/2001-03-25/MySQL-python-0.3.5/MySQL-python-0.3.5/MySQLdb.py>.
#
# [Dustman 2001-05-11] "MySQLdb: a Python interface for MySQL" (release
# 0.9.1); Andy Dustman; 2001-05-11;
# <http://www.ravenbrook.com/project/p4dti/import/2001-10-16/MySQL-python-0.9.1/MySQL-python-0.9.1/doc/MySQLdb.html>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-10-25 NB Created.
#
# 2001-11-21 GDR Improved text of warning for unsupported releases.
# what_release now copes if MySQLdb.__version__ is missing.
#
# 2002-01-31 GDR Support MySQLdb release 0.9.1; include code for turning
# off date/time conversion; replace check_supported method with connect.
#
# 2004-08-02 NB Add support for MySQLdb 1.0.0.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/mysqldb_support.py#3 $
