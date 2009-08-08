#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#         CONFIG.PY -- CONFIGURATION PARAMETERS FOR THE P4DTI
#
#           Richard Brooksby, Ravenbrook Limited, 2000-12-08
#
#
# 1. INTRODUCTION
#
# This is the configuration script for the Perforce Defect Tracking
# Integration (P4DTI) <http://www.ravenbrook.com/project/p4dti/>.
#
# Edit this script according to the instructions in section 5.1, "P4DTI
# configuration", of the "Perforce Defect Tracking Integration
# Administrator's Guide" [RB 2000-08-10].
#
# The intended readership of this document is all P4DTI administrators.
#
# This document is not confidential.
#
# Developers: If you add parameters to this file, update section 2.1 of
# init.py as well.

import message


# 2. ESSENTIAL CONFIGURATION PARAMETERS
#
# You must provide suitable values for these parameters.

# The name of the defect tracking system you're integrating with.
dt_name = "Bugzilla"

# The e-mail address of the P4DTI administrator.
administrator_address = "????@????.com"

# The hostname and port number of the Perforce server.
p4_port = "perforce.????.com:1666"

# The replicator's user name and password on the Perforce server.
p4_user = "P4DTI-replicator0"
p4_password = ""

# The e-mail address from which the replicator appears to sends e-mail.
replicator_address = "p4dti-replicator0@????.com"

# The address of the SMTP server that the replicator uses to send
# e-mail.
smtp_server = "smtp.????.com"

# Issues modified after this date will be replicated; others will be
# ignored.
start_date = "2000-12-31 23:59:59"


# 3. DEFECT TRACKER CONFIGURATION PARAMETERS
#
# You must provide suitable values for the configuration parameters for
# your chosen defect tracker.


# 3.1. This section has been removed (was Teamtrack configuration parameters)

if 0:

    pass
# 3.2. Bugzilla configuration parameters

elif dt_name == "Bugzilla":

    # The distingished Bugzilla state that maps to the Perforce state
    # "closed", or None if you don't want to distinguish it.  Case
    # insensitive.
    closed_state = "RESOLVED"

    # The list of Bugzilla fields that will be replicated to Perforce
    # jobs in addition to the default fields "bug_status",
    # "short_desc", "assigned_to" and "resolution".
    replicated_fields = ["longdesc",
                         "priority",
                         "bug_severity",
                         "product"]

    # A list of default fields which should not be replicated to
    # Perforce.  Should only include "bug_status", "assigned_to",
    # "short_desc" or "resolution".
    omitted_fields = []

    # A list of pairs of strings for translating Bugzilla bug fields
    # to Perforce job fields.  The P4DTI has a default translation;
    # fill this in if you want different job field names in Perforce.
    field_names = []

    # Set this to 1 to prevent the replicator from replacing the
    # Perforce jobspec.
    keep_jobspec = 0

    # The host on which the Bugzilla MySQL server is running.
    dbms_host = "localhost"

    # The port number on which the Bugzilla MySQL server is listening
    # (an integer).
    dbms_port = 3306

    # The name of the database in which Bugzilla is storing its data on
    # the MySQL server.
    dbms_database = "bugs"

    # The user name and password that the replicator uses to log in to
    # MySQL to use the Bugzilla database.
    dbms_user = "bugs"
    dbms_password = ""

    # The directory in which Bugzilla is installed.  This is needed to
    # run the "processmail" script after the replicator makes changes to
    # Bugzilla bug records.  Set this to None if you don't want the
    # replicator to run processmail.  e.g. bugzilla_directory =
    # "/home/httpd/html/bugzilla"
    bugzilla_directory = None


# 4. OTHER CONFIGURATION PARAMETERS
#
# You may provide suitable values for these configuration parameters if
# you wish.  However, the default values should be fine.

# The replicator identifier.
rid = "replicator0"

# The Perforce server identifier.
sid = "perforce0"

