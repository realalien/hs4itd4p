#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#                P4.PY -- PYTHON INTERFACE TO PERFORCE
#
#             Gareth Rees, Ravenbrook Limited, 2000-09-25
#
#
# 1. INTRODUCTION
#
# This module defines the 'p4' class, which provides an interface to
# Perforce.
#
# "p4 help usage" (p4 2002.1) says:
#
# 	The -G flag causes all output (and batch input for form commands
# 	with -i) to be formatted as marshalled Python dictionary objects.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.
#
#
# 1.1. Using the p4 class
#
# To use this class, create an instance, passing appropriate parameters
# if necessary (if parameters are missing, the interface doesn't supply
# values for them, so Perforce will pick up its normal defaults from
# environment variables).
#
#   import p4
#   p4i = p4.p4(port = 'perforce:1666', user = 'root')
#
# The 'run' method takes a Perforce command and returns a list of
# dictionaries; for example:
#
#   >>> for c in p4i.run('changes -m 2'):
#   ...     print c['change'], c['desc']
#   ...
#   10021 Explaining how to use the autom
#   10020 Archiving new mail
#
# To pass information to Perforce, supply a dictionary as the second
# argument, for example:
#
#   >>> job = p4i.run('job -o job000001')[0]
#   >>> job['Title'] = string.replace(job['Title'], 'p4dti', 'P4DTI')
#   >>> p4i.run('job -i', job)
#   [{'code': 'info', 'data': 'Job job000001 saved.', 'level': 0}]
#
# Note the [0] at the end of line 1 of the above example: the run()
# method always returns a list, even of 1 element.  This point is easy
# to forget.

import catalog
import marshal
import os
import re
import string
import tempfile
import types
import portable
import locale
import codecs

error = 'Perforce error'


# 2. THE P4 CLASS

