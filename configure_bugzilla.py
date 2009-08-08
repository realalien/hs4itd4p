#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#   CONFIGURE_BUGZILLA.PY -- BUILD P4DTI CONFIGURATION FOR BUGZILLA
#
#           Richard Brooksby, Ravenbrook Limited, 2000-12-07
#
#
# 1. INTRODUCTION
#
# This is the automatic configurator for the Bugzilla integration of the
# Perforce Defect Tracking Integration (P4DTI).  Configuration
# generators are documented in detail in [GDR 2000-10-16, 8].
#
# This code takes a basic set of configuration parameters [RB
# 2000-08-10, 5.1] and generates a full set of parameters for the
# "dt_bugzilla", "p4", and "replicator" classes, as well as a Perforce
# jobspec.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import bugzilla
import catalog
import check_config
import dt_bugzilla
import logger
import os
import string
import translator
import types
import mysqldb_support

error = "Bugzilla configuration error"

# perforce keyword translator.
keyword_translator = translator.keyword_translator()

# enum translator (just like keyword translator except '' <-> 'NONE')
enum_translator = dt_bugzilla.enum_translator(keyword_translator)

# make_state_pairs: (strings * string) -> (string * string) list.  Make
# a list of pairs of state names (Bugzilla state, Perforce state).  This
# list will be used to translate between states, and also to generate
# the possible values for the Status field in Perforce.
#
# The closed_state argument is the Bugzilla state which maps to the
# special state 'closed' in Perforce, or None if there is no such state.
# See requirement 45.  See design decision [RB 2000-11-28 14:44:36
# GMT].
#
# The case of state names in these pairs is normalized for usability in
# Perforce: see design decision [RB 2000-11-28 14:24:32 GMT].

def make_state_pairs(states, closed_state):
    state_pairs = []
    state_p4_to_dt = {}
    found_closed_state = 0
    if closed_state != None:
        p4_closed_state = keyword_translator.translate_0_to_1(
            string.lower(closed_state))

    # Perforce jobs can't have state "new" (this indicates a fresh job
    # and Perforce changes the state to "open").  Nor can they have
    # state "ignore", because that is used in the submit form to
    # indicate that a job shouldn't be fixed by the change.
    #
    # Unfortunately, "new" and "ignore" are common names for states in
    # defect trackers (the former is in the Bugzilla workflow and in
    # the default workflow in TeamTrack), so we don't disallow them,
    # but prefix them with 'bugzilla_'.  Then we quit if two Bugzilla
    # states map to the same state in Perforce, ruling out the
    # unlikely situation that someone has a Bugzilla status of
    # 'BUGZILLA_CLOSED'.  See job000141.

    prohibited_states = ['new', 'ignore']
    prohibited_state_prefix = 'bugzilla_'

    for dt_state in states:
        p4_state = keyword_translator.translate_0_to_1(
            string.lower(dt_state))

        if closed_state != None:
            if p4_state == p4_closed_state:
                p4_state = 'closed'
                found_closed_state = 1
            elif p4_state == 'closed':
                p4_state = prohibited_state_prefix + p4_state

        if p4_state in prohibited_states:
            p4_state = prohibited_state_prefix + p4_state
        if (state_p4_to_dt.has_key(p4_state)
            and state_p4_to_dt[p4_state] != dt_state):
            # "Two Bugzilla states '%s' and '%s' map to the same
            # Perforce state '%s'."
            raise error, catalog.msg(300, (dt_state,
                                           state_p4_to_dt[p4_state],
                                           p4_state))
        state_p4_to_dt[p4_state] = dt_state
        pair = (dt_state, p4_state)
        if pair not in state_pairs:
            state_pairs.append(pair)

    if closed_state != None and not found_closed_state:
        # "You specified the closed_state '%s', but there's no such
        # Bugzilla state."
        raise error, catalog.msg(301, closed_state)
    return state_pairs


