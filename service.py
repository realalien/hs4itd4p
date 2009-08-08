#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#              SERVICE.PY -- NT SERVICE MANAGER FOR P4DTI
#
#             Nick Levine, Ravenbrook Limited, 2001-11-05
#
#
# 1. INTRODUCTION
#
# This Python script manages the P4DTI replicator as a service on
# Windows NT. See Chapter 18 ("Windows NT Services") of [Hammond &
# Robinson, 2000].
#
# We require the service to have the following properties:
#
# 1. it can be installed, uninstalled, started and stopped;
#
# 2. it handles startup failures gracefully - note that there is no
#    usable stdout on which to report errors;
#
# 3. it has the same functionality as run() in replicator.py - in
#    particular the same behaviour with respect to poll_period;
#
# 4. it can be started on system boot and halted on system shutdown,
#    can be started or halted from control panel or command line, and
#    these modes of interaction can be mixed;
#
# 5. it keeps running if the user who launched it logs off the system;
#
# 6. it does not prevent the system being run as a script;
#
# 7. it does not add to installation complexity;
#
# 8. it can be tested via the test suite (in particular it can work
#    with alternate configuration files by recognizing the environment
#    variable P4DTI_CONFIG).
#
# The intended readership of this document is project developers.
#
# This document is not confidential.
#
#
# 1.1. Architecture
#
# The code in this module is used in three cases:
#
#  1. By the P4DTI administrator installing, starting, stopping or
# removing the service.  (See main(), section 3).
#
#  2. By the nt_service test case in test_p4dti.py, which installs,
# starts, stops and uninstalls the service, just as the administrator
# does.
#
#  3. By the Python service manager application, when the service is
# started and stopped.  See the p4dti_service class in section 2.

import catalog
import message
import os
import sys
import win32serviceutil
import win32service
import win32event


# 2. SERVICE FRAMEWORK
#
# Modelled after examples in [Hammond & Robinson 2000].

