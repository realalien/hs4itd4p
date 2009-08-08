#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#         INIT.PY -- INITIALIZE REPLICATOR AND DEFECT TRACKER
#
#           Richard Brooksby, Ravenbrook Limited, 2000-12-08
#
#
# 1. INTRODUCTION
#
# This module must:
#
#  1. Supply default values for configuration parameters added since
# release 1.0.6.
#
#  2. Check the configuration parameters, construct configuration and
# generate a jobspec by calling the method configure_DT.configuration().
#
#  3. Construct the defect tracker object 'dt'.
#
#  4. Construct the replicator object 'r' and call its init() method.
#
#  5. Update the Perforce jobspec, unless it's the first time the
# replicator has run and there are existing jobs (see job000219 and
# job000240).
#
# The design for this module is given in [GDR 2000-09-13, 5].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import check_config
from config_loader import config
import p4
import re
import replicator
import socket
import string
import os

error = "P4DTI Initialization error"


# 2. CHECK PARAMETERS


# 2.1. Supply defaults for new parameters
#
# We supply default values for configuration parameters that have been
# added since the first supported release (1.0.7) so that if people use
# an old configuration file with a new P4DTI release, at least things
# won't break.  See job000347.

default_parameters = {
    'configure_name': config.dt_name,
    'field_names': [],
    'job_url': None,
    'keep_jobspec': 0,
    'log_max_message_length': 10000,
    'migrate_p': lambda job: 0,
    'migrated_user_groups': [],
    'migrated_user_password': 'password',
    'omitted_fields': [],
    'p4_config_file': '',
    'prepare_issue': lambda dict, job: None,
    'replicate_job_p': lambda job: 0,
    'translate_jobspec': lambda job: job,
    'use_deleted_selections': 1,
    'use_perforce_jobnames': 0,
    'use_stdout_log': 1,
    'use_windows_event_log': 0,
    'use_system_log': 1,
    }
for k, v in default_parameters.items():
    if not hasattr(config, k):
        setattr(config, k, v)


# 2.2. Check generic parameters
#
# Defect tracker specific configuration parameters are checked by the
# configuration generator for that defect tracker.

if config.administrator_address != None:
    check_config.check_email(config, 'administrator_address')
check_config.check_changelist_url(config, 'changelist_url')
check_config.check_string_or_none(config, 'closed_state')
check_config.check_string(config, 'configure_name')
check_config.check_string_or_none(config, 'log_file')
check_config.check_job_url(config, 'job_url')
check_config.check_bool(config, 'keep_jobspec')
check_config.check_int(config, 'log_level')
check_config.check_int(config, 'log_max_message_length')
check_config.check_function(config, 'migrate_p')
check_config.check_string(config, 'p4_client_executable')
check_config.check_string(config, 'p4_port')
check_config.check_string(config, 'p4_user')
check_config.check_string(config, 'p4_password')
check_config.check_string(config, 'p4_server_description')
check_config.check_int(config, 'poll_period')
check_config.check_function(config, 'prepare_issue')
check_config.check_function(config, 'replicate_job_p')
check_config.check_function(config, 'replicate_p')
check_config.check_email(config, 'replicator_address')
check_config.check_identifier(config, 'rid')
check_config.check_identifier(config, 'sid')
if config.smtp_server != None:
    check_config.check_host(config, 'smtp_server')
check_config.check_date(config, 'start_date')
check_config.check_function(config, 'translate_jobspec')
check_config.check_bool(config, 'use_deleted_selections')
check_config.check_bool(config, 'use_perforce_jobnames')
if os.name == 'nt':
    check_config.check_bool(config, 'use_windows_event_log')
check_config.check_bool(config, 'use_stdout_log')
if os.name == 'posix':
    check_config.check_bool(config, 'use_system_log')


# 3. CALL THE CONFIGURATION GENERATOR; MAKE A DEFECT TRACKER INTERFACE
#
# Import configuration generator and defect tracker module based on
# configuration parameters configure_name and dt_name (respectively).
# We don't want people to have to edit this file (or any P4DTI files)
# just to add a new defect tracker or make a new configuration.
#
# This allows people to prepare advanced configurations by writing their
# own configuration generator and specifying it in the configure_name
# parameter.  See [GDR 2000-10-16, 8.6].