# Given the name of an enum column, calculate the values and default.
def translate_enum(column, bz_type):
    if not bz_type['type'] == 'enum':
        # "The '%s' column of Bugzilla's 'bugs' table is not an enum
        # type."
        raise error, catalog.msg(302, column)
    values = bz_type['values']
    values = map(enum_translator.translate_0_to_1, values)
    default = bz_type['default']
    if default != None:
        default = enum_translator.translate_0_to_1(default)
    values = string.join(values,'/')
    return values, default

# Some Bugzilla fields should not be changed from Perforce, either
# because they can not be changed from Bugzilla
# (e.g. 'creation_ts', 'delta_ts', 'lastdiffed'), or because they
# can only be changed in Bugzilla in very restricted ways
# (e.g. 'groupset', 'product', 'version', 'component',
# 'target_milestone', 'everconfirmed'), or because changing them
# in Bugzilla has complex side-effects which can't be sensibly
# reproduced here (e.g. 'votes', 'keywords').

read_only_fields = ['bug_id',
                    'groupset',
                    'creation_ts',
                    'delta_ts',
                    'product',
                    'version',
                    'component',
                    'target_milestone',
                    'votes',
                    'keywords',
                    'lastdiffed',
                    'everconfirmed',
                    'estimated_time',
                    'remaining_time',
                    'alias']

# Some Bugzilla fields can only be appended to.
# In particular, the 'Descriptions' section of a Bugzilla bug
# is actually a number of rows from another table, to which
# the Bugzilla web interface allows one to add a row.
# We fake this as if it's a regular field of the table, but
# retain the append-only restriction.

append_only_fields = ['longdesc']

# These Bugzilla fields are replicated by default.  If they are in
# replicated_fields, that's a configuration error.  If fields other
# than these are in omitted_fields, that's a configuration error too.
default_fields = ['bug_status',
                  'assigned_to',
                  'short_desc',
                  'resolution',
                  ]

# Map bugzilla field name to a name we can use in Perforce and a
# comment.

bz_field_map = {
    'longdesc':          ('Description',
                          "Description and comments."),
    'assigned_to':       ('Assigned_To',
                          "User to which the bug is assigned."),
    'groupset':          ('Groupset',
                          None),
    'bug_file_loc':      ('URL',
                          "The bug's URL."),
    'bug_severity':      ('Severity',
                          "The bug's severity."),
    'bug_status':        ('Status',
                          "The bug's status."),
    'creation_ts':       ('Creation_Timestamp',
                          "Time created."),
    'delta_ts':          ('Update_Timestamp',
                          "Time last updated."),
    'short_desc':        ('Summary',
                          "The bug's summary."),
    'op_sys':            ('OS',
                          "The OS to which the bug applies."),
    'priority':          ('Priority',
                          "The bug's priority."),
    'product':           ('Product',
                          "The product."),
    'rep_platform':      ('Platform',
                          "The hardware platform to which the bug "
                          "applies."),
    'reporter':	         ('Reporter',
                          "The Bugzilla user who reported the bug."),
    'version':	         ('Version',
                          "The product version."),
    'component':	 ('Component',
                          "The product component."),
    'resolution':	 ('Resolution',
                          "The manner in which the bug was resolved."),
    'target_milestone':  ('TargetMilestone',
                          "The bug's target milestone."),
    'qa_contact':	 ('QA_Contact',
                          "The Bugzilla user who is the QA contact for "
                          "this bug."),
    'status_whiteboard': ('StatusWhiteboard',
                          "The bug's status whiteboard."),
    'votes':	         ('Votes',
                          "The number of votes for this bug."),
    'keywords':	         ('Keywords',
                          "Keywords for this bug."),
    'lastdiffed':	 ('LastDiffed',
                          "Time last compared for automated e-mail."),
    'everconfirmed':     ('EverConfirmed',
                          "Has this bug ever been confirmed?"),
    'bug_id':            ('Bug_number',
                          "Bug number."),
    'reporter_accessible': ('Reporter_accessible',
                            "Accessible to the bug reporter."),
    'assignee_accessible': ('Assignee_accessible',
                            "Accessible to the assignee."),
    'qacontact_accessible': ('QAContact_accessible',
                             "Accessible to the QA Contact."),
    'cclist_accessible': ('CCList_accessible',
                          "Accessible to the CC List."),
    'alias':             ('Alias',
                          "Bug alias."),
    'estimated_time':    ('EstimatedTime',
                          "Estimated time in hours."),
    'remaining_time':    ('RemainingTime',
                          "Remaining time in hours."),
    'deadline':          ('Deadline',
                          "Deadline for fixing the bug."),
    }


