#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#                  REPLICATOR.PY -- P4DTI REPLICATOR
#
#             Gareth Rees, Ravenbrook Limited, 2000-08-09
#
#
# 1. INTRODUCTION
#
# This Python module implements the P4DTI replicator: the component of
# the P4DTI that copies data from the defect tracker to Perforce and
# vice versa [RB 2000-08-10], in order to keep the defect tracker state
# consistent with the Perforce state [Requirements, 1] and to provide
# the ability to ask questions involving both the defect tracking system
# and Perforce [Requirements, 5].
#
# The replicator is independent of any particular defect tracker: it
# interacts with the defect tracker through the abstract interfaces
# declared in the dt_interface module and documented in [GDR 2000-10-16,
# 7].  This is to make it possible to integrate Perforce with new defect
# tracking systems [Requirements, 20, 21] and to simplify the design of
# the replicator so that it is modifiable [Requirements, 25], stable
# [Requirements, 27] and maintainable [Requirements, 30].
#
# See [GDR 2000-09-13] for the design of the replicator, its algorithms,
# and the specification of the data it stores in Perforce.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import dt_interface
import message
import p4
import re
import smtplib
import string
import sys
import time
import stacktrace
import types


# 2. CURSOR WRAPPER FOR LISTS
#
# list_cursor is a class that wraps up a list as a cursor with a
# fetchone() method.
#
# This class is used because the specification of the 'all_issues' and
# 'changed_entities' methods in the defect_tracker class has changed
# since P4DTI 1.1.1 was released.  In release 1.1.1 they were documented
# to return lists of issues.  Now they are documented to return cursors.
# We still want to support people who wrote code that returned lists, so
# this module examines the results of these methods and wraps lists with
# this class.

class list_cursor:
    def __init__(self, list):
        self.list = list

    def fetchone(self):
        if self.list:
            result = self.list[0]
            self.list = self.list[1:]
            return result
        else:
            return None


# 3. DEFECT TRACKER INTERFACE TO PERFORCE
#
# The replicator attempts to be as symmetric as possible, for simplicity
# of design.  It treats Perforce as much as possible in the same way as
# the defect tracker.
#
# It should be possible to develop a dt_perforce module that implements
# a full defect tracker interface to Perforce.  However, there will need
# to be some changes to the abstract interface [GDR 2000-10-16, 7]
# because the situation is not 100% symmetric (for example, changelists
# are only replicated in one direction).
#
# We haven't had the time to develop the revised interface and the
# implementation, so for the moment the dt_perforce class is a
# placeholder.  Eventually it will be fully functional and take over all
# Perforce operations from the replicator, which can then be simplified
# and made fully symmetric.

class dt_perforce(dt_interface.defect_tracker):
    error = "Perforce interface error"
    p4 = None

    def __init__(self, p4_interface, config):
        assert isinstance(p4_interface, p4.p4)
        self.p4 = p4_interface


# 4. REPLICATOR

