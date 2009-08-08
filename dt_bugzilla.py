#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#        DT_BUGZILLA.PY -- DEFECT TRACKER INTERFACE (BUGZILLA)
#
#             Nick Barnes, Ravenbrook Limited, 2000-11-21
#
#
# 1. INTRODUCTION
#
# This Python module implements an interface between the P4DTI
# replicator and the Bugzilla defect tracker [Requirements, 18], by
# defining the classes listed in [GDR 2000-10-16, 7].  In particular, it
# defines the following classes:
#
# [3] bugzilla_bug(dt_interface.defect_tracker_issue) [GDR 2000-10-16,
# 7.2]
#
# [4] bugzilla_fix(dt_interface.defect_tracker_fix) [GDR 2000-10-16,
# 7.3]
#
# [5] bugzilla_filespec(dt_interface.defect_tracker_filespec) [GDR
# 2000-10-16, 7.4].
#
# [6] dt_bugzilla(dt_interface.defect_tracker) [GDR 2000-10-16, 7.1].
#
# [7] Translators [GDR 2000-10-16, 7.5] for dates [GDR 2000-10-16,
# 7.5.1], elapsed times, foreign keys, single select fields, states [GDR
# 2000-10-16, 7.5.2], multi-line text fields [GDR 2000-10-16, 7.5.3] and
# users [GDR 2000-10-16, 7.5.4].
#
# This module accesses the Bugzilla database using the Python interface
# to Bugzilla [NB 2000-11-14c] and accesses and stores data according to
# the Bugzilla database schema [NB 2000-11-14a] and the Bugzilla schema
# extensions [NB 2000-11-14b].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import dt_interface
import message
import re
import string
import translator
import types
import time


# 2. DATA AND UTILITIES


# 2.1. Error object
#
# All exceptions raised by this module use 'error' as the exception
# object.

error = 'Bugzilla module error'


# 3. BUGZILLA BUG INTERFACE
#
# This class implements the replicator's interface to the bugs in
# Bugzilla [GDR 2000-10-16, 7.2].