class p4dti_service(win32serviceutil.ServiceFramework):

    # Service name in the Windows registry.
    _svc_name_ = 'p4dti_service'

    # Pretty name in the control panel "Services" applet.
    _svc_display_name_ = 'P4DTI'

    # 2001-11-09 -- Regrettably, installation by another script (for
    # example the test suite) results in a relative path in for
    # PythonClass in the registry, and so the service cannot
    # start. We therefore generate the path by hand and pass it to the
    # win32serviceutil code.

    # 2004-04-15 -- svcPath doesn't name a file. It's a string which
    # looks like the name of a file. The "type" component is the name
    # of the service, the rest is the file (less its "py" extension)
    # which the service needs to run. This is a "Python Win32
    # Extensions" hack; one of the things service.py has to do is to
    # generate this string and pass it to win32serviceutil.

    import service
    svcPath = (os.path.splitext(os.path.abspath(service.__file__))[0]
               + '.' + _svc_name_)

    def __init__(self, args):
        # Extract any configuration information from the argument
        # list; then load the configuration.
        args = self.process_arglist(args)
        # Initialize ServiceFramework.
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Create an event which we will use to wait on. The "service
        # stop" event request will set this event.
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def process_arglist(self, args):
        # We may want to load an alternate configuration file, or
        # specify alternate values for certain configuration
        # variables. We cannot control them in the usual way (through
        # an environment variable) because we are running in a system
        # environment, so we pass the values as command-line
        # arguments.
        evt_log = log_level = admin_address = None
        if len(args) > 1:
            import getopt
            try:
                opts, more = getopt.getopt(args[1:], None,
                                           ['p4dti-config=',
                                            'p4dti-evtlog=',
                                            'p4dti-loglevel=',
                                            'p4dti-adminaddr=',
                                            ])
                for opt, val in opts:
                    if opt == '--p4dti-config':
                        os.environ['P4DTI_CONFIG'] = val
                    if opt == '--p4dti-evtlog':
                        evt_log = 1
                    if opt == '--p4dti-loglevel':
                        log_level = val
                    if opt == '--p4dti-adminaddr':
                        admin_address = val
                args = [args[0]] + more
            except:
                pass

        # Now we can load the configuration...
        from config_loader import config
        # ... and reconfigure the configuration...
        if evt_log is not None:
            # Pass any value, to enable logging to NT Event Log
            config.use_windows_event_log = 1
        if log_level is not None:
            config.log_level = int(log_level)
        if admin_address is not None:
            # Pass empty string, to register administrator_address None
            # (i.e. no mail will be sent).
            config.administrator_address = admin_address or None
        # When running as an NT service, stdout goes nowhere.
        config.use_stdout_log = 0
        # ... and keep a handle on it.
        self.config = config

        # Return remaining args
        return args

    def SvcStop(self):
        # Before we do anything, tell the Service Manager that we
        # are intending to halt.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Then set the event.
        win32event.SetEvent(self.hWaitStop)

    # Irrespective of logging configuration, all services ought to
    # notify the event log on startup and shutdown.
    def SvcDoRun(self):
        # "The P4DTI service has started."
        self.log(catalog.msg(1011))
        try:
            self.run_logging_errors()
        finally:
            # "The P4DTI service has halted."
            self.log(catalog.msg(1012))

    # 2001-11-13 NDL -- Renamed method as log() so that test suite
    # will believe that messages 1011 & 1012 are in use.
    def log(self, msg):
        assert isinstance(msg, message.message)
        # If the problem occurs before the logger has been created,
        # don't confuse matters further by trying to write to it.
        # Startup is a common time for errors (faulty configuration, for
        # example), so we do not expect to be able to go via the
        # replicator to get a handle on the logger.  Instead, write
        # directly to the Windows Event Log.
        if hasattr(self.config, 'logger'):
            self.config.logger.log(msg)
        else:
            import servicemanager
            servicemanager.LogInfoMsg(str(msg))

    def run_logging_errors(self):
        # Attempt to log fatal errors before raising them. It's worth
        # doing this because full tracebacks in the Windows Event log
        # can be fairly unreadable.
        try:
            self.run()
        except:
            type, value = sys.exc_info()[:2]
            self.log_fatal_error(type, value)
            raise

    def log_fatal_error(self, type, value):
        if value is not None:
            err = '%s: %s' % (type, value)
        else:
            err = str(type)
        # "Fatal error in P4DTI service: %s."
        self.log(catalog.msg(1010, err))

    def run(self):
        # Create and initialize an instance of replicator.replicator.
        from init import r
        # Event loop analagous to that of run() in replicator.py.
        r.prepare_to_run()
        while 1:
            r.carefully_poll_databases()
            timeout = r.poll_period * 1000            # in milliseconds
            rc = win32event.WaitForSingleObject(self.hWaitStop, timeout)
            # Test return code to see whether our Event was signalled.
            if rc == win32event.WAIT_OBJECT_0:
                # We've been asked to halt. Bail out of loop:
                break


# 3. RUN AS SCRIPT
#
# If this script is run with no arguments, default behaviour is to
# install the service (and have it start up automatically on system
# boot). We ensure that the Python Service Manager is registered first
# (it does not appear to do any harm if this step is repeated).
#
# Note that when this script is used to start the service, it passes a
# message to the NT Service Manager; the script then returns
# immediately, and typically without any indication as to whether the
# p4dti startup was successful or not. The service runs in a system
# environment (as the "default user"), and the current directory is
# something like c:\winnt\system32. We extract any values against
# certain configuration environment variables at invocation time and
# pass them into the service on its command line; the service can then
# extract these values from its argument list and act on them
# appropriately.
#
# It is a mistake to attempt to remove a service which is still running,
# but it's difficult to do anything about this mistake after the fact,
# short of a reboot. We would like to prevent this by preceding 'remove'
# actions with a 'stop': we get an error if the service wasn't running
# at the time but we can catch return code 1062
# (ERROR_SERVICE_NOT_ACTIVE - see [Microsoft 2001-07-06]) and only worry
# about other non-zero codes. There is no immediately obvious clean way
# to prevent an error message from the win32serviceutil code (it just
# prints to stdout), but this is probably not going to be a problem.

