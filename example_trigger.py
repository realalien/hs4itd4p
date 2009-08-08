#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#  EXAMPLE_TRIGGER.PY -- AN EXAMPLE PERFORCE TRIGGER FOR ENFORCING WORKFLOW
#
#           Richard Brooksby, Ravenbrook Limited, 2000-12-06
#
#
# 1. INTRODUCTION
#
# This is an example Perforce trigger script for preventing changes
# to areas of the Perforce repository without certain defect tracker
# conditions being met [Requirements, 57].
#
# This document is intended for administrators of the Perforce Defect
# Tracking Integration (P4DTI).
#
# This document is not confidential.
#
#
# 2. USING THE TRIGGER
#
# First, read section 5.2.2, "Installing Perforce triggers to enforce
# workflow" of the "Perforce Defect Tracking Integration Administrator's
# Guide" [RB 2000-08-10, 5.2.2].
#
# To use this trigger, first adapt the code to make it test the
# condition that you want to enforce.
#
# This example script insists that submissions fix to status "closed" at
# least one issue which has a priority of "critical".  This almost
# certainly isn't quite what you want, so you'll need to do some
# programming.
#
# You will also need to configure the P4DTI to replicate the fields that
# you want to check.  Most likely you'll want to check that the
# "priority" or "severity" or something similar is above a certain
# level, or that the "approval" field has been set by a manager, or
# something like that.  You need to make sure the relevant fields are
# replicated.  See section 5.1, "P4DTI configuration" of the "Perforce
# Defect Tracking Integration Administrator's Guide" [RB 2000-08-10,
# 5.1].
#
# Be sure to read the "Triggers" section in chapter 6 of the "Perforce
# System Administrator's Guide" [Perforce 2000-10-11].  Then use the "p4
# triggers" command to insert a line like:
#
#         enforce-critical //depot/release/master/... "/usr/local/bin/python /whatever-path-to/your-trigger.py %serverport% root %client% %changelist%"
#
# Where "root" is a user which has access to Perforce without a
# password.  (Or you could edit this script to include the password.)
#
# See "Perforce Defect Tracking Integration Administrator's Guide" for
# more information about this and other aspects of configuring the P4DTI
# [RB 2000-08-10].

import sys
import os
import marshal

def p4(command):
    stream = os.popen("p4 -G " + command, "r")
    results = []
    try:
        while 1:
            results.append(marshal.load(stream))
    except EOFError:
        pass
    if (len(results) == 1
        and results[0].has_key('code')
        and results[0]["code"] == "error"):
        raise "Perforce Error", results[0]["data"]
    return results

def check_fix():
    usage = "python %s serverport user client changelist" % sys.argv[0]

    if len(sys.argv) != 5:
        sys.exit(usage)

    serverport, user, client, change = sys.argv[1:5]

    os.environ["P4PORT"] = serverport
    os.environ["P4USER"] = user
    os.environ["P4CLIENT"] = client

    fixes = p4("fixes -c %s" % change)

    # Fixes look like this:
    #  [{'Change': '1',
    #    'Client': 'newton-lime',
    #    'Date': '976102677',
    #    'User': 'newton',
    #    'code': 'stat',
    #    'Job': '00003',
    #    'Status': 'closed'},
    #   ...]

    # Enforce the rule that every submission must close at least one
    # job with critical severity.  It might affect other jobs as well,
    # but we don't care.

    for fix in fixes:
        assert fix.has_key("Change") and fix["Change"] == change
        assert fix.has_key("Status")

        job = p4("job -o %s" % fix["Job"])[0]

        if (fix["Status"] == "closed"
            and job.has_key("Severity")
            and job["Severity"] == "critical"):
            sys.exit(0)

    # No job was found that passed the test, so print a message to tell
    # the submittor why we're refusing to accept the change.
    print("Submissions to this codeline must fix at least one "
          "critical issue.")
    sys.exit(1)

if __name__ == '__main__':
    check_fix()


# A. REFERENCES
#
# [Perforce 2000-10-11] "Perforce 2000.1 System Administrator's Guide";
# Perforce Software; 2000-10-11;
# <http://www.perforce.com/perforce/doc.001/manuals/p4sag/>.
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Administrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-08-10;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ag/>.
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-06 RB Created to solve Ravenbrook job job000043.
#
# 2000-12-15 RB Fixed usage message to take script name from argv.
# Detabbed to four spaces for consistency with the rest of our Python
# source.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-04-29 GDR Formatted as a document.  Added reference to
# requirements.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/example_trigger.py#2 $