class bugzilla_bug(dt_interface.defect_tracker_issue):
    dt = None # The defect tracker this bug belongs to.
    bug = None # The dictionary representing the bugzilla bug.
    p4dti_bug = None # Dictionary representing the p4dti_bugs record.

    def __init__(self, bug, dt):
        # the set of keys which we explictly use in this class.
        for key in ['bug_id',
                    'reporter',
                    'qa_contact',
                    'everconfirmed',
                    'assigned_to',
                    'groups',
                    'bug_status',
                    'resolution']:
            assert bug.has_key(key)
        assert isinstance(dt, dt_bugzilla)
        self.dt = dt
        self.bug = bug
        self.p4dti_bug = self.dt.bugzilla.bug_p4dti_bug(bug)

    def __getitem__(self, key):
        assert isinstance(key, types.StringType)
        if self.bug.has_key(key):
            return self.bug[key]
        else:
            return self.p4dti_bug[key]

    def __repr__(self):
        return repr({'bug':self.bug,
                     'p4dti':self.p4dti_bug})

    def has_key(self, key):
        return self.bug.has_key(key) or self.p4dti_bug.has_key(key)

    def add_filespec(self, filespec):
        filespec_record = {}
        filespec_record['filespec'] = filespec
        filespec_record['bug_id'] = self.bug['bug_id']
        filespec = bugzilla_filespec(self, filespec_record)
        filespec.add()

    def add_fix(self, change, client, date, status, user):
        fix_record = {}
        fix_record['bug_id'] = self.bug['bug_id']
        fix_record['changelist'] = change
        fix_record['client'] = client
        fix_record['p4date'] = date
        fix_record['status'] = status
        fix_record['user'] = user
        fix = bugzilla_fix(self, fix_record)
        fix.add()

    def corresponding_id(self):
        if (self.p4dti_bug != None
            and self.p4dti_bug.has_key('jobname')):
            return self.p4dti_bug['jobname']
        else:
            return self.dt.config.jobname_function(self.bug)

    def id(self):
        return str(self.bug['bug_id'])

    def filespecs(self):
        filespecs = self.dt.bugzilla.filespecs_from_bug_id(
            self.bug['bug_id'])
        return map(lambda f, self=self: bugzilla_filespec(self, f),
                   filespecs)

    def fixes(self):
        fixes =  self.dt.bugzilla.fixes_from_bug_id(self.bug['bug_id'])
        return map(lambda f, self=self: bugzilla_fix(self, f), fixes)

    def readable_name(self):
        return str(self.bug['bug_id'])

    def rid(self):
        if self.p4dti_bug == None: # not yet replicated
            return ""
        else:
            return self.p4dti_bug['rid']

    def make_p4dti_bug(self, jobname, created=0):
        assert self.p4dti_bug == None
        self.p4dti_bug = {}
        self.p4dti_bug['bug_id'] = self.bug['bug_id']
        self.p4dti_bug['jobname'] = jobname
        self.dt.bugzilla.add_p4dti_bug(self.p4dti_bug, created)

    def setup_for_replication(self, jobname):
        self.make_p4dti_bug(jobname, created=0)

    # Check Bugzilla permissions.
    # 
    # In Bugzilla, permissions are mostly checked in
    # CheckCanChangeField() in process_bug.cgi.  The test changed in
    # Bugzilla 2.17.
    # 
    # This was the test in Bugzilla versions up to 2.16.5:
    #
    # 0. disabled users can't make any change;
    #    (this is not in CheckCanChangeField():
    #    disabled users can't even log in)
    # 1. anyone can make a null change;
    # 2. anyone can make a change which just adds or removes
    #    whitespace at the beginning or end of a value;
    # 3. anyone can add a comment record;
    # 4. anyone in the "editbugs" group can make any change;
    # 5. the bug's reporter can change the bug status;
    # 6. anyone in the "canconfirm" group can change the status to any
    #    opened status.
    # 7. anyone can change the status to any opened status if the bug has
    #    'everconfirmed' set.
    # 8. The reporter, or assigned_to, or qa_contact of a bug can make
    #    any change to the bug other than a change to an opened status.
    # 9. Nobody else can make a change.
    #
    # An opened status is NEW, REOPENED, or ASSIGNED.
    #
    # This is the test in Bugzilla versions from 2.17.7:
    #
    # 0. disabled users can't make any change;
    #    (this is not in CheckCanChangeField():
    #    disabled users can't even log in)
    # 1. anyone can make a null change;
    # 2. anyone can make a change which just adds or removes
    #    whitespace at the beginning or end of a value;
    # 3. anyone can add a comment record;
    # 4. anyone in the "editbugs" group can make any change;
    # 10. anyone in the "canconfirm" group can change the status from
    #    UNCONFIRMED to any opened status;
    # 11. The assigned_to or qa_contact can make any change;
    # 12. The reporter can make any change except:
    #    12.1. changing the status from UNCONFIRMED to any opened state;
    #    12.2. changing the target milestone;
    #    12.3. changing the priority (unless the
    #         letsubmitterchoosepriority parameter is set)
    # 9. Nobody else can make a change.
    # 
    # Note that there is not a check made of whether the user is in
    # the bug group(s) of the bug.  There is an implicit check of this
    # in buglist.pl and bug_form.pl; if the user is not in the bug
    # group(s), the bug is not displayed and cannot be changed.

    def opened_status(self, status):
        assert isinstance(status, types.StringType)
        return status in ['NEW', 'REOPENED', 'ASSIGNED']

    def can_change_field(self, user, user_groups, key, new, pre_217):
        old = self.bug[key]
        assert isinstance(key, types.StringType)
        assert type(old) == type(new)
        # 0. disabled users handled by check_permissions().
        # 1. null changes are eliminated by the replicator.
        assert (old != new)
        # 2. whitespace changes.
        if (isinstance(old, basestring)
            and isinstance(new, basestring)
            and old.strip() == new.strip()):
            return 1
        # 3. anyone can add a description record.
        if key == 'longdesc':
            return 1
        # 4. editbugs handled by check_permissions().
        if pre_217:
            if key == 'bug_status':
                # 5: reporter can change status
                if user == self.bug['reporter']:
                    return 1
                if self.opened_status(new):
                    # 6. canconfirm
                    if 'canconfirm' in user_groups:
                        return 1
                    # 7. everconfirmed
                    if self.bug['everconfirmed'] == 1:
                        return 1
            if (key != 'bug_status') or not self.opened_status(new):
                # 8. reporter/assigned_to/qa_contact
                if (user == self.bug['reporter']
                    or user == self.bug['assigned_to']
                    or user == self.bug['qa_contact']):
                    return 1
        else:
            # 10: canconfirm can confirm
            if ((key == 'bug_status') and
                (old == 'UNCONFIRMED') and
                self.opened_status(new) and
                ('canconfirm' in user_groups)):
                return 1
            # 11. assigned_to or qa_contact can make any change
            if ((user == self.bug['assigned_to']) or
                (user == self.bug['qa_contact'])):
                return 1
            # 12. reporter can do anything except:
            if user == self.bug['reporter']:
                # 12.1. confirming 
                if ((key == 'bug_status') and
                    (old == 'UNCONFIRMED') and
                    self.opened_status(new)):
                    return 0
                # 12.2 changing target milestone
                if key == 'target_milestone':
                    return 0
                # 12.3 changing priority
                if ((key == 'priority') and
                    not int(self.dt.params.get('letsubmitterchoosepriority', '1'))):
                    return 0
                return 1
        # 9. nobody else
        return 0

    def check_permissions(self, user, changes):
        # user 0 can't do anything.
        if user == 0:
            # "User 0 cannot edit bug %d."
            raise error, catalog.msg(538, (self.bug['bug_id']))

        # 0. disabled users can't do anything.
        if self.dt.bugzilla.user_is_disabled(user):
            # "User %d is disabled, so cannot edit bug %d."
            raise error, catalog.msg(537, (user, self.bug['bug_id']))

        bug_groups = self.bug['groups']
        user_groups = self.dt.bugzilla.user_groups(user)
        product_groups = self.dt.bugzilla.product_editor_groups(self.bug['product'])
        pre_217 = self.dt.bugzilla.bugzilla_version < '2.17'

        # 4. user in editbugs can make any change.
        if 'editbugs' in user_groups:
            return

        # Are we in the bug's groups?
        for g in bug_groups:
            if g not in user_groups:
                # "User %d must be in group '%s' to edit bug %d."
                raise error, catalog.msg(555, (user, g, self.bug['bug_id']))

        for g in product_groups:
            if g not in user_groups:
                # "User %d must be in group '%s' to edit bug %d in product '%s'."
                raise error, catalog.msg(556, (user, g, self.bug['bug_id'],
                                               self.bug['product']))

        for key, newvalue in changes.items():
            if not self.can_change_field(user, user_groups, key, newvalue, pre_217):
                # "User %d doesn't have permission to change field '%s'
                # of bug %d to %s."
                raise error, catalog.msg(501, (user, key,
                                               self.bug['bug_id'],
                                               newvalue))

    # Enforce Bugzilla's transition invariants:
    #
    # 1. bugs in 'RESOLVED', 'VERIFIED', and 'CLOSED' states must have
    # a valid 'resolution' field, whereas bugs in other states must
    # have an empty 'resolution' field.
    # 2. only certain transitions are allowable.

    allowable_transitions = {
        'UNCONFIRMED': ['NEW',         # confirm
                        'ASSIGNED',    # assign
                        'RESOLVED'],   # resolve
        'NEW':         ['ASSIGNED',    # accept
                        'RESOLVED'],   # resolve
        'ASSIGNED':    ['NEW',         # reassign
                        'RESOLVED'],   # resolve
        'RESOLVED':    ['VERIFIED',    # verify
                        'CLOSED',      # close
                         'REOPENED'],   # reopen
        'VERIFIED':    ['CLOSED',      # close
                        'REOPENED'],   # reopen
        'CLOSED':      ['REOPENED'],   # reopen
        'REOPENED':    ['NEW',         # reassign
                        'ASSIGNED',    # accept
                        'RESOLVED']    # resolve
        }

    def transition_allowed(self, old_status, new_status):
        return new_status in self.allowable_transitions[old_status]

    def status_needs_resolution(self, status):
        return status in ['RESOLVED', 'VERIFIED', 'CLOSED']

    def enforce_invariants(self, changes):
        if (changes.has_key('resolution')
            and changes['resolution'] == 'DUPLICATE'):
            # "The P4DTI does not support marking bugs as DUPLICATE from
            # Perforce."
            raise error, catalog.msg(502)

        if changes.has_key('bug_status'):
            # We are making a transition.
            if not self.transition_allowed(self.bug['bug_status'],
                                           changes['bug_status']):
                # "Bugzilla does not allow a transition from status '%s'
                # to '%s'."
                raise error, catalog.msg(503, (self.bug['bug_status'],
                                               changes['bug_status']))
            # Changing from 'UNCONFIRMED' sets everconfirmed.
            if (self.bug['bug_status'] == 'UNCONFIRMED'
                and self.bug['everconfirmed'] != 1):
                changes['everconfirmed'] = 1

            if (self.status_needs_resolution(changes['bug_status'])
                and not self.status_needs_resolution(
                self.bug['bug_status'])):
                # We are transitioning to a status which requires a
                # resolution from one which does not.

                if (changes.has_key('resolution')
                    and changes['resolution'] == ''):

                    # We are also clearing the resolution.  This may
                    # happen due to a timing problem; if one p4 user
                    # correctly transitions a bug to REOPENED and
                    # clears the resolution field, and then another p4
                    # user transitions the bug to RESOLVED without
                    # setting the resolution, without an intervening
                    # replication, we may end up here.

                    changes['resolution'] = 'FIXED'

                if (self.bug['resolution'] == ''
                    and not changes.has_key('resolution')):

                    # We are not setting the resolution field.  We
                    # can't force Perforce users to set the resolution
                    # field, and even if procedures require it we can
                    # still get here due to a race problem.  If it
                    # does happen, we set the resolution to FIXED.

                    changes['resolution'] = 'FIXED'

            if not self.status_needs_resolution(changes['bug_status']):
                # We are transitioning to a status which requires
                # an empty resolution.  If we don't have an empty
                # resolution, put one in.
                if changes.has_key('resolution'):
                    if changes['resolution'] != '':
                        changes['resolution'] = ''
                else:
                    if self.bug['resolution'] != '':
                        changes['resolution'] = ''

    # Some Bugzilla fields can not be updated from Perforce, or can
    # only be updated by appending.

    def restrict_fields(self, changes):
        for key in changes.keys():
            if key in self.dt.config.read_only_fields:
                # "Cannot change Bugzilla field '%s'."
                raise error, catalog.msg(504, key)
            if key in self.dt.config.append_only_fields:
                new = changes[key]
                old = self.bug[key]
                if (len(new) < len(old)
                    or new[:len(old)] != old):
                    # "Can only append to Bugzilla field '%s'."
                    raise error, catalog.msg(505, key)
            if (key in ['reporter', 'assigned_to'] and
                changes[key] == 0):
                    # "Can't change Bugzilla field '%s' to 0."
                    raise error, catalog.msg(540, key)


    def update(self, user, changes):
        changes_bug = {}
        changes_p4dti_bug = {}
        assert isinstance(user, types.IntType)

        for key, value in changes.items():
            assert isinstance(key, types.StringType)
            if self.bug.has_key(key):
                changes_bug[key] = value
            elif self.p4dti_bug.has_key(key):
                changes_p4dti_bug[key] = value
            else:
                # "Updating non-existent Bugzilla field '%s'."
                raise error, catalog.msg(506, key)

        self.restrict_fields(changes_bug)
        self.enforce_invariants(changes_bug)
        self.check_permissions(user, changes_bug)

        self.dt.bugzilla.update_bug(changes_bug, self.bug, user)

        # Add processmail script to pending queue.
        self.dt.bugzilla.bugmail(self.bug['bug_id'], user)

        # Now the bug is updated in the database, update our copy.
        for key, value in changes_bug.items():
            self.bug[key] = value

        self.dt.bugzilla.update_p4dti_bug(changes_p4dti_bug,
                                          self.bug['bug_id'])
        # Now the p4dti_bug is updated in the database, update our copy.
        for key, value in changes_p4dti_bug.items():
            self.p4dti_bug[key] = value

    # Delete this bug.
    def delete(self):
        self.dt.bugzilla.delete_bug(self.bug['bug_id'])