def prepare_issue_advanced(config, bz, p4, dict, job):
    # Deduce a reporter for the issue, unless we have one already.
    if dict.get('reporter', "") == "":
        for field in ['P4DTI-user', config.job_owner_field, 'User']:
            if job.has_key(field):
                p4_user = job[field]
                # note: this is a lax translator
                bz_user = config.user_translator.translate_1_to_0(
                    job[field], bz, p4)
                if bz_user != config.user_translator.bugzilla_id:
                    dict['reporter'] = bz_user
                    break

    # Set creation_ts to the 'Date' field, suitably translated.
    # (otherwise creation_ts gets now()).
    if job.has_key(config.job_date_field) and dict.get('creation_ts', '') == '':
        dict['creation_ts'] = config.date_translator.translate_1_to_0(
            job[config.job_date_field], bz, p4)

    # If no summary, get short description from the first line of the
    # long description.
    if dict.get('short_desc','') == '':
        short_desc = string.strip(job.get('Description', ''))
        newline_pos = string.find(short_desc, '\n')
        if newline_pos >= 0:
            short_desc = short_desc[:newline_pos]
        if short_desc == '':
            short_desc = 'No description'
        dict['short_desc'] =  short_desc

    bugzilla_resolved_statuses = ['RESOLVED',
                                  'VERIFIED',
                                  'CLOSED']

    # Must fill in resolution for new jobs.
    if (dict.has_key('bug_status')
        and dict['bug_status'] in bugzilla_resolved_statuses
        and dict.get('resolution','') == ''):
        if job.get(config.job_status_field, '') == 'suspended':
            dict['resolution'] = 'LATER'
        else:
            dict['resolution'] = 'FIXED'


    # Supply default values for product, component and version as
    # promised in [GDR 2001-11-14, 3].
    bz.new_issue_defaults(dict)

    # Call user hook (see [GDR 2001-11-14, 3]).
    config.prepare_issue(dict, job)


def translate_jobspec_advanced(config, dt, p4, job):
    # Call user hook (see [GDR 2001-11-14, 4.6]).
    return config.translate_jobspec(job)

def get_fields_bz_to_p4(config, bugs_types):
    fields_bz_to_p4 = {}
    fields_p4_to_bz = {}
    # particular requested mappings
    field_names_bz_to_p4 = {}

    bz_fields = default_fields + config.replicated_fields
    for f in config.omitted_fields:
        bz_fields.remove(f)
    
    for (bz_field, p4_field) in config.field_names:
        field_names_bz_to_p4[bz_field] = p4_field
    
    for bz_field in bz_fields:
        if not bugs_types.has_key(bz_field):
            # "Bugzilla's table 'bugs' does not have a '%s' column."
            raise error, catalog.msg(307, bz_field)

        if field_names_bz_to_p4.has_key(bz_field):
            p4_field = field_names_bz_to_p4[bz_field]
        elif bz_field_map.has_key(bz_field):
            p4_field = bz_field_map[bz_field][0]
        else:
            desc = config.bugzilla.field_description(bz_field)
            if desc is None:
                desc = "bugzilla_" + bz_field
            p4_field = keyword_translator.translate_0_to_1(desc)

        if fields_p4_to_bz.has_key(p4_field):
            # "Bugzilla fields '%s' and '%s' both map to Perforce field '%s'."
            raise error, catalog.msg(324, (bz_field,
                                           fields_p4_to_bz[p4_field],
                                           p4_field))
        fields_bz_to_p4[bz_field] = p4_field
        fields_p4_to_bz[p4_field] = bz_field
    return fields_bz_to_p4