class replicator:


    # 4.1. Data

    # Configuration module.
    config = None

    # Defect tracker.
    dt = None

    # Defect tracker interface to Perforce.  This is a placeholder; at
    # the moment the implementation is incomplete, but eventually it
    # will be there.
    dt_p4 = None

    # Replicator identifier.
    rid = None

    # Interface to Perforce.
    p4 = None

    # The number of columns to format e-mail messages to.
    columns = 80

    # The replicator's counter on the Perforce server.
    counter = None

    # Error object for fatal errors raised by the replicator.
    error = 'P4DTI Replicator error'

    # Map from feature name to whether the defect tracker supports it.
    # See [GDR 2000-10-16, 3.5] for names of features.
    feature = {}


    # 4.2. Initialization

    def __init__(self, dt, p4_interface, config):
        assert isinstance(dt, dt_interface.defect_tracker)
        assert isinstance(p4_interface, p4.p4)
        self.job_updates = {}
        self.dt = dt
        self.config = config
        self.rid = config.rid

        # Set the log failure hook to send a message to the P4DTI
        # administrator.
        def log_failed_hook(err, context, r=self):
            # Log the failure anyway; you never know if some other
            # logger may be able to handle it.
            r.config.logger.log(context)
            # "Error in P4DTI logger: %s"
            r.mail_report(catalog.msg(913, err), [context])
        self.config.logger.set_log_failed_hook(log_failed_hook)

        # This is incomplete.  Eventually there will be a real defect
        # tracker interface to Perforce.
        self.dt_p4 = dt_perforce(p4_interface, config)
        self.p4 = p4_interface

        # Replicator ids must match.
        if self.rid != self.dt.rid:
            # "The replicator's RID ('%s') doesn't match the defect
            # tracker's RID ('%s')."
            raise self.error, catalog.msg(833, (self.rid, self.dt.rid))

        # Make a counter name for this replicator.
        if not self.counter:
            self.counter = 'P4DTI-%s' % self.rid

        # Make a client for the replicator.
        self.create_client()

        # Initialize the defect tracking system.
        self.dt.init()
        self.determine_supported_features()

    # create_client().  Creates a client if one does not exist, or if
    # the existing client is broken.

    def create_client(self):
        client = self.p4.run('client -o')[0]
        try:
            self.p4.run('client -i', client)
        except p4.error, message:
            # "Can't use Perforce client %s."
            self.log(927, self.p4.client)
            self.log(message)
            # "Attempting to make working Perforce client %s."
            self.log(928, self.p4.client)
            # Strip out all non-essential entries in the client record.
            for k in client.keys():
                if k[0:4] == 'View' or k in ['LineEnd', 'Options', 'Host', 'code']:
                    del client[k]
            client['Description'] = 'Client created and used by P4DTI replicator.'
            self.p4.run('client -i', client)

    # determine_supported_features().  Determine which optional features
    # are supported by the defect tracker interface.

    def determine_supported_features(self):
        self.feature = {}
        if hasattr(self.dt, 'supports'):
            # Query the defect tracker's supports() method if available.
            for feature in ['filespecs', 'fixes', 'migrate_issues',
                            'new_issues', 'new_users']:
                self.feature[feature] = self.dt.supports(feature)
        else:
            # Otherwise check to see if the defect tracker and the
            # configuration offer the required interface, as promised in
            # [GDR 2000-10-16, 13.4].
            self.feature['filespecs'] = 1
            self.feature['fixes'] = 1
            self.feature['migrate_issues'] = 1
            for m in ['new_issue', 'new_issues_start',
                      'new_issues_end']:
                if not hasattr(self.dt, m):
                    self.feature['migrate_issues'] = 0
            if not hasattr(self.config, 'prepare_issue_advanced'):
                self.feature['migrate_issues'] = 0
            self.feature['new_issues'] = self.feature['migrate_issues']
            if not hasattr(self.config, 'translate_jobspec_advanced'):
                self.feature['migrate_issues'] = 0
            self.feature['new_users'] = hasattr(self.dt, 'add_user')

    # check_first_time().  Take a look at the old jobspec.  If it has no
    # P4DTI fields, then we assume that this is the first time the P4DTI
    # has been run.  If so, check for the existence of jobs; if there
    # are any, don't go ahead with the change to the jobspec but instead
    # warn the administrator.  See job000219.

    def check_first_time(self):
        if (self.config.jobspec
            and not self.p4.jobspec_has_p4dti_fields(
            self.p4.get_jobspec(),
            warn = 0)
            and self.p4.run('jobs')):
            # "You must delete your Perforce jobs before running the
            # P4DTI for the first time.  See section 5.2.3 of the
            # Administrator's Guide."
            raise self.error, catalog.msg(914)

    # update_and_check_jobspec().  If keep_jobspec is set, check the
    # current jobspec against the one we want to install.  Otherwise,
    # just go ahead and install the jobspec.  Advanced configurations
    # can turn this off by clearing config.jobspec [IG, 8.6].
    # 
    # Subsequently, the installed jobspec is checked to ensure that we
    #can run the P4DTI with it.

    def update_and_check_jobspec(self):
        if self.config.jobspec and not self.config.keep_jobspec:
                self.p4.install_jobspec(self.config.jobspec)
        self.check_jobspec()

    def check_jobspec(self):
        self.p4.check_jobspec(self.config.jobspec)

    def extend_jobspec(self, force=0):
        self.p4.extend_jobspec(self.config.jobspec, force)

    # start_logger().  Has the logger been started?  If not, start it.
    # (We must be careful not to set the logger counter to 0 more than
    # once; this will confuse Perforce [Seiwald 2000-09-11].)

    def start_logger(self):
        counters = self.p4.run('counters')
        for c in counters:
            if c.get('counter') == 'logger':
                return
        self.p4.run('counter logger 0')


    # 4.3. Logging

    # log(msg, args = ()).  Write the message to the replicator's log.
    # The msg argument can be a message instance, the number of a
    # message in the catalog (with the remaining arguments used to fill
    # in the message parameters), or a string.

    def log(self, msg, args = ()):
        if isinstance(msg, message.message):
            self.config.logger.log(msg)
        elif isinstance(msg, types.IntType):
            self.config.logger.log(catalog.msg(msg, args))
        else:
            # "%s"
            self.config.logger.log(catalog.msg(910, msg.encode('utf8')))


    # 4.4. Perforce interface
    #
    # These methods provide the replicator with an interface to
    # Perforce.  In time they can be moved to the dt_perforce class
    # (section 3).

    # all_jobs().  Return a list of all jobs.

    def all_jobs(self):
        return self.p4.run('jobs')

    # changed_entities().  Return a 3-tuple consisting of (a) changed
    # jobs, (b) changed changelists, and (c) the last log entry that
    # was considered.  The changed jobs are those that are due for
    # replication by this replicator (that is, the P4DTI-rid field of
    # the job matches the replicator id), or new jobs which pass the
    # replicate_job_p check.  The last log entry will be passed to
    # mark_changes_done.

    def changed_entities(self):
        # Get all entries from the log since the last time we updated
        # the counter.
        log_entries = self.p4.run('logger -t %s' % self.counter)
        jobs = {}
        changelists = []
        last_log_entry = None # The last entry number in the log.
        for e in log_entries:
            last_log_entry = int(e['sequence'])
            if e['key'] == 'job':
                jobname = e['attr']
                # Can we account for this log entry on the basis of
                # updates we made in the previous poll?  If so, ignore
                # the entry.
                if self.job_updates.get(jobname):
                    n_updates = self.job_updates[jobname]
                    self.job_updates[jobname] = n_updates - 1
                elif jobname == 'new':
                    # "Perforce has a job called 'new', which is
                    # illegal and will stop the P4DTI from working."
                    raise self.error, catalog.msg(896)
                elif not jobs.has_key(jobname):
                    job = self.job(jobname)
                    p4dti_rid = job.get('P4DTI-rid', 'None')
                    if (p4dti_rid == self.rid
                        or (p4dti_rid == 'None'
                            and self.config.replicate_job_p(job))):
                        jobs[jobname] = job
            elif e['key'] == 'change':
                # Collect new and updated changelists here.  A
                # changelist can change (using p4 change -f) without any
                # related jobs changing, so we need to replicate
                # changelists as well as replicating the fixes of
                # changed jobs.
                change_number = e['attr']
                try:
                    changelist = self.p4.run('change -o %s'
                                             % change_number)[0]
                    changelists.append(changelist)
                except p4.error:
                    # The changelist might not exist any more: it might
                    # have been a pending changelist that's been
                    # renumbered.  So don't replicate it.  Should it be
                    # deleted from the defect tracker?  GDR 2000-11-02.
                    pass
        self.job_updates = {}
        return jobs, changelists, last_log_entry

    # mark_changes_done(log_entry).  Update the Perforce database to
    # record the fact that the replicator has replicated all changes up
    # to log_entry.

    def mark_changes_done(self, log_entry):
        assert log_entry == None or isinstance(log_entry, types.IntType)
        # Update counter to last entry number in the log that we've
        # replicated.  If this is the last entry in the log, it has the
        # side-effect of deleting the log (see "p4 help undoc").
        if log_entry:
            self.p4.run('logger -t %s -c %d'
                        % (self.counter, log_entry))

    # clear_logger().  Clear the logger.

    def clear_logger(self):
        last_log_entry = self.p4.counter_value('logger')
        self.p4.run('logger -t %s -c %s'
                    % (self.counter, last_log_entry))

    # job(jobname).  Return the Perforce job with the given name if it
    # exists, or an empty job specification (otherwise).

    def job(self, jobname):
        assert isinstance(jobname, basestring)
        jobs = self.p4.run('job -o %s' % jobname)
        if len(jobs) != 1 or not jobs[0].has_key('Job'):
            # "Expected a job but found %s."
            raise self.error, catalog.msg(837, str(jobs))
        # Compare job names case-insensitively (see job000313).
        elif string.lower(jobs[0]['Job']) != string.lower(jobname):
            # "Asked for job '%s' but got job '%s'."
            raise self.error, catalog.msg(838, (jobname,
                                                jobs[0]['Job']))
        else:
            return jobs[0]

    # job_filespecs(job).  Return a list of filespecs for the given job.
    # Each element of the list is a filespec, as a string.

    def job_filespecs(self, job):
        assert isinstance(job, types.DictType)
        # if no P4DTI-filespecs field, do the right thing:
        job_filespecs = job.get('P4DTI-filespecs', '')
        filespecs = string.split(job_filespecs, '\n')
        # Since Perforce text fields are terminated with a newline, the
        # last item of the list must be an empty string.  Remove it.
        if filespecs[-1] != '':
            # "P4DTI-filespecs field has value '%s': this should end
            # in a newline."
            raise self.error, catalog.msg(839, job_filespecs)
        return filespecs[:-1]

    # job_fixes(job).  Return a list of fixes for the given job.  Each
    # element of the list is a dictionary with keys Change, Client,
    # User, Job, and Status.

    def job_fixes(self, job):
        assert isinstance(job, types.DictType)
        return self.p4.run('fixes -j %s' % job['Job'])

    # job_format(job).  Format a job so that people can read it.  Also,
    # indent the first line of the job so that it can be included in the
    # body of a mail message without being wrapped; see mail().

    def job_format(self, job):
        def format_item(i):
            key, value = i
            if '\n' in value:
                if value[-1] == '\n':
                    value = value[0:-1]
                value = string.join(string.split(value,'\n'),'\n\t')
                return "%s:\n\t%s" % (key, value)
            else:
                return "%s: %s" % (key, value)
        items = job.items()
        # Remove special Perforce system fields.
        items = filter(lambda i: i[0] not in ['code','specdef'], items)
        # Sort into lexical order.
        items.sort()
        return string.join(map(format_item, items), '\n')

    # job_mail_recipients(job).  Work out the people associated with the
    # job who should receive e-mail when there's a problem with that job
    # (namely the job's owner and the last person to edit the job,
    # unless either of these is the replicator).

    def job_mail_recipients(self, job):
        recipients = []

        # Owner of the job, if any.
        owner = job.get(self.config.job_owner_field, None)
        if owner:
            owner_address = self.user_email_address(owner)
            if owner_address:
                # "Job owner"
                comment = catalog.msg(925)
                recipients.append((comment, owner_address))

        # Last person to change the job, if neither replicator nor
        # owner.
        changer = job.get('P4DTI-user', None)
        if changer and changer not in [self.config.p4_user, owner]:
            changer_address = self.user_email_address(changer)
            if changer_address:
                # "Job changer"
                comment = catalog.msg(926)
                recipients.append((comment, changer_address))

        return recipients

    # job_modifier(job).  Return our best guess at who last modified the
    # job.
    #
    # If the Perforce server supports the 'fix_update' feature, then
    # this is easy: just return the P4DTI-user field (for safety in the
    # case of race conditions -- user changes interleaved with P4DTI
    # changes -- we substitute the job owner if P4DTI-user is the
    # replicator).
    #
    # However, in Perforce servers that don't support this feature, the
    # "always" fields in a job don't get modified when a job is fixed.
    # This means that the P4DTI-user field may not be accurate, since
    # there may have been fixes added later.
    #
    # So our strategy for finding the owner is as follows:
    #
    #  1. Is there a fix record, submitted more recently than the job
    # has been modified, by someone other than the replicator?  If so,
    # take the person who submitted the most recent such fix as the
    # modifier.
    #
    #  2. If not, does the P4DTI-user field contain a user other than
    # the replicator?  If so, take them as the modifier.
    #
    #  3. If not, take the job owner as the modifier.
    #
    # Note that this doesn't give a 100% accurate answer (for example,
    # if you fix a job and then delete the fix), but it's right in all
    # but a few exceptional cases.
    #
    # See job000133 and job000270 for the motivation.

    def job_modifier(self, job):
        modifier = job.get('P4DTI-user', self.config.p4_user)
        if modifier == self.config.p4_user:
            modifier = job.get(self.config.job_owner_field, modifier)

        # Perforce 2002.1 updates 'always' fields when someone modifies
        # a job by making a fix.  So the modifier is accurate.
        if self.p4.supports('fix_update'):
            return modifier

        # Dates in job fields look like 2000/12/31 23:59:59, but dates
        # in fixes are seconds since 1970-01-01 00:00:00, so convert the
        # job modification time to an integer for comparison.
        match = re.match('^(\d{4})/(\d{2})/(\d{2}) '
                         '(\d{2}):(\d{2}):(\d{2})$',
                         job.get(self.config.job_date_field,
                                 '1970/01/01 00:00:00'))
        if not match:
            # "Job '%s' has a date field in the wrong format: %s."
            raise self.error, catalog.msg(889, (job['Job'], job))
        date = time.mktime(tuple(map(int, match.groups()) + [0,0,-1]))
        fixes = self.job_fixes(job)
        for f in fixes:
            if (int(f['Date']) > date
                and f['User'] != self.config.p4_user):
                modifier = f['User']
                date = int(f['Date'])
        return modifier

    # Map from Perforce job name to the number of times we've updated
    # the job in this poll.  Used by changed_entities and updated by
    # update_job and replicate_fixes_dt_to_p4.
    job_updates = {}

    def record_job_update(self, job):
        jobname = job['Job']
        self.job_updates[jobname] = self.job_updates.get(jobname, 0) + 1

    # update_job(job, changes).  Update the job in Perforce by applying
    # the given changes.  Also update the "job" dictionary to reflect
    # these changes, and also any changes made by Perforce, such as
    # picking up the new jobname (if job['Job'] is 'new').

    update_job_re = re.compile('^Job ([^ ]+) (.*)')

    def update_job(self, job, changes = {}, force = False):
        assert isinstance(job, types.DictType)
        assert isinstance(changes, types.DictType)
        for key, value in changes.items():
            job[key] = value
        if force:
            command = 'job -i -f'
        else:
            command = 'job -i'
        results = self.p4.run(command, job)

        # Check that the results of the 'job -i' command are as
        # expected: Perforce should say something like 'Job job012345
        # saved.' or 'Job job012345 not changed.'  If the jobname was
        # 'new', then record the jobname that Perforce gave the new
        # job so that we can call setup_for_replication() in
        # replicate_many().
        if len(results) == 1 and results[0].has_key('data'):
            match = self.update_job_re.match(results[0]['data'])
            if not match or match.group(1) == 'new':
                # "Expected Perforce output of 'job -i' to say 'Job
                # jobname ...', but found '%s'."
                raise self.error, catalog.msg(897, results[0]['data'])
            elif job['Job'] == 'new':
                job['Job'] = match.group(1)
            elif job['Job'] != match.group(1):
                # "Tried to update job '%s', but Perforce replied '%s'."
                raise self.error, catalog.msg(899, (job['Job'],
                                                    results[0]['data']))
            if match.group(2) == 'saved.':
                self.record_job_update(job)
        else:
            # "Unexpected output from Perforce command 'job -i': %s."
            raise self.error, catalog.msg(898, results)

    # Return the e-mail address of a Perforce user, or None if the
    # address can't be found.

    def user_email_address(self, user):
        assert isinstance(user, basestring)
        # Even though "p4 user -o foo" doesn't actually create a user,
        # it does fail if the user foo doesn't exist and there are no
        # spare licenses.  So trap that case.  See job000204.
        try:
            u = self.p4.run('user -o %s' % user)
        except:
            return None
        # Existing users have Access and Update fields in the returned
        # structure; non-existing users don't.
        if (len(u) == 1 and u[0].has_key('Access')
            and u[0].has_key('Update') and u[0].has_key('Email')):
            return u[0]['Email']
        else:
            return None


    # 4.5. Entry points

    # check_consistency().  Run a consistency check on the two
    # databases, reporting any inconsistencies.

    def check_consistency(self):
        # "Checking consistency for replicator '%s'."
        self.log(871, self.rid)
        self.check_jobspec()
        n = 0 # Number of inconsistencies found.

        # Get issues and jobs.
        issues_cursor = self.dt.all_issues()
        # Support old all_issues specification [GDR 2000-10-16, 13.1].
        if not hasattr(issues_cursor, 'fetchone'):
            issues_cursor = list_cursor(issues_cursor)
        issue_id_to_job = {}
        jobs = {}
        for j in self.p4.run('jobs -e P4DTI-rid=%s' % self.rid):
            jobs[j['Job']] = j

        while 1:
            issue = issues_cursor.fetchone()
            if issue == None:
                break
            id = issue.id()
            jobname = issue.corresponding_id()
            # "Checking issue '%s' against job '%s'."
            self.log(890, (id, jobname))

            # Report if issue has no corresponding job.
            if issue.rid() != self.rid:
                if self.config.replicate_p(issue):
                    # "Issue '%s' should be replicated but is not."
                    self.log(872, id)
                    n = n + 1
                continue
            issue_id_to_job[id] = jobname
            if not jobs.has_key(jobname):
                # "Issue '%s' should be replicated to job '%s' but that
                # job either does not exist or is not replicated."
                self.log(873, (id, jobname))
                n = n + 1
                continue

            # Get corresponding job.
            job = jobs[jobname]
            del jobs[jobname]

            # Report if mapping is in error.
            job_issue_id = job.get('P4DTI-issue-id', 'None')
            if job_issue_id != id:
                # "Issue '%s' is replicated to job '%s' but that job is
                # replicated to issue '%s'."
                self.log(874, (id, jobname, job_issue_id))
                n = n + 1

            # Report if job and issue contents don't match.
            changes = self.translate_issue_dt_to_p4(issue, job, 1)
            if changes:
                # "Job '%s' would need the following set of changes in
                # order to match issue '%s': %s."
                self.log(875, (jobname, id, str(changes)))
                n = n + 1

            # Report if filespecs don't match.
            n = n + self.check_filespecs(issue, job)

            # Report if fixes don't match.
            n = n + self.check_fixes(issue, job)

        # There should be no remaining jobs, so any left are in error.
        for job in jobs.values():
            job_issue_id = job.get('P4DTI-issue-id', 'None')
            if issue_id_to_job.has_key(job_issue_id):
                # "Job '%s' is marked as being replicated to issue '%s'
                # but that issue is being replicated to job '%s'."
                self.log(881, (job['Job'], job_issue_id,
                               issue_id_to_job[job_issue_id]))
                n = n + 1
            else:
                # "Job '%s' is marked as being replicated to issue '%s'
                # but that issue either doesn't exist or is not being
                # replicated by this replicator."
                self.log(882, (job['Job'], job_issue_id))
                n = n + 1

        # Report on success/failure.
        if len(issue_id_to_job) == 1:
            # "Consistency check completed.  1 issue checked."
            self.log(883)
        else:
            # "Consistency check completed.  %d issues checked."
            self.log(884, len(issue_id_to_job))
        if n == 0:
            # "Looks all right to me."
            self.log(885)
        elif n == 1:
            # "1 inconsistency found."
            self.log(886)
        else:
            # "%d inconsistencies found."
            self.log(887, n)

    # check_filespecs(issue, job).  Report if the sets of filespecs
    # differ between the issue and the job.  Return the number of
    # inconsistencies found.

    def check_filespecs(self, issue, job):
        if not self.feature['filespecs']:
            return 0
        n = 0 # Number of inconsistencies found.
        issuename = issue.readable_name()
        jobname = job['Job']
        p4_filespecs = self.job_filespecs(job)
        dt_filespecs = issue.filespecs()
        diffs = self.filespecs_differences(dt_filespecs, p4_filespecs)
        for p4_filespec, dt_filespec in diffs:
            if p4_filespec and not dt_filespec:
                # "Job '%s' has associated filespec '%s' but there is no
                # corresponding filespec for issue '%s'."
                self.log(876, (jobname, p4_filespec, issuename))
                n = n + 1
            elif not p4_filespec and dt_filespec:
                # "Issue '%s' has associated filespec '%s' but there is
                # no corresponding filespec for job '%s'."
                self.log(877, (issuename, dt_filespec.name(), jobname))
                n = n + 1
            else:
                # Corresponding filespecs can't differ (since their only
                # attribute is their name).
                assert 0
        return n

    # check_fixes(issue, job).  Report if the sets of fixes differ
    # between the issue and the job.  Return the number of
    # inconsistencies found.

    def check_fixes(self, issue, job):
        if not self.feature['fixes']:
            return 0
        n = 0 # Number of inconsistencies found.
        issuename = issue.readable_name()
        jobname = job['Job']
        p4_fixes = self.job_fixes(job)
        dt_fixes = issue.fixes()
        diffs = self.fixes_differences(dt_fixes, p4_fixes)
        for p4_fix, dt_fix in diffs:
            if p4_fix and not dt_fix:
                # "Change %s fixes job '%s' but there is no
                # corresponding fix for issue '%s'."
                self.log(878, (p4_fix['Change'], jobname, issuename))
                n = n + 1
            elif not p4_fix and dt_fix:
                # "Change %d fixes issue '%s' but there is no
                # corresponding fix for job '%s'."
                self.log(879, (dt_fix.change(), issuename, jobname))
                n = n + 1
            else:
                # "Change %s fixes job '%s' with status '%s', but change
                # %d fixes issue '%s' with status '%s'."
                self.log(880, (p4_fix['Change'], jobname,
                               p4_fix['Status'], dt_fix.change(),
                               issuename, dt_fix.status()))
                n = n + 1
        return n

    # migrate_users() ensures that there is a defect tracker user
    # corresponding to each Perforce user.

    def migrate_users(self):
        if not self.feature['new_users']:
            # "Defect tracker '%s' does not support migration of
            # Perforce users."
            raise self.error, catalog.msg(906, self.config.dt_name)
        self.dt.add_replicator_user()
        p4_users = self.p4.run("users")
        for user in p4_users:
            self.dt.add_user(user['User'],
                             user['Email'],
                             user['FullName'])

    # migrate() migrates all existing Perforce jobs to the DT.  Note
    # that we can't just call replicate_new_issue_p4_to_dt here because
    # that method assumes we have the new jobspec in place (so that we
    # can replicate backwards) which we don't until migration is
    # finished.  Instead, we replicate backwards in a bunch after
    # migration succeeds.

    def migrate(self, starting_with = None):
        if not self.feature['migrate_issues']:
            # "Defect tracker '%s' does not support migration of
            # Perforce jobs."
            raise self.error, catalog.msg(905, self.config.dt_name)
        jobs = self.all_jobs()
        try:
            self.dt.new_issues_start()
            for job in jobs:
                if starting_with and job['Job'] != starting_with:
                    continue
                else:
                    starting_with = None
                if job.get('P4DTI-rid', 'None') != 'None':
                    # "Not migrating job '%s' (already replicated)."
                    self.log(916, job['Job'])
                elif not self.config.migrate_p(job):
                    # "Not migrating job '%s' (migrate_p returned 0)."
                    self.log(917, job['Job'])
                else:
                    try:
                        # "Before translating jobspec, job '%s' is %s"
                        self.log(915, (job['Job'], job))
                        job = self.config.translate_jobspec_advanced(
                            self.config, self.dt, self.dt_p4, job)
                        if not isinstance(job, types.DictType):
                            # "Expected translate_jobspec to return a
                            # dictionary, but instead it returned %s."
                            raise self.error, catalog.msg(924, job)
                        # "After translating jobspec, job '%s' is %s"
                        self.log(918, (job['Job'], job))
                        issue = self.create_issue(job)
                    except:
                        # "Migrating job '%s'..."
                        self.log(921, job['Job'])
                        raise
                    # "Migrated job '%s' to issue '%s'."
                    self.log(892, (job['Job'], issue.readable_name()))
                    # Replicate filespecs, fixes and changelists.
                    self.replicate_filespecs_p4_to_dt(issue, job)
                    self.replicate_fixes_p4_to_dt(issue, job)
        finally:
            self.dt.new_issues_end()

        # "Migration completed."
        self.log(895)

    # poll().  Poll the defect tracker and Perforce, replicate changes,
    # then stop.

    def poll(self):
        self.check_first_time()
        self.update_and_check_jobspec()
        self.start_logger()
        self.poll_databases()

    # refresh_perforce_jobs().  Replicate all issues from the defect
    # tracker.  Note: does not delete jobs first.

    def refresh_perforce_jobs(self):
        self.update_and_check_jobspec()
        self.replicate_all_dt_to_p4()
        self.start_logger()
        self.clear_logger()

    # carefully_poll_databases(). Poll once, handling exceptions

    def carefully_poll_databases(self):
        try:
            self.poll_databases()
            # Reset poll period when the poll was successful.
            self.poll_period = self.config.poll_period
        except AssertionError:
            # Assertions indicate severe bugs in the replicator.  It
            # might cause serious data corruption if we continue.
            # We also want these failures to be reported, and they
            # might go unreported if the replicator carried on
            # going.
            raise
        except KeyboardInterrupt:
            # Allow people to stop the replicator with Control-C.
            raise
        except:
            self.mail_report(
                # "The replicator failed to poll successfully."
                catalog.msg(863),
                # "The replicator failed to poll successfully,
                # because of the following problem:"
                [catalog.msg(864)])
            # The poll failed; it's likely that it will fail again
            # for the same reason the next time we poll.  Back off
            # exponentially so as not to mail bomb the admin.  See
            # job000215 and job000135.
            self.poll_period = self.poll_period * 2

    # prepare_to_run(). Invoked once when run() is called, to preform
    # startup tasks.

    def prepare_to_run(self):
        self.check_first_time()
        self.update_and_check_jobspec()
        self.start_logger()
        self.poll_period = self.config.poll_period
        self.mail_startup_message()

    # run().  Repeatedly (handling exceptions) poll and replicate
    # changes.

    def run(self):
        self.prepare_to_run()
        while 1:
            self.carefully_poll_databases()
            time.sleep(self.poll_period)


    # 4.6. E-mail

    # mail(recipients, subject, body).  Send e-mail to the given
    # recipients (pls the administrator) with the given subject and
    # body.  The recipients argument is a list of pairs (role, address).
    # The body argument is a list of paragraphs.  Paragraphs belonging
    # to the message.message class will be wrapped to 80 columns.
    # Ordinary strings will be left alone.  Log the contents of the
    # message.

    def mail(self, recipients, subject, body):
        assert isinstance(recipients, types.ListType)
        assert isinstance(subject, message.message)
        assert isinstance(body, types.ListType)
        # Always e-mail the administrator
        recipients.append(('P4DTI administrator',
                           self.config.administrator_address))
        # Build the contents of the RFC822 To: header.
        to = string.join(map(lambda r: "%s <%s>" % r, recipients), ', ')
        # "Mailing '%s'."
        self.log(800, to)
        self.log(subject)
        map(self.log, body)
        # Don't send e-mail if administrator_address or smtp_server is
        # None.
        if (self.config.administrator_address == None
            or self.config.smtp_server == None):
            return
        smtp = smtplib.SMTP(self.config.smtp_server)
        message_paragraphs = [
            ("From: %s\n"
             "To: %s\n"
             "Subject: %s"
             % (self.config.replicator_address, to, subject)),
            # "This is an automatically generated e-mail from the
            # Perforce Defect Tracking Integration replicator '%s'."
            catalog.msg(865, self.rid),
            ] + body
        def fmt(s, columns = self.columns):
            if isinstance(s, message.message):
                return s.wrap(columns)
            else:
                return s.encode('utf8')
        message_text = string.join(map(fmt, message_paragraphs), "\n\n")
        smtp.sendmail(self.config.replicator_address,
                      map(lambda r: r[1], recipients),
                      message_text)
        smtp.quit()

    # exception_message(exc_info).  Return a message object describing
    # the given exception, or None if there was no exception.  The
    # exc_info argument must be the results of calling sys.exc_info().

    def exception_message(self, exc_info):
        exc_type, exc_value = exc_info[0:2]
        if isinstance(exc_value, message.message):
            return exc_value
        elif exc_type is not None:
            # "Error (%s): %s"
            return catalog.msg(891, (exc_type, exc_value))
        else:
            # We're not in the context of an exception, so there's
            # nothing to report.
            return None

    def stacktrace(self, exc_info):
        return string.join(apply(stacktrace.format_exception, exc_info),
                           '')

    # mail_report(subject, intro, extra=[], job=None, error=1).  Compose
    # and send e-mail when something's gone wrong.  If a job argument is
    # supplied, it's the job to which the mail applies, and is used to
    # deduce who to send the e-mail to.  If no job argument is supplied,
    # then mail is to the administrator (only).  Iff error is 1, the
    # mail includes an error message and traceback.

    def mail_report(self, subject, intro, extra=[], job=None, error=1):
        assert isinstance(subject, message.message)
        assert isinstance(intro, types.ListType)
        assert isinstance(extra, types.ListType)
        for m in intro + extra:
            assert (isinstance(m, basestring)
                    or isinstance(m, message.message))
        assert job is None or isinstance(job, types.DictType)
        if error:
            try:
                exc_info = sys.exc_info()
                msg = self.exception_message(exc_info)
                body = intro + [ msg ] + extra + [
                    # "Here's a full Python traceback:"
                    catalog.msg(852),
                    self.stacktrace(exc_info),
                    ]
            finally:
                # Break circular reference.  See [van Rossum 2000-03-22,
                # 3.1] and rule code/python/compatible.
                del exc_info
        else:
            body = intro + extra
        if job is None:
            self.mail([], subject, body)
        else:
            # "If you are having continued problems, please contact
            # your P4DTI administrator <%s>."
            m = catalog.msg(853, self.config.administrator_address)
            body.append(m)
            self.mail(self.job_mail_recipients(job), subject, body)

    # mail_startup_message(self).  Send a message to the administrator
    # when the replicator starts to run.  It exercises the SMTP server,
    # which is the only way we can really test that part of the
    # configuration.  This is very important, because the replicator may
    # often be run unattended, so we can't rely on log messages being
    # read.
    #
    # Also this is a good time to tell the administrator about any
    # unmatched and duplicate user records, as he may wish to take
    # action to fix them.

    def mail_startup_message(self):
        unmatches = self.config.user_translator.unmatched_users(
            self.dt, self.dt_p4)
        (unmatched_dt_users, unmatched_p4_users, dt_user_msg,
         p4_user_msg) = unmatches[0:4]
        if len(unmatches) >= 8:
            (duplicate_dt_users, duplicate_p4_users,
             duplicate_dt_msg, duplicate_p4_msg) = unmatches[4:8]
        else:
            duplicate_dt_users = None
            duplicate_p4_users = None

        # "The P4DTI replicator has started."
        subject = catalog.msg(866)
        body = [ subject ]
        if unmatched_p4_users:
            body = body + [
                # "The following Perforce users do not correspond to
                # defect tracker users.  The correspondence is based on
                # the e-mail addresses in the defect tracker and
                # Perforce user records."
                catalog.msg(867),
                p4_user_msg,
                self.format_email_table(unmatched_p4_users),
                ]
        if unmatched_dt_users:
            body = body + [
                # "The following defect tracker users do not correspond
                # to Perforce users.  The correspondence is based on the
                # e-mail addresses in the defect tracker and Perforce
                # user records."
                catalog.msg(870),
                dt_user_msg,
                self.format_email_table(unmatched_dt_users),
                ]
        if duplicate_p4_users:
            body = body + [
                duplicate_p4_msg,
                self.format_email_table(duplicate_p4_users),
                ]
        if duplicate_dt_users:
            body = body + [
                duplicate_dt_msg,
                self.format_email_table(duplicate_dt_users),
                ]
        self.mail([], subject, body)

    # format_email_table(self, user_dict).  Format a table of users and
    # e-mail addresses.  The users argument is a dictoinary mapping
    # userid to e-mail address.  Return a string containing the table.

    def format_email_table(self, user_dict):
        # "User"
        user_header = catalog.msg(868).text
        # "E-mail address"
        email_header = catalog.msg(869).text
        longest_user = len(user_header)
        longest_email = len(email_header)
        users = user_dict.keys()
        users.sort()
        for u in users:
            if len(u) > longest_user:
                longest_user = len(u)
            if len(user_dict[u]) > longest_email:
                longest_email = len(user_dict[u])
        spaces = longest_user + 2 - len(user_header)
        table = [ "  %s%s%s" % (user_header, ' ' * spaces,
                                email_header),
                  "  " + "-" * (longest_user + 2 + longest_email) ]
        for u in users:
            email = user_dict[u]
            if email == '':
                email = '<none>'
            spaces = longest_user + 2 - len(u)
            table.append("  %s%s%s" % (u, ' ' * spaces, email))
        return string.join(table, "\n")


    # 4.7. Replication

    # fixes_differences(dt_fixes, p4_fixes).  Each argument is a list of
    # fixes for the same job/issue.  Return list of pairs (p4_fix,
    # dt_fix) of corresponding fixes which differ.  Elements of pairs
    # are None where there is no corresponding fix.

    def fixes_differences(self, dt_fixes, p4_fixes):
        assert isinstance(dt_fixes, types.ListType)
        assert isinstance(p4_fixes, types.ListType)

        # Make hash from change number to p4 fix.
        p4_fix_by_change = {}
        for p4_fix in p4_fixes:
            assert isinstance(p4_fix, types.DictType)
            p4_fix_by_change[int(p4_fix['Change'])] = p4_fix

        # Make pairs (dt fix, corresponding p4 fix or None).
        pairs = []
        for dt_fix in dt_fixes:
            assert isinstance(dt_fix, dt_interface.defect_tracker_fix)
            if not p4_fix_by_change.has_key(dt_fix.change()):
                pairs.append((None, dt_fix))
            else:
                p4_fix = p4_fix_by_change[dt_fix.change()]
                del p4_fix_by_change[dt_fix.change()]
                if dt_fix.status() != p4_fix['Status']:
                    pairs.append((p4_fix, dt_fix))

        # Remaining p4 fixes are unpaired.
        for p4_fix in p4_fix_by_change.values():
            pairs.append((p4_fix, None))

        return pairs

    # filespecs_differences(dt_filespecs, p4_filespecs).  Each argument
    # is a list of filespecs for the same job/issue.  Return list of
    # pairs (p4_filespec, dt_filespec) of filespecs which differ.
    # Elements of pairs are None where there is no corresponding
    # filespec (this is always the case since there is no associated
    # information with a filespec; the function is like this for
    # consistency with fixes_differences, and so that it is easy to
    # extend if there is ever a way to associate information with a
    # filespec, for example the nature of the association -- see
    # requirement 55).

    def filespecs_differences(self, dt_filespecs, p4_filespecs):
        assert isinstance(dt_filespecs, types.ListType)
        assert isinstance(p4_filespecs, types.ListType)

        # Make hash from name to p4 filespec.
        p4_filespec_by_name = {}
        for p4_filespec in p4_filespecs:
            assert isinstance(p4_filespec, basestring)
            p4_filespec_by_name[p4_filespec] = p4_filespec

        # Make pairs (dt filespec, None).
        pairs = []
        for dt_filespec in dt_filespecs:
            assert isinstance(dt_filespec,
                              dt_interface.defect_tracker_filespec)
            if not p4_filespec_by_name.has_key(dt_filespec.name()):
                pairs.append((None, dt_filespec))
            else:
                del p4_filespec_by_name[dt_filespec.name()]

        # Make pairs (None, p4 filespec).
        for p4_filespec in p4_filespec_by_name.values():
            pairs.append((p4_filespec, None))

        return pairs

    # conflict_policy(issue, job).  This method is called when both the
    # issue and the corresponding job have changed since the last time
    # they were consistent.  Return 'p4' if the Perforce job is correct
    # and should be replicated to the defect tracker.  Return 'dt' if
    # the defect tracking issue is correct and should be replicated to
    # Perforce.  Return anything else to indicate that the replicator
    # should take no further action.
    #
    # The default policy is to return 'dt'.  This is because we're
    # treating the Perforce jobs database as a scratch copy of the real
    # data in the defect tracker.  So when there's a conflict the defect
    # tracker is correct.  See job000102 for details.

    def conflict_policy(self, issue, job):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        return 'dt'

    # poll_databases(). Poll the DTS for changed issues. Poll Perforce
    # for changed jobs and changelists.  Replicate all of these
    # entities.

    def poll_databases(self):
        # "Poll starting."
        self.log(911)
        if hasattr(self.dt, 'poll_start'):
            self.dt.poll_start()
        try:
            # Get the changed issues (ignore changed changelists if any
            # since we only replicate changelists from Perforce to the
            # defect tracker).
            changed_issues, _, dt_marker = self.dt.changed_entities()
            # Support old changed_entities specification [GDR
            # 2000-10-16, 13.1].
            if not hasattr(changed_issues, 'fetchone'):
                changed_issues = list_cursor(changed_issues)
            changed_jobs, changelists, p4_marker = self.changed_entities()

            # Replicate the issues and the jobs.
            self.replicate_many(changed_issues, changed_jobs)

            # Replicate the affected changelists.
            if self.feature['fixes']:
                for c in changelists:
                    self.replicate_changelist_p4_to_dt(c)

            # Tell the defect tracker and Perforce that we've finished
            # replicating these changes.
            self.dt.mark_changes_done(dt_marker)
            self.mark_changes_done(p4_marker)
        finally:
            if hasattr(self.dt, 'poll_end'):
                self.dt.poll_end()
        # "Poll finished."
        self.log(912)

    # replicate_all_dt_to_p4().  Go through all the issues in the defect
    # tracker, set them up for replication if necessary, and replicate
    # them to Perforce.

    def replicate_all_dt_to_p4(self):
        all_issues_cursor = self.dt.all_issues()
        # Support old all_issues specification [GDR 2000-10-16, 13.1].
        if not hasattr(all_issues_cursor, 'fetchone'):
            all_issues_cursor = list_cursor(all_issues_cursor)
        while 1:
            issue = all_issues_cursor.fetchone()
            if not issue:
                break
            if issue.rid():
                # only replicate issues which we replicate
                if issue.rid() != self.rid:
                    continue
            else:
                # only start replicating issues which we should replicate
                if not self.config.replicate_p(issue):
                    continue
            jobname = self.issue_jobname(issue)
            self.replicate(issue, { 'Job': jobname }, 'dt', force=True)

    def replicate_changelist_p4_to_dt(self, changelist):
        assert isinstance(changelist, types.DictType)
        change = int(changelist['Change'])
        client = changelist['Client']
        date = self.config.date_translator.translate_1_to_0(
            changelist['Date'], self.dt, self.dt_p4)
        description = self.config.text_translator.translate_1_to_0(
            changelist['Description'], self.dt, self.dt_p4)
        status = changelist['Status']
        user = self.config.user_translator.translate_1_to_0(
            changelist['User'], self.dt, self.dt_p4)
        if self.dt.replicate_changelist(change, client, date,
                                        description, status, user):
            # "Replicated changelist %d."
            self.log(802, change)

    # issue_jobname(issue).  Return the name of the job to which the
    # issue should be replicated.  If we've replicated this issue before
    # (that is, if issue.rid() is not the empty string), then the defect
    # tracker already knows the jobname.  If the administrator has
    # specified 'use_perforce_jobnames', use 'new'.  Otherwise, ask the
    # defect tracker to suggest a name.

    def issue_jobname(self, issue):
        if not issue.rid() and self.config.use_perforce_jobnames:
            return 'new'
        else:
            return issue.corresponding_id()

    # replicate_many(issues_cursor, jobs).  Replicate the issues and
    # jobs.  The issues argument is a list of issues (which must belong
    # to a subclass of defect_tracker_issue; the jobs list is a hash
    # from jobname to job).
    #
    # The reason why the arguments have different conventions (list vs
    # hash) is that the algorithm for getting the changed jobs from the
    # p4 logger outpt involves constructing a hash from jobname to job,
    # and it seems silly to turn this hash back into a list only to
    # immediately turn it back into a hash again.

    def replicate_many(self, issues_cursor, jobs):
        assert hasattr(issues_cursor, 'fetchone')
        assert isinstance(jobs, types.DictType)

        while 1:
            issue = issues_cursor.fetchone()
            if issue == None:
                break
            assert isinstance(issue, dt_interface.defect_tracker_issue)

            # Don't replicate issues which fail replicate_p.  (But if
            # the issue is already set up for replication, don't ask
            # again.)
            if not issue.rid() and not self.config.replicate_p(issue):
                continue

            jobname = self.issue_jobname(issue)
            if jobs.has_key(jobname):
                job = jobs[jobname]
                self.replicate(issue, job, 'both')
                del jobs[jobname]
            else:
                job = self.job(jobname)
                self.replicate(issue, job, 'dt')

        # Now go through the remaining changed jobs.
        for job in jobs.values():
            assert isinstance(job, types.DictType)
            issue_id = job.get('P4DTI-issue-id', 'None')
            if issue_id != 'None':
                issue = self.dt.issue(issue_id)
                if not issue:
                    # "Asked for issue '%s' but got an error instead."
                    raise self.error, catalog.msg(888, issue_id)
                self.replicate(issue, job, 'p4')
            else:
                # Job is new in Perforce, so create new issue in the
                # defect tracker.
                self.replicate_new_issue_p4_to_dt(job)

    # Replicate newly-created job over to defect tracker
    def replicate_new_issue_p4_to_dt(self, job):
        if not self.feature['new_issues']:
            return
        jobname = job['Job']
        try:
            issue = self.create_issue(job)
        except:
            self.mail_report(
                # "Job '%s' could not be replicated to the defect
                # tracker."
                catalog.msg(908, jobname),
                # "The replicator failed to replicate Perforce job '%s'
                # to the defect tracker, because of the following
                # problem:"
                [catalog.msg(909, jobname)],
                [], job)
            return

        issuename = issue.readable_name()
        # "Migrated job '%s' to issue '%s'."
        self.log(892, (jobname, issuename))
        if self.config.replicate_p(issue):
            try:
                # The result of replicating back may be different from
                # the original job.
                job['P4DTI-rid'] = self.rid
                job['P4DTI-issue-id'] = issue.id()
                # "Post-migration replication of issue '%s' to job
                # '%s'."
                self.log(894, (issue.readable_name(), job['Job']))
                changes = self.translate_issue_dt_to_p4(issue, job, 1)
                if changes:
                    # "-- Defect tracker made changes as a result of
                    # the update: %s."
                    self.log(826, changes)
                    self.update_job(job, changes)
                self.replicate_filespecs_p4_to_dt(issue, job)
                self.replicate_fixes_p4_to_dt(issue, job)
            except:
                # Undo our half-completed work: delete the issue and
                # revert the job.
                issue.delete()
                self.update_job(job, { 'P4DTI-rid': 'None',
                                       'P4DTI-issue-id': 'None' })
                self.mail_report(
                    # "Job '%s' could not be replicated to issue '%s'."
                    catalog.msg(848, (jobname, issuename)),
                    # "The replicator failed to replicate Perforce job
                    # '%s' to defect tracker issue '%s', because of the
                    # following problem:"
                    [catalog.msg(851, (jobname, issuename))],
                    [], job)

    # replicate(issue, job, changed).  Replicate an issue to or from the
    # corresponding job.  The changed argument is 'dt' if the defect
    # tracking issue has changed but not the Perforce job; 'p4' if vice
    # versa; 'both' if both have changed.
    #
    # Basically this method is a series of conditions that end in one of
    # the following cases:
    #
    #  1. Replicate the issue to the job or vice versa (the normal mode
    # of operation).
    #
    #  2. Overwrite the job with the issue or vice versa (if they have
    # both changed and the conflict policy says to overwrite).  This is
    # just like replication, except that the old version of the
    # overwritten entity gets mailed to its owner as a record in case
    # data was lost.
    #
    #  3. Do nothing (if both have changed and the conflict policy says
    # to do nothing).
    #
    #  4. Revert the job from the issue (if we tried to replicate the
    # job to the issue but it failed, probably due to lack of privileges
    # or invalid data).

    def replicate(self, issue, job, changed, force = False):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        assert changed in ['dt','p4','both']

        issuename = issue.readable_name()
        jobname = job['Job']

        # Figure out what to do with this issue and job.  Do nothing?
        # Overwrite issue with job?  Overwrite job with issue?

        # Only the defect tracker issue has changed.
        if changed == 'dt':
            # "Replicating issue '%s' to job '%s'."
            self.log(804, (issuename, jobname))
            self.replicate_issue_dt_to_p4(issue, job, force=force)
            if not issue.rid():
                # If we started out with jobname == 'new', then by
                # this time it must have been set to the new jobname
                # by the update_job() method.
                if job['Job'] == 'new':
                    # "Replicated issue '%s' to Perforce, but didn't
                    # get a jobname for it (the 'Job' field is still
                    # 'new')."
                    raise self.error, catalog.msg(904, (issue.id()))
                issue.setup_for_replication(job['Job'])
                # "Set up issue '%s' to replicate to job '%s'."
                self.log(803, (issue.id(), job['Job']))

        # Only the Perforce job has changed.
        elif changed == 'p4':
            # "Replicating job '%s' to issue '%s'."
            self.log(805, (jobname, issuename))
            try:
                self.replicate_issue_p4_to_dt(issue, job)
            except:
                self.revert_issue_dt_to_p4(issue, job)

        # Both have changed.  Apply the conflict resolution policy.
        else:
            assert changed == 'both'
            # "Issue '%s' and job '%s' have both changed.  Consulting
            # conflict resolution policy."
            self.log(806, (issuename, jobname))
            decision = self.conflict_policy(issue, job)
            if decision == 'dt':
                # "Defect tracker issue '%s' and Perforce job '%s'
                # have both changed since the last time the replicator
                # polled the databases.  The replicator's conflict
                # resolution policy decided to overwrite the job with
                # the issue."
                reason = [ catalog.msg(841, (issuename, jobname)) ]
                self.overwrite_issue_dt_to_p4(issue, job, reason, 0)
            elif decision == 'p4':
                # "Defect tracker issue '%s' and Perforce job '%s'
                # have both changed since the last time the replicator
                # polled the databases.  The replicator's conflict
                # resolution policy decided to overwrite the issue
                # with the job."
                reason = [ catalog.msg(842, (issuename, jobname)) ]
                self.overwrite_issue_p4_to_dt(issue, job, reason, 0)
            else:
                # "Conflict resolution policy decided: no action."
                self.log(807)

    # revert_issue_dt_to_p4(self, issue, job).  This is called when an
    # error has occurred in replicating from Perforce to the defect
    # tracker.  The most likely reason for this is a privilege failure
    # (the user is not allowed to edit that issue in that way) or a
    # failure to put valid values in the job fields.  In this case, set
    # the job back to a copy of the issue.

    def revert_issue_dt_to_p4(self, issue, job):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        issuename = issue.readable_name()
        jobname = job['Job']
        # Save exception information because we might need to send a
        # message with two stack tracebacks!
        exc_info = sys.exc_info()
        try:
            try:
                # Get the issue again, since it might have been changed
                # in memory in the course of the failed replication.
                # Note new variable name so as not to overwrite the old
                # issue.  (Can we avoid all this nonsense by keeping
                # better track of old and new issues?)  GDR 2000-10-31.
                issue_2 = self.dt.issue(issue.id())
                if not issue_2:
                    # "Issue '%s' not found."
                    raise self.error, catalog.msg(840, issue.id())
                self.overwrite_issue_dt_to_p4(
                    issue_2, job, [
                    # "The replicator failed to replicate Perforce job
                    # '%s' to defect tracker issue '%s', because of the
                    # following problem:"
                    catalog.msg(851, (jobname, issuename)),
                    ])
            except:
                # Replicating back to Perforce failed.  Report both
                # errors to the administrator.
                self.mail_report(
                    # "Job '%s' could not be replicated to issue '%s'."
                    catalog.msg(848, (jobname, issuename)), [
                    # "The replicator failed to replicate Perforce job
                    # '%s' to defect tracker issue '%s' because of this
                    # problem:"
                    catalog.msg(854, (jobname, issuename)),
                    self.exception_message(exc_info),
                    # "Here's a full Python traceback:"
                    catalog.msg(852),
                    self.stacktrace(exc_info),
                    # "The replicator attempted to restore the job to a
                    # copy of the issue, but this failed too, because of
                    # the following problem:"
                    catalog.msg(855),
                    ], [
                    # "The replicator has now given up."
                    catalog.msg(856),
                    ])
        finally:
            # Break circular reference.  See [van Rossum 2000-03-22,
            # 3.1] and rule code/python/compatible.
            del exc_info

    # overwrite_issue_p4_to_dt(self, issue, job, reason).  As
    # replicate_issue_p4_to_dt, but e-mails an old copy of the issue to
    # the owner of the job and the administrator.  The reason argument
    # is a list of message objects giving the reason for the
    # overwriting.  If the error argument is 1, the mail message
    # includes an error message and stack traceback.

    def overwrite_issue_p4_to_dt(self, issue, job, reason, error=1):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        assert isinstance(reason, types.ListType)
        issuename = issue.readable_name()
        jobname = job['Job']
        # "Overwrite issue '%s' with job '%s'."
        self.log(810, (issuename, jobname))
        # Build e-mail before overwriting so we get the old issue.
        # "Issue '%s' overwritten by job '%s'."
        subject = catalog.msg(857, (issuename, jobname))
        extra = [
            # "The replicator has therefore overwritten defect tracker
            # issue '%s' with Perforce job '%s'."
            catalog.msg(858, (issuename, jobname)),
            # "The defect tracker issue looked like this before being
            # overwritten:"
            catalog.msg(859),
            str(issue),
            ]
        self.replicate_issue_p4_to_dt(issue, job)
        self.mail_report(subject, reason, extra, job, error)

    # overwrite_issue_dt_to_p4(self, issue, job, reason).  As
    # replicate_issue_dt_to_p4, but e-mails an old copy of the issue to
    # the owner of the job and the administrator.  The reason argument
    # is a list of strings or message objects given a reason for the
    # overwriting.  If the error argument is 1, the mail message
    # includes an error message and stack traceback.

    def overwrite_issue_dt_to_p4(self, issue, job, reason, error=1):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        assert isinstance(reason, types.ListType)
        issuename = issue.readable_name()
        jobname = job['Job']
        # "Overwrite job '%s' with issue '%s'."
        self.log(811, (jobname, issuename))
        # Build e-mail before overwriting so we get the old job.
        # "Job '%s' overwritten by issue '%s'."
        subject = catalog.msg(860, (jobname, issuename))
        extra = [
            # "The replicator has therefore overwritten Perforce job
            # '%s' with defect tracker issue '%s'.  See section 2.2 of
            # the P4DTI User Guide for more information."
            catalog.msg(861, (jobname, issuename)),
            # "The job looked like this before being overwritten:"
            catalog.msg(862),
            self.job_format(job),
            ]
        self.replicate_issue_dt_to_p4(issue, job, force=True)
        self.mail_report(subject, reason, extra, job, error)

    # replicate_issue_dt_to_p4(issue, old_job).  Replicate the given
    # issue from the defect tracker to Perforce.

    def replicate_issue_dt_to_p4(self, issue, job, force = False):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)

        # Transform the issue into a job.  This has to be done first
        # because the job might be new, and we won't be able to
        # replicate fixes or filespecs until the job's been created
        # (p4 fix won't accept non-existent jobnames).  I suppose I
        # could create a dummy job to act as a placeholder here, but
        # that's not easy at all -- you have to know quite a lot about
        # the jobspec to be able to create a job.
        changes = self.translate_issue_dt_to_p4(issue, job)
        if changes:
            # "-- Changed fields: %s."
            self.log(812, changes)
            self.update_job(job, changes, force=force)
        else:
            # "-- No issue fields were replicated."
            self.log(813)

        self.replicate_filespecs_dt_to_p4(issue, job)
        self.replicate_fixes_dt_to_p4(issue, job, force)

    # replicate_filespecs_dt_to_p4(issue, job).  Replicate filespecs
    # from the defect tracker to Perforce.

    def replicate_filespecs_dt_to_p4(self, issue, job):
        if not self.feature['filespecs']:
            return
        dt_filespecs = issue.filespecs()
        p4_filespecs = self.job_filespecs(job)
        if self.filespecs_differences(dt_filespecs, p4_filespecs):
            names = map(lambda f: f.name(), dt_filespecs)
            self.update_job(job, { 'P4DTI-filespecs':
                                   string.join(names,'\n') })
            # "-- Filespecs changed to '%s'."
            self.log(814, string.join(names))

    # replicate_fixes_dt_to_p4(issue, job).  Replicate fixes from the
    # defect tracker to Perforce.

    def replicate_fixes_dt_to_p4(self, issue, job, force=False):
        if not self.feature['fixes']:
            return
        p4_fixes = self.job_fixes(job)
        dt_fixes = issue.fixes()
        job_status = None
        diffs = self.fixes_differences(dt_fixes, p4_fixes)
        jobname = job['Job']
        for p4_fix, dt_fix in diffs:
            if p4_fix and not dt_fix:
                self.p4.run('fix -d -c %s %s'
                            % (p4_fix['Change'], jobname))
                self.record_job_update(job)
                # "-- Deleted fix for change %s."
                self.log(815, p4_fix['Change'])
            elif not p4_fix and dt_fix:
                try:
                    self.p4.run('fix -s %s -c %d %s'
                                % (dt_fix.status(), dt_fix.change(),
                                   jobname))
                except p4.error, message:
                    # We get an error here if the changelist was somehow
                    # deleted.  In this case there's not much we can do
                    # except log the error.  See job000128.
                    self.log(message)
                else:
                    self.record_job_update(job)
                    job_status = dt_fix.status()
                    # "-- Added fix for change %d with status %s."
                    self.log(816, (dt_fix.change(), dt_fix.status()))
            elif p4_fix['Status'] != dt_fix.status():
                self.p4.run('fix -s %s -c %d %s'
                            % (dt_fix.status(), dt_fix.change(),
                               jobname))
                self.record_job_update(job)
                job_status = dt_fix.status()
                # "-- Fix for change %d updated to status %s."
                self.log(817, (dt_fix.change(), dt_fix.status()))
            else:
                # This should't happen, since fixes_differences returns
                # only a list of pairs which differ.
                assert 0

        # It might be the case that the job status has been changed in
        # the course of creating a fix record.  Restore the correct
        # status if necessary.
        if (job_status and job_status
            != job.get(self.config.job_status_field, None)):
            self.update_job(job, {
                'Status': job[self.config.job_status_field] },
                            force=force)

    # replicate_issue_p4_to_dt(issue, job).  Replicate the given job
    # from Perforce to the defect tracker.

    def replicate_issue_p4_to_dt(self, issue, job):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)

        self.replicate_fixes_p4_to_dt(issue, job)
        self.replicate_filespecs_p4_to_dt(issue, job)

        # Transform the job into an issue and update the issue.
        changes = self.translate_issue_p4_to_dt(issue, job)
        if changes:
            # "-- Changed fields: %s."
            self.log(824, repr(changes))
            p4_user = self.job_modifier(job)
            dt_user = self.config.user_translator.translate_1_to_0(
                p4_user, self.dt, self.dt_p4)
            issue.update(dt_user, changes)
        else:
            # "-- No job fields were replicated."
            self.log(825)

        # The issue may have changed as a consequence of updating it.
        # For example, in TeamTrack the issue's owner changes when an
        # issue goes through a transition.  So we fetch the issue again,
        # check for changes and replicate them back to the job if we
        # find them.  See job000053.
        new_issue = self.dt.issue(issue.id())
        if not new_issue:
            # "Issue '%s' not found."
            raise self.error, catalog.msg(840, issue.id())
        new_changes = self.translate_issue_dt_to_p4(new_issue, job, 1)
        if new_changes:
            # "-- Defect tracker made changes as a result of the update:
            # %s."
            self.log(826, new_changes)
            self.update_job(job, new_changes)

    # replicate_filespecs_p4_to_dt(issue, job).  Replicate filespecs for
    # the given job from Perforce to the defect tracker.

    def replicate_filespecs_p4_to_dt(self, issue, job):
        if not self.feature['filespecs']:
            return
        p4_filespecs = self.job_filespecs(job)
        dt_filespecs = issue.filespecs()
        filespec_diffs = self.filespecs_differences(dt_filespecs,
                                                    p4_filespecs)
        for p4_filespec, dt_filespec in filespec_diffs:
            if dt_filespec and not p4_filespec:
                dt_filespec.delete()
                # "-- Deleted filespec %s."
                self.log(822, dt_filespec.name())
            elif not dt_filespec:
                issue.add_filespec(p4_filespec)
                # "-- Added filespec %s."
                self.log(823, p4_filespec)
            else:
                # This should't happen, since filespecs_differences
                # returns only a list of pairs which differ.
                assert 0

    # replicate_fixes_p4_to_dt(issue, job).  Replicate fixes for the
    # given job from Perforce to the defect tracker.  Ensures that the
    # changelists for the fixes are also replicated.
    #
    # If you change this function, you may have to change the regression
    # test for job000385; see test_p4dti.py.

    def replicate_fixes_p4_to_dt(self, issue, job, failed_before = 0):
        if not self.feature['fixes']:
            return
        p4_fixes = self.job_fixes(job)
        dt_fixes = issue.fixes()
        fix_diffs = self.fixes_differences(dt_fixes, p4_fixes)
        for p4_fix, dt_fix in fix_diffs:
            if dt_fix and not p4_fix:
                dt_fix.delete()
                # "-- Deleted fix for change %d."
                self.log(818, dt_fix.change())
            else: # p4 fix has changed
                # "-- Considering Perforce fix %s."
                self.log(819, p4_fix)
                (change, client, date, status,
                 user) = self.translate_fix_p4_to_dt(p4_fix)
                # make sure changelist is replicated
                try:
                    changelist = self.p4.run('change -o %s' %
                                             change)[0]
                except p4.error:
                    # The changelist might have been renumbered since we
                    # called job_fixes; see job000385.  If it has, then
                    # try again.  But don't get stuck in an infinite
                    # loop.
                    if failed_before:
                        raise
                    else:
                        self.replicate_fixes_p4_to_dt(issue, job,
                                                      failed_before = 1)
                        return
                self.replicate_changelist_p4_to_dt(changelist)
                if not dt_fix: # new fix; add to DT
                    issue.add_fix(change, client, date, status, user)
                    # "-- Added fix for change %s with status %s."
                    self.log(820, (p4_fix['Change'], p4_fix['Status']))
                elif dt_fix.status() != p4_fix['Status']:
                    # status changed
                    dt_fix.update(change, client, date, status, user)
                    # "-- Fix for change %s updated to status %s."
                    self.log(821, (p4_fix['Change'], p4_fix['Status']))
                else:
                    # This should't happen, since fixes_differences
                    # returns only a list of pairs which differ.
                    assert 0

    # translate_fix_p4_to_dt(p4_fix).  Translate a Perforce fix record
    # to a defect tracker fix object.

    def translate_fix_p4_to_dt(self, p4_fix):
        assert isinstance(p4_fix, types.DictType)
        change = int(p4_fix['Change'])
        client = p4_fix['Client']
        date = self.config.date_translator.translate_1_to_0(
            p4_fix['Date'], self.dt, self.dt_p4)
        status = p4_fix['Status']
        user = self.config.user_translator.translate_1_to_0(
            p4_fix['User'], self.dt, self.dt_p4)
        return change, client, date, status, user

    # translate_issue_dt_to_p4(issue, job).  Return changes as a
    # dictionary but don't apply them yet.  The optional third argument
    # missing_is_empty determines whether a missing field in a Perforce
    # job is considered identical to an empty string.

    def translate_issue_dt_to_p4(self, issue, job, missing_is_empty=0):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        p4_default_value = None
        if missing_is_empty:
            p4_default_value = ''
        changes = {}
        # Do the P4DTI fields need to be changed?  If so, record in
        # changes.
        for key, value in [('P4DTI-rid', self.rid),
                           ('P4DTI-issue-id', issue.id())]:
            if job.get(key, None) != value:
                changes[key] = value
        # What about the replicated fields?
        for dt_field, p4_field, trans in self.config.field_map:
            try:
                p4_value = trans.translate_0_to_1(
                    issue[dt_field], self.dt, self.dt_p4, issue, job)
            except:
                # "Translating issue field '%s' (value '%s') to job
                # field '%s'..."
                self.log(922, (dt_field, issue[dt_field], p4_field))
                raise
            if job.get(p4_field, p4_default_value) != p4_value:
                changes[p4_field] = p4_value
        return changes

    # translate_issue_p4_to_dt(issue, job).  Return changes as a
    # dictionary but don't apply them yet.

    def translate_issue_p4_to_dt(self, issue, job):
        assert isinstance(issue, dt_interface.defect_tracker_issue)
        assert isinstance(job, types.DictType)
        changes = {}
        for dt_field, p4_field, trans in self.config.field_map:
            # Missing fields indicate optional fields without a value --
            # this happens when the empty string has been supplied for
            # the value.  So supply the empty string ourselves.  See
            # job000181.
            p4_value = job.get(p4_field, '')
            try:
                dt_value = trans.translate_1_to_0(
                    p4_value, self.dt, self.dt_p4, issue, job)
            except:
                # "Translating job field '%s' (value '%s') to issue
                # field '%s'..."
                self.log(923, (p4_field, p4_value, dt_field))
                raise
            if dt_value != issue[dt_field]:
                changes[dt_field] = dt_value
        return changes

    # create_issue(job).  Makes a new issue corresponding to the
    # job.  Returns the new issue.

    def create_issue(self, job):
        assert isinstance(job, types.DictType)
        dict = {}
        for dt_field, p4_field, trans in self.config.field_map:
            # Missing fields indicate optional fields without a value --
            # this happens when the empty string has been supplied for
            # the value.  So supply the empty string ourselves.  See
            # job000181.  When migrating, this will also happen for
            # fields which we are about to add to the jobspec.
            p4_value = job.get(p4_field, '')
            dt_value = trans.translate_1_to_0(
                p4_value, self.dt, self.dt_p4, None, job)
            dict[dt_field] = dt_value
        # "Raw issue: %s"
        self.log(919, dict)
        self.config.prepare_issue_advanced(
            self.config, self.dt, self.dt_p4, dict, job)
        # "Prepared issue: %s"
        self.log(920, dict)
        return self.dt.new_issue(dict, job['Job'])