# 4. BUGZILLA FIX INTERFACE
#
# This class implements the replicator's interface to a fix record in
# Bugzilla [GDR 2000-10-16, 7.3].

class bugzilla_fix(dt_interface.defect_tracker_fix):
    bug = None # The Bugzilla bug to which the fix refers.
    fix = None # The dictionary representing the bugzilla fix record.

    def __init__(self, bug, dict):
        assert isinstance(bug, bugzilla_bug)
        assert isinstance(dict, types.DictType)
        for key in ['changelist',
                    'client',
                    'p4date',
                    'status',
                    'bug_id',
                    'user']:
            assert dict.has_key(key)
        self.bug = bug
        self.fix = dict

    def __getitem__(self, key):
        assert isinstance(key, types.StringType)
        return self.fix[key]

    def __repr__(self):
        return repr(self.fix)

    def __setitem__(self, key, value):
        assert isinstance(key, types.StringType)
        self.fix[key] = value

    def add(self):
        self.bug.dt.bugzilla.add_fix(self.fix)

    def change(self):
        return self.fix['changelist']

    def delete(self):
        self.bug.dt.bugzilla.delete_fix(self.fix)

    def status(self):
        return self.fix['status']

    def update(self, change, client, date, status, user):
        changes = {}
        if self.fix['changelist'] != change:
            changes['changelist'] = change
        if self.fix['client'] != client:
            changes['client'] = client
        if self.fix['p4date'] != date:
            changes['p4date'] = date
        if self.fix['status'] != status:
            changes['status'] = status
        if self.fix['user'] != user:
            changes['user'] = user
        if len(changes) != 0:
            self.bug.dt.bugzilla.update_fix(changes,
                                            self.fix['bug_id'],
                                            self.fix['changelist'])


# 5. BUGZILLA FILESPEC INTERFACE
#
# This class implements the replicator's interface to a filespec record
# in Bugzilla [GDR 2000-10-16, 7.4].

class bugzilla_filespec(dt_interface.defect_tracker_filespec):
    bug = None # The Bugzilla bug to which the filespec refers.
    filespec = None # The dictionary representing the filespec record.

    def __init__(self, bug, dict):
        self.bug = bug
        self.filespec = dict

    def __getitem__(self, key):
        return self.filespec[key]

    def __repr__(self):
        return repr(self.filespec)

    def __setitem__(self, key, value):
        self.filespec[key] = value

    def add(self):
        self.bug.dt.bugzilla.add_filespec(self.filespec)

    def delete(self):
        self.bug.dt.bugzilla.delete_filespec(self.filespec)

    def name(self):
        return self.filespec['filespec']


# 6. BUGZILLA INTERFACE
#
# The dt_bugzilla class implements a generic interface between the
# replicator and the Bugzilla defect tracker [GDR 2000-10-16, 7.1].
# Some configuration can be done by passing a configuration hash to the
# constructor; for more advanced configuration you should subclass this
# and replace some of the methods.

