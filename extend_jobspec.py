#                Perforce Defect Tracking Integration Project
#                 <http://www.ravenbrook.com/project/p4dti/>
#
#             EXTEND_JOBSPEC.PY -- ADD REPLICATOR FIELDS TO THE JOBSPEC
#
#                Nick Barnes, Ravenbrook Limited, 2003-12-11
#
#
# 1. INTRODUCTION
#

# This Python script extends the existing Perforce jobspec by adding
# the fields required for replication.  In the event of a name clash,
# it will overwrite an existing field only if the -f or --force
# options are given.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import getopt
import sys

if __name__ == '__main__':
    force = 0
    options, args = getopt.getopt(sys.argv[1:], 'f', ['force'])
    for o, a in options:
        if o in ['-f', '--force']:
            force = 1

    from init import r
    r.extend_jobspec(force=force)

# A. REFERENCES
# 
#
# B. DOCUMENT HISTORY
#
# 2003-12-11 NB Created.
#
#
# C. COPYRIGHT AND LICENSE
#
# This file is copyright (c) 2003 Perforce Software, Inc.  All rights
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/extend_jobspec.py#1 $
