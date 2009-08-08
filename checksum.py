#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#     CHECKSUM.PY -- CHECKSUM THE P4DTI SOURCES TO DETECT CHANGES
#
#             Gareth Rees, Ravenbrook Limited, 2001-03-05.
#
#
# 1. INTRODUCTION
#
# This Python script prints an MD5 checksum of the P4DTI sources.  The
# purpose is to allow Perforce support to easily determine if an
# organization has altered the P4DTI sources (and so are running an
# unsupported configuration) by asking the customer to run checksum.py
# and comparing the result to the checksum for the release.  This fixes
# job000252.
#
# The intended readership is project developers.
#
# This document is not confidential.


import md5

# We produced this by running p4 files "*.py" and removing (a) deleted
# files and (b) files that people are supposed to change, namely
# config.py and example_trigger.py.

files = [
    'bugzilla.py',
    'catalog.py',
    'check.py',
    'check_config.py',
    'check_jobs.py',
    'check_jobspec.py',
    'checksum.py',
    'config_loader.py',
    'configure_bugzilla.py',
    'dt_bugzilla.py',
    'dt_interface.py',
    'extend_jobspec.py',
    'init.py',
    'logger.py',
    'message.py',
    'migrate.py',
    'migrate_users.py',
    'mysqldb_support.py',
    'p4.py',
    'poll.py',
    'portable.py',
    'refresh.py',
    'replicator.py',
    'run.py',
    'service.py',
    'stacktrace.py',
    'translator.py',
    ]

# Python 1.5.2 doesn't have md5.hexdigest(), so we do it ourselves:
def hexify(s):
    result = ""
    for c in s:
       result = result + ("%02x" % ord(c))
    return result

if __name__ == '__main__':
    cs = md5.new()
    for file in files:
        cs.update(open(file, 'r').read())
    print hexify(cs.digest())


# A. REFERENCES
#
#
# B. Document History
#
# 2001-03-05 GDR Created.
#
# 2001-03-07 NB Made it work on Python 1.5.2.
#
# 2001-03-29 RB Corrected title, description, and creation date.
#
# 2001-08-07 GDR Formatted as a document.  Updated files.
#
# 2001-10-23 GDR Added new commands: migrate.py, migrate_users.py and
# poll.py.
#
# 2001-10-25 GDR Added mysqldb_support.py.
#
# 2001-11-07 GDR Added check_jobs.py.
#
# 2001-11-07 NDL Added config_loader.py and service.py.
#
# 2001-11-14 GDR Added teamtrack_query.py.
#
# 2002-02-25 GDR Execute only when main.
#
# 2003-05-21 NB Removed TeamTrack files.
#
# 2003-09-17 NB Added portable.py.
#
# 2003-12-12 NB Add extend_jobspec and check_jobspec.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/checksum.py#1 $