class dt_bugzilla(dt_interface.defect_tracker):

    rid = None
    sid = None
    bugzilla = None
    cached_users = 0 # Are the user records fresh?

    def __init__(self, config):
        self.config = config
        self.rid = config.rid
        self.sid = config.sid
	self.bugzilla = config.bugzilla
        self.cached_users = 0

    def log(self, msg, args = ()):
        if not isinstance(msg, message.message):
            msg = catalog.msg(msg, args)
        self.config.logger.log(msg)

    def all_issues(self):
        bugs = self.bugzilla.all_bugs_since(self.config.start_date)
        return map(lambda bug,dt=self: bugzilla_bug(bug,dt), bugs)

    def poll_start(self):
        self.bugzilla.lock_tables()
        self.cached_users = 0
        self.bugzilla.clear_caches()

    def poll_end(self):
        self.bugzilla.unlock_tables()
        self.bugzilla.invoke_deferred_commands()

    def changed_entities(self):
        replication = self.bugzilla.new_replication()
        last = self.bugzilla.latest_complete_replication()
        bugs = self.bugzilla.changed_bugs_since(last)
        return (map(lambda bug,dt=self: bugzilla_bug(bug,dt), bugs),
                {}, # changed changelists
                replication)

    def mark_changes_done(self, replication):
        self.bugzilla.end_replication()

    def init(self):
        # ensure that bugzilla.replication is valid even outside a
        # replication cycle, so that all_issues() works.  See
        # job000221.  NB 2001-02-22.
        self.bugzilla.first_replication(self.config.start_date)

    # Supported features; see [GDR 2000-10-16, 3.5].
    feature = {
        'filespecs': 1,
        'fixes': 1,
        'migrate_issues': 1,
        'new_issues': 1,
        'new_users': 1,
        }

    def supports(self, feature):
        return self.feature.get(feature, 0)

    def issue(self, bug_id):
        bug = self.bugzilla.bug_from_bug_id(int(bug_id))
        return bugzilla_bug(bug, self)

    def add_user(self, p4user, email, fullname):
        userid = self.bugzilla.userid_from_email(email)
        if userid:
            # "Perforce user '%s <%s>' already exists in Bugzilla as
            # user %d."
            self.log(533, (p4user, email, userid))
            return userid
        else:
            dict = {}
            dict['login_name'] = email
            dict['password'] = self.config.migrated_user_password
            dict['realname'] = fullname
            dict['disabledtext'] = ''
            all_groups = self.bugzilla.groups()
            for g in self.config.migrated_user_groups:
                if not all_groups.has_key(g):
                    # "'%s' not a Bugzilla group."
                    raise error, catalog.msg(535, group)
            dict['groups'] = self.config.migrated_user_groups
            userid = self.bugzilla.add_user(dict)
            # "Perforce user '%s <%s>' added to Bugzilla as user %d."
            self.log(534, (p4user, email, userid))
            return userid

    def add_replicator_user(self):
        email = self.config.replicator_address
        userid = self.bugzilla.userid_from_email(email)
        if userid:
            # "Perforce replicator user <%s> already exists in
            # Bugzilla as user %d."
            self.log(553, (email, userid))
            return userid
        else:
            dict = {}
            dict['login_name'] = email
            dict['password'] = self.config.migrated_user_password
            dict['realname'] = "Perforce defect tracking integration"
            dict['groups'] = []
            dict['disabledtext'] = "This user can access Bugzilla only as the P4DTI replicator process"
            userid = self.bugzilla.add_user(dict)
            # "Perforce replicator user <%s> added to Bugzilla as user %d."
            self.log(554, (email, userid))
            return userid

    def new_issues_start(self):
        self.bugzilla.lock_tables()
        self.cached_users = 0
        self.bugzilla.clear_caches()

    def new_issues_end(self):
        self.bugzilla.unlock_tables()
        self.bugzilla.invoke_deferred_commands()

    # new_issue_defaults(dict).  Supply default values for the product,
    # component and version fields where possible (see [AG, 6.2]).

    def new_issue_defaults(self, dict):
        assert isinstance(dict, types.DictType)
        dict['product'] = dict.get('product', '')
        dict['component'] = dict.get('component', '')
        dict['version'] = dict.get('version', '')

        # Infer product if there's only one product in Bugzilla.
        products = self.bugzilla.products()
        if len(products) == 1 and dict['product'] == '':
            dict['product'] = products.keys()[0]
        if not dict.has_key('product'):
            # No product: can't infer anything else.
            return
        product_name = dict['product']

        # Infer component if there's only one for this product.
        components = self.bugzilla.components_of_product(product_name)
        if len(components) == 1 and dict['component'] == '':
            dict['component'] = components.keys()[0]

        # Infer version if there's only one for this product.
        versions = self.bugzilla.versions_of_product(product_name)
        if len(versions) == 1 and dict['version'] == '':
            dict['version'] = versions[0]

    def new_issue(self, dict, jobname):
        # Only know how to deal with these fields at bug creation.
        for key, value in dict.items():
            if (value != '' and
                value != 0 and
                not key in ['resolution',
                           'groups',
                           'assigned_to',
                           'bug_file_loc',
                           'bug_severity',
                           'bug_status',
                           'op_sys',
                           'priority',
                           'rep_platform',
                           'target_milestone',
                           'qa_contact',
                           'longdesc',
                           'short_desc',
                           'product',
                           'component',
                           'version',
                           'reporter',
                           'creation_ts',
                           'delta_ts',
                           ]):
                # "Can't create Bugzilla bug with field '%s'."
                raise error, catalog.msg(531, key)

        # must have non-empty summary
        if not dict.has_key('short_desc'):
            # "Can't create Bugzilla bug without short_desc field."
            raise error, catalog.msg(517)
        if dict['short_desc'] == '':
            # "Can't create Bugzilla bug with empty short_desc field."
            raise error, catalog.msg(518)

        # must have reporter
        if not dict.has_key('reporter'):
            # "Can't create Bugzilla bug without reporter field."
            raise error, catalog.msg(532)
        user = dict['reporter']

        # this user has been produced by the lax user translator; it
        # could be 0 or the P4DTI user.  The P4DTI user is allowed
        # here (think about migration, in which case the reporter may
        # be ancient history in Perforce).
        if user == 0:
            # "Can't create Bugzilla bug with reporter 0."
            raise error, catalog.msg(539)

        # Supply defaults for product, component and version if
        # possible.
        self.new_issue_defaults(dict)

        # Product must exist.
        products = self.bugzilla.products()
        if dict.get('product', '') == '':
            # "Can't create Bugzilla bug without product field."
            raise error, catalog.msg(519)
        product_name = dict['product']
        if not products.has_key(product_name):
            # "Can't create Bugzilla bug for non-existent product '%s'."
            raise error, catalog.msg(520, product_name)

        # Get product record.
        product = products[product_name]

        # Component must exist.
        components = self.bugzilla.components_of_product(product_name)
        if len(components) == 0:
            # "Can't create Bugzilla bug for product '%s' with no
            # components."
            raise error, catalog.msg(521, product_name)
        if dict.get('component', '') == '':
            # "Can't create Bugzilla bug without component field."
            raise error, catalog.msg(522)
        if not components.has_key(dict['component']):
            # "Can't create Bugzilla bug: product '%s' has no component
            # '%s'."
            raise error, catalog.msg(523, (product_name,
                                           dict['component']))
        component = components[dict['component']]

        # Version must exist.
        versions = self.bugzilla.versions_of_product(product_name)
        if len(versions) == 0:
            # "Can't create Bugzilla bug for product '%s' with no
            # versions."
            raise error, catalog.msg(524, product_name)
        if dict.get('version', '') == '':
            # "Can't create Bugzilla bug without version field."
            raise error, catalog.msg(525)
        version = dict['version']
        if not version in versions:
            # "Can't create Bugzilla bug: product '%s' has no version
            # '%s'."
            raise error, catalog.msg(526, (product_name, version))

        email = self.bugzilla.email_from_userid(user)

        # permissions for the reporter to create the bug.
        user_groups = self.bugzilla.user_groups(user)
        product_groups = self.bugzilla.product_creator_groups(product_name)
        for group in product_groups:
            if group not in user_groups:
                # "User '%s' isn't in Bugzilla group '%s' required to make bug
                # for product '%s'; creating bug anyway."
                self.log(527, (email, group, product_name))

        if not dict.has_key('groups'):
            dict['groups'] = []

        bug_groups = dict['groups']

        all_groups = self.bugzilla.groups()
        for group in bug_groups:
            if not all_groups.has_key(group):
                # "Can't create Bugzilla bug with invalid group
                # '%s'."
                raise error, catalog.msg(528, group)

        # what groups must a bug go into?
        mandatory_groups = self.bugzilla.new_bug_groups(product_name, user_groups)
        for group in mandatory_groups:
            if not group in bug_groups:
                bug_groups.append(group)

        dict['groups'] = bug_groups

        if product['votestoconfirm'] != 0:
            default_bug_status = 'UNCONFIRMED'
        else:
            default_bug_status = 'NEW'

        if dict.has_key('bug_status'):
            bug_status = dict['bug_status']
            # if the bug_status is not the default for this product,
            # check the user has the permissions.
            if (bug_status != default_bug_status
                and not ('editbugs' in user_groups)
                and not ('canconfirm' in user_groups)):
                # "User '%s' doesn't have permissions to create Bugzilla
                # bug for product '%s' with status '%s'; creating bug
                # anyway."
                self.log(529, (email, product_name, bug_status))
        else:
            bug_status = default_bug_status
            dict['bug_status'] = bug_status

        if bug_status != 'UNCONFIRMED':
            dict['everconfirmed'] = 1
        else:
            dict['everconfirmed'] = 0

        if not dict.has_key('resolution'):
            dict['resolution'] = ''

        if (dict['resolution'] == ''
            and bug_status in ['RESOLVED', 'VERIFIED', 'CLOSED']):
            # "Can't create Bugzilla bug with bug_status '%s' and no
            # resolution."
            raise error, catalog.msg(530, bug_status)

        # other defaults
        if dict.get('assigned_to', 0) == 0:
            dict['assigned_to'] = component['initialowner']

        if not dict.has_key('bug_file_loc'):
            dict['bug_file_loc'] = ''

        if dict.get('bug_severity', '') == '':
            dict['bug_severity'] = 'normal'

        if dict.get('op_sys', '') == '':
            dict['op_sys'] = 'other'

        if dict.get('priority', '') == '':
            dict['priority'] = 'P2'

        if dict.get('rep_platform', '') == '':
            dict['rep_platform'] = 'Other'

        if dict.get('target_milestone', '') == '':
            dict['target_milestone'] = product['defaultmilestone']

        if dict.get('qa_contact', 0) == 0:
            dict['qa_contact'] = component['initialqacontact']

        if not dict.has_key('longdesc'):
            dict['longdesc'] = 'No initial comment.'

        if not dict.has_key('delta_ts'):
            dict['delta_ts'] = '' # quotation will turn this into now()

        bug_id = self.bugzilla.add_bug(dict)
        bug = self.issue(bug_id)
        # in future might want another jobname here.
        bug.make_p4dti_bug(jobname, created=1)
        return bug


    def replicate_changelist(self, change, client, date, description,
                             status, user):
        dt_changelists = self.bugzilla.changelists(change)
        if len(dt_changelists) == 0:
            # no existing changelist; make a new one
            dt_changelist={}
            self.transform_changelist(dt_changelist, change, client,
                                      date, description, status, user)
            self.bugzilla.add_changelist(dt_changelist)
            return 1
        else: # determine the changes
            changes = self.transform_changelist(dt_changelists[0],
                                                change, client, date,
                                                description, status,
                                                user)
            if changes:
                self.bugzilla.update_changelist(changes, change)
                return 1
            else:
                return 0

    def transform_changelist(self, dt_changelist,
                             change, client, date, description,
                             status, user):
        changes = {}
        changes['changelist'] = change
        changes['client'] = client
        changes['p4date'] = date
        changes['description'] = description
        # "(x and 1) or 0" gives the int value of the boolean x.
        changes['flags'] = ((status == 'submitted') and 1) or 0
        changes['user'] = user
        for key, value in changes.items():
            if (not dt_changelist.has_key(key)
                or dt_changelist[key] != value):
                dt_changelist[key] = value
            else:
                del changes[key]
        return changes

