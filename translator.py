#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#      TRANSLATOR.PY -- TRANSLATE FIELDS BETWEEN DEFECT TRACKERS
#
#             Gareth Rees, Ravenbrook Limited, 2001-03-13
#
#
# 1. INTRODUCTION
#
# This module defines the translator class.  An instance of a translator
# class translates between corresponding fields in two defect trackers.
# For example, we could make a state translator that translates between
# an issue state in TeamTrack and a job state in Perforce.
#
# The translator class is generic: it doesn't know anything about the
# identities of the defect tracker it translates between, so it calls
# them "defect tracker 0" and "defect tracker 1".  In the P4DTI, defect
# tracker 1 is conventionally Perforce.
#
# Each kind of field will need its own translator subclass; for example,
# in the TeamTrack integration we have date_translator,
# single_select_translator, state_translator, text_translator,
# user_translator and so on.  When the P4DTI starts up, the
# configuration generator makes instances of each translator subclass,
# passing additional data where necessary.  For example, the
# single_select_translator needs to know the name of the TeamTrack field
# it is translating, so that it can pick out the selections that apply
# to that field.
#
# The aim of the translator class is to make the replicator implentation
# cleaner and easier to maintain and understand.  Rather than having a
# big switch statement, or a fixed set of field types, the replicator
# instead has a list of (field in defect tracker 0, field in defect
# tracker 1, translator) triples which it can iterate over.
#
# I wish I could think of better names than translate_0_to_1 and
# translate_1_to_0 for the translation methods.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import dt_interface
import re
import string


# 2. TRANSLATOR CLASS
#
# This is an abstract class that defines the interface for all
# translators.
#
# The translator class itself implements the null translator.  It
# doesn't change values, but its methods do check the types of its
# arguments.
#
# See [GDR 2000-10-16, 6.5] for more documentation.

class translator:

    # 2.1. TRANSLATE FROM DEFECT TRACKER 0 TO DEFECT TRACKER 1
    #
    # Translate a value from defect tracker 0 to defect tracker 1.
    # Arguments:
    #
    # value    The value (in defect tracker 0) being translated.
    # dt0      Defect tracker 0.
    # dt1      Defect tracker 1.
    # issue0   The issue in defect tracker 0 from which the value comes,
    #          or None if the value doesn't come from an issue.
    # issue1   The issue in defect tracker 0 from which the field comes,
    #          or None if the value doesn't come from an issue.
    #
    # Returns a suitable translation of value for defect tracker 1, or
    # raises an error if translation is impossible.
    #
    # This method takes defect trackers as arguments because it may need
    # to query the defect tracker to carry out the translation.  For
    # example, in the TeamTrack integration the user translator needs to
    # discover all the users in TeamTrack and Perforce so that it can
    # match them up by e-mail address.  A translator that does not need
    # these arguments may specify defaults for them and be used without
    # them (for example, the keyword translator in section 3 below does
    # this so that it can be used during configuration before any defect
    # tracker objects have been constructed).
    #
    # This method takes issues as arguments because some translators
    # need to know about the whole issue in order to carry out the
    # translation.  For example, in the TeamTrack integration the state
    # translator needs to know the project to which the issue belongs
    # (because different projects may have different states with the
    # same name which correspond to the same Perforce state).  Most
    # translators will ignore the issue arguments.

    def translate_0_to_1(self, value, dt0, dt1, issue0 = None,
                         issue1 = None):
        assert isinstance(dt0, dt_interface.defect_tracker)
        assert isinstance(dt1, dt_interface.defect_tracker)
        assert (issue0 == None
                or isinstance(issue0, dt_interface.defect_tracker_issue))

        # The issue1 argument is conventionally the Perforce job.
        # Unfortunately, Perforce jobs are just ordinary dictionaries,
        # and don't belong to a subclass of defect_tracker_issue, so we
        # can't check the type of the issue1 argument.  This should be
        # corrected.

        #assert (issue1 == None
        #        or isinstance(issue1, dt_interface.defect_tracker_issue))
        return value

    # 2.2. TRANSLATE FROM DEFECT TRACKER 1 TO DEFECT TRACKER 0
    #
    # Translate a value from defect tracker 0 to defect tracker 1.
    # Arguments:
    #
    # value    The value (in defect tracker 1) being translated.
    # ...      (other arguments are the same as translate_0_to_1)
    #
    # Returns a suitable translation of value for defect tracker 0, or
    # raises an error if translation is impossible.
    #
    # The notes for translate_0_to_1() in section 2.1 also apply to this
    # method.

    def translate_1_to_0(self, value, dt0, dt1, issue0 = None,
                         issue1 = None):
        assert isinstance(dt0, dt_interface.defect_tracker)
        assert isinstance(dt1, dt_interface.defect_tracker)
        assert (issue0 == None
                or isinstance(issue0, dt_interface.defect_tracker_issue))
        # See comment in translate_0_to_1 above.
        #assert (issue1 == None
        #        or isinstance(issue1, dt_interface.defect_tracker_issue))
        return value