# A format string used to build a URL for change descriptions in the
# defect tracker's user interface, or None if there is no URL for change
# descriptions.  For example, if you are running p4web: changelist_url =
# "http://????.????.com:8080/%d?ac=10"
changelist_url = None

# A format string used to build a URL for job descriptions in the
# defect tracker's user interface, or None if there is no URL for job
# descriptions.  For example, if you are running perfbrowse:
# job_url = "http://????.????.com/????/perfbrowse.cgi?@job+%s"
job_url = None

# The name of the replicator's log file, or None if log messages should
# not go to a file.  Note that log messages go to the standard output
# anyway, to syslog under Unix and Linux, and to the event log under
# Windows.
log_file = "p4dti.log"

# The minimum priority of messages to include in the replicator log.
# Set this to message.ERR, message.WARNING, message.NOTICE,
# message.INFO, message.DEBUG.
log_level = message.INFO

# The path to the Perforce client executable that the replicator uses.
p4_client_executable = "p4"

# Human-readable description of Perforce server.
p4_server_description = "Perforce server on " + p4_port

# Name of a p4 config file that the replicator creates and uses
# (to avoid placing password on the command line).  Will get
# overwritten if it already exists.
p4_config_file = "p4config"

# The period of time between polls of the servers, in seconds.
poll_period = 10

# Advanced users only.  A function that selects which issues to start
# replicating.  See section 2 of the the Advanced Administrator's Guide.
def replicate_p(issue):
    return 1

# Set this to 1 to use Perforce-style jobnames (like job000001) for
# replicated issues rather than using the defect tracker's name.
use_perforce_jobnames = 0

# Set this to 1 to log activity to the Windows Event Log; 0
# otherwise.
use_windows_event_log = 0

# Set this to 1 to log activity to the Unix syslog; 0
# otherwise.
use_system_log = 1


# A. REFERENCES
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Administrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-08-10.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-08 RB Created unified passive config script from Bugzilla and
# TeamTrack configurations.  Added dt_name parameter.
#
# 2000-12-18 NB Updated to reflect configuration items now in masters.
#
# 2001-01-11 NB replicated_fields now supported for Bugzilla.
#
# 2001-01-15 NB Moved replicated_fields into the DT-specific parts so
# we can give meaningful defaults.
#
# 2001-01-18 NB Get rid of bugzilla_user.
#
# 2001-01-19 GDR Get rid of TeamTrack *TIMETOFIX fields, because we
# don't properly support them yet.
#
# 2001-01-22 NB Better comments for log_file and dbms_port.
#
# 2001-01-25 NB Added bugzilla_directory.
#
# 2001-02-14 GDR Added start_date parameter.
#
# 2001-02-16 NB Added replicate_p parameter.
#
# 2001-02-16 RB Added documentation reference to replicate_p parameter.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-13 GDR Removed verbose parameter; added log_level.
#
# 2001-03-17 GDR Re-ordered parameters to separate parameters that must
# be changes from parameters where the defaults are OK.
#
# 2001-07-03 GDR Added teamtrack_version parameter.
#
# 2001-07-09 NB Added job_url parameter.
#
# 2001-09-12 GDR Added use_windows_event_log parameter.
#
# 2001-10-05 GDR Added use_perforce_jobnames parameter.
#
# 2001-11-22 RB Updated reference for replicate_p to point to the new
# Advanced Administrator's Guide.
#
# 2002-06-26 RB Moved use_windows_event_log to section 4, since it now
# applies to Bugzilla on Windows as well as TeamTrack.
#
# 2002-10-25 RB Added use_system_log to section 4.
#
# 2003-08-07 DRJ Removed TeamTrack section.
#
# 2003-09-25 NB Added p4_config_file.
#
# 2003-11-25 NB Added field_map and omitted_fields.
#
# 2003-12-08 NB Added keep_jobspec.
#
#
# C. COPYRIGHT AND LICENCE
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/config.py#1 $