# 7. TRANSLATORS
#
# These classes translate values of particular types between Bugzilla
# and Perforce [GDR 2000-10-16, 7.5].


# 7.1. State translator
#
# This class translates bug statuses [GDR 2000-10-16, 7.5.2].

class status_translator(translator.translator):
    # A map from Bugzilla status name to Perforce status name.
    status_bz_to_p4 = {}

    # A map from Perforce status name to Bugzilla status name (the
    # reverse of the above map).
    status_p4_to_bz = {}

    def __init__(self, statuses):
        # Compute the maps.
        for bz_status, p4_status in statuses:
            assert isinstance(bz_status, basestring)
            assert isinstance(p4_status, basestring)
            self.status_bz_to_p4[bz_status] = p4_status
            self.status_p4_to_bz[p4_status] = bz_status

    def translate_0_to_1(self, bz_status, bz, p4, issue=None, job=None):
        assert isinstance(bz_status, basestring)
        if self.status_bz_to_p4.has_key(bz_status):
            return self.status_bz_to_p4[bz_status]
        else:
            # "No Perforce status corresponding to Bugzilla status
            # '%s'."
            raise error, catalog.msg(509, bz_status)

    def translate_1_to_0(self, p4_status, bz, p4, issue=None, job=None):
        assert isinstance(p4_status, basestring)
        if self.status_p4_to_bz.has_key(p4_status):
            return self.status_p4_to_bz[p4_status]
        else:
            # "No Bugzilla status corresponding to Perforce status
            # '%s'."
            raise error, catalog.msg(510, p4_status)


# 7.2. Enumerated field translator
#
# This class translates values in enumerated fields.  Because enumerated
# fields in Bugzilla are mapped to select fields in Perforce, we have to
# translate the value using the keyword translator [GDR 2000-10-16,
# 7.5.2] so that it is valid in Perforce.

class enum_translator(translator.translator):
    keyword_translator = None
    def __init__(self, keyword_translator):
        self.keyword_translator = keyword_translator

    def translate_0_to_1(self, bz_enum,
                         bz = None, p4 = None,
                         issue = None, job = None):
        assert isinstance(bz_enum, basestring)
        if bz_enum == '':
            return 'NONE'
        else:
            return self.keyword_translator.translate_0_to_1(bz_enum)

    def translate_1_to_0(self, p4_enum,
                         bz = None, p4 = None,
                         issue = None, job = None):
        if p4_enum == 'NONE':
            return ''
        else:
            return self.keyword_translator.translate_1_to_0(p4_enum)


# 7.3. Date translator
#
# The date_translator class translates date fields between defect
# trackers Bugzilla (0) and Perforce (1) [GDR 2000-10-16, 7.5.1].
#
# Some Perforce dates are reported in the form 2000/01/01 00:00:00
# (e.g., dates in changeslists) and others are reported as seconds since
# 1970-01-01 00:00:00 (e.g., dates in fixes).  I don't know why this is,
# but I have to deal with it by checking for both formats.
#
# MySQL datetime values are in the form 'YYYY-MM-DD hh:mm:ss'.
#
# Note that we deliberately prevent MySQLdb from using DateTime types
# for datetime values (see job000193, configure_bugzilla.py).  Maybe one
# day that will change.

class date_translator(translator.translator):
    p4_date_regexps = [
        re.compile("^([0-9][0-9][0-9][0-9])/([0-9][0-9])/([0-9][0-9]) "
                   "([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$"),
        re.compile("^[0-9]+$")
        ]

    bz_date_regexp = re.compile(
        "^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9]) "
        "([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")

    def translate_0_to_1(self, bz_date, bz, p4, issue=None, job=None):
        assert isinstance(bz_date, basestring)
        assert isinstance(bz, dt_bugzilla)
        assert isinstance(p4, dt_interface.defect_tracker)
        assert issue == None or isinstance(issue, bugzilla_bug)
        match = self.bz_date_regexp.match(bz_date)
        if match:
            return ('%s/%s/%s %s:%s:%s' %
                    (match.group(1), match.group(2), match.group(3),
                     match.group(4), match.group(5), match.group(6)))
        else:
            return ''

    def translate_1_to_0(self, p4_date, bz, p4, issue=None, job=None):
        assert isinstance(p4_date, basestring)
        assert isinstance(bz, dt_bugzilla)
        assert isinstance(p4, dt_interface.defect_tracker)
        assert issue == None or isinstance(issue, bugzilla_bug)
        match = self.p4_date_regexps[0].match(p4_date)
        if match:
            return ('%s-%s-%s %s:%s:%s' %
                    (match.group(1), match.group(2), match.group(3),
                     match.group(4), match.group(5), match.group(6)))

        elif self.p4_date_regexps[1].match(p4_date):
            return time.strftime("%Y-%m-%d %H:%M:%S",
                                 time.gmtime(int(p4_date)))
        else:
            return '' # becomes 0000-00-00 00:00:00 on insertion


# 7.4. Timestamp translator
#
# The timestamp_translator class translates timestamp fields between
# defect trackers Bugzilla (0) and Perforce (1).
#
# Some Perforce dates are reported in the form 2000/01/01 00:00:00
# (e.g., dates in changeslists) and others are reported as seconds since
# 1970-01-01 00:00:00 (e.g., dates in fixes).  I don't know why this is,
# but I have to deal with it by checking for both formats.
#
# MySQL timestamps are YYYYMMDDhhmmss.
#
# If there's nothing in Perforce, translate to '', which will get set
# to now() in MySQL.

