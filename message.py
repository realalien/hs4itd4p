#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#       MESSAGE.PY -- MESSAGE OBJECTS FOR LOGGING AND EXCEPTIONS
#
#             Gareth Rees, Ravenbrook Limited, 2001-03-11
#
#
# 1. INTRODUCTION
#
# This module defines these classes:
#
#  1. message.  Each message has an id, text, priority and product.  A
# set of priority levels are defined.  Messages have methods for
# printing and computing check digits.
#
#  2. factory.  A message factory is an object used to create messages
# (typically for the same product).
#
#  3. catalog_factory.  A message factory that creates messages whose
# priority and text comes from a message catalog.
#
# These classes are intended to
#
#  1. Allow administrators to debug their configuration [Requirements,
# 63] by providing each message with a unique message id that can be
# used to look up troubleshooting information.  See also job000030
# (Users can't get help based on messages).
#
#  2. Help Perforce support to assist administrators [Requirements, 33,
# 34, 35] ditto.
#
#  3. Help developers debug modifications of the P4DTI [Requirements,
# 25] by providing debugging messages and allowing them to control the
# messages they see.  See also job000065 (Not enough logging control).
#
#  4. Help integrators debug their extensions to new defect trackers
# [Requirements, 21] ditto.
#
#  5. Internationalize the P4DTI.
#
# See [RB 2000-10-16] for the decision to adopt ISBN-style checkdigits
# on message ids.
#
# See [RB 2000-12-16] for the decision to make messages and exceptions
# into classes.
#
# Because we want people to be able to extend the P4DTI [Requirements,
# 25], we need to make it easy for people to allocate message ids
# without clashing with existing ones or ones which other integrators
# are using.  So each message has a "product" field which forms part of
# the message id.  Messages from the supported P4DTI have
# product="P4DTI".
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import math
import os
import string
import types


# 2. MESSAGE PRIORITIES
#
# These are based on the syslog priorities on Unix.  The first two
# priorities aren't relevant for the P4DTI, but I've included them for
# completeness.
#
# Prorities must be numbers because the logger module needs to compare
# priorities when deciding whether a message is severe enough to log.
#
# On Unix we arrange for the values for these priorities to exactly
# match the syslog priorities, so that the values can be passed directly
# to syslog().  On Windows, we supply our own values (namely the values
# in syslog.h on FreeBSD).

NOT_USED = -99
if os.name == 'posix':
    import syslog
    EMERG = syslog.LOG_EMERG
    ALERT = syslog.LOG_ALERT
    CRIT = syslog.LOG_CRIT
    ERR = syslog.LOG_ERR
    WARNING = syslog.LOG_WARNING
    NOTICE = syslog.LOG_NOTICE
    INFO = syslog.LOG_INFO
    DEBUG = syslog.LOG_DEBUG
else:
    EMERG = 0    # System is unusable (not used).
    ALERT = 1    # Action must be taken immediately (not usedk).
    CRIT = 2     # Fatal error; the P4DTI will stop.
    ERR = 3      # Error, but not a fatal error.
    WARNING = 4  # Pay attention: something may be wrong.
    NOTICE = 5   # Expected condition, but significant.
    INFO = 6     # For information only.
    DEBUG = 7    # Unlikely to be useful except for debugging.


# 3. MESSAGE CLASS

