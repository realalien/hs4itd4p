#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#             DT_INTERFACE.PY -- DEFECT TRACKER INTERFACES
#
#             Gareth Rees, Ravenbrook Limited, 2001-03-13
#
#
# 1. INTRODUCTION
#
# This module defines abstract interfaces for defect trackers and
# associated data.  The aim of these classes is to:
#
#  1. Allow people to develop integrations with new defect trackers
# [Requirements, 25] without having to know about the internals of the
# replicator.
#
#  2. Keep the cost of maintaining integrations low [Requirements, 29]
# by isolating changes.
#
#  3. Allow the replicator be maintained [Requirements, 30, 32] without
# knowing any details of the defect tracker it is replicating to.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.


# 2. DEFECT TRACKER CLASS
#
# The defect_tracker class is an abstract class representing the
# interface between the replicator and the defect tracker.  You can't
# use this class; you must subclass it and use the subclass.
#
# The interface to this class is documented in [GDR 2000-10-16, 7.1].

class defect_tracker:
    pass


# 3. DEFECT TRACKER ISSUE CLASS
#
# The defect_tracker_issue class is an abstract class representing an
# issue in the defect tracker.  You can't use this class; you must
# subclass it and use the subclass.
#
# The interface to this class is documented in [GDR 2000-10-16, 7.2].

class defect_tracker_issue:
    pass


# 4. DEFECT TRACKER FIX CLASS
#
# The defect_tracker_fix class is an abstract class representing a fix
# record in the defect tracker.  You can't use this class; you must
# subclass it and use the subclass.
#
# The interface to this class is documented in [GDR 2000-10-16, 7.3].

class defect_tracker_fix:
    pass


# 5. DEFECT TRACKER FILESPEC CLASS
#
# The defect_tracker_filespec class is an abstract class representing an
# filespec associated with an issue in the defect tracker.  You can't
# use this class; you must subclass it and use the subclass.
#
# The interface to this class is documented in [GDR 2000-10-16, 7.4].

class defect_tracker_filespec:
    pass


# A. REFERENCES
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-03-13 GDR Created.  Moved defect_tracker, defect_tracker_issue,
# defect_tracker_filespec and defect_tracker_fix classes here from
# replicator.py.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/dt_interface.py#2 $