class timestamp_translator(translator.translator):
    p4_date_regexps = [
        re.compile("^([0-9][0-9][0-9][0-9])/([0-9][0-9])/([0-9][0-9]) "
                   "([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$"),
        re.compile("^[0-9]+$")
        ]

    bz_timestamp_regexp = re.compile(
        "^([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])"
        "([0-9][0-9])([0-9][0-9])([0-9][0-9])$")

    def translate_0_to_1(self, bz_date, bz, p4, issue=None, job=None):
        assert isinstance(bz_date, basestring)
        assert isinstance(bz, dt_bugzilla)
        assert isinstance(p4, dt_interface.defect_tracker)
        assert issue == None or isinstance(issue, bugzilla_bug)
        match = self.bz_timestamp_regexp.match(bz_date)
        if match:
            return ('%s/%s/%s %s:%s:%s' %
                    (match.group(1), match.group(2), match.group(3),
                     match.group(4), match.group(5), match.group(6)))
        else:
            return ''

    def translate_1_to_0(self, p4_date, bz, p4, issue=None, job=None):
        assert isinstance(p4_date, basestring)
        assert isinstance(bz, dt_bugzilla)
        assert isinstance(p4, dt_interface.defect_tracker)
        assert issue == None or isinstance(issue, bugzilla_bug)
        match = self.p4_date_regexps[0].match(p4_date)
        if match:
            return ('%s%s%s%s%s%s' %
                    (match.group(1), match.group(2), match.group(3),
                     match.group(4), match.group(5), match.group(6)))

        elif self.p4_date_regexps[1].match(p4_date):
            return time.strftime("%Y%m%d%H%M%S",
                                 time.gmtime(int(p4_date)))
        else:
            return ''


# 7.6. Text translator
#
# The text_translator class translates multi-line text fields between
# defect trackers Bugzilla (0) and Perforce (1) [GDR 2000-10-16, 7.5.3].

class text_translator(translator.translator):
    # Transform Bugzilla text field contents to Perforce text field
    # contents by adding a newline.

    def translate_0_to_1(self, bz_string, bz, p4, issue=None, job=None):
        assert isinstance(bz_string, basestring)
        # Add final newline, unless the string is empty.
        if bz_string:
            bz_string = bz_string + '\n'
        return bz_string

    # Transform Perforce text field contents to Bugzilla text field
    # contents by removing a line ending.

    def translate_1_to_0(self, p4_string, bz, p4, issue=None, job=None):
        assert isinstance(p4_string, basestring)
        # Remove final newline (if any).
        if p4_string and p4_string[-1] == '\n':
            p4_string = p4_string[:-1]
        return p4_string


# 7.7. Integer translator
#
# The int_translator class translates integer fields between defect
# trackers Bugzilla (0) and Perforce (1).

class int_translator(translator.translator):
    # Transform Bugzilla integer field contents to Perforce word field
    # contents by converting line endings.

    def translate_0_to_1(self, bz_int, bz, p4, issue=None, job=None):
        assert (isinstance(bz_int, types.IntType)
                or isinstance(bz_int, types.LongType))
        s = str(bz_int)
        # Note that there's a difference between Python 1.5.2 and Python
        # 1.6 here, in whether str of a long ends in an L.
        if s[-1:] == 'L':
            s = s[:-1]
        return s

    # Transform Perforce word field contents to Bugzilla integer field
    # contents.

    def translate_1_to_0(self, p4_string, bz, p4, issue=None, job=None):
        assert isinstance(p4_string, basestring)
        try:
            if p4_string == '':
                return 0L
            else:
                return long(p4_string)
        except:
            # "Perforce field value '%s' could not be translated to a
            # number for replication to Bugzilla."
            raise error, catalog.msg(511, p4_string)


# 7.7. User translator
#
# The user_translator class translates user fields between defect
# trackers Bugzilla (0) and Perforce (1) [GDR 2000-10-16, 7.5.3].
#
# A Perforce user field contains a Perforce user name (for example,
# "nb").  The Perforce user record contains an e-mail address (for
# example, "nb@ravenbrook.com").
#
# A Bugzilla user field contains an integer (MySQL type 'mediumint'),
# (for example, 3).  The Bugzilla user record (MySQL table 'profiles')
# contains an e-mail address (MySQL column 'login_name') (for example,
# "nb@ravenbrook.com").  For some Bugzilla user fields
# (e.g. qa_contact), the integer may be 0, meaning "None".
#
# To translate a user field, we find an identical e-mail address.
#
# If there is no such Perforce user, we just use the e-mail address,
# because we can (in fact) put any string into a Perforce user field.
#
# If there is no such Bugzilla user, we check whether the Perforce user
# field is in fact the e-mail address of a Bugzilla user (for example,
# one that we put there because there wasn't a matching Perforce user).
# If so, we use that Bugzilla user.
#
# Sometimes, a Perforce user field which cannot be translated into
# Bugzilla is an error.  For instance, if a Perforce user sets the
# qa_contact field of a job to a nonsense value, we should catch that
# and report it as an error.
#
# Sometimes, however, we should allow such values.  For instance, when
# translating the user field of a fix record or changelist: we should
# not require _all_ past and present Perforce users to have Bugzilla
# user records.  In that case, we should translate to a default value.
# For this purpose, the replicator has a Bugzilla user of its own.
#
# To distinguish between these two cases, we have a switch
# 'allow_unknown'.  If allow_unknown is 1, we use the default
# translation.  If allow_unknown is 0, we report an error.