# 3. KEYWORD TRANSLATOR CLASS
#
# This class translates "keywords" between any defect tracker and
# Perforce.  By "keywords" I mean job field names in Perforce, and
# values in "select" fields in Perforce jobs.
#
# Defect tracker keywords can (in general) contain whitespace and
# punctuation characters.
#
# But Perforce job field names can't contain whitespace, hashes, or
# double quotes.  Values in "select" fields in Perforce jobspecs also
# can't contain semicolons or slashes.
#
# The translation must be one-to-one so that values in "select" fields
# in Perforce can be accurately translated back to the defect tracker.
#
# We use the following translation:
#
# DT  Perforce  Description
# ---------------------------------
#         _     (space to underscore)
#  \      \\    (we use backslash to escape so it must escape itself)
#  _      \_    (underscore to backslash underscore)
#  ;      \:    (semicolon to backslash colon)
#  #      \=    (hash to backslash equals)
#  /      \|    (slash to backslash bar)
#  "      \'    (double quote to backslash apostrophe)
#  c      \xab  (where c is some other whitespace character and ab is
#                its hex representation).
#
# See job000195 for the motivation behind this design.

class keyword_translator(translator):

    # 3.1. Fixed translations
    #
    # specials is a list of pairs (defect tracker string, Perforce
    # string).  dt_to_p4 is a map from defect tracker string to Perforce
    # string.  p4_to_dt is a map from Perforce string to defect tracker
    # string.
    #
    # 'dt_to_p4' and 'p4_to_dt' are generated from specials when an
    # instance is created.

    specials = [(' ', '_'),
                ('_', '\\_'),
                ('\\', '\\\\'),
                (';', '\\:'),
                ('/', '\\|'),
                ('#', '\\='),
                ('"', "\\'"),
             ]
    dt_to_p4 = {}
    p4_to_dt = {}

    def __init__(self):
        for (dt,p4) in self.specials:
            self.dt_to_p4[dt] = p4
            self.p4_to_dt[p4] = dt


    # 3.2. Translate a matched single character to an escape sequence

    def char_to_p4(self, match):
        if self.dt_to_p4.has_key(match.group(0)):
            return self.dt_to_p4[match.group(0)]
        else:
            return '\\x%02x' % ord(match.group(0))

    # 3.3. Translate a matched escape sequence to a single character

    def p4_to_char(self, match):
        if self.p4_to_dt.has_key(match.group(0)):
            return self.p4_to_dt[match.group(0)]
        else:
            return chr(string.atoi(match.group(1)[2:], 0x10))

    # 3.4. Translate a keyword from the defect tracker to Perforce
    #
    # This method ignores its arguments dt0 and dt1 so that it can be
    # called during confguration generation, before any defect tracker
    # objects have been constructed.  See configure_bugzilla.py.

    def translate_0_to_1(self, s, dt0 = None, dt1 = None, issue0 = None,
                         issue1 = None):
        return re.sub('[\\s_;/#"\\\\]', self.char_to_p4, s)

    # 3.5. Translate a keyword from Perforce to the defect tracker.
    #
    # See the comment for translate_0_to_1() in section 3.4 above.

    def translate_1_to_0(self, s, dt0 = None, dt1 = None, issue0 = None,
                         issue1 = None):
        return re.sub("_|\\\\([_\\\\:|=']|x[0-9a-f]{2})",
                      self.p4_to_char, s)


# 4. USER TRANSLATOR CLASS
#
# A user translator is a translator between users in two defect
# trackers, but it implements the additional method unmatched_users.
#
# This class is the abstract base class for all user translators.
#
# See [GDR 2000-10-16, 7.5.3] for documentation.

class user_translator(translator):
    pass


# A. REFERENCES
#
# [GDR 2000-10-16] "Perforce Defect Tracking Integration Integrator's
# Guide"; Gareth Rees; Ravenbrook Limited; 2000-10-16;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/manual/ig/>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-02-21 GDR Created (as keyword.py).
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-13 GDR Renamed as translator.py.  Formatted as a document.
# Included translator interface (from replicator.py).  Moved unit test
# for keyword_translator to test/ directory.
#
# 2001-03-19 GDR Added user_translator class.
#
# 2001-03-21 GDR Corrected description of unmatched_users return value.
# Added references to IG.
#
# 2003-05-21 NB Fixed some broken comments.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/translator.py#2 $