class message:
    id = None
    priority = None
    product = None
    text = None

    def __init__(self, id, text, priority, product):
        assert isinstance(id, types.IntType)
        assert id >= 0
        assert isinstance(text, basestring)
        assert isinstance(priority, types.IntType)
        assert priority >= EMERG and priority <= DEBUG
        assert isinstance(product, types.StringType)
        if isinstance(text, unicode):
            text = text.encode('utf8')
        self.id = id
        self.priority = priority
        self.text = text
        self.product = product


    # 3.1. Format the message as a string, including the message id.

    def __str__(self):
        return "(%s)  %s" % (self.message_id(), self.text)


    # 3.2. Compute a message check-digit.
    #
    # Compute the check-digit (0-9 or X) for the given message id and
    # return it as a string.  See [RB 2000-10-16] for the design
    # decision and justification.

    def check_digit(self):
        id = self.id
        sum = 0
        i = 0
        while 1:
            if id <= 0:
                break
            else:
                i = i + 1
                sum = sum + i * (id % 10)
                id = int(math.floor(id / 10))
        return "0123456789X"[sum % 11]


    # 3.3. Format a message id for display
    #
    # Message ids look like P-NC, where P is the project name, N is the
    # id number and C is the check digit.  Or just NC if the product is
    # empty.  See [RB 2000-10-16] for the design decision.

    def message_id(self):
        if self.product:
            return "%s-%d%s" % (self.product, self.id,
                                self.check_digit())
        else:
            return "%d%s" % (self.id, self.check_digit())


    # 3.4. Text-wrap the message
    #
    # Text-wrap the message to the given number of columns.

    def wrap(self, columns):
        text = str(self)
        lines = [ ]
        pos = 0
        length = len(text)
        while pos < length:
            if pos + columns >= length:
                space = length
            else:
                space = string.rfind(text, ' ', pos, pos + columns + 1)
                if space == -1:
                    space = string.find(text, ' ', pos, length)
                    if space == -1:
                        space = length
            while space > 0 and text[space-1] == ' ':
                space = space - 1
            lines.append(text[pos:space])
            while space < length and text[space] == ' ':
                space = space + 1
            pos = space
        return string.join(lines, '\n')


# 4. MESSAGE FACTORY CLASS
#
# A message factory has a new() method which constructs a message
# object.

class factory:
    priority = None
    product = None

    def __init__(self, priority = INFO, product = ""):
        assert isinstance(priority, types.IntType)
        assert priority >= EMERG and priority <= DEBUG
        assert isinstance(product, types.StringType)
        self.priority = priority
        self.product = product

    def new(self, id, text, priority = None, product = None):
        if priority == None:
            priority = self.priority
        if product == None:
            product = self.product
        return message(id, text, priority, product)


# 5. CATALOG MESSAGE FACTORY CLASS
#
# The new() method of this message factory class doesn't need to be
# passed the fixed text of the message, only the arguments (as a tuple).
# It looks up the fixed text in the message catalog and uses that fixed
# text together with the arguments to build the message text.
#
# This class is intended to:
#
#  1. Support future localization of the P4DTI (by using different
# message catalogs for different languages); and
#
#  2. Help developers to prevent message ids from clashing, by providing
# a catalog of all messages.
#
# The catalog argument is a dictionary mapping message id to (priority,
# format string).  It must not have an entry for id 0, because id 0 is
# used when an invalid message id is passed to the new() method.

class catalog_factory(factory):
    catalog = None

    def __init__(self, catalog, product = ""):
        assert isinstance(catalog, types.DictType)
        assert not catalog.has_key(0)
        factory.__init__(self, product = product)
        self.catalog = catalog

    def new(self, id, args = ()):
        if self.catalog.has_key(id):
            (priority, format) = self.catalog[id]
            try:
                return factory.new(self, id, format % args, priority)
            except TypeError:
                return factory.new(self, 0, "Message %s has format "
                                   "string '%s' but arguments %s."
                                   % (id, format, args), ERR)
        else:
            return factory.new(self, 0, "No message with id '%s' "
                               "(args = %s)." % (id,args), ERR)


# A. REFERENCES
#
# [RB 2000-12-16] "Should exceptions be classes?" (e-mail message);
# Richard Brooksby; Ravenbrook; 2000-12-16;
# <http://info.ravenbrook.com/mail/2000/12/16/06-47-37/0.txt>.
#
# [RB 2000-10-16] "Message IDs" (e-mail message); Richard Brooksby;
# Ravenbrook Limited; 2000-10-16;
# <http://info.ravenbrook.com/mail/2000/10/16/10-50-49/0.txt>.
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-03-11 GDR Created.
#
# 2001-05-22 GDR catalog_factory.new generates useful error messages
# when passed an invalid message id or the wrong arguments.
#
# 2001-08-16 GDR Made use of division operator in check_digit() portable
# between Python releases.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/message.py#2 $