class user_translator(translator.user_translator):
    # A map from Bugzilla user ids to Perforce user names
    user_bz_to_p4 = {}

    # A map from Perforce user names to Bugzilla user ids
    user_p4_to_bz = {}

    # A map from Bugzilla user ids to (downcased) email addresses
    bz_id_to_email = None

    # A map from (downcased) email addresses to Bugzilla user ids
    bz_email_to_id = None

    # A map from (downcased) email addresses to Perforce user names
    p4_email_to_user = None

    # A map from Perforce user names to (downcased) email addresses
    p4_user_to_email = None

    # A map from Perforce user names to Perforce full names.
    p4_user_to_fullname = None

    # A map from Perforce user name to email address for users with
    # duplicate email addresses in Perforce.
    p4_duplicates = None

    # A map from Bugzilla user id to email address for users with
    # duplicate (downcased) email addresses in Bugzilla.
    bz_duplicates = None

    # A map from Perforce user name to email address for Perforce
    # users that can't be matched with users in Bugzilla.
    p4_unmatched = None

    # A map from Bugzilla user real name to email address for Bugzilla
    # users that can't be matched with users in Perforce.
    bz_unmatched = None

    # The Bugzilla P4DTI user email address (config.replicator_address)
    bugzilla_user = None

    # The Bugzilla P4DTI user id
    bugzilla_id = None

    # The Perforce P4DTI user name (config.p4_user)
    p4_user = None

    # A switch controlling whether this translator will translate
    # Perforce users without corresponding Bugzilla users into
    # the Bugzilla P4DTI user id.
    allow_unknown = 0

    tables_populated = 0

    def __init__(self, bugzilla_user, p4_user,
                 allow_unknown = 0):
        self.bugzilla_user = string.lower(bugzilla_user)
        self.p4_user = p4_user
        self.allow_unknown = allow_unknown

    # Deduce and record the mapping between Bugzilla userid and
    # Perforce username.
    def init_users(self, bz, p4):

        if self.tables_populated and bz.cached_users:
            return

        # Clear the maps.
        self.user_bz_to_p4 = {}
        self.user_p4_to_bz = {}
        self.bz_email_to_id = {}
        self.bz_id_to_email = {}
        self.p4_email_to_user = {}
        self.p4_user_to_email = {}
        self.p4_duplicates = {}
        self.bz_duplicates = {}
        self.p4_unmatched = {}
        self.bz_unmatched = {}
        self.p4_user_to_fullname = {}

        # Populate the Perforce-side maps.
        p4_users = p4.p4.run("users")
        for u in p4_users:
            email = string.lower(u['Email'])
            user = u['User']
            self.p4_user_to_fullname[user] = u['FullName']
            self.p4_user_to_email[user] = email
            if self.p4_email_to_user.has_key(email):
                matching_user = self.p4_email_to_user[email]
                # "Perforce users '%s' and '%s' both have email address
                # '%s' (when converted to lower case)."
                bz.log(541, (user, matching_user, email))
                self.p4_duplicates[matching_user] = email
                self.p4_duplicates[user] = email
            else:
                self.p4_email_to_user[email] = user

        # Check the Perforce P4DTI user exists:
        if not self.p4_user_to_email.has_key(self.p4_user):
            # "Perforce P4DTI user '%s' is not a known Perforce user."
            raise error, catalog.msg(542, self.p4_user)

        p4_email = self.p4_user_to_email[self.p4_user]

        # Check that the Perforce P4DTI user has a unique email address:
        if self.p4_duplicates.has_key(self.p4_user):
            duplicate_users = []
            for (user, email) in self.p4_duplicates.items():
                if email == p4_email and user != self.p4_user:
                    duplicate_users.append(user)
            # "Perforce P4DTI user '%s' has the same e-mail address
            # '%s' as these other Perforce users: %s."
            raise error, catalog.msg(543,
                                     (self.p4_user,
                                      p4_email,
                                      duplicate_users))

        # Make a list of all the user ids matching the Bugzilla P4DTI user.
        bugzilla_ids = []

        # Populate the Bugzilla-side maps.
        bz_users = bz.bugzilla.user_id_and_email_list()
        for (id, email) in bz_users:
            email = string.lower(email)
            self.bz_id_to_email[id] = email
            # Collect ids matching the Bugzilla P4DTI user
            if email == self.bugzilla_user:
                bugzilla_ids.append(id)
            if self.bz_email_to_id.has_key(email):
                matching_id = self.bz_email_to_id[email]
                bz_real_name = bz.bugzilla.real_name_from_userid(id)
                matching_real_name = bz.bugzilla.real_name_from_userid(matching_id)
                # "Bugzilla users '%s' and '%s' both have email address
                # '%s' (when converted to lower case)."
                bz.log(544, (bz_real_name, matching_real_name, email))
                self.bz_duplicates[bz_real_name] = email
                self.bz_duplicates[matching_real_name] = email
            else:
                self.bz_email_to_id[email] = id

        # Check that the Bugzilla P4DTI user exists:
        if len(bugzilla_ids) == 0:
            # "Bugzilla P4DTI user '%s' is not a known Bugzilla user."
            raise error, catalog.msg(513, self.bugzilla_user)

        # Check that the Bugzilla P4DTI user is unique:
        if len(bugzilla_ids) > 1:
            # "Bugzilla P4DTI user e-mail address '%s' belongs to
            # several Bugzilla users: %s."
            raise error, catalog.msg(545, (self.bugzilla_user, bugzilla_ids))

        # There can be only one.
        self.bugzilla_id = bugzilla_ids[0]

        # The Perforce-specific and Bugzilla-specific maps are now
        # complete.  Note that the p4_user_to_email map and the
        # bz_id_to_email map may have duplicate values (in which case
        # the keys in the inverse maps are the first-seen
        # corresponding keys).

        # Populate the translation maps.
        # We could do this at the same time as one of the previous phases,
        # but IMO it's cleaner to separate it out like this.

        for (id, email) in self.bz_id_to_email.items():
            if self.p4_email_to_user.has_key(email):
                p4_user = self.p4_email_to_user[email]
                # Already matched?
                if self.user_p4_to_bz.has_key(p4_user):
                    matching_id = self.user_p4_to_bz[p4_user]
                    bz_real_name = bz.bugzilla.real_name_from_userid(id)
                    self.bz_unmatched[bz_real_name] = email
                    # "Bugzilla user '%s' (e-mail address '%s') not
                    # matched to any Perforce user, because Perforce
                    # user '%s' already matched to Bugzilla user %d."
                    bz.log(546,
                           (bz_real_name, email, p4_user, matching_id))
                else:
                    self.user_bz_to_p4[id] = p4_user
                    self.user_p4_to_bz[p4_user] = id
                    # "Bugzilla user %d matched to Perforce user '%s' by
                    # e-mail address '%s'."
                    bz.log(547, (id, p4_user, email))
            else:
                bz_real_name = bz.bugzilla.real_name_from_userid(id)
                self.bz_unmatched[bz_real_name] = email
                # "Bugzilla user '%s' (e-mail address '%s') not matched
                # to any Perforce user."
                bz.log(548, (bz_real_name, email))

        # Identify unmatched Perforce users.
        for (user, email) in self.p4_user_to_email.items():
            if not self.user_p4_to_bz.has_key(user):
                self.p4_unmatched[user] = email
                # "Perforce user '%s' (e-mail address '%s') not matched
                # to any Bugzilla user."
                bz.log(549, (user, email))

        # Ensure that Bugzilla P4DTI user and Perforce P4DTI user
        # correspond.
        if self.user_bz_to_p4.has_key(self.bugzilla_id):
            # Bugzilla P4DTI user has P4 counterpart:
            p4_bugzilla_user = self.user_bz_to_p4[self.bugzilla_id]
            # But is it the p4_user?
            if (p4_bugzilla_user != self.p4_user):
                # "Bugzilla P4DTI user '%s' has e-mail address
                # matching Perforce user '%s', not Perforce P4DTI
                # user '%s'."
                raise error, catalog.msg(512,
                                         (self.bugzilla_user,
                                          p4_bugzilla_user,
                                          self.p4_user))
        else:
            if self.user_p4_to_bz.has_key(self.p4_user):
                bz_user = self.user_p4_to_bz[self.p4_user]
                bz_email = self.bz_id_to_email[bz_user]
                # "Bugzilla P4DTI user '%s' does not have a matching
                # Perforce user.  It should match the Perforce user
                # '%s' but that matches the Bugzilla user %d (e-mail
                # address '%s')."
                raise error, catalog.msg(550, (self.bugzilla_user,
                                               self.p4_user,
                                               bz_user,
                                               bz_email))
            else:
                # "Bugzilla P4DTI user '%s' does not have a matching
                # Perforce user.  It should match the Perforce user
                # '%s' (which has e-mail address '%s')."
                raise error, catalog.msg(551, (self.bugzilla_user,
                                               self.p4_user,
                                               p4_email))

        # always translate 0 to 'None' and back again
        self.user_p4_to_bz['None'] = 0
        self.user_bz_to_p4[0] = 'None'
        self.tables_populated = 1
        bz.cached_users = 1

    def unmatched_users(self, bz, p4):
        self.init_users(bz, p4)
        # "A user field containing one of these users will be translated
        # to the user's e-mail address in the corresponding Perforce job
        # field."
        bz_user_msg = catalog.msg(515)
        # "It will not be possible to use Perforce to assign bugs to
        # these users.  Changes to jobs made by these users will be
        # ascribed in Bugzilla to the replicator user <%s>."
        p4_user_msg = catalog.msg(516, self.bugzilla_user)
        # "These Perforce users have duplicate e-mail addresses.  They
        # may have been matched with the wrong Bugzilla user."
        duplicate_p4_user_msg = catalog.msg(536)
        # "These Bugzilla users have duplicate e-mail addresses (when
        # converted to lower case).  They may have been matched with
        # the wrong Perforce user."
        duplicate_bz_user_msg = catalog.msg(552)
        return (self.bz_unmatched, self.p4_unmatched,
                bz_user_msg, p4_user_msg,
                self.bz_duplicates, self.p4_duplicates,
                duplicate_bz_user_msg, duplicate_p4_user_msg)

    keyword = translator.keyword_translator()

    def translate_1_to_0(self, p4_user, bz, p4, issue=None, job=None):
        if not self.user_p4_to_bz.has_key(p4_user):
            self.init_users(bz, p4)
        if self.user_p4_to_bz.has_key(p4_user):
            return self.user_p4_to_bz[p4_user]
        else:
            bz_email = self.keyword.translate_1_to_0(p4_user)
            if self.bz_email_to_id.has_key(bz_email):
                return self.bz_email_to_id[bz_email]
            elif self.allow_unknown:
                return self.bugzilla_id
            else:
                # "There is no Bugzilla user corresponding to Perforce
                # user '%s'."
                raise error, catalog.msg(514, p4_user)

    def translate_0_to_1(self, bz_user, bz, p4, issue=None, job=None):
        if not bz.cached_users:
            self.init_users(bz, p4)
        if self.user_bz_to_p4.has_key(bz_user):
            return self.user_bz_to_p4[bz_user]
        else:
            bz_email = self.bz_id_to_email[bz_user]
            return self.keyword.translate_0_to_1(bz_email)


