#              Perforce Defect Tracking Integration Project
#               <http://www.ravenbrook.com/project/p4dti/>
#
#                 LOGGER.PY -- PROGRAM LOGGING CLASSES
#
#             Gareth Rees, Ravenbrook Limited, 2000-10-16
#
#
# 1. INTRODUCTION
#
# This Python module implements classes for program logging -- recording
# information about the activity of a program.
#
# Logging is primarily intended to record what the integration does so
# that the administrator can:
#
#  1. undo it in an emergency [Requirements, 67];
#
#  2. debug their configuration [Requirements, 63];
#
#  3. remove the integration [Requirements, 64];
#
# and so that developers can:
#
#  4. debug modififcations of the system [Requirements, 25];
#
#  5. debug their extensions to new defect trackers [Requirements, 21].
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import message
import os
import sys
import time
import types


# 2. ABSTRACT LOGGER CLASS
#
# "logger" is an abstract class for message logs, providing uniform
# message formatting and control of logging based on the priority of
# messages, but no actual logging.
#
# When constructing an instance of this class or a subclass, pass the
# minimum priority of message that should be written to the log (e.g.,
# message.DEBUG to see all debug-level messages, or message.ERROR to
# only see errors).

class logger:
    # Experienced a failure?
    has_failed = 0

    # Minimum priority of messages to log.
    priority = message.INFO

    # Maximum length of a log message.
    max_length = 10000

    def __init__(self, priority = message.INFO, max_length = 10000):
        assert isinstance(priority, types.IntType)
        self.priority = priority
        self.has_failed = 0
        self.max_length = max_length


    # 2.1. Convert a message to a string with truncation
    #
    # Truncate message to max_length to avoid very large log messages
    # causing the Windows event log or Linux system log to crash.

    def stringify_message(self, msg):
        assert isinstance(msg, message.message)
        return str(msg)[0:self.max_length]


    # 2.2. Format a message with date
    #
    # format_with_date(msg).  Format log message and return the message
    # as a string.  Messages are prefixed with the current date and time
    # in UTC and the message id.  See message.py for details of the
    # formatting of message ids.
    #
    # The reason for the existence of this method is that not all
    # logging methods record the date (in particular, file_logger
    # doesn't).

    def format_with_date(self, msg):
        assert isinstance(msg, message.message)
        date = time.strftime('%Y-%m-%d %H:%M:%S UTC',
                             time.gmtime(time.time()))
        return "%s  %s" % (date, self.stringify_message(msg))


    # 2.3. Maybe log a message
    #
    # maybe_log(msg).  Write the message to the log (using the write()
    # method), but only if its priority is higher than self.priority.

    def maybe_log(self, msg):
        assert isinstance(msg, message.message)
        # Higher priorities have lower numbers, hence the sense of
        # this test.
        if msg.priority <= self.priority:
            self.write(msg)


    # 2.4. Write a message to the log
    #
    # write(msg).  Write the message to the log.  There is no
    # implementation in the logger class (it's an abstract class).
    # Subclasses should provide the appopriate mechanism.

    def write(self, msg):
        assert isinstance(msg, message.message)
        # logger is an abstract class; no implementation of write().
        assert 0


    # 2.5. Log a message
    #
    # log(msg). Invoke maybe_log(), with error handling. This method
    # is the external interface to the logger.  You may not override
    # this method in a subclass unless you support identical error
    # handling.  Override the maybe_log method instead.

    def log(self, msg):
        assert isinstance(msg, message.message)
        try:
            self.maybe_log(msg)
        except:
            type, value = sys.exc_info()[:2]
            self.advise_failed('%s: %s' % (type, value))


    # 2.6. Handle a log failure
    #
    # advise_failed(err).  Handle the error message by calling
    # log_failed_hook().  But only once per logger.  We will only
    # advise that a log has failed once.  Otherwise the administrator
    # could be bombarded with failure messages.

    def advise_failed(self, err):
        # Is this the first time this logger has run into problems?
        if not self.has_failed:
            self.has_failed = 1
            context = self.failure_context()
            self.log_failed_hook(err, context)


    # 2.7. User hook for log failure
    #
    # By default we just re-raise the error.  This hook can be set
    # elsewhere (by the replicator, for instance, to a method that
    # sends mail to an administrator).  For example, in a method in
    # the replicator class one could write:
    #
    #    def log_failed_hook(err, context, r=self):
    #        r.mail_report(...)
    #    self.config.logger.set_log_failed_hook(log_failed_hook)
    #
    # in order to mail the failure report to the administrator.

    def log_failed_hook(self, err, context):
        raise

    def set_log_failed_hook(self, hook):
        assert type(hook) in [types.FunctionType, types.MethodType]
        self.log_failed_hook = hook


    # 2.8. Describe context of log failure
    #
    # failure_context().  Return a message object describing the
    # context of the log failure, suitable for using as an
    # introduction to a failure report.

    def failure_context(self):
        # "An attempt to write a log message to %s failed."
        return catalog.msg(1018, self)


# 3. FILE LOGGER CLASS
#
# This subclass of logger appends messages to a file stream, or to the
# standard output if no file is specified when the instance is created.
# The output buffer is flushed after each message is written so that the
# log can be recovered even if the program crashes.