configure_name = string.lower(config.configure_name)
configure_module = __import__('configure_' + configure_name)
config = configure_module.configuration(config)

dt_name = 'dt_' + string.lower(config.dt_name)
dt_module = __import__(dt_name)
dt = getattr(dt_module, dt_name)(config)


# 4. MAKE A PERFORCE INTERFACE AND A "DEFECT TRACKER" FOR PERFORCE

p4_interface = p4.p4(client = ('p4dti-%s' % socket.gethostname()),
                     client_executable = config.p4_client_executable,
                     password = config.p4_password,
                     port = config.p4_port,
                     user = config.p4_user,
		     config_file = config.p4_config_file,
                     logger = config.logger)



# 5. MAKE THE REPLICATOR AND INITIALIZE IT

r = replicator.replicator(dt, p4_interface, config)


# A. REFERENCES
#
# [GDR 2000-09-13] "Replicator design"; Gareth Rees; Ravenbrook Limited;
# 2000-09-13;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/replicator/>.
#
# [GDR 2001-03-14] "test_p4dti.py -- Test the P4DTI"; Gareth Rees;
# Ravenbrook Limited; 2001-03-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/test/test_p4dti.py>.
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-11-30 GDR Added changelist_url configuration parameter.
#
# 2000-12-04 GDR Alphabetized parameters.  Added replicator_address.
# Made sure to pass all parameters to configure_teamtrack.
#
# 2000-12-08 RB Moved configuration parameters to config.py.  Merged
# separate TeamTrack and Bugzilla activation scripts.
#
# 2001-01-11 NB Bugzilla startup has changed because configure_bugzilla
# now opens the MySQL connection.
#
# 2001-01-18 NB bugzilla_user has gone.
#
# 2001-01-25 NB Added bugzilla_directory.
#
# 2001-02-04 GDR Added start_date parameter.
#
# 2001-02-16 NB Added replicate_p configuration parameter.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-13 GDR Removed verbose parameter; added log_level.
#
# 2001-03-14 GDR Pass rid and sid parameters to configure_teamtrack.
#
# 2001-03-15 GDR Formatted as a document.  Use messages when raising
# errors.  Store configuration in config module.
#
# 2001-03-22 GDR Use the configure_name parameter, if specified, to make
# the name of the configuration generator.  Don't update the jobspec if
# the configuration generator returned None.
#
# 2001-06-15 GDR Removed call to replicator.init() -- that function no
# longer exists.
#
# 2001-06-22 NB Move jobspec manipulation code into p4.py.
#
# 2001-06-22 NB Changed p4 jobspec interface.
#
# 2001-06-25 NB Changed interface to p4 jobspecs.
#
# 2001-07-09 NB Added job_url config parameter.
#
# 2001-07-14 GDR Supply default values for new configuration parameters
# to fix job000347.  Removed try/except around imports; this was
# obscuring other import errors; see job000315 and job000336.
#
# 2001-08-07 GDR Added support for the P4DTI_CONFIG environment
# variable.
#
# 2001-09-12 GDR Added `use_windows_event_log' configuration parameter.
#
# 2001-09-24 GDR Don't reload the P4DTI configuration if already loaded.
#
# 2001-10-25 GDR Added migrate_p to default parameters.
#
# 2001-11-05 GDR Added prepare_issue, replicate_job_p to default
# parameters.
#
# 2001-11-07 NDL Extracted code to load configuration and moved it to
# config_loader.py.
#
# 2001-11-20 GDR Added translate_jobspec.  Don't update the Perforce
# jobspec here, do it in replicator.py.
#
# 2001-11-21 GDR Added migrate_user_password.  Check migration
# configuration parameters.  Load configuration and defect tracker
# modules in a neater way.
#
# 2001-11-22 GDR Added use_deleted_selections.
#
# 2001-11-26 GDR Added log_max_message_length.
#
# 2001-11-27 GDR Added migrated_user_groups.
#
# 2002-03-28 NB Correct lambda syntax.
#
# 2002-10-25 RB Defaulted new parameter "use_system_log" to 1, for
# compatibility with older P4DTI config files.
#
# 2003-05-21 NB Removed teamtrack_version from the default_parameters
# table.
#
# 2003-09-25 NB Add p4_config_file.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/init.py#2 $