def check_bugzilla_directory(config):
    dir = config.bugzilla_directory
    if dir is None:
        config.bugmail_command = None
        return
    # strip any trailing / character
    if (len(dir) > 1
        and (dir[-1:] == '/' or
             dir[-1:] == '\\')):
        dir = dir[:-1]
    if not os.path.isdir(dir):
        # "Configuration parameter 'bugzilla_directory' does not
        # name a directory."
        raise error, catalog.msg(303)
    config.bugzilla_directory = dir
    # Check processmail
    if os.name == 'posix':
        processmail = 'processmail'
    elif os.name == 'nt':
        # processmail name is different on Windows
        processmail = 'processmail.pl'
    if os.access(os.path.join(dir, processmail), os.X_OK):
        config.bugmail_command = processmail
    else:
        bugmail = os.path.join('contrib', 'sendbugmail.pl')
        if os.access(os.path.join(dir, bugmail), os.R_OK):
            config.bugmail_command = bugmail
        else:
            # "Configuration parameter 'bugzilla_directory' does not
            # name a directory containing a mail-processing script."
            raise error, catalog.msg(304)

def check_field_lists(config):
    # 1. Validate the replicated_fields config parameter.
    bz_fields = []
    for f in config.replicated_fields:
        if f in default_fields:
            # "Field '%s' specified in 'replicated_fields' is a system field: leave it out!"
            raise error, catalog.msg(311, f)
        if f in bz_fields:
            # "Field '%s' appears twice in 'replicated_fields'."
            raise error, catalog.msg(312, f)
        else:
            bz_fields.append(f)

    # 2. Build a list of the fields we will replicate.
    bz_fields = bz_fields + default_fields

    # 3. Validate the omitted_fields config parameter.
    fields = []
    for f in config.omitted_fields:
        if f not in default_fields:
            # "Field '%s' specified in 'omitted_fields' is not a system field: leave it out!"
            raise error, catalog.msg(319, f)
        if f in fields:
            # "Field '%s' appears twice in 'omitted_fields'."
            raise error, catalog.msg(320, f)
        else:
            fields.append(f)
        bz_fields.remove(f)

    # bz_fields is now the set of fields we will replicate.

    # 4. Validate the field_names config parameter.
    bz_fields_check = []
    p4_fields_check = []
    for (bz_field, p4_field) in config.field_names:
        if bz_field in bz_fields_check:
            # "Bugzilla field '%s' appears twice in 'field_names'."
            raise error, catalog.msg(322, bz_field)
        bz_fields_check.append(bz_field)
        if bz_field not in bz_fields:
            # "Field '%s' in 'field_names' is not a replicated field."
            raise error, catalog.msg(321, bz_field)
        if p4_field in p4_fields_check:
            # "Perforce field '%s' appears twice in 'field_names'."
            raise error, catalog.msg(323, p4_field)
        p4_fields_check.append(p4_field)

def get_user_name_length(config):
    # Get the types of the 'profiles' table from Bugzilla.  In
    # particular we need to know the size of the 'login_name' column.
    profiles_types = config.bugzilla.get_types('profiles')
    if not profiles_types.has_key('login_name'):
        # "Bugzilla's table 'profiles' does not have a 'login_name'
        # column."
        raise error, catalog.msg(305)
    if profiles_types['login_name']['type'] != 'text':
        # "The 'login_name' column of Bugzilla's 'profiles' table does
        # not have a 'text' type."
        raise error, catalog.msg(306)
    return profiles_types['login_name']['length']