class file_logger(logger):
    file = None

    def __init__(self, file = sys.stdout, priority = message.INFO,
                 max_length = 10000):
        # Test interface, not type, since sys.stdout is not a native
        # file objectin environments like PythonWin.
        assert hasattr(file, 'write') and hasattr(file, 'flush')
        logger.__init__(self, priority, max_length)
        self.file = file

    def write(self, msg):
        assert isinstance(msg, message.message)
        self.file.write(self.format_with_date(msg))
        self.file.write('\n')
        self.file.flush()

    def failure_context(self):
        if self.file is sys.stdout:
            # "An attempt to write a log message to standard output
            # failed."
            return catalog.msg(1017)
        else:
            destination = getattr(self.file, 'name', str(self.file))
            # "An attempt to write a log message to %s failed."
            return catalog.msg(1018, destination)


# 4. SYSTEM LOGGER CLASS
#
# This subclass of logger logs messages to the system log on Unix (using
# syslog).  On other operating systems, it does nothing.

class sys_logger(logger):
    def __init__(self, priority = message.INFO, max_length = 10000):
        logger.__init__(self, priority, max_length)
        if os.name == 'posix':
            import syslog
            self.syslog = syslog.syslog
            syslog.openlog('p4dti', syslog.LOG_PID, syslog.LOG_DAEMON)
            syslog.setlogmask(syslog.LOG_UPTO(priority))

    def syslog(self, priority, text):
        pass

    # 4.1. Log a message to the system log
    #
    # We override the maybe_log() method rather than the write()
    # method because we use syslog's logmask feature instead of
    # checking the priority ourselves.

    def maybe_log(self, msg):
        assert isinstance(msg, message.message)
        self.syslog(msg.priority, self.stringify_message(msg))

    def failure_context(self):
        # "An attempt to write a log message to the system log failed."
        return catalog.msg(1019)


# 5. LOGGER CLASS FOR MULTIPLE LOGS
#
# This is a meta-logger that writes the message to each of a list of
# other loggers.  This is so that the administrator can arrange for
# messages to go to several places in the integration configuration [RB
# 2000-08-10, 5.1].

class multi_logger(logger):
    loggers = []

    def __init__(self, loggers = [], priority = message.INFO,
                 max_length = 10000):
        assert isinstance(loggers, types.ListType)
        for l in loggers:
            assert(isinstance(l, logger))
        logger.__init__(self, priority, max_length)
        self.loggers = loggers

    def maybe_log(self, msg):
        assert isinstance(msg, message.message)
        for l in self.loggers:
            l.log(msg)

    def set_log_failed_hook(self, hook):
        assert type(hook) in [types.FunctionType, types.MethodType]
        # Call superclass method.
        logger.set_log_failed_hook(self, hook)
        for l in self.loggers:
            l.set_log_failed_hook(hook)


# 6. WINDOWS EVENT LOGGER CLASS

class win32_event_logger(logger):
    # Application name.
    application = None

    # Map from message priority to Windows event type.
    event_type = None

    def __init__(self, rid, priority = message.INFO,
                 max_length = 10000):
        logger.__init__(self, priority, max_length)
        self.application = "P4DTI-" + rid
        # The "Event Message File" is eventlog.dll, in the same
        # directory as the message.py module.
        emf = os.path.join(
            os.path.dirname(os.path.abspath(message.__file__)),
            "eventlog.dll")
        import win32evtlogutil
        win32evtlogutil.AddSourceToRegistry(self.application, emf)
        import win32evtlog
        self.event_type = {
            message.EMERG:   win32evtlog.EVENTLOG_ERROR_TYPE,
            message.ALERT:   win32evtlog.EVENTLOG_ERROR_TYPE,
            message.CRIT:    win32evtlog.EVENTLOG_ERROR_TYPE,
            message.ERR:     win32evtlog.EVENTLOG_ERROR_TYPE,
            message.WARNING: win32evtlog.EVENTLOG_WARNING_TYPE,
            message.NOTICE:  win32evtlog.EVENTLOG_WARNING_TYPE,
            message.INFO:    win32evtlog.EVENTLOG_INFORMATION_TYPE,
            message.DEBUG:   win32evtlog.EVENTLOG_INFORMATION_TYPE,
            }

    def write(self, msg):
        assert isinstance(msg, message.message)
        import win32evtlogutil
        win32evtlogutil.ReportEvent(self.application, 0, 0,
                                    self.event_type[msg.priority],
                                    [self.stringify_message(msg)])

    def failure_context(self):
        # "An attempt to write a log message to the NT event log
        # failed."
        return catalog.msg(1020)


# A. REFERENCES
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
# 2000-10-16 GDR Created.
#
# 2000-11-30 GDR Added some type checking.
#
# 2001-01-19 NB Added sys_logger.
#
# 2001-01-26 NB Removed extra \n.
#
# 2001-03-01 NB Fix for job000237.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-11 GDR Formatted as a document.  Uses the message class.
# Check digit computation moved to message.py.  Loggers pay attention to
# message priority.
#
# 2001-04-10 NB job000292: Added call to str() as our message objects
# were upsetting syslog.syslog.
#
# 2001-09-12 GDR Added logger class for the Windows event log.
#
# 2001-11-06 NDL File logger works in PythonWin.
#
# 2001-11-20 NDL Added log_failed_hook.
#
# 2001-11-26 GDR Truncate log messages to a specified length.
#
# 2001-12-07 GDR Test files by interface, not type; don't assume it has
# a 'name' attribute.  Allow log failure hooks to be methods.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/logger.py#2 $
