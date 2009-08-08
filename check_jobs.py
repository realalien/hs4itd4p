#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#          CHECK_JOBS.PY -- CHECK THAT JOBS MATCH THE JOBSPEC
#
#             Gareth Rees, Ravenbrook Limited, 2001-11-07
#
#
# 1. INTRODUCTION
#
# This script checks that Perforce jobs match the Perforce jobspec and
# so can be fetched with a command like "p4 -G job -o job000001".  See
# See section 6.3.1, "Making Perforce jobs consistent with the jobspec"
# of the P4DTI Administrator's Guide [RB 2000-08-10].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

from config_loader import config
import catalog
import p4

def check_jobs():
    p4i = p4.p4(port = config.p4_port,
                client_executable = config.p4_client_executable,
                user = config.p4_user,
                password = config.p4_password)
    jobs = p4i.run('jobs')
    failures = 0
    for j in jobs:
        try:
            p4i.run('job -o %s' % j['Job'])
        except p4.error, msg:
            # "Job '%s' doesn't match the jobspec:"
            print str(catalog.msg(1008, j['Job']))
            print str(msg)
            failures = failures + 1
    if failures == 0:
        # "All jobs match the jobspec."
        print str(catalog.msg(1009))

if __name__ == '__main__':
    check_jobs()


# A. REFERENCES
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Administrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-08-10;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ag/>
#
#
# B. DOCUMENT HISTORY
#
# 2001-11-07 GDR Created.
#
# 2001-12-02 GDR Use port, password, user from configuration.
#
# 2002-02-25 GDR Execute only when main.
#
# 2003-05-23 NB Pass the client executable down into p4.
#
#
# C. COPYRIGHT AND LICENSE
#
# This file is copyright (c) 2001 Perforce Software, Inc.  All
# rights reserved.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/check_jobs.py#2 $