def action(argv):
    handler = win32serviceutil.HandleCommandLine
    return handler(p4dti_service,
                   argv = argv,
                   serviceClassString = p4dti_service.svcPath)

# ActivePython 2.4 build 243 breaks win32serviceutil.HandleCommandLine
# by causing an error if service-specific command-line arguments are
# passed in.  We use service-specific arguments for controlling P4DTI
# items such as the log level and the config file, particularly for
# running automated tests.  So instead of using HandleCommandLine to
# start the service we use an underlying function StartService.

def start_service(arguments):
    try:
	win32serviceutil.StartService(p4dti_service._svc_name_,
				      args = arguments)
        return 0
    except win32service.error, (hr, fn, msg):
        print "Error starting service: %s" % msg
	return hr

def main(argv):
    # Things to do before an install.
    if len(argv) <= 1:
        # "Installing service to start automatically..."
        print catalog.msg(1013)
        argv = argv + '--startup auto install'.split()
    if argv[-1] == 'install':
        service_exe = win32serviceutil.LocatePythonServiceExe()
        cmd = '"%s" /register' % service_exe
        os.system(cmd)

    # Start a service.  Construct a command line and pass it into
    # start_service.

    if argv[1] == 'start':
	arguments = []
        controls = (('P4DTI_CONFIG',    '--p4dti-config'),
                    ('P4DTI_EVTLOG',    '--p4dti-evtlog'),
                    ('P4DTI_LOGLEVEL',  '--p4dti-loglevel'),
                    ('P4DTI_ADMINADDR', '--p4dti-adminaddr'),
                    )
        for key, arg in controls:
            if os.environ.has_key(key):
                arguments = arguments + [arg, os.environ[key]]
	return start_service(arguments)

    # Things to do before a remove.
    if argv[1] == 'remove':
        # "Ensuring service is stopped first..."
        print catalog.msg(1014)
        rc = action([argv[0]] + ['stop'])
        if rc == 0:
            pass
        elif rc == 1062:
            # "OK (can ignore that error). Proceed with the remove..."
            print catalog.msg(1015)
        else:
            return rc


    # Now proceed with the action.
    rc = action(argv)
    sys.stdout.flush()
    return rc


if __name__ == '__main__':
    main(sys.argv)


# A. REFERENCES
#
# [Hammond & Robinson 2000] "Python Programming on Win32"; Mark
# Hammond & Andy Robinson; O'Reilly & Associates, Inc.; 2000.
#
# [Microsoft 2001-07-06] "System Errors - Numerical Order"; Microsoft;
# 2001-07-06;
# <http://msdn.microsoft.com/library/default.asp?url=/library/en-us/wcesdkr/htm/_sdk_system_errors___numerical_order.asp>.
#
# [NDL 2001-11-15] "very minor problem with nt services" (email
# message); Nick Levine; Ravenbrook Ltd.; 2001-11-15;
# <http://info.ravenbrook.com/mail/2001/11/15/11-21-14/0.txt>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-11-05 NDL Created.
#
# 2001-11-09 NDL Added hooks etc. for test suite.
#
# 2001-11-13 GDR Set use_stdout_log to 0 to avoid logging to stdout.
# Method and variable names use underscore to separate words.
#
# 2001-11-15 NDL Add link to email describing a minor problem with the
# interaction of older (e.g. build 132) versions of win32all with this
# code and the test suite.
#
# 2001-11-20 NDL Added catalog messages for output from main().
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/service.py#1 $