# A. REFERENCES
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
# [NB 2000-11-14a] "Bugzilla database schema"; Nick Barnes; Ravenbrook
# Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/tool/cgi/bugzilla-schema/>.
#
# [NB 2000-11-14b] "Bugzilla database schema extensions for integration
# with Perforce"; Nick Barnes; Ravenbrook Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/bugzilla-p4dti-schema/>.
#
# [NB 2000-11-14c] "Python interface to Bugzilla: design"; Nick Barnes;
# Ravenbrook Limited; 2000-11-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/python-bugzilla-interface/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-05 NB Fixes for job job000089 and job000118.  We update
# bugs_activity and have a new table p4dti_bugs_activity which
# duplicates bugs_activity rows added by this replicator.  A complicated
# select then identifies bugs which have been changed other than by the
# replicator.  Locking added.  Fixes, filespecs, and changelists now
# work.
#
# 2000-12-07 RB Changed call to create bugzilla object to pass explicit
# parameters (see corresponding change in bugzilla.py there).
#
# 2000-12-13 NB Enforce allowable transitions.  Fix signature of
# bugzilla_fix.update.  Pass logger through to SQL interface.
#
# 2000-12-15 NB Added verbosity control.
#
# 2001-01-11 NB Added translators for timestamps, enums, and ints.
# Refined the user translator so that we catch more errors.  Added a big
# comment explaining the user translator.  Changed the initialization
# code, as now we get a DB connection rather than the parameters for
# opening one.
#
# 2001-01-12 NB Fixed text translator (newlines are just \n).  Moved
# configuration of read-only and append-only fields to
# configure_bugzilla.py.  Stop added to bugs_activity for some fields.
#
# 2001-01-23 NB Fix something that changed in python 1.6 (str(long)).
# user translator now has unmatched_users method.  Removed duplicate
# call to bugzilla.create_p4dti_tables().
#
# 2001-01-26 NB Processmail support.
#
# 2001-02-08 NB Better checking.
#
# 2001-02-19 NB Moved keyword translation to p4.py, as it is specific to
# Perforce but generic to defect trackers.
#
# 2002-02-23 NB Made error messages more consistent.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-12 GDR Use messages for errors and e-mails.
#
# 2001-03-13 GDR Removed action field from table p4dti_bugs and all
# methods that use it (since conflict resolution is now always
# immediate).  Get translator class from translator, not replicator.
# Get defect tracker classes from dt_interface, not replicator.
#
# 2001-03-15 GDR Get the configuration from the config module.
#
# 2001-03-21 GDR The setup_for_replication() method takes a jobname
# argument.
#
# 2001-05-09 NB add_issue() allows us to add bugs to Bugzilla.
#
# 2001-06-21 NB Treat email addresses case-insensitively.  job000337.
#
# 2001-06-25 NB Added has_key to a bug and fixed date translation of
# empty dates.
#
# 2001-06-26 NB changed interface to changed_entities.
#
# 2001-06-26 NB Add bugzilla_bug.delete(), for deleting a bug.  Needed
# when creating a bug from a new Perforce job, if replicating fails
# half-way.  Also added argument to 'setup_for_replication()', to record
# in the defect tracker that this issue was created by migration from
# Perforce.  Also changed changed_entities interface.
#
# 2001-06-27 NB all_issues and changed_entities can't call the same
# underlying function.  See job000340.
#
# 2001-06-27 NB remove second argument from setup_for_replication by
# making new_issue set the issue up for replication (code moved from
# replicator.py) and extracting the common code.
#
# 2001-07-03 NB Restored middle result of changed_entities.
#
# 2001-07-13 NB date translator should return '' if match fails, so we
# can tell that it did.  MySQL will then convert that to the zero date
# anyway.
#
# 2001-07-16 GDR Call first_replication() to ensure there's a record in
# the replications table.
#
# 2001-09-19 NB Bugzilla 2.14 (job000390): move some functionality to
# bugzilla.py, which knows the Bugzilla version.
#
# 2001-10-02 GDR Report Perforce users with duplicate e-mail addresses.
#
# 2001-10-28 GDR Formatted as a document.
#
# 2001-11-01 NB Add disabled user check (job000124).
#
# 2001-11-01 NB Add poll_start and poll_end, for job000306.
#
# 2001-11-05 GDR New method new_issue_defaults.
#
# 2001-12-04 GDR New method supports.
#
# 2002-01-29 GDR User translator applies the keyword translator for
# unknown users, in case they have spaces or other forbidden characters.
#
# 2002-02-01 GDR Setup a new bug for replication without checking
# replicate_p, as specified in the IG.
#
# 2002-04-03 NB Translate bogus timestamps from Perforce into '',
# which will become now() in the Bugzilla MySQL interface.
#
# 2002-04-03 NB Added better default behaviour in creating issue.
# Handled user of 0 in qacontact field (and prohibited elsewhere).
# job000494.
#
# 2002-04-03 NB Handle migration when numeric fields are being
# replicated (the translator needs to handle '' and the new_issue
# script needs to disregard zero fields).  job000496.
#
# 2002-06-14 NB A big rewrite of the user translator, prompted by
# job000533.
#
# 2003-05-22 NB Add_replicator_user method to add the replicator user.
# Also update the can_change_field() logic and comments.
#
# 2004-05-28 NB Bugzilla 2.17.7 support: change processmail invocation
# system to use bugmail when present; changed interface to bugzilla.py
# for groups, products, and components. support membership of a single
# bug in multiple groups; changed bug change permission rules; test
# per-product group memberships when creating or editing bugs.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/dt_bugzilla.py#3 $