class p4:
    client = None
    client_executable = None
    logger = None
    password = None
    port = None
    user = None
    config_file = None
    unicode = False
    encoding = 'utf-8'


    # 2.1. Create an instance
    #
    # We supply a default value for the client_executable parameter, but
    # for no others; Perforce will use its own default values if these
    # are not supplied.  If logger is None then no messages will be
    # logged.
    #
    # We check that the server and client are recent enough to support
    # various options required for the operation of the P4DTI.  See
    # the method check_changelevels.

    def __init__(self, client = None, client_executable = 'p4',
                 logger = None, password = None, port = None,
                 user = None, config_file = None):
        self.client = client
        self.client_executable = client_executable
        self.logger = logger
        self.password = password
        self.port = port
        self.user = user
	self.config_file = config_file

	# If config_file is specified then create and fill
	# config file.
        # In future we might check whether the config file
        # already exists.
	if self.config_file:
	    f = open(self.config_file, 'w')
	    portable.protect_file(self.config_file)
	    f.write("P4PASSWD="+self.password+"\n")
	    f.close()
            # Set P4CONFIG environment variable so that the p4 command
            # picks up the config file.  Relies on putenv() being
            # implemented, which it is on any POSIX system, and Windows.
	    os.environ["P4CONFIG"]=self.config_file

        # discover and check the client and server changelevels.
        self.check_changelevels()

        # discover server Unicode status
        self.check_unicode()

    # 2.2. Write a message to the log
    #
    # But only if a logger was supplied.

    def log(self, id, args = ()):
        if self.logger:
            msg = catalog.msg(id, args)
            self.logger.log(msg)
	
    # 2.3. Dump a marshalled object (marshalling version 0) to a file.
    # 
    # This utility function is required because Python 2.4 breaks
    # binary compatibility of marshalled objects.  p4 -G expects
    # marshalled objects of format 0 (i.e. Python < 2.4).

    def marshal_dump_0(self, obj, file):
        if marshal.__dict__.has_key('version'):
            marshal.dump(obj, file, 0)
        else:
            marshal.dump(obj, file)

    # 2.4. Run a Perforce command
    #
    # run(arguments, input): Run the Perforce client with the given
    # command-line arguments, passing the dictionary 'input' to the
    # client's standard input.
    #
    # The arguments should be a Perforce command and its arguments, like
    # "jobs -o //foo/...".  Options should generally include -i or -o to
    # avoid forms being put up interactively.
    #
    # Return a list of dictionaries containing the output of the
    # Perforce command.  (Each dictionary contains one Perforce entity,
    # so "job -o" will return a list of one element, but "jobs -o" will
    # return a list of many elements.)

    def run(self, arguments, input = None, repeat = False):
        assert isinstance(arguments, basestring)
        assert input is None or isinstance(input, types.DictType)

        # Build a command line suitable for use with CMD.EXE on Windows
        # NT, or /bin/sh on POSIX.  Make sure to quote the Perforce
        # command if it contains spaces.  See job000049.
        if ' ' in self.client_executable:
            command_words = ['"%s"' % self.client_executable]
        else:
            command_words = [self.client_executable]
        command_words.append('-G')
        if self.port:
            command_words.extend(['-p', self.port])
        if self.user:
            command_words.extend(['-u', self.user])
        if self.password and not self.config_file:
            command_words.extend(['-P', self.password])
        if self.client:
            command_words.extend(['-c', self.client])
        if self.unicode:
            command_words.extend(['-C', 'utf8'])
        command_words.append(arguments.encode('utf8'))

        # Pass the input dictionary (if any) to Perforce.
        temp_filename = None
        if input:
            input = self.encode_dict(input)
            tempfile.template = 'p4dti_data'
            temp_filename = tempfile.mktemp()
            # Python marshalled dictionaries are binary, so use mode
            # 'wb'.
            temp_file = open(temp_filename, 'wb')
            self.marshal_dump_0(input, temp_file)
            temp_file.close()
            command_words.extend(['<', temp_filename])
            # "Perforce input: '%s'."
            self.log(700, input)
        command = string.join(command_words, ' ')
        # "Perforce command: '%s'."
        self.log(701, command)

        stream = portable.popen_read_binary(command)
        # Read the results of the Perforce command.
        results = []
        try:
            while 1:
                results.append(marshal.load(stream))
        except EOFError:
            if temp_filename:
                os.remove(temp_filename)

        for r in results:
            if isinstance(r,dict):
                for (k,v) in r.items():
                    if isinstance(v, str):
                        r[k] = v.decode(self.encoding, 'replace')

        # Check the exit status of the Perforce command, rather than
        # simply returning empty output when the command didn't run for
        # some reason (such as the Perforce server being down).  This
        # code was inserted to resolve job job000158.  RB 2000-12-14
        exit_status = stream.close()
        if exit_status != None:
            # "Perforce status: '%s'."
            self.log(702, exit_status)
        # "Perforce results: '%s'."
        self.log(703, results)

        # Check for errors from Perforce (either errors returned in the
        # data, or errors signalled by the exit status, or both) and
        # raise a Python exception.
        #
        # Perforce signals an error by the presence of a 'code' key in
        # the dictionary output.  (This isn't a totally reliable way to
        # spot an error in a Perforce command, because jobs can have
        # 'code' fields too.  See job000003.  However, the P4DTI makes
        # sure that its jobs don't have such a field.)
        if (len(results) == 1 and results[0].has_key('code')
            and results[0]['code'] == 'error'):
            msg = results[0]['data'].strip()
            if exit_status:
                if msg.find('Unicode') != -1:
                    self.unicode = not(self.unicode)
                    unicode_switch = (self.unicode and 'on') or 'off'
                    if (not repeat):
                        # "Perforce message '%s'.  Switching Unicode
                        # mode %s to retry."
                        self.log(734, (msg, unicode_switch))
                        return self.run(arguments, input, repeat = True)
                    else:
                        # "Perforce message '%s'.  Is P4CHARSET set with a
                        # non-Unicode server? Reverting to Unicode mode %s."
                        raise error, catalog.msg(736, (msg, unicode_switch))
                else:
                    # "%s  The Perforce client exited with error code %d."
                    raise error, catalog.msg(706, (msg, exit_status))
            else:
                # "%s"
                raise error, catalog.msg(708, msg)
        elif exit_status:
            # "The Perforce client exited with error code %d.  The
            # server might be down; the server address might be
            # incorrect; or your Perforce license might have expired."
            raise error, catalog.msg(707, exit_status)
        else:
            return results

    # Modify a dictionary which has some Unicode elements, such that
    # they are all encoded according to our chosen encoding

    def encode_dict(self, unicode_dict):
        d = {}
        for (k,v) in unicode_dict.items():
            if isinstance(v, unicode):
                v = v.encode(self.encoding, 'replace')
            d[k] = v
        return d

    # 2.5. Does the Perforce server support a feature?
    #
    # supports(feature) returns 1 if the Perforce server has the
    # feature, 0 if it does not.  You can interrogate the following
    # features:
    #
    # fix_update     Does Perforce update 'always' fields in a job when it
    #                is changed using the 'fix' command?
    # p4dti          Is the Perforce version supported by the P4DTI?
    # counter_value  Are counter values returned in a 'value' field?
    # info_unicode   Does p4 -G info report unicode status?

    def supports(self, feature):
        if feature == 'p4dti':
            return self.server_changelevel >= 18974
        elif feature == 'fix_update':
            return self.server_changelevel >= 29455
        elif feature == 'counter_value':
            return self.server_changelevel >= 86944
        elif feature == 'info_unicode':
            return self.server_changelevel >= 85665
        else:
            return 0

    # 2.6. Check the Perforce client and server changelevels.
    # 
    # We check that the Perforce client and server are recent enough
    # to support various operations required by the P4DTI, and store
    # the client and server changelevels in the p4 object for other
    # subsequent checks (for example, those made by the 'supports'
    # function above).
    # 
    # We check that the Perforce client named by the client_executable
    # parameter is recent enough that it supports the -G option.  If
    # we use the -G option on an old client, we get an error
    # "ValueError: bad marshal data" (the marshal module is failing to
    # read Perforce's error message "Invalid option: -G.").
    #
    # We get the client changelevel by running "p4 -V" and parsing the
    # output. It should contain a line which looks like
    # "Rev. P4/NTX86/2000.2/19520 (2000/12/18)."  In this example the
    # changelevel is 19520.  If no line looks like this, then raise an
    # error anyway.  (This makes the module fragile if Perforce change
    # the format of the output of "p4 -V".)
    # 
    # We check that the Perforce server named by the port parameter is
    # recent enough that it supports p4 -G jobspec -i.
    #
    # We get the server changelevel by running "p4 info" and parsing
    # the output (because the output format of "p4 -G info" is
    # different in Perforce 2003.2beta from previous Perforce
    # releases, and may change again in future).  It should contain a
    # line which looks like "Server version: P4D/FREEBSD4/2002.2/40318
    # (2003/01/17)" In this example, the changelevel is 40318.  If no
    # line looks like this, then raise an error anyway (this makes the
    # module fragile if Perforce change the format of the output of
    # "p4 info".
    #
    # Note that for "p4 info" we do not need the user, the client, or
    # the password.

    def check_changelevels(self):
        # client changelevel first.
        self.client_changelevel = 0
        supported_client = 16895
        (command, result, status) = self.run_p4_command('-V')
        match = re.search('Rev\\. [^/]+/[^/]+/[^/]+/([0-9]+)', result)
        if match:
            self.client_changelevel = int(match.group(1))
            if self.client_changelevel < supported_client:
                # "Perforce client changelevel %d is not supported
                # by P4DTI.  Client must be at changelevel %d or
                # above."
                raise error, catalog.msg(704, (self.client_changelevel,
                                               supported_client))
        else:
            # "The command '%s' didn't report a recognizable version
            # number.  Check your setting for the 'p4_client_executable'
            # parameter."
            raise error, catalog.msg(705, command)

        # now server changelevel.
        self.server_changelevel = 0
        if self.port:
            command = '-p %s info' % self.port
        else:
            command = 'info'
        (command, result, status) = self.run_p4_command(command)
        if status:
            # "The Perforce client exited with error code %d.  The
            # server might be down; the server address might be
            # incorrect; or your Perforce license might have expired."
            raise error, catalog.msg(707, status)
        match = re.search('Server version: '
                          '[^/]+/[^/]+/[^/]+/([0-9]+)', result)
        if match:
            self.server_changelevel = int(match.group(1))
        else:
            # "The Perforce command 'p4 info' didn't report a
            # recognisable version."
            raise error, catalog.msg(835)
        if not self.supports('p4dti'):
            # "The Perforce server changelevel %d is not supported by
            # the P4DTI.  See the P4DTI release notes for Perforce
            # server versions supported by the P4DTI."
            raise error, catalog.msg(834, self.server_changelevel)

    # Determine Unicode status of the Perforce server.  This should be
    # easier than this, but one can't say p4 -C none to force the
    # client into non-Unicode mode, so any P4CHARSET from the
    # environment, the registry, or a config file will give us a
    # Unicode client.

    def check_unicode(self):
        # Figure out Unicode support from p4 info output,
        # if we're using a P4D which provides it there.
        # Otherwise we can look at the "unicode" counter
        # (which we can only inspect if we 
        info = self.run("info")[0]
        if self.supports('info_unicode'):
            self.unicode = info.has_key('unicode')
        else:
            self.unicode = True # Force -C utf8 on first attempt
            unicode_counter = self.counter_value('unicode')
            self.unicode = (unicode_counter == '1')
        if self.unicode:
            self.encoding = 'utf8'
        else:
            (_, self.encoding) = locale.getdefaultlocale()
            try:
                codec = codecs.lookup(self.encoding)
            except LookupError:
                # default to Latin-1 encoding, which is
                # at least defined for every octet.
                self.encoding = 'latin-1'

    # Run a Perforce command without -G.  Returns the command, the
    # output text, and the exit status.

    def run_p4_command(self, arguments):
        command = self.client_executable
        # quote P4 executable if it contains a space; see job000049.
        if ' ' in command:
            command = '"%s"' % command
        command = command + ' ' + arguments
        # "Perforce command: '%s'."
        self.log(701, command)
        stream = os.popen(command ,'r')
        result = stream.read()
        exit_status = stream.close()
        if exit_status:
            # "Perforce status: '%s'."
            self.log(702, exit_status)
        # "Perforce results: '%s'."
        self.log(703, result)
        return (command, result, exit_status)

    # 3. HANDLING JOBSPECS
    #
    # Jobspecs passed to or from Perforce ("p4 -G jobspec -i"
    # or "p4 -G jobspec -o") look like this:
    #
    # { 'Comments': '# Form comments...',
    #   'Fields0':  '101 Job word 32 required',
    #   'Fields1':  '102 State select 32 required',
    #   'Values1':  '_new/assigned/closed/verified/deferred',
    #   'Presets1': '_new',
    #   ...
    # }
    #
    # Jobspec structures in the rest of the P4DTI look like this
    # [GDR 2000-10-16, 8.4]:
    #
    # ('# A Perforce Job Specification.\n'
    #   ...,
    #    [(101, 'Job', 'word', 32, 'required', None, None, None, None),
    #     (102, 'Status', 'select', 10, 'required', 'open', 'open/suspended/closed/duplicate', None, None),
    #     ...])
    #
    # The elements in each tuple being:
    #
    #  0: number;
    #  1: name;
    #  2: "datatype" (word/text/line/select/date);
    #  3: length (note: relates to GUI display only);
    #  4: "persistence" (optional/default/required/once/always);
    #  5: default, or None;
    #  6: possible values for select fields, as /-delimited string, or None;
    #  7: string describing the field (for the jobspec comment), or None;
    #  8: a translator object (not used in this module) or None).
    # 
    # The comment is not parsed on reading the jobspec, but is
    # constructed (from the per-field comments) when writing it.

    # 3.1. Jobspec Utilities
    # 
    # compare_field_by_number: this is a function for passing to
    # sort() which allows us to sort jobspec field descriptions based
    # on the field number.

    def compare_field_by_number(self, x, y):
        if x[0] < y[0]:
            return -1
        elif x[0] > y[0]:
            return 1
        else:
            # "Jobspec fields '%s' and '%s' have the same
            # number %d."
            raise error, catalog.msg(710, (x[1], y[1], x[0]))

    # jobspec_attribute_names[i] is the name of attribute i in a
    # jobspec representation tuple.  Used for generating messages
    # about jobspecs.

    jobspec_attribute_names = [
        'code',
        'name',
        'datatype',
        'length',
        'fieldtype',
        'preset',
        'values',
        'comment',
        'translator', # not really needed
        ]

    # jobspec_map builds a map from a jobspec, mapping one of the
    # tuple elements (e.g. number, name) to the whole tuple.

    def jobspec_map(self, jobspec, index):
        map = {}
        comment, fields = jobspec
        for field in fields:
            map[field[index]] = field
        return map

    # 3.2. Install a new jobspec

    def install_jobspec(self, description):
        comment, fields = description
        assert isinstance(fields, types.ListType)
        # "Installing jobspec from comment '%s' and fields %s."
        self.log(712, (comment, fields))
        for field in fields:
            assert isinstance(field, types.TupleType)
            assert len(field) >= 8

        def make_comment(field):
            if field[7] == None:
                return ""
            else:
                return "# %s: %s\n" % (field[1], field[7])

        # we will need the jobspec as a dictionary in order to
        # give it to Perforce.
        jobspec_dict = {}

        fields.sort(self.compare_field_by_number)

        i = 0
        for field in fields:
            jobspec_dict['Fields%d' % i] = ("%s %s %s %s %s"
                                            % field[0:5])
            i = i + 1

        i = 0
        for field in fields:
            if field[6] != None:
                jobspec_dict['Values%d' % i] = "%s %s" % (field[1],
                                                          field[6])
                i = i + 1

        i = 0
        for field in fields:
            if field[5] != None:
                jobspec_dict['Presets%d' % i] = "%s %s" % (field[1],
                                                           field[5])
                i = i + 1

        jobspec_dict['Comments'] = (comment +
                                    string.join(map(make_comment,
                                                    fields),
                                                ""))

        self.run('jobspec -i', jobspec_dict)

    # 3.3. Get the jobspec.
    #
    # Get the jobspec and convert it into P4DTI representation.
    # 
    # Does very little checking on the output of 'jobspec -o'.
    # Ought to validate it much more thoroughly than this.

    def get_jobspec(self):

        jobspec_dict = self.run('jobspec -o')[0]
        fields = []
        fields_dict = {}
        fields_re = re.compile('^Fields[0-9]+$')
        presets_re = re.compile('^Presets[0-9]+$')
        values_re = re.compile('^Values[0-9]+$')
        comments_re = re.compile('^Comments$')
        comment = ""
        for k,v in jobspec_dict.items():
            if fields_re.match(k): # found a field
                words = string.split(v)
                name = words[1]
                if not fields_dict.has_key(name):
                    fields_dict[name] = {}
                fields_dict[name]['code'] = int(words[0])
                fields_dict[name]['datatype'] = words[2]
                fields_dict[name]['length'] = int(words[3])
                fields_dict[name]['disposition'] = words[4]
            elif presets_re.match(k): # preset for a non-optional field
                space = string.find(v,' ')
                name = v[0:space]
                preset = v[space+1:]
                if not fields_dict.has_key(name):
                    fields_dict[name] = {}
                fields_dict[name]['preset'] = preset
            elif values_re.match(k): # values for a select field
                space = string.find(v,' ')
                name = v[0:space]
                values = v[space+1:]
                if not fields_dict.has_key(name):
                    fields_dict[name] = {}
                fields_dict[name]['values'] = values
            elif comments_re.match(k): # comments for a field
                comment = v
        for k,v in fields_dict.items():
            fields.append((v['code'],
                           k,
                           v['datatype'],
                           v['length'],
                           v['disposition'],
                           v.get('preset', None),
                           v.get('values', None),
                           None,
                           None))
        fields.sort(self.compare_field_by_number)
        # "Decoded jobspec as comment '%s' and fields %s."
        self.log(711, (comment, fields))
        return comment, fields


    # 3.4. Extending the current jobspec.
    #
    # extend_jobspec adds the given fields to the current jobspec if
    # not already present.

    def extend_jobspec(self, description, force = 0):
        current_jobspec = self.get_jobspec()
        comment, field_list = current_jobspec
        _, new_fields = description
        new_fields.sort(self.compare_field_by_number)
        current_fields = self.jobspec_map(current_jobspec, 1)
        new_field_names = map(lambda x: x[1], new_fields)
        field_numbers = map(lambda x: x[0], field_list)
        # counters for finding a free field number.
        free_number_p4dti = 194
        free_number = 106
        for field_spec in new_fields:
            field = field_spec[1]
            if current_fields.has_key(field):
                current_spec = current_fields[field]
                if (current_spec[2] != field_spec[2] or
                    current_spec[3] != field_spec[3] or
                    current_spec[4] != field_spec[4] or
                    current_spec[5] != field_spec[5] or
                    current_spec[6] != field_spec[6]):
                    if force:
                        # "Forcing replacement of field '%s' in jobspec."
                        self.log(727, field)
                        current_fields[field] = ((current_spec[0],) +
                                                 field_spec[1:7] +
                                                 (None,None,))
                    else:
                        # "Retaining field '%s' in jobspec despite change."
                        self.log(728, field)
                else:
                    # "No change to field '%s' in jobspec."
                    self.log(733, field)
            else:
                if field_spec[0] in field_numbers:
                    # Field numbering clashes; find a free field number.
                    if field[0:6] == 'P4DTI-':
                        while free_number_p4dti in field_numbers:
                            free_number_p4dti = free_number_p4dti - 1
                        number = free_number_p4dti
                    else:
                        while free_number in field_numbers:
                            free_number = free_number + 1
                        number = free_number
                    if free_number >= free_number_p4dti:
                        # "Too many fields in jobspec."
                        raise error, catalog.msg(730)
                    field_spec = (number, ) + field_spec[1:]
                # "Adding field '%s' to jobspec."
                self.log(729, field)
                current_fields[field] = field_spec
                field_numbers.append(field_spec[0])
                
        # Also report jobspec names fields not touched.
        for field in current_fields.keys():
            if field not in new_field_names:
                # "Retaining unknown field '%s' in jobspec."
                self.log(732, field)
                
        self.install_jobspec((comment, current_fields.values()))


    # 3.5. Jobspec validation.
    # 
    # jobspec_has_p4dti_fields: Does the jobspec include all the P4DTI
    # fields, with the right types etc.  The set of things we actually
    # require is fairly limited.  For instance, we don't insist on
    # having particular field numbers.
    #
    # Note that the P4DTI-filespecs field is not required for correct
    # operation of the P4DTI.

    p4dti_fields = {
        'P4DTI-rid': {2: 'word',
                      4: 'required',
                      5: 'None',
                      },
        'P4DTI-issue-id': {2: 'word',
                           4: 'required',
                           5: 'None',
                           },
        'P4DTI-user': {2: 'word',
                       4: 'always',
                       5: '$user',
                       },
        'P4DTI-filespecs': {},
        }

    def jobspec_has_p4dti_fields(self, jobspec, warn = 1):
        map = self.jobspec_map(jobspec, 1)
        correct = 1
        for k,v in self.p4dti_fields.items():
            if map.has_key(k):
                for i, value in v.items():
                    if map[k][i] != value:
                        if warn:
                            # "Jobspec P4DTI field '%s' has incorrect
                            # attribute '%s': '%s' (should be '%s')."
                            self.log(714, (k, self.jobspec_attribute_names[i],
                                           map[k][i], value))
                        correct = 0
            elif v:
                if warn:
                    # "Jobspec does not have required P4DTI field '%s'."
                    self.log(713, k)
                correct = 0
        return correct

    # validate_jobspec: look at a jobspec and find out whether we can
    # run P4DTI with it.

    def validate_jobspec(self, jobspec):
        if not self.jobspec_has_p4dti_fields(jobspec):
            # "Jobspec does not support P4DTI."
            raise error, catalog.msg(715)

    # increasing order of restriction on Perforce job fields, based on
    # datatype:

    restriction_order = {
        'text':   1,
        'line':   2,
        'word':   3,
        'select': 4,
        'date':   5,
        }

    # check_jobspec: does the current jobspec include the fields we want?
    # Warn on any problem areas, error if they will be fatal.

    def check_jobspec(self, description):
        satisfactory = 1
        _, wanted_fields = description
        actual_jobspec = self.get_jobspec()
        self.validate_jobspec(actual_jobspec)
        actual_fields = self.jobspec_map(actual_jobspec, 1)
        wanted_fields = self.jobspec_map(description, 1)
        # remove P4DTI fields, which are checked by validate_jobspec()
        for field in self.p4dti_fields.keys():
            if actual_fields.has_key(field):
                del actual_fields[field]
            if wanted_fields.has_key(field):
                del wanted_fields[field]
        shared_fields = []
        # check that all wanted fields are present.
        for field in wanted_fields.keys():
            if actual_fields.has_key(field):
                shared_fields.append(field)
            else: # field is absent.
                # "Jobspec does not have field '%s'."
                self.log(716, field)
                satisfactory = 0
        for field in shared_fields:
            # field is present
            actual_spec = actual_fields[field]
            wanted_spec = wanted_fields[field]
            del actual_fields[field]
            # check datatype
            actual_type = actual_spec[2]
            wanted_type = wanted_spec[2]
            if actual_type == wanted_type:
                # matching datatypes
                if actual_type == 'select':
                    # select fields should have matching values.
                    actual_values = string.split(actual_spec[6], '/')
                    wanted_values = string.split(wanted_spec[6], '/')
                    shared_values = []
                    for value in wanted_values:
                        if value in actual_values:
                            shared_values.append(value)
                    for value in shared_values:
                            actual_values.remove(value)
                            wanted_values.remove(value)
                    if wanted_values:
                        if len(wanted_values) > 1:
                            # "The jobspec does not allow values '%s'
                            # in field '%s', so these values cannot be
                            # replicated from the defect tracker."
                            self.log(718, (string.join(wanted_values, '/'), field))
                        else:
                            # "The jobspec does not allow value '%s'
                            # in field '%s', so this value cannot be
                            # replicated from the defect tracker."
                            self.log(719, (wanted_values[0], field))
                    if actual_values:
                        if len(actual_values) > 1:
                            # "Field '%s' in the jobspec allows values
                            # '%s', which cannot be replicated to the
                            # defect tracker."
                            self.log(720, (field, string.join(actual_values, '/')))
                        else:
                            # "Field '%s' in the jobspec allows value
                            # '%s', which cannot be replicated to the
                            # defect tracker."
                            self.log(721, (field, actual_values[0]))
            elif ((wanted_type == 'date' and (actual_type == 'word' or
                                              actual_type == 'select')) or
                  (actual_type == 'date' and (wanted_type == 'word' or
                                              wanted_type == 'select'))):
                # "Field '%s' in the jobspec should be a '%s' field,
                # not '%s'.  This field cannot be replicated to or
                # from the defect tracker."
                self.log(724, (field, wanted_type, actual_type))
                satisfactory = 0
            else:
                wanted_order = self.restriction_order[wanted_type]
                actual_order = self.restriction_order.get(actual_type, None)
                if actual_order is None:
                    # "Jobspec field '%s' has unknown datatype '%s'
                    # which may cause problems when replicating this
                    # field."
                    self.log(731, (field, actual_type))
                elif wanted_order > actual_order:
                    # "Jobspec field '%s' has a less restrictive
                    # datatype ('%s' not '%s') which may cause
                    # problems replicating this field to the defect
                    # tracker."
                    self.log(723, (field, actual_type, wanted_type))
                else:
                    # "Jobspec field '%s' has a more restrictive
                    # datatype ('%s' not '%s') which may cause
                    # problems replicating this field from the defect
                    # tracker."
                    self.log(722, (field, actual_type, wanted_type))
            # check persistence
            if actual_spec[4] != wanted_spec[4]:
                # "Field '%s' in the jobspec should have persistence
                # '%s', not '%s'.  There may be problems replicating
                # this field to or from the defect tracker."
                self.log(725, (field, wanted_spec[4], actual_spec[4]))
        if actual_fields:
            for field in actual_fields.keys():
                # "Perforce job field '%s' will not be replicated to the
                # defect tracker."
                self.log(726, field)

        # Possibly should also check that some of the
        # Perforce-required fields are present.  See the lengthy
        # comment below (under "jobspec_has_p4_fields").

        if not satisfactory:
            # "Current jobspec cannot be used for replication."
            raise error, catalog.msg(717)
        
    # Notes for writing a function "jobspec_has_p4_fields": Does the
    # jobspec have the fields which are required by Perforce?
    # 
    # In the default Perforce jobspec. the first five fields look like
    # this:
    # 
    # 101 Job         word   32 required
    # 102 Status      select 10 required
    # 103 User        word   32 required
    # 104 Date        date   20 always
    # 105 Description text    0 required
    # 
    # Perforce documentation emphasizes that the names and types of
    # the first five fields should not be changed.  But in fact, there
    # isn't much actually required for correct operation of Perforce:
    # 
    # Field 101:
    #   - the job name, used in various commands and automatically generated
    #     by Perforce server if a job is created with value 'new' in this
    #     field.
    #   - required;
    #   - a word;
    # 
    # Field 102:
    #   - the job status, used in various commands;
    #   - required;
    #   - a select;
    #   - if the Values don't include 'closed' then things will break
    #     (because 'p4 fix' will set it to 'closed' anyway).
    #
    # Field 103:
    #     - the job user.
    #     - Output by "p4 jobs" if it is a "word".
    #
    # Field 104:
    #     - the date.
    #     - Output by "p4 jobs" if it is a "date".
    # 
    # Field 105:
    #   - the job description, output by various commands;
    #   - required;
    #   - text or line.

    # 4. COUNTERS

    def counter_value(self, counter):
        dict = self.run('counter %s' % counter)
        if self.supports('counter_value'):
            val = dict[0]['value']
        else:
            val = dict[0]['data']
        return val

