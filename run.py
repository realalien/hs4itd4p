#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#                  RUN.PY -- RUN THE P4DTI REPLICATOR
#
#             Nick Barnes, Ravenbrook Limited, 2000-11-16
#
#
# 1. INTRODUCTION
#
# This Python script runs the P4DTI replicator.  See section 5.5,
# "Starting and stopping the replicator manually" of the P4DTI
# Administrator's Guide [RB 2000-08-10].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

if __name__ == '__main__':
    from init import r
    r.run()


# A. REFERENCES
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Administrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-08-10;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ag/>.
#
#
# B. Document History
#
# 2000-11-16 NB Created.
#
# 2000-12-08 RB Moved config_teamtrack to init_teamtrack.  Removed
# redundant "r.init()" as this is in init_teamtrack.  Moved
# config_teamtrack to init_teamtrack.  Merged TeamTrack and Bugzilla
# activation scripts.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-17 GDR Formatted as a document.
#
# 2002-02-25 GDR Execute only when main.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/run.py#2 $
