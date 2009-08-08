#                Perforce Defect Tracking Integration Project
#                 <http://www.ravenbrook.com/project/p4dti/>
#
#                        CATALOG.PY -- MESSAGE CATALOG
#
#                 Gareth Rees, Ravenbrook Limited, 2001-03-12
#
#
# 1. INTRODUCTION
#
# This module defines message catalogs for the P4DTI.  A message
# catalog is a dictionary mapping message id to the formatting string
# used to build the message.  When the message is printed, arguments
# will be substituted for the format specifiers using the % operator.
#
# These message catalogs are intended to be used by the
# message.catalog_factory class in the message module in order to:
#
#  1. Support future localization of the P4DTI (by using different
# message catalogs for different languages); and
#
#  2. Help developers to prevent message ids from clashing, by
# providing a catalog of all messages.
#
# The name of a catalog should include the product name and the ISO
# language code for the language [ISO 639].
#
# The P4DTI's message system is documented in detail in section 6.6,
# "Logging and error handling" of the P4DTI Integrator's Guide [GDR
# 2000-10-16].
#
# If you change a message in a catalog, make sure to also change the
# comment in the code next to each use of the message (there may be
# several uses) and the entry in section 11.2 of the Administrator's
# Guide.
#
# Never re-use message ids.  If you stop using a message, then leave a
# placeholder in this file with priority message.NOT_USED.  (This will
# mean that an attempt to use the message results in an error.)
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import message


# 2. P4DTI MESSAGES IN ENGLISH
#
# This is a catalog of messages in English for the "P4DTI" product.