# A. REFERENCES
#
# [GDR 2000-09-13] "Replicator design"; Gareth Rees; Ravenbrook Limited;
# 2000-09-13;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/replicator/>.
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
# [RB 2000-08-10] "Perforce Defect Tracking Integration Architecture";
# Richard Brooksby; Ravenbrook Limited; 2000-08-10;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/design/architecture/>.
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
# [Seiwald 2000-09-11] "Re: Is 'p4 counter logger 0' idempotent?"
# (e-mail message); Christopher Seiwald; Perforce Software; 2000-09-11;
# <http://info.ravenbrook.com/mail/2000/09/11/16-45-04/0.txt>.
#
# [Seiwald 2000-11-28] "Re: Can we rely on 'always' fields not appearing
# in 'job -o newjob'?" (e-mail message); Christopher Seiwald; Perforce
# Software; 2000-11-28;
# <http://info.ravenbrook.com/mail/2000/11/28/17-31-46/0.txt>.
#
# [van Rossum 2000-03-22] "Python Library Reference (version 1.5.2)";
# Guide van Rossum; 2000-03-22;
# <http://www.python.org/doc/1.5.2p2/lib/lib.html>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-12-05 NB addess -> address
#
# 2000-12-05 GDR Imported p4 module so replicator can catch p4.error.
# Added replicator method mail_concerning_job() for e-mailing people
# about a job.  There were several places where the owner of a job was
# been fetched and e-mailed, some of which were buggy.  This method
# replaces all those instances, hopefully correctly.
#
# 2000-12-06 GDR Fixed the replicator's user_email_address method so
# that it really returns None when there is no such user.
#
# 2000-12-06 GDR Updated supported Perforce changelevel to 18974 (this
# is the changelevel we document against).
#
# 2000-12-06 GDR Fixing job000133 (replicator gets wrong user when a job
# is fixed): When the last person who changed the job is the replicator
# user, update the issue on behalf of the job owner instead.
#
# 2000-12-06 GDR If the owner of a job and the person who last changed
# it are the same (a common occurrence), include them only once in any
# e-mail sent by the replicator about that job.
#
# 2000-12-06 GDR E-mail messages from the replicator concerning
# overwritten jobs are much improved.
#
# 2000-12-06 GDR The overwriting methods now send e-mail with the new
# issue/job in them, not the old issue/job.
#
# 2000-12-07 GDR When there's no error message (typically in the case of
# assertion failure), say so.  Format the job properly in all messages
# (including the one sent by the conflict method).  Use "Perforce job"
# and "defect tracker issue" for clarity.  (Even better would be to have
# a defect_tracker.name so it could say "TeamTrack issue".)
#
# 2000-12-07 GDR Created new class dt_perforce; a placeholder for an
# eventual full implementation of a defect_tracker subclass that
# interfaces to Perforce.
#
# 2001-01-19 NB Better stack traces.
#
# 2001-01-19 GDR Handle empty fields.  Fix comments.
#
# 2001-01-23 NB SMTP server test (unmatched users).
#
# 2001-02-04 GDR Updated definition of defect_tracker.all_issues()
# method.
#
# 2001-02-12 GDR Fixed bug in check_consisteney.
#
# 2001-02-13 GDR Don't send e-mail if administrator_address or
# smtp_server is None.
#
# 2001-02-14 GDR user_email_address returns None if the user doesn't
# exist, even when there are no spare licenses (see job000204).
#
# 2001-02-16 NB Added replicate-p configuration parameter.
#
# 2001-02-21 GDR The replicator backs off exponentially if it fails to
# poll successfully, so as not to mailbomb the administrator.
#
# 2001-02-22 GDR replicate_changelist_p4_to_dt applies a text translator
# to the change description, since a change description can have several
# lines of text.
#
# 2001-02-23 GDR Added a corresponding_id method to the
# defect_tracker_issue class.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-11 GDR Use messages for errors, logging and e-mail.
#
# 2001-03-13 GDR Removed the recording of conflicts.  Conflict
# resolution is always immediate.  Moved translator class to translator
# module.  Moved defect tracker interface classes to dt_interface.py.
#
# 2001-03-14 GDR Use messages when consistency checking.
#
# 2001-03-15 GDR Get configuration from config module.
#
# 2001-03-16 GDR Added refresh_perforce_jobs() method.
#
# 2001-03-21 GDR The setup_for_replication() method takes a jobname
# argument.
#
# 2001-03-23 GDR New method job_modifier returns a best guess at who
# last modified the job, to fix job000270.
#
# 2001-03-24 GDR Check supported Perforce server changelevel in p4.py,
# not replicator.__init__ (so that we find out if p4 -G jobspec -i will
# work before actually trying it in init.py).
#
# 2001-03-25 RB Moved message 889 to catalog due to merge from version
# 1.0 sources.
#
# 2001-05-17 GDR Defect tracker methods 'add_issue' and
# 'changed_entities' may return cursors as well as lists.
#
# 2001-05-19 GDR Added progress report for consistency checking.
#
# 2001-05-22 GDR Compare job names case-insensitively when fetching a
# job to work around job000313.
#
# 2001-06-14 GDR The reason argument to overwrite_issue_dt_to_p4 must
# consist only of messages, since they are logged as well as mailed.
# Each call to the defect_tracker.issue() method now has error checking.
#
# 2001-06-15 NB Moved functionality out of init because it's not all
# required by all the scripts.  Creation of client and calling
# defect_tracker.init moved to __init__ method.  Checking of jobspec
# moved to new method check_jobspec and called from check, refresh and
# run.
#
# 2001-06-25 NB post-migration replication now works!
#
# 2001-06-25 NB Now support the 'use_perforce_jobnames' configuration
# parameter by specifying 'new' for the jobname in replicate_many()
# and then recording the jobname when we find out what it is in
# update_job().
#
# 2001-06-26 NB Now support the creation of new jobs in Perforce.
# Also moved the replication of changelists, and changed the interface
# to changed_entities (so that changelists are replicated iff the
# matching fixes are replicated).
#
# 2001-06-27 NB Moved code from new_issue out to the defect tracker
# (changed new_issue interface).
#
# 2001-06-29 NB Produce full traceback if migration fails.
#
# 2001-06-30 GDR The replicator doesn't stop if it can't replicate a fix
# because the changelist has been deleted (see job000128).
#
# 2001-07-04 NB Changed issue creation system so we use the regular
# field map.
#
# 2001-08-06 GDR Specify -1 for DST argument to mktime().
#
# 2001-10-02 GDR Include users with duplicate e-mail addresses in
# startup message.  See job000308.
#
# 2001-10-03 GDR Handle renumbered changelist race condition during
# replication of fixes from Perforce to the defect tracker; see
# job000385.
#
# 2001-10-07 GDR Reformatted as a document.
#
# 2001-10-23 GDR Renamed poll() as poll_databases(); added poll() entry
# point.  Report error if jobname is still new after update_job.  Don't
# call replicate_issue_p4_to_dt after migrating; just replicate fixes
# and filespecs.  Wrap migration code with checks that the feature is
# supported.  Protect new_issues_end with a try ... finally.
#
# 2001-10-29 GDR Send e-mail if create_issue fails.  Always log e-mail
# even if it doesn't get sent.
#
# 2001-11-01 NB Add calls to poll_start and poll_end, for job000306.
#
# 2001-11-05 GDR Rename migrate_issue as prepare_issue_advanced; new
# configuration parameter replicate_job_p.
#
# 2001-11-07 NDL Extracted contents of run() into smaller functions
# to make them acessible to NT service code.
#
# 2001-11-09 NDL Added debug messages at start and end of
# poll_databases().
#
# 2001-11-19 NDL Changed text of message 891 (to make it more general).
#
# 2001-11-20 GDR Rename pre_migrate_issue to translate_jobspec_advanced.
# Update Perforce jobspec in entry points where needed.
#
# 2001-11-21 GDR Allow migration to be run multiple times.  Use hasattr
# consistently.
#
# 2001-11-22 GDR Simplify migration by not replicating back (this means
# that migration doesn't touch Perforce jobs).
#
# 2001-11-26 GDR More debugging messages when migrating.
#
# 2001-11-27 GDR Support starting migration at a particular job.
#
# 2001-11-28 GDR Don't assume that jobs have fields other than 'Job':
# use job.get(field, default) consistently.  Don't delete all jobs when
# refreshing; instead replicate from the defect tracker, taking care
# never to run "p4 job -o JOB" in case a job fails to match the jobspec.
#
# 2001-11-29 GDR Added messages explaining what was happening when an
# error happened.  Consider missing field equal to empty one when
# replicating back from the defect tracker or when checking consistency.
#
# 2001-12-04 GDR Handle sets of supported features.
#
# 2001-12-08 GDR Don't include an error message and stack traceback in
# an ordinary conflict report.  Delete traceback variables as advised in
# [van Rossum 2000-03-22, 3.1].
#
# 2002-01-28 GDR Don't replicate changes in Perforce that we made in the
# previous poll (see record_job_update).  In Perforce 2002.1, use the
# P4DTI-user field as an accurate guide as to who last edited the job
# (see job_modifier).
#
# 2002-01-31 GDR Don't replicate changelists unless the defect tracker
# supports the fixes feature.
#
# 2002-02-01 GDR Put replicate_* functions in a more logical order.
# Call config.replicate_p directly rather than via the defect tracker
# issue.
#
# 2002-03-28 NB Correct lambda syntax.
#
# 2003-05-21 NB Removed a specialized piece of control flow which
# protects against some TeamTrack-specific errors.
#
# 2003-05-22 NB Code to add the replicator user to Bugzilla when
# migrating Perforce users.
#
# 2003-05-30 NB When replicating all issues to Perforce, take care not
# to replicate ones which are replicated by someone else.
#
# 2003-05-30 NB Work around broken client spec or depot list.
#
# 2003-12-05 NB Changed interface to jobspec-checking function.
#
# 2003-12-12 NB Change jobspec-related functions to expose them to new
# scripts.
#
# 2006-02-28 NB Counter value marshal format has changed. job001342.
#
# 2006-07-23 NB Use p4 job -i -f when running the refresh.py script.
# job001468.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/replicator.py#4 $