# A. REFERENCES
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
#
# B. DOCUMENT HISTORY
#
# 2000-09-25 GDR Created.  Moved Perforce interface from replicator.py.
#
# 2000-12-07 GDR Provided defaults for all configuration parameters so
# that you can make a p4 object passing no parameters to get the default
# Perforce behaviour.
#
# 2000-12-14 RB Added check for the exit status of the "p4" command so
# that the caller can tell the difference between empty output and a
# connection (or other) error.
#
# 2000-12-15 NB Added verbosity control.
#
# 2001-01-23 GDR Added check that Perforce client version is supported.
#
# 2001-02-14 GDR Report the Perforce error message together with the
# exit status when we have both.
#
# 2001-02-19 NB Keyword translation updated and moved here (as it is
# Perforce-specific.
#
# 2001-02-21 GDR Moved keyword translator to its own file (keyword.py)
# so that there's no import loop.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-12 GDR Use messages for errors and logging.
#
# 2001-03-13 GDR Removed verbose parameter and verbosity control; this
# was made redundant by the log_level parameter.
#
# 2001-03-15 GDR Formatted as a document.  Take configuration as
# variables.
#
# 2001-03-24 GDR Check the Perforce server changelevel.
#
# 2001-05-18 GDR Don't log Perforce exit status if it's None.
#
# 2001-06-22 NB New jobspec class containing common code for
# converting lists of tuples into a jobspec dictionary.
#
# 2001-06-22 NB Get jobspec from p4 into our internal list-of-tuples
# format.
#
# 2001-06-25 NB jobspec field codes need to be integers.
#
# 2001-06-29 NB Fixed jobspec parsing (it worked if the fields were in
# the right order).  Also added debugging messages 711 and 712.
#
# 2002-01-28 GDR New method 'supports' tells you whether the Perforce
# server supports a feature.
#
# 2003-08-20 DRJ Creates and uses a P4CONFIG file if asked.
#
# 2003-09-17 NB os.chmod doesn't work on Windows, so write a new
# routine to achieve it and put it in a new module portable.py.
#
# 2003-09-25 NB Change name of config file parameter.
#
# 2003-11-03 NB Moved changelevel checking to a separate function, and
# use "p4 info" without -G for the server changelevel, because "p4 -G
# info" output is changing in Perforce 2003.2.
#
# 2003-12-05 NB Extend jobspec-checking functions.
#
# 2003-12-12 NB Add extend_jobspec.
#
# 2005-01-03 NB Add marshal_dump_0.
#
# 2006-02-28 NB Counter value marshal format has changed. job001342.
#
#
# C. COPYRIGHT AND LICENSE
#
# This file is copyright (c) 2001-2004 Perforce Software, Inc.  All
# rights reserved.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/p4.py#6 $