p4dti_en_catalog = {


    # 2.1. Messages from bugzilla.py (100-199)

    100: (message.DEBUG, "Executing SQL command '%s'."),
    101: (message.DEBUG, "MySQL returned '%s'."),
    102: (message.DEBUG, "fetchone() returned '%s'."),
    103: (message.DEBUG, "fetchall() returned '%s'."),
    104: (message.DEBUG, "Running command '%s'."),
    105: (message.NOT_USED, "Given '%s' when expecting a string or integer."),
    106: (message.ERR, "Select '%s' of %s returns no rows."),
    107: (message.ERR, "Select '%s' of %s expecting one row but returns %d."),
    108: (message.ERR, "Trying to fetch a row from non-select '%s'."),
    109: (message.ERR, "Select '%s' of %s returned an unfetchable row."),
    110: (message.ERR, "Trying to fetch rows from non-select '%s'."),
    111: (message.ERR, "Select '%s' of %s returned unfetchable rows."),
    112: (message.ERR, "Select '%s' of %s expecting no more than one row but returns %d."),
    113: (message.ERR, "Select '%s' of %s returns %d columns but %d values."),
    115: (message.NOT_USED, "Select '%s' of %s returns %d keys but %d columns."),
    116: (message.ERR, "Couldn't insert row in table '%s'."),
    117: (message.ERR, "Couldn't update row in table '%s' where %s."),
    118: (message.NOT_USED,
          "Old P4DTI/Bugzilla schema version %s detected; "
          "dropping old tables and replacing with version %s."),
    119: (message.WARNING,
          "Old P4DTI/Bugzilla schema version %s detected; "
          "altering tables to upgrade to schema version %s."),
    120: (message.CRIT,
          "Unknown or future P4DTI/Bugzilla schema version %s detected."),
    121: (message.WARNING,
          "Your P4DTI/Bugzilla schema is prior to release 1.0.2. "
          "Altering tables to upgrade schema to release 1.0.2."),
    122: (message.CRIT,
          "Nothing in p4dti_replications table: database corrupted?"),
    123: (message.CRIT,
          "Bugzilla version %s is not supported by the P4DTI."),
    124: (message.INFO,
          "Bugzilla version %s detected, with these additional tables present: %s."),
    125: (message.INFO,
          "Bugzilla version %s detected."),
    126: (message.NOT_USED,
          "P4DTI configuration specifies Bugzilla version %s, but version %s detected."),
    127: (message.NOT_USED,
          "Bugzilla's fielddefs table does not include '%s'."),
    128: (message.INFO, "Running %d deferred commands..."),
    129: (message.WARNING, "The Bugzilla configuration parameters are missing from the Bugzilla database.  This means that the P4DTI won't support Bugzilla features like 'emailsuffix'.  If you need these features, edit your Bugzilla configuration parameters and restart the P4DTI.  See section 5.3.3 of the P4DTI Administrator's Guide."),
    130: (message.WARNING, "Bugzilla configuration parameter 'p4dti' is turned off.  You won't see Perforce fixes in Bugzilla until you turn it on.  See section 5.3.3 of the P4DTI Administrator's Guide."),
    131: (message.WARNING, "Bugzilla version %s detected, with these tables missing: %s and these additional tables present: %s. The P4DTI may fail to operate correctly."),
    132: (message.WARNING, "Bugzilla version %s detected, with these tables missing: %s.  The P4DTI may fail to operate correctly."),
    133: (message.WARNING, "Bugzilla is not configured to store text in UTF-8 encoding.  Replication of non-ASCII text data from Bugzilla may be incorrect."),
    134: (message.CRIT,
          "MySQL version %s is not supported by the P4DTI."),
    135: (message.INFO,
          "MySQL version %s detected."),
    136: (message.WARNING,
          "MySQL version %s detected.  Use of this version is deprecated due to poor Unicode support."),
    137: (message.CRIT,
          "Could not determine MySQL version."),
    138: (message.WARNING,
          "Bugzilla is configured to store text in UTF-8 encoding, but the Bugzilla database is not configured for that encoding (table '%s' has character set '%s').  Replication of non-ASCII text data may be incorrect."),
    139: (message.WARNING,
          "Bugzilla is configured to store text in UTF-8 encoding, but the Bugzilla database is not configured for that encoding (column '%s' has character set '%s').  Replication of non-ASCII text data may be incorrect."),
    140: (message.INFO,
          "Bugzilla table '%s' has character set '%s'."),
    141: (message.INFO,
          "Bugzilla column '%s' has character set '%s'."),


    # 2.2. Messages from check_config.py (200-299)

    200: (message.CRIT, "Configuration parameter '%s' must be 0 or 1."),
    201: (message.CRIT, "Configuration parameter '%s' (value '%s') is not a valid date.  The right format is 'YYYY-MM-DD HH:MM:SS'."),
    202: (message.CRIT, "Configuration parameter '%s' (value '%s') is not a valid e-mail address."),
    203: (message.CRIT, "Configuration parameter '%s' must be a function."),
    204: (message.CRIT, "Configuration parameter '%s' must be an integer."),
    205: (message.CRIT, "Configuration parameter '%s' must be a list."),
    206: (message.CRIT, "Configuration parameter '%s' must be a list of %s."),
    207: (message.CRIT, "Configuration parameter '%s' must be a string."),
    208: (message.CRIT, "Configuration parameter '%s' must be None or a string."),
    209: (message.CRIT, "Configuration parameter '%s' (value '%s') must be from 1 to 32 characters long, start with a letter or number, and consist of letters, numbers and underscores only."),
    210: (message.CRIT, "Configuration parameter '%s' (value '%s') must contain exactly one %%d format specifier, any number of doubled percents, but no other format specifiers."),
    211: (message.CRIT, "Configuration parameter '%s' (value '%s') must contain exactly one %%s format specifier, any number of doubled percents, but no other format specifiers."),
    212: (message.CRIT, "Configuration parameter '%s' must be a list of pairs of strings."),


    # 2.3. Messages from configure_bugzilla.py (300-399)

    300: (message.CRIT, "Two Bugzilla states '%s' and '%s' map to the same Perforce state '%s'."),
    301: (message.CRIT, "You specified the closed_state '%s', but there's no such Bugzilla state."),
    302: (message.CRIT, "The '%s' column of Bugzilla's 'bugs' table is not an enum type."),
    303: (message.CRIT, "Configuration parameter 'bugzilla_directory' does not name a directory."),
    304: (message.CRIT, "Configuration parameter 'bugzilla_directory' does not name a directory containing a mail-processing script."),
    305: (message.CRIT, "Bugzilla's table 'profiles' does not have a 'login_name' column."),
    306: (message.CRIT, "The 'login_name' column of Bugzilla's 'profiles' table does not have a 'text' type."),
    307: (message.CRIT, "Bugzilla's table 'bugs' does not have a '%s' column."),
    308: (message.CRIT, "The 'bug_status' column of Bugzilla's 'bugs' table is not an enum type."),
    309: (message.CRIT, "The 'resolution' column of Bugzilla's 'bugs' table is not an enum type."),
    310: (message.CRIT, "The 'resolution' column of Bugzilla's 'bugs' table does not have a 'FIXED' value."),
    311: (message.CRIT, "Field '%s' specified in 'replicated_fields' is a system field: leave it out!"),
    312: (message.CRIT, "Field '%s' appears twice in 'replicated_fields'."),
    313: (message.NOT_USED, "Field '%s' specified in 'replicated_fields' list not in Bugzilla 'bugs' table."),
    314: (message.CRIT, "Field '%s' specified in 'replicated_fields' list has type '%s': this is not yet supported by P4DTI."),
    315: (message.CRIT, "Field '%s' specified in 'replicated_fields' list has floating-point type: this is not yet supported by P4DTI."),
    316: (message.CRIT, "You can't have a field called 'code' in the Perforce jobspec."),
    317: (message.CRIT, "Too many fields to replicate: Perforce jobs can contain only 99 fields."),
    318: (message.NOT_USED, "Jobspec fields '%s' and '%s' have the same number %d."),
    319: (message.CRIT, "Field '%s' specified in 'omitted_fields' is not a system field: leave it out!"),
    320: (message.CRIT, "Field '%s' appears twice in 'omitted_fields'."),
    321: (message.CRIT, "Field '%s' in 'field_names' is not a replicated field."),
    322: (message.CRIT, "Bugzilla field '%s' appears twice in 'field_names'."),
    323: (message.CRIT, "Perforce field '%s' appears twice in 'field_names'."),
    324: (message.CRIT, "Bugzilla fields '%s' and '%s' both map to Perforce field '%s'."),


    # 2.4. Messages from configure_teamtrack.py (400-499)
    # That module has been removed, so all these messages are now NOT_USED.

    400: (message.NOT_USED, "Two TeamTrack states '%s' and '%s' map to the same Perforce state '%s'."),
    401: (message.NOT_USED, "You specified the closed_state '%s', but there's no such TeamTrack state."),
    402: (message.NOT_USED, "Couldn't get descriptions for TeamTrack system fields STATE, OWNER, and TITLE."),
    403: (message.NOT_USED, "Field '%s' specified in 'replicated_fields' list not in TeamTrack FIELDS table."),
    404: (message.NOT_USED, "Field '%s' specified in 'replicated_fields' list is a system field: leave it out!"),
    405: (message.NOT_USED, "Field '%s' appears twice in 'replicated_fields'."),
    406: (message.NOT_USED, "Field '%s' has type %d: this is not supported by P4DTI."),
    407: (message.NOT_USED, "You can't have a field called 'code' in the Perforce jobspec."),
    408: (message.NOT_USED, "Too many fields to replicate: Perforce jobs can contain only 99 fields."),


    # 2.5. Messages from dt_bugzilla.py (500-599)

    500: (message.NOT_USED, "User %d isn't in the right bug group to edit bug %d."),
    501: (message.ERR, "User %d doesn't have permission to change field '%s' of bug %d to %s."),
    502: (message.ERR, "The P4DTI does not support marking bugs as DUPLICATE from Perforce."),
    503: (message.ERR, "Bugzilla does not allow a transition from status '%s' to '%s'."),
    504: (message.ERR, "Cannot change Bugzilla field '%s'."),
    505: (message.ERR, "Can only append to Bugzilla field '%s'."),
    506: (message.ERR, "Updating non-existent Bugzilla field '%s'."),
    507: (message.NOT_USED, "Bugzilla does not have a group called '%s'."),
    508: (message.NOT_USED, "Bugzilla's fielddefs table does not include '%s'."),
    509: (message.ERR, "No Perforce status corresponding to Bugzilla status '%s'."),
    510: (message.ERR, "No Bugzilla status corresponding to Perforce status '%s'."),
    511: (message.ERR, "Perforce field value '%s' could not be translated to a number for replication to Bugzilla."),
    512: (message.ERR, "Bugzilla P4DTI user '%s' has e-mail address matching Perforce user '%s', not Perforce P4DTI user '%s'."),
    513: (message.ERR, "Bugzilla P4DTI user '%s' is not a known Bugzilla user."),
    514: (message.ERR, "There is no Bugzilla user corresponding to Perforce user '%s'."),
    515: (message.NOTICE, "A user field containing one of these users will be translated to the user's e-mail address in the corresponding Perforce job field."),
    516: (message.NOTICE, "It will not be possible to use Perforce to assign bugs to these users.  Changes to jobs made by these users will be ascribed in Bugzilla to the replicator user <%s>."),
    517: (message.ERR, "Can't create Bugzilla bug without short_desc field."),
    518: (message.ERR, "Can't create Bugzilla bug with empty short_desc field."),
    519: (message.ERR, "Can't create Bugzilla bug without product field."),
    520: (message.ERR, "Can't create Bugzilla bug for non-existent product '%s'."),
    521: (message.ERR, "Can't create Bugzilla bug for product '%s' with no components."),
    522: (message.ERR, "Can't create Bugzilla bug without component field."),
    523: (message.ERR, "Can't create Bugzilla bug: product '%s' has no component '%s'."),
    524: (message.ERR, "Can't create Bugzilla bug for product '%s' with no versions."),
    525: (message.ERR, "Can't create Bugzilla bug without version field."),
    526: (message.ERR,  "Can't create Bugzilla bug: product '%s' has no version '%s'."),
    527: (message.NOTICE, "User '%s' isn't in Bugzilla group '%s' required to make bug for product '%s'; creating bug anyway."),
    528: (message.ERR, "Can't create Bugzilla bug with invalid group '%s'."),
    529: (message.NOTICE, "User '%s' doesn't have permissions to create Bugzilla bug for product '%s' with status '%s'; creating bug anyway."),
    530: (message.ERR, "Can't create Bugzilla bug with bug_status '%s' and no resolution."),
    531: (message.ERR, "Can't create Bugzilla bug with field '%s'."),
    532: (message.ERR, "Can't create Bugzilla bug without reporter field."),
    533: (message.NOTICE, "Perforce user '%s <%s>' already exists in Bugzilla as user %d."),
    534: (message.NOTICE, "Perforce user '%s <%s>' added to Bugzilla as user %d."),
    535: (message.ERR, "'%s' not a Bugzilla group."),
    536: (message.NOTICE, "These Perforce users have duplicate e-mail addresses.  They may have been matched with the wrong Bugzilla user."),
    537: (message.ERR, "User %d is disabled, so cannot edit bug %d."),
    538: (message.ERR, "User 0 cannot edit bug %d."),
    539: (message.ERR, "Can't create Bugzilla bug with reporter 0."),
    540: (message.ERR, "Can't change Bugzilla field '%s' to 0."),
    541: (message.DEBUG, "Perforce users '%s' and '%s' both have email address '%s' (when converted to lower case)."),
    542: (message.ERR, "Perforce P4DTI user '%s' is not a known Perforce user."),
    543: (message.ERR, "Perforce P4DTI user '%s' has the same e-mail address '%s' as these other Perforce users: %s."),
    544: (message.DEBUG, "Bugzilla users '%s' and '%s' both have email address '%s' (when converted to lower case)."),
    545: (message.ERR, "Bugzilla P4DTI user e-mail address '%s' belongs to several Bugzilla users: %s."),
    546: (message.DEBUG, "Bugzilla user '%s' (e-mail address '%s') not matched to any Perforce user, because Perforce user '%s' already matched to Bugzilla user %d."),
    547: (message.DEBUG, "Bugzilla user %d matched to Perforce user '%s' by e-mail address '%s'."),
    548: (message.DEBUG, "Bugzilla user '%s' (e-mail address '%s') not matched to any Perforce user."),
    549: (message.DEBUG, "Perforce user '%s' (e-mail address '%s') not matched to any Bugzilla user."),
    550: (message.ERR, "Bugzilla P4DTI user '%s' does not have a matching Perforce user.  It should match the Perforce user '%s' but that matches the Bugzilla user %d (e-mail address '%s')."),
    551: (message.ERR, "Bugzilla P4DTI user '%s' does not have a matching Perforce user.  It should match the Perforce user '%s' (which has e-mail address '%s')."),
    552: (message.NOTICE, "These Bugzilla users have duplicate e-mail addresses (when converted to lower case).  They may have been matched with the wrong Perforce user."),
    553: (message.NOTICE, "Perforce replicator user <%s> already exists in Bugzilla as user %d."),
    554: (message.NOTICE, "Perforce replicator user <%s> added to Bugzilla as user %d."),
    555: (message.ERR, "User %d must be in group '%s' to edit bug %d."),
    556: (message.ERR, "User %d must be in group '%s' to edit bug %d in product '%s'."),

    # 2.6. Messages from dt_teamtrack.py (600-699)
    # That module has been removed, so all these messages are now NOT_USED.

    600: (message.NOT_USED, "-- Transition: %d; User: %s."),
    601: (message.NOT_USED, "Installing field '%s' in the TS_CASES table."),
    602: (message.NOT_USED, "Partially installed the new fields in the TS_CASES table. Previous installation was not up to date."),
    603: (message.NOT_USED, "Installed all new fields in the TS_CASES table."),
    604: (message.NOT_USED, "Put '%s' parameter in replicator configuration with value '%s'."),
    605: (message.NOT_USED, "Updated '%s' parameter in replicator configuration to have value '%s'."),
    606: (message.NOT_USED, "Reading table %s."),
    607: (message.NOT_USED, "Warning: table '%s' has two entries called '%s'."),
    608: (message.NOT_USED, "Reading FIELDS and SELECTIONS tables."),
    609: (message.NOT_USED, "Reading PROJECTS and STATES tables."),
    610: (message.NOT_USED, "Reading PROJECTS table to discover available transitions."),
    611: (message.NOT_USED, "Reading SELECTIONS table to find type prefixes."),
    612: (message.NOT_USED, "Reading USERS table."),
    613: (message.NOT_USED, "Matched TeamTrack user '%s' with Perforce user '%s' by e-mail address '%s'."),
    614: (message.NOT_USED, "No transition from state '%s' to state '%s'."),
    615: (message.NOT_USED, "No login id in TeamTrack's USERS table corresponding to replicator's login id '%s'."),
    616: (message.NOT_USED, "No LAST_CHANGE record for this replicator."),
    617: (message.NOT_USED, "TeamTrack database version %d is not supported by the P4DTI.  The minimum supported version is %d."),
    618: (message.NOT_USED, "Incorrect date in Perforce: '%s' is not in the format 'YYYY/mm/dd HH:MM:SS'."),
    619: (message.NOT_USED, "Incorrect time in Perforce: '%s' is not in the format 'H:MM:SS'."),
    620: (message.NOT_USED, "No such table: %s."),
    621: (message.NOT_USED, "No TeamTrack entity in table '%s' with id %d."),
    622: (message.NOT_USED, "No TeamTrack entity in table '%s' with name '%s'."),
    623: (message.NOT_USED, "No TeamTrack selection name for selection id '%d'."),
    624: (message.NOT_USED, "No TeamTrack selection for field '%s' corresponding to Perforce selection '%s'."),
    625: (message.NOT_USED, "No Perforce state corresponding to TeamTrack state '%s'."),
    626: (message.NOT_USED, "No state name for TeamTrack state %d."),
    627: (message.NOT_USED, "Perforce state '%s' is unknown."),
    628: (message.NOT_USED, "No TeamTrack state in project '%s' corresponding to Perforce state '%s'."),
    629: (message.NOT_USED, "These TeamTrack users will appear as themselves in Perforce even though there is no such Perforce user."),
    630: (message.NOT_USED, "These Perforce users will appear in TeamTrack as the user (None).  It will not be possible to assign issues to these users."),
    631: (message.NOT_USED, "TeamTrack query: SELECT * FROM %s WHERE %s."),
    632: (message.NOT_USED, "TeamTrack query: SELECT * FROM %s."),
    633: (message.NOT_USED, "The TeamTrack field %s is append-only: you're not allowed to edit previous comments."),
    634: (message.NOT_USED, "Matched TeamTrack user '%s' with Perforce user '%s' by userid."),
    635: (message.NOT_USED, "Two TeamTrack users ('%s' and '%s') have the same e-mail address '%s'."),
    636: (message.NOT_USED, "These TeamTrack users have duplicate e-mail addresses.  They may have been matched with the wrong Perforce user."),
    637: (message.NOT_USED, "These Perforce users have duplicate e-mail addresses.  They may have been matched with the wrong TeamTrack user."),
    638: (message.NOT_USED, "Perforce user '%s <%s>' already maps to TeamTrack as user '%s'."),
    639: (message.NOT_USED, "Perforce user '%s <%s>' added to TeamTrack as user '%s'."),
    640: (message.NOT_USED, "Can't submit new issue to TeamTrack: SUBMITTER %d is unknown."),
    641: (message.NOT_USED, "Submitted new issue to TeamTrack with issue id %05d, but couldn't find it in the database."),
    642: (message.NOT_USED, "No TeamTrack state corresponding to Perforce state '%s'."),


    # 2.7. Messages from p4.py (700-799)

    700: (message.DEBUG, "Perforce input: '%s'."),
    701: (message.DEBUG, "Perforce command: '%s'."),
    702: (message.DEBUG, "Perforce status: '%s'."),
    703: (message.DEBUG, "Perforce results: '%s'."),
    704: (message.ERR, "Perforce client changelevel %d is not supported by P4DTI.  Client must be at changelevel %d or above."),
    705: (message.ERR, "The command '%s' didn't report a recognizable version number.  Check your setting for the 'p4_client_executable' parameter."),
    706: (message.ERR, "%s  The Perforce client exited with error code %d."),
    707: (message.ERR, "The Perforce client exited with error code %d.  The server might be down; the server address might be incorrect; or your Perforce license might have expired."),
    708: (message.ERR, "%s"),
    709: (message.NOT_USED, "The Perforce interface does not support the operating system '%s'."),
    710: (message.CRIT, "Jobspec fields '%s' and '%s' have the same number %d."),
    711: (message.DEBUG, "Decoded jobspec as comment '%s' and fields %s."),
    712: (message.DEBUG, "Installing jobspec from comment '%s' and fields %s."),
    713: (message.WARNING, "Jobspec does not have required P4DTI field '%s'."),
    714: (message.WARNING, "Jobspec P4DTI field '%s' has incorrect attribute '%s': '%s' (should be '%s')."),
    715: (message.ERR, "Jobspec does not support P4DTI."),
    716: (message.WARNING, "Jobspec does not have field '%s'."),
    717: (message.ERR, "Current jobspec cannot be used for replication."),
    718: (message.WARNING, "The jobspec does not allow values '%s' in field '%s', so these values cannot be replicated from the defect tracker."),
    719: (message.WARNING, "The jobspec does not allow value '%s' in field '%s', so this value cannot be replicated from the defect tracker."),
    720: (message.WARNING, "Field '%s' in the jobspec allows values '%s', which cannot be replicated to the defect tracker."),
    721: (message.WARNING, "Field '%s' in the jobspec allows value '%s', which cannot be replicated to the defect tracker."),
    722: (message.WARNING, "Jobspec field '%s' has a more restrictive datatype ('%s' not '%s') which may cause problems replicating this field from the defect tracker."),
    723: (message.WARNING, "Jobspec field '%s' has a less restrictive datatype ('%s' not '%s') which may cause problems replicating this field to the defect tracker."),
    724: (message.WARNING, "Field '%s' in the jobspec should be a '%s' field, not '%s'.  This field cannot be replicated to or from the defect tracker."),
    725: (message.WARNING, "Field '%s' in the jobspec should have persistence '%s', not '%s'.  There may be problems replicating this field to or from the defect tracker."),
    726: (message.WARNING, "Perforce job field '%s' will not be replicated to the defect tracker."),
    727: (message.WARNING, "Forcing replacement of field '%s' in jobspec."),
    728: (message.INFO, "Retaining field '%s' in jobspec despite change."),
    729: (message.INFO, "Adding field '%s' to jobspec."),
    730: (message.ERR, "Too many fields in jobspec."),
    731: (message.WARNING, "Jobspec field '%s' has unknown datatype '%s' which may cause problems when replicating this field."),
    732: (message.INFO, "Retaining unknown field '%s' in jobspec."),
    733: (message.INFO, "No change to field '%s' in jobspec."),
    734: (message.INFO, "Perforce message '%s'.  Switching Unicode mode %s to retry."),
    735: (message.NOT_USED,  "Perforce message '%s'.  Reverting to Unicode mode %s."),
    736: (message.ERR,  "Perforce message '%s'.  Is P4CHARSET set with a non-Unicode server? Reverting to Unicode mode %s."),



    # 2.8. Messages from replicator.py (800-999)

    800: (message.INFO, "Mailing '%s'."),
    802: (message.INFO, "Replicated changelist %d."),
    803: (message.INFO, "Set up issue '%s' to replicate to job '%s'."),
    804: (message.INFO, "Replicating issue '%s' to job '%s'."),
    805: (message.INFO, "Replicating job '%s' to issue '%s'."),
    806: (message.NOTICE, "Issue '%s' and job '%s' have both changed.  Consulting conflict resolution policy."),
    807: (message.INFO, "Conflict resolution policy decided: no action."),
    808: (message.NOT_USED, "Job '%s' could not be replicated to issue '%s': %s: %s"),
    810: (message.NOTICE, "Overwrite issue '%s' with job '%s'."),
    811: (message.NOTICE, "Overwrite job '%s' with issue '%s'."),
    812: (message.INFO, "-- Changed fields: %s."),
    813: (message.INFO, "-- No issue fields were replicated."),
    814: (message.INFO, "-- Filespecs changed to '%s'."),
    815: (message.INFO, "-- Deleted fix for change %s."),
    816: (message.INFO, "-- Added fix for change %d with status %s."),
    817: (message.INFO, "-- Fix for change %d updated to status %s."),
    818: (message.INFO, "-- Deleted fix for change %d."),
    819: (message.DEBUG, "-- Considering Perforce fix %s."),
    820: (message.INFO, "-- Added fix for change %s with status %s."),
    821: (message.INFO, "-- Fix for change %s updated to status %s."),
    822: (message.INFO, "-- Deleted filespec %s."),
    823: (message.INFO, "-- Added filespec %s."),
    824: (message.INFO, "-- Changed fields: %s."),
    825: (message.INFO, "-- No job fields were replicated."),
    826: (message.INFO, "-- Defect tracker made changes as a result of the update: %s."),
    827: (message.NOT_USED, "Checking changelists to see if they need replicating..."),
    828: (message.NOT_USED, "-- %d changelists to check."),
    829: (message.NOT_USED, "The replicator failed to poll successfully: %s: %s"),
    830: (message.NOT_USED, "The replicator identifier must consist of letters, numbers and underscores only: '%s' is not allowed."),
    831: (message.NOT_USED, "The Perforce server identifier must consist of letters, numbers and underscores only: '%s' is not allowed."),
    832: (message.NOT_USED, "The replicator identifier must consist of letters, numbers and underscores only: '%s' is not allowed."),
    833: (message.CRIT, "The replicator's RID ('%s') doesn't match the defect tracker's RID ('%s')."),
    834: (message.CRIT, "The Perforce server changelevel %d is not supported by the P4DTI.  See the P4DTI release notes for Perforce server versions supported by the P4DTI."),
    835: (message.CRIT, "The Perforce command 'p4 info' didn't report a recognisable version."),
    836: (message.NOT_USED, "P4DTI fields not found in Perforce jobspec."),
    837: (message.ERR, "Expected a job but found %s."),
    838: (message.ERR, "Asked for job '%s' but got job '%s'."),
    839: (message.ERR, "P4DTI-filespecs field has value '%s': this should end in a newline."),
    840: (message.ERR, "Issue '%s' not found."),
    841: (message.NOTICE, "Defect tracker issue '%s' and Perforce job '%s' have both changed since the last time the replicator polled the databases.  The replicator's conflict resolution policy decided to overwrite the job with the issue."),
    842: (message.NOTICE, "Defect tracker issue '%s' and Perforce job '%s' have both changed since the last time the replicator polled the databases.  The replicator's conflict resolution policy decided to overwrite the issue with the job."),
    844: (message.NOT_USED, "1 issue has changed."),
    845: (message.NOT_USED, "%d issues have changed."),
    846: (message.NOT_USED, "1 job has changed."),
    847: (message.NOT_USED, "%d jobs have changed."),
    848: (message.NOTICE, "Job '%s' could not be replicated to issue '%s'."),
    849: (message.NOT_USED, "The replicator failed to replicate Perforce job '%s' to defect tracker issue '%s'.  There was no error message.  See the Python traceback below for more details about the error."),
    850: (message.NOT_USED, "There was no error message from TeamTrack.  The most likely reasons for this problem are: you don't have permission to update the issue; the job contained data that was invalid in TeamTrack; or the job was missing a field that is required in TeamTrack."),
    851: (message.NOTICE, "The replicator failed to replicate Perforce job '%s' to defect tracker issue '%s', because of the following problem:"),
    852: (message.NOTICE, "Here's a full Python traceback:"),
    853: (message.NOTICE, "If you are having continued problems, please contact your P4DTI administrator <%s>."),
    854: (message.NOTICE, "The replicator failed to replicate Perforce job '%s' to defect tracker issue '%s' because of this problem:"),
    855: (message.NOTICE, "The replicator attempted to restore the job to a copy of the issue, but this failed too, because of the following problem:"),
    856: (message.NOTICE, "The replicator has now given up."),
    857: (message.NOTICE, "Issue '%s' overwritten by job '%s'."),
    858: (message.NOTICE, "The replicator has therefore overwritten defect tracker issue '%s' with Perforce job '%s'."),
    859: (message.NOTICE, "The defect tracker issue looked like this before being overwritten:"),
    860: (message.NOTICE, "Job '%s' overwritten by issue '%s'."),
    861: (message.NOTICE, "The replicator has therefore overwritten Perforce job '%s' with defect tracker issue '%s'.  See section 2.2 of the P4DTI User Guide for more information."),
    862: (message.NOTICE, "The job looked like this before being overwritten:"),
    863: (message.NOTICE, "The replicator failed to poll successfully."),
    864: (message.NOTICE, "The replicator failed to poll successfully, because of the following problem:"),
    865: (message.INFO, "This is an automatically generated e-mail from the Perforce Defect Tracking Integration replicator '%s'."),
    866: (message.INFO, "The P4DTI replicator has started."),
    867: (message.NOTICE, "The following Perforce users do not correspond to defect tracker users.  The correspondence is based on the e-mail addresses in the defect tracker and Perforce user records."),
    868: (message.INFO, "User"),
    869: (message.INFO, "E-mail address"),
    870: (message.INFO, "The following defect tracker users do not correspond to Perforce users.  The correspondence is based on the e-mail addresses in the defect tracker and Perforce user records."),
    871: (message.INFO, "Checking consistency for replicator '%s'."),
    872: (message.ERR, "Issue '%s' should be replicated but is not."),
    873: (message.ERR, "Issue '%s' should be replicated to job '%s' but that job either does not exist or is not replicated."),
    874: (message.ERR, "Issue '%s' is replicated to job '%s' but that job is replicated to issue '%s'."),
    875: (message.ERR, "Job '%s' would need the following set of changes in order to match issue '%s': %s."),
    876: (message.ERR, "Job '%s' has associated filespec '%s' but there is no corresponding filespec for issue '%s'."),
    877: (message.ERR, "Issue '%s' has associated filespec '%s' but there is no corresponding filespec for job '%s'."),
    878: (message.ERR, "Change %s fixes job '%s' but there is no corresponding fix for issue '%s'."),
    879: (message.ERR, "Change %d fixes issue '%s' but there is no corresponding fix for job '%s'."),
    880: (message.ERR, "Change %s fixes job '%s' with status '%s', but change %d fixes issue '%s' with status '%s'."),
    881: (message.ERR, "Job '%s' is marked as being replicated to issue '%s' but that issue is being replicated to job '%s'."),
    882: (message.ERR, "Job '%s' is marked as being replicated to issue '%s' but that issue either doesn't exist or is not being replicated by this replicator."),
    883: (message.INFO, "Consistency check completed.  1 issue checked."),
    884: (message.INFO, "Consistency check completed.  %d issues checked."),
    885: (message.INFO, "Looks all right to me."),
    886: (message.ERR, "1 inconsistency found."),
    887: (message.ERR, "%d inconsistencies found."),
    888: (message.ERR, "Asked for issue '%s' but got an error instead."),
    889: (message.ERR, "Job '%s' has a date field in the wrong format: %s."),
    890: (message.INFO, "Checking issue '%s' against job '%s'."),
    891: (message.ERR, "Error (%s): %s"),
    892: (message.INFO, "Migrated job '%s' to issue '%s'."),
    893: (message.NOT_USED, "Installed post-migration jobspec."),
    894: (message.INFO, "Post-migration replication of issue '%s' to job '%s'."),
    895: (message.INFO, "Migration completed."),
    896: (message.ERR, "Perforce has a job called 'new', which is illegal and will stop the P4DTI from working."),
    897: (message.ERR, "Expected Perforce output of 'job -i' to say 'Job jobname ...', but found '%s'."),
    898: (message.ERR, "Unexpected output from Perforce command 'job -i': %s."),
    899: (message.ERR, "Tried to update job '%s', but Perforce replied '%s'."),
    900: (message.NOT_USED, "Issue '%s' is marked as being replicated to job '%s' but that job is marked as not being replicated (P4DTI-rid = None)."),
    901: (message.NOT_USED, "Migration failed."),
    902: (message.NOT_USED, "Here's a full Python traceback:\n%s"),
    903: (message.NOT_USED, "It looks as if migration has already been run (the P4 jobspec has P4DTI fields).  Please revert the Perforce and defect tracker databases before attempting to run migration again.  A future P4DTI release will have a migration script which will handle this better."),
    904: (message.ERR, "Replicated issue '%s' to Perforce, but didn't get a jobname for it (the 'Job' field is still 'new')."),
    905: (message.CRIT, "Defect tracker '%s' does not support migration of Perforce jobs."),
    906: (message.CRIT, "Defect tracker '%s' does not support migration of Perforce users."),
    907: (message.NOT_USED, "Your configuration doesn't support migration.  These parameters need values: %s."),
    908: (message.NOTICE, "Job '%s' could not be replicated to the defect tracker."),
    909: (message.NOTICE, "The replicator failed to replicate Perforce job '%s' to the defect tracker, because of the following problem:"),
    910: (message.INFO, "%s"),
    911: (message.DEBUG, "Poll starting."),
    912: (message.DEBUG, "Poll finished."),
    913: (message.ERR, "Error in P4DTI logger: %s"),
    914: (message.CRIT, "You must delete your Perforce jobs before running the P4DTI for the first time.  See section 5.2.3 of the Administrator's Guide."),
    915: (message.DEBUG, "Before translating jobspec, job '%s' is %s"),
    916: (message.DEBUG, "Not migrating job '%s' (already replicated)."),
    917: (message.DEBUG, "Not migrating job '%s' (migrate_p returned 0)."),
    918: (message.DEBUG, "After translating jobspec, job '%s' is %s"),
    919: (message.DEBUG, "Raw issue: %s"),
    920: (message.DEBUG, "Prepared issue: %s"),
    921: (message.INFO, "Migrating job '%s'..."),
    922: (message.INFO, "Translating issue field '%s' (value '%s') to job field '%s'..."),
    923: (message.INFO, "Translating job field '%s' (value '%s') to issue field '%s'..."),
    924: (message.ERR, "Expected translate_jobspec to return a dictionary, but instead it returned %s."),
    925: (message.INFO, "Job owner"),
    926: (message.INFO, "Job changer"),
    927: (message.WARNING, "Can't use Perforce client %s."),
    928: (message.WARNING, "Attempting to make working Perforce client %s."),

    # 2.9. Messages from init.py, check.py, check_jobs.py, run.py,
    # refresh.py, mysqldb_support.py, service.py, portable.py,
    # logger.py (1000-1099)

    1000: (message.NOT_USED, "The defect tracker '%s' is not supported."),
    1001: (message.NOT_USED, "You must delete your Perforce jobs before running the P4DTI for the first time.  See section 5.2.3 of the Administrator's Guide."),
    1002: (message.NOTICE, "WARNING!  This script will update all jobs in Perforce.  Please use it according to the instructions in section 9.2 of the P4DTI Administrator's Guide.  Are you sure you want to go ahead?"),
    1003: (message.NOT_USED, "TeamTrack version %s is not supported by the P4DTI."),
    1004: (message.NOT_USED, "The configuration module '%s' could not be imported."),
    1005: (message.CRIT, "MySQLdb version '%s' (release '%s') detected.  This release is incompatible with the P4DTI."),
    1006: (message.WARNING, "MySQLdb version '%s' (release '%s') detected.  This release is not supported by the P4DTI, but may work."),
    1007: (message.INFO, "MySQLdb version '%s' (release '%s') detected.  This release is supported by the P4DTI."),
    1008: (message.ERR, "Job '%s' doesn't match the jobspec:"),
    1009: (message.INFO, "All jobs match the jobspec."),
    1010: (message.CRIT, "Fatal error in P4DTI service: %s."),
    1011: (message.INFO, "The P4DTI service has started."),
    1012: (message.INFO, "The P4DTI service has halted."),
    1013: (message.INFO, "Installing service to start automatically..."),
    1014: (message.INFO, "Ensuring service is stopped first..."),
    1015: (message.INFO, "OK (can ignore that error). Proceed with the remove..."),
    1016: (message.NOT_USED, "Error in P4DTI logger: %s"),
    1017: (message.ERR, "An attempt to write a log message to standard output failed."),
    1018: (message.ERR, "An attempt to write a log message to %s failed."),
    1019: (message.ERR, "An attempt to write a log message to the system log failed."),
    1020: (message.ERR, "An attempt to write a log message to the NT event log failed."),
    1021: (message.CRIT, "The P4DTI does not support the operating system '%s'."),
    1022: (message.WARNING, "MySQLdb version '%s' (release '%s') detected.  This release is supported by the P4DTI, but deprecated.  Future versions of the P4DTI may not support this release."),
    1023: (message.WARNING, "MySQLdb version '%s' (release '%s') detected. This old release is not supported by the P4DTI, and may not provide functions on which the P4DTI relies."),
    1024: (message.WARNING, "MySQLdb version '%s' (release '%s') detected.  This release is supported by the P4DTI, but deprecated.  Operation with Unicode text may be incorrect.  Future versions of the P4DTI may not support this release."),
    
    # 2.10. Messages from teamtrack_query.py (1100-1199)
    # That module has been removed, so all these messages are now NOT_USED.

    1100: (message.NOT_USED, "Usage:\n\n  python teamtrack_query.py\n\tPrint usage and list of tables.\n\n  python teamtrack_query.py [options] TABLE [FIELD1 FIELD2 ...]\n\tShow contents of TABLE.\n\tSpecify optional FIELDs to restrict the output.\n\nOptions:\n  -q QUERY\tRestrict output to records matching QUERY.\n  -r\t\tFormat output as series of records.\n  -t\t\tFormat output as table.\n\nTABLE should be one of %s."),
    1101: (message.NOT_USED, "Table '%s' not recognized."),
    1102: (message.NOT_USED, "Table '%s' has no field named '%s'."),
    1103: (message.NOT_USED, "Unknown option: '%s'."),

    }