def make_p4_field_spec(bz_field,
                       p4_field,
                       bz_type,
                       user_name_length,
                       strict_user_translator):
    if bz_field_map.has_key(bz_field):
        p4_comment = bz_field_map[bz_field][1]
    else:
        p4_comment = None
        
    if p4_comment is None:
        p4_comment = ("Bugzilla's '%s' field" % bz_field)
        
    bz_type_class = bz_type['type']
    p4_values = None
    p4_length = None

    # if there is a default, use it.
    if bz_type.get('default'):
        p4_class = 'default'
        p4_default = bz_type['default']
    else:
        p4_class = 'optional'
        p4_default = None

    # Figure out the Perforce types, lengths, values, and default, and
    # the translator.
    # Maybe this should be table-driven.
    if bz_type_class == 'float':
        # "Field '%s' specified in 'replicated_fields' list has
        # floating-point type: this is not yet supported by P4DTI."
        raise error, catalog.msg(315, bz_field)
    elif bz_type_class == 'user':
        p4_type = 'word'
        p4_length = user_name_length
        trans = strict_user_translator
    elif bz_type_class == 'enum':
        p4_type = 'select'
        p4_values, p4_default = translate_enum(bz_field, bz_type)
        trans = enum_translator
    elif bz_type_class == 'int':
        p4_type = 'word'
        trans = dt_bugzilla.int_translator()
    elif bz_type_class == 'date':
        p4_type = 'date'
        p4_length = 20
        trans = dt_bugzilla.date_translator()
    elif bz_type_class == 'timestamp':
        p4_type = 'date'
        p4_length = 20
        trans = dt_bugzilla.timestamp_translator()
    elif bz_type_class == 'text':
        p4_type = 'text'
        trans = dt_bugzilla.text_translator()
    else:
        # "Field '%s' specified in 'replicated_fields' list has type
        # '%s': this is not yet supported by P4DTI."
        raise error, catalog.msg(314, (bz_field,
                                       bz_type['sql_type']))

    # "p4 -G" uses the field "code" to indicate whether the Perforce
    # command succeeded or failed.  See job000003.
    if p4_field == 'code':
        # "You can't have a field called 'code' in the Perforce
        # jobspec."
        raise error, catalog.msg(316)

    # Fixed-length fields get the length from Bugzilla.
    if p4_length == None:
        p4_length = bz_type['length']

    if bz_field in read_only_fields:
        p4_comment = (p4_comment + "  DO NOT MODIFY.")

    if bz_field in append_only_fields:
        p4_comment = (p4_comment + "  ONLY MODIFY BY APPENDING.")

    return ( p4_field,
             p4_type,
             p4_length,
             p4_class,
             p4_default,
             p4_values,
             p4_comment,
             trans,
             )

