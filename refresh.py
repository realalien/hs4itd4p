#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#  REFRESH.PY -- REFRESH ALL JOBS THEM FROM THE DEFECT TRACKER
#
#             Gareth Rees, Ravenbrook Limited, 2000-12-08
#
#
# 1. INTRODUCTION
#
# This script updates all the jobs on the Perforce server by
# replicating issues and fixes from the defect tracker to Perforce.
# It should be used according to the instructions in section 9.2,
# "Refreshing jobs in Perforce" of the P4DTI Administrator's Guide [RB
# 2000-08-10].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import sys

if __name__ == '__main__':
    # "WARNING!  This script will update all jobs in Perforce.  Please
    # use it according to the instructions in section 9.2 of the P4DTI
    # Administrator's Guide.  Are you sure you want to go ahead?"
    sys.stdout.write(catalog.msg(1002).wrap(79))
    sys.stdout.write(' ')
    sys.stdout.flush()
    if sys.stdin.readline()[0] in 'yY':
        from init import r
        r.refresh_perforce_jobs()


# A. REFERENCES
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Administrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-08-10;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ag/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-08 GDR Created.
#
# 2000-12-18 NB config_teamtrack replaced with init.
#
# 2001-02-12 GDR Fixed typo.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-16 GDR Moved deletion of jobs to replicator's
# refresh_perforce_jobs() method.  Formatted as document.  Added warning
# to introduction.  Added warning before the script runs.
#
# 2001-10-01 GDR Flush stdout after printing the warning so the script
# will work on a terminal with buffered output.
#
# 2001-11-28 GDR Refreshing only updates all jobs; it no longer deletes
# them.  Warning message changed accordingly.
#
# 2002-02-25 GDR Execute only when main.
#
# 2002-03-25 NB Updated comments to reflect behaviour: refreshing
# doesn't delete jobs (job000483).
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/refresh.py#2 $