# 3. A P4DTI MESSAGE FACTORY
#
# We define 'factory', a message factory for the P4DTI and 'msg()', a function
# to get messages from it.

factory = message.catalog_factory(p4dti_en_catalog, "P4DTI")

def msg(id, args = ()):
    return factory.new(id, args)


# A. REFERENCES
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Richard Brooksby; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
# [ISO 639] "Code for the representation of names of languages"; ISO;
# 1988-04-01.
#
#
# B. DOCUMENT HISTORY
#
# 2001-03-12 GDR Created.
#
# 2001-03-14 GDR Added consistency checking messages from replicator.py.
#
# 2001-03-15 GDR Added messages from init.py.
#
# 2001-03-25 RB  Added 889 due to merge from version 1.0 sources.
#
# 2001-04-10 NB  Added 118 due to merge from version 1.0 sources.
#
# 2001-05-09 NB  Added a number of messages to dt_bugzilla.py for adding issues.
#
# 2001-05-15 GDR Added 631, set 844 to 847 to NOT_USED, since cursor
# implementation means we don't get this information.
#
# 2001-05-18 GDR Added 632.  Improved 606, 631, 888.  Set 606, 608-612
# to NOT_USED since we use 631 and 632 to log this information.
#
# 2001-06-14 GDR Added 891.
#
# 2001-06-22 NB Moved message 318 to 710 (configure_bugzilla.py to p4.py).
#
# 2001-06-25 NB Changed jobspec error message to reflect new usage.
#
# 2001-06-25 NB Added 896, 897, 898, 899, 900.
#
# 2001-06-29 NB Added 901, 902, 903, 711, 712.
#
# 2001-07-03 GDR Added 1003.
#
# 2001-07-09 NB Added 211.
#
# 2001-07-16 NB Message 118 not used.  Added 119-122 to support schema
# upgrades and replication since start date.
#
# 2001-07-17 GDR Error messages that only appear in e-mail messages get
# priority NOTICE.
#
# 2001-09-10 NB Modified message 105.  See job000262.
#
# 2001-09-25 GDR Message 126 not used.  See job000393.
#
# 2001-10-01 GDR Added 633.
#
# 2001-10-02 GDR Added 634, 635, 636, 637.
#
# 2001-10-18 GDR Improved error messages for bad dates and times.
#
# 2001-10-23 GDR Added 904, 905, 906, 907.
#
# 2001-10-25 NB Added 1005, 1006, 1007.
#
# 2001-10-25 GDR Added 638, 639, 640.
#
# 2001-10-29 GDR Added 908, 909.
#
# 2001-11-01 NB Fix 500, add 537.
#
# 2001-11-06 GDR Added 641.
#
# 2001-11-07 GDR Added 1008, 1009.
#
# 2001-11-07 NDL Added 1010.
#
# 2001-11-09 NDL Added 911, 912, 1011, 1012.
#
# 2001-11-14 GDR Added 1100-1103.
#
# 2001-11-19 NDL Added 1013-1015.
#
# 2001-11-20 NDL Added 1016-1020.  Made 891 more general.
#
# 2001-11-20 GDR Renumbered 1016->913, 1001->914.
#
# 2001-11-21 GDR Better text for 1006.  893 and 903 are not used.
#
# 2001-11-26 GDR Added 642, 915-920.
#
# 2001-11-26 NDL Added 129, 130.
#
# 2001-11-29 GDR Added 128, 921-924.
#
# 2001-12-04 GDR Rephrased 905, 906.  827, 828, 907 no longer used.
#
# 2002-02-01 GDR Added 925, 926.
#
# 2002-04-03 NB Added 538, 539, 540 (job000494).
#
# 2002-06-14 NB Added 541 to 552.
#
# 2003-05-21 NB Make all TeamTrack messages NOT_USED.  Also reformat a
# comment for line length.
#
# 2003-05-23 NB Added 553, 554.
#
# 2003-05-30 NB Add 927, 928.
#
# 2003-09-17 NB Moved 709 to 1021.
#
# 2003-09-24 NB Added 131 and 132.
#
# 2003-11-25 NB Added 212.
#
# 2003-12-05 NB Added 713, 714, 715.
#
# 2003-12-10 NB Add 716 to 726.
#
# 2003-12-12 NB Add 727 to 733; make 836 NOT_USED.
#
# 2004-05-28 NB Bugzilla 2.17.7 support (added 555, 556; removed 500,
# 507; changed 128, 304, 527-529).
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/catalog.py#5 $