def configuration(config):
    # Check Bugzilla specific configuration parameters.
    check_config.check_string_or_none(config, 'bugzilla_directory')
    check_config.check_host(config, 'dbms_host')
    check_config.check_int(config, 'dbms_port')
    check_config.check_string(config, 'dbms_database')
    check_config.check_string(config, 'dbms_user')
    check_config.check_string(config, 'dbms_password')
    check_config.check_string(config, 'migrated_user_password')
    check_config.check_list_of(config, 'migrated_user_groups',
                               types.StringType, 'strings')
    check_config.check_list_of(config, 'replicated_fields',
                               types.StringType, 'strings')
    check_config.check_list_of(config, 'omitted_fields',
                               types.StringType, 'strings')
    check_config.check_list_of_string_pairs(config, 'field_names')

    check_bugzilla_directory(config)
    check_field_lists(config)

    # Handle logger.  We need a list of logger objects:
    log_params = {
        'priority': config.log_level,
        'max_length': config.log_max_message_length,
        }
    # The log messages should go to (up to) three places:
    # 1. to standard output (if running from a command line);
    loggers = []
    if config.use_stdout_log:
        loggers.append(apply(logger.file_logger, (), log_params))
    # 2. to the file named by the log_file configuration parameter (if
    # not None);
    if config.log_file != None:
        loggers.append(apply(logger.file_logger,
                             (open(config.log_file, "a"),),
                             log_params))
    # 3. to the Windows event log (if use_windows_event_log is true).
    if os.name == 'nt' and config.use_windows_event_log:
        loggers.append(apply(logger.win32_event_logger,
                             (config.rid,),
                             log_params))
    # 4. to the Unix syslog (if use_system_log is true).
    if os.name == 'posix' and config.use_system_log:
        loggers.append(apply(logger.sys_logger,
                             (),
                             log_params))

    # now a single logger object which logs to all of the logger objects
    # in our list:
    config.logger = logger.multi_logger(loggers)

    # Open a connection to the Bugzilla database.  This makes a DB-API
    # v2.0 connection object.  To work with a database other than
    # MySQL, change this to make an appropriate connection object.
    # Note that in that case changes are also needed in bugzilla.py
    # where we deal with MySQL-specific types such as tinyint.
    db = mysqldb_support.connect(config)

    # Make a Bugzilla DB object.  Note that this same object is used
    # subsequently by the replicator itself.
    config.bugzilla = bugzilla.bugzilla(db, config)

    # Get the types of the 'bugs' table from Bugzilla
    bugs_types = config.bugzilla.get_types('bugs')

    # Check field names against Bugzilla database and construct
    # a map, Bugzilla field name to Perforce field name.
    fields_bz_to_p4 = get_fields_bz_to_p4(config, bugs_types)

    user_name_length = get_user_name_length(config)

    # strict user translator doesn't allow unknown users
    strict_user_translator = dt_bugzilla.user_translator(
        config.replicator_address, config.p4_user, allow_unknown = 0)

    # lax user translator does allow unknown users
    lax_user_translator = dt_bugzilla.user_translator(
        config.replicator_address, config.p4_user, allow_unknown = 1)

    # p4_fields maps Bugzilla field name to the jobspec data (number,
    # name, type, length, dispositon, preset, values, help text,
    # translator).  The fields Job and Date are special: they are not
    # replicated from Bugzilla but are required by Perforce, so we
    # have them here.  Note that their help text is given (the other
    # help texts will be obtained from the bz_field_map).

    p4_fields = { \
        '(JOB)':       ( 101, 'Job', 'word', 32, 'required',
                         None, None,
                         "The job name.",
                         None ),
        '(DATE)':      ( 104, 'Date', 'date', 20, 'always',
                         '$now', None,
                         "The date this job was last modified.",
                         None ),
        # P4DTI fields:
        '(FILESPECS)': ( 191, 'P4DTI-filespecs', 'text', 0, 'optional',
                         None, None,
                         "Associated filespecs.",
                         None ),
        '(RID)':       ( 192, 'P4DTI-rid', 'word', 32, 'required',
                         'None', None,
                         "P4DTI replicator identifier. Do not edit!",
                         None ),
        '(ISSUE)':     ( 193, 'P4DTI-issue-id', 'word', 32, 'required',
                         'None', None,
                         "Bugzilla issue database identifier. Do not "
                         "edit!",
                         None ),
        '(USER)':      ( 194, 'P4DTI-user', 'word', 32, 'always',
                         '$user', None,
                         "Last user to edit this job. You can't edit "
                         "this!",
                         None ),
        }

    if fields_bz_to_p4.has_key('bug_status'):
        if bugs_types['bug_status']['type'] != 'enum':
            # "The 'bug_status' column of Bugzilla's 'bugs' table is not an
            # enum type."
            raise error, catalog.msg(308)
        # Make a list of (Bugzilla state, Perforce state) pairs.
        state_pairs = make_state_pairs(bugs_types['bug_status']['values'],
                                       config.closed_state)


        # Work out the legal values of the State field in the jobspec.  Note
        # that "closed" must be a legal state because "p4 fix -c CHANGE
        # JOBNAME" always sets the State to "closed" even if "closed" is not
        # a legal value.  See job000225.
        legal_states = map((lambda x: x[1]), state_pairs)
        if 'closed' not in legal_states:
            legal_states.append('closed')
        state_values = string.join(legal_states, '/')
        p4_fields['bug_status'] = ( 102,
                                    fields_bz_to_p4['bug_status'],
                                    'select',
                                    bugs_types['bug_status']['length'],
                                    'required',
                                    state_pairs[0][1],
                                    state_values,
                                    bz_field_map['bug_status'][1],
                                    dt_bugzilla.status_translator(state_pairs))

    if fields_bz_to_p4.has_key('assigned_to'):
        p4_fields['assigned_to'] = ( 103,
                                     fields_bz_to_p4['assigned_to'],
                                     'word', user_name_length,
                                     'required',
                                     '$user', None,
                                     bz_field_map['assigned_to'][1],
                                     strict_user_translator)

    if fields_bz_to_p4.has_key('short_desc'):
        p4_fields['short_desc'] = ( 105,
                                    fields_bz_to_p4['short_desc'],
                                    'text',
                                    bugs_types['short_desc']['length'],
                                    'required',
                                    '$blank', None,
                                    bz_field_map['short_desc'][1],
                                    dt_bugzilla.text_translator() )

    if fields_bz_to_p4.has_key('resolution'):
        if bugs_types['resolution']['type'] != 'enum':
            # "The 'resolution' column of Bugzilla's 'bugs' table is not an
            # enum type."
            raise error, catalog.msg(309)
        if not 'FIXED' in bugs_types['resolution']['values']:
            # "The 'resolution' column of Bugzilla's 'bugs' table does not
            # have a 'FIXED' value."
            raise error, catalog.msg(310)

        # Make a list of possible resolutions.
        (resolutions,
         default_resolution) = translate_enum('resolution',
                                              bugs_types['resolution'])
        p4_fields['resolution'] = ( 106,
                                    fields_bz_to_p4['resolution'],
                                    'select',
                                    bugs_types['resolution']['length'],
                                    'required',
                                    default_resolution,
                                    resolutions,
                                    bz_field_map['resolution'][1],
                                    enum_translator)

    # Additional replicated fields will be sequential from this field id.
    p4_field_id = 110

    # Go through the replicated_fields list, build structures and add
    # them to p4_fields.
    for bz_field in config.replicated_fields:
        p4_field = fields_bz_to_p4[bz_field]
        p4_fields[bz_field] = ((p4_field_id, ) +
                               make_p4_field_spec(bz_field, p4_field,
                                                  bugs_types[bz_field],
                                                  user_name_length,
                                                  strict_user_translator))
        p4_field_id = p4_field_id + 1
        if p4_field_id >= 191:
            # "Too many fields to replicate: Perforce jobs can contain
            # only 99 fields."
            raise error, catalog.msg(317)

    comment = ("# A Perforce Job Specification automatically "
               "produced by the\n"
               "# Perforce Defect Tracking Integration\n")

    jobspec = (comment, p4_fields.values())

    # Set configuration parameters needed by dt_bugzilla.
    config.append_only_fields = append_only_fields
    config.read_only_fields = read_only_fields
    config.jobname_function = lambda bug: 'bug%d' % bug['bug_id']

    # Set configuration parameters needed by the replicator.
    config.date_translator = dt_bugzilla.date_translator()
    config.job_owner_field = fields_bz_to_p4.get('assigned_to', 'User')
    config.job_status_field = fields_bz_to_p4.get('bug_status', 'Status')
    config.job_date_field = 'Date'
    config.jobspec = jobspec
    config.prepare_issue_advanced = prepare_issue_advanced
    config.text_translator = dt_bugzilla.text_translator()
    config.translate_jobspec_advanced = translate_jobspec_advanced
    config.user_translator = lax_user_translator

    # The field_map parameter is a list of triples (Bugzilla database
    # field name, Perforce field name, translator) required by the
    # replicator.  We use the filter to remove the fields that aren't
    # replicated: these have no translator.
    config.field_map = \
        map(lambda item: (item[0], item[1][1], item[1][8]),
            filter(lambda item: item[1][8] != None, p4_fields.items()))

    return config


# A. REFERENCES
#
# [GDR 2001-11-14] "Perforce Defect Tracking Integration Advanced
# Administrator's Guide"; Gareth Rees; Ravenbrook Limited; 2001-11-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/aag/>.
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-07 RB Branched and adapted from configure_teamtrack.py.
#
# 2000-12-08 GDR Translate state name "ignore" to "_ignore".
#
# 2000-12-13 NB State names need to be lower case in Perforce.  Also
# logger object needed for the bugzilla.bugzilla object.
#
# 2000-12-15 NB Added verbosity support.
#
# 2001-01-11 NB Added support for replicated_fields.  Also support
# closed_state, and move MySQL connection code here (out of bugzilla.py)
# so that we only open one connection when starting up.  Also sorted out
# the size of the jobspec fields.
#
# 2001-01-12 NB Moved configuration of read-only and append-only fields
# here from dt_bugzilla.py.  Added configuration of fields not recorded
# in the bugs_activity table.  Added comments for read-only and
# append-only fields.
#
# 2001-01-15 NB Added a table for field names and comments, because the
# automatically-generated ones were terrible.  Added validation for
# config parameters.
#
# 2001-01-18 NB Removed bugzilla_user.  Moved configuration checks out
# to check_config.py.  Pass replicator_user to Bugzilla.
#
# 2001-01-19 NB closed_state and log_file may be None.  Use system
# logger.
#
# 2001-01-25 NB Added bugzilla_directory to support processmail.
#
# 2001-01-26 NB Pass p4_server_description to Bugzilla.
#
# 2001-02-04 GDR Added start_date parameter.
#
# 2001-02-08 NB Prevent the existence of DateTime from changing our
# behaviour.  (job000193).
#
# 2001-02-09 NB Added checks for bugzilla_directory.
#
# 2001-02-13 GDR Allow administrator_address and smtp_server to be None.
#
# 2001-02-16 NB Added replicate_p configuration parameter.
#
# 2001-02-19 NB Moved keyword translation to p4.py.
#
# 2001-02-22 GDR Moved keyword translation to keyword.py.  Made sure
# that 'closed' is a legal job state in Perforce.  Added text translator
# to replicator config.
#
# 2001-02-26 GDR Refer to "Bugzilla" explicitly in messages, not just
# "defect tracker".
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-12 GDR Use messages for errors.
#
# 2001-03-13 GDR Removed verbose parameter; added log_level.  Removed
# P4DTI-action field.  Made P4DTI-filespec field optional.  Get
# keyword_translator from translator, not keyword.
#
# 2001-03-15 GDR Store configuration in config module.
#
# 2001-03-23 GDR Added job-date-field to replicator configuration.
#
# 2001-06-22 NB Moved common jobspec code into p4.py.
#
# 2001-06-22 NB Added initial comment to the jobspec description.
#
# 2001-09-19 NB Bugzilla 2.14 (job000390): new fields, some
# functionality moved to bugzilla.py.
#
# 2001-10-25 NB Add check of MySQLdb module version.  Moved code to
# ensure MySQLdb uses strings for dates and times to after the point
# at which we know that the MySQLdb release is supported.
#
# 2001-10-28 GDR Formatted as a document.
#
# 2001-11-05 GDR Added prepare_issue_advanced to replicator
# configuration.
#
# 2001-11-20 GDR Added translate_jobspec_advanced to replicator
# configuration.  Put jobspec in config rather than returning it.
#
# 2001-11-26 GDR Support log_max_message_length configuration parameter.
#
# 2001-11-27 GDR Check migrated_user_groups.
#
# 2002-01-07 NB Use correct translator for enum fields (job000445).
#
# 2002-01-31 GDR Use mysqldb_support.connnect to connect to the MySQL
# database.  This turns off date/time conversion in a way that's
# portable between MySQLdb releases.
#
# 2002-04-02 NB User fields should default to the current user,
# otherwise we get '0' which is no user at all.  job000491.
#
# 2002-04-03 NB Take default for user fields from bugzilla interface.
# Clarify distinction between strict and lax user translators.
#
# 2002-06-26 RB Merged Bugzilla for Windows 2000 port.
#
# 2002-10-25 RB Added back logging to syslog under control of new
# configuration parameter "use_system_log".
#
# 2003-05-21 NB Fixed some comments which incorrectly referred to TeamTrack.
#
# 2003-11-25 NB Rewrite the jobspec-creation code, and the handling of
# the relevant configuration parameters.  This is a step towards
# configurable jobspec.
#
# 2004-05-28 NB Add bugmail as alternative to processmail.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/configure_bugzilla.py#5 $
