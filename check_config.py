#                Perforce Defect Tracking Integration Project
#                 <http://www.ravenbrook.com/project/p4dti/>
#
#            CHECK_CONFIG.PY -- VALIDATE CONFIGURATION PARAMETERS
#
#                 Nick Barnes, Ravenbrook Limited, 2001-01-18
#
#
# 1. INTRODUCTION
#
# This module defines a set of functions that check that a parameter is
# suitable for a particular purpose (e.g., using as an e-mail address).
# They return if the parameter is suitable and raise a clear error
# message if it is not.
#
# Checking the configuration is intended to:
#
#  1. Keep the support cost low by allowing administrators to identify
# and fix incorrect configurations by themselves [Requirements, 35];
#
#  2. Keep installation time low by finding problems with the
# configuration early [Requirements, 63].
#
# See job000048, job000075, job000165, job000168 and job000170 for
# problems we've had with inadequate configuration checking.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import catalog
import re
import types

error = "P4DTI configuration error"


# 2. CHECKING FUNCTIONS


# 2.1. Check that parameter is a boolean (0 or 1)

def check_bool(config, name):
    param = getattr(config, name)
    if param not in [0,1]:
        # "Configuration parameter '%s' must be 0 or 1."
        raise error, catalog.msg(200, name)


# 2.2. Check that parameter is a date
#
# We require dates to be strings of the form "2001-03-14 12:34:56" [ISO
# 8601].

def check_date(config, name):
    param = getattr(config, name)
    check_string(config, name)
    date_re = "^(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)$"
    match = re.match(date_re, param)
    if match:
        year,month,date,hour,minute,second = map(int, match.groups())
        if (1 <= month and month <= 12 and 1 <= date and date <= 31
            and hour <= 23 and minute <= 59 and second <= 59):
            return
    # "Configuration parameter '%s' (value '%s') is not a valid date.
    # The right format is 'YYYY-MM-DD HH:MM:SS'."
    raise error, catalog.msg(201, (name, param))


# 2.3. Check that parameter looks like an e-mail address
#
# [RFC 822] defines an 'addr-spec' as follows.
#
#   addr-spec   =  local-part "@" domain
#   local-part  =  word *("." word)
#   word        =  atom
#   domain      =  sub-domain *("." sub-domain)
#   sub-domain  =  domain-ref
#   domain-ref  =  atom
#   atom        =  1*<any CHAR except specials, SPACE and CTLs>
#   specials    =  "(" / ")" / "<" / ">" / "@" /  "," / ";" / ":" / "\"
#   		   / <"> /  "." / "[" / "]"
#
# (A CHAR is an ASCII character.)
#
# This isn't the full story.  "Structured field bodies" in RFC822 also
# permit quoting, domain literals and comments.  This code doesn't
# recognise these features.  So users of the P4DTI will have to get by
# without.

def check_email(config, name):
    param = getattr(config, name)
    check_string(config, name)
    atom_re = "[!#$%&'*+\\-/0-9=?A-Z^_`a-z{|}~]+"
    email_re = "^%s(\\.%s)*@%s(\\.%s)*$" % (atom_re, atom_re,
                                            atom_re, atom_re)
    if not re.match(email_re, param):
        # "Configuration parameter '%s' (value '%s') is not a valid
        # e-mail address."
        raise error, catalog.msg(202, (name, param))


# 2.4. Check that parameter is a Python function

def check_function(config, name):
    param = getattr(config, name)
    if (type(param) not in [types.FunctionType,
                            types.MethodType,
                            types.BuiltinFunctionType,
                            types.BuiltinMethodType]
        and not hasattr(param, '__call__')):
        # "Configuration parameter '%s' must be a function."
        raise error, catalog.msg(203, name)


# 2.5. Check that parameter looks like a network host
#
# We don't do more than check that the parameter is a string.  We could
# check that it matches a regexp or we could look it up in DNS.  But in
# fact it's not a severe problem not fail to try to check that the host
# exists at this point, because the P4DTI tries to connect to all hosts
# (defect tracker, Perforce, SMTP) when it starts up so any problems
# will be found quickly.

def check_host(config, name):
    check_string(config, name)


# 2.6. Check that parameter is an integer

def check_int(config, name):
    param = getattr(config, name)
    if not isinstance(param, types.IntType):
        # "Configuration parameter '%s' must be an integer."
        raise error, catalog.msg(204, name)


# 2.7. Check that parameter is a list

def check_list_of(config, name, type, typename):
    check_list(config, name)
    param = getattr(config, name)
    for item in param:
        if not isinstance(item, type):
            # "Configuration parameter '%s' must be a list of %s."
            raise error, catalog.msg(206, (name, typename))

def check_list_of_string_pairs(config, name):
    check_list(config, name)
    param = getattr(config, name)
    for item in param:
        if not (isinstance(item, types.TupleType) and
                len(item) == 2 and
                isinstance(item[0], types.StringType) and
                isinstance(item[1], types.StringType)):
            # "Configuration parameter '%s' must be a list of pairs of strings."
            raise error, catalog.msg(212, name)

def check_list(config, name):
    param = getattr(config, name)
    if not isinstance(param, types.ListType):
        # "Configuration parameter '%s' must be a list."
        raise error, catalog.msg(205, name)

# 2.8. Check that parameter is a string

def check_string(config, name):
    param = getattr(config, name)
    if not isinstance(param, types.StringType):
        # "Configuration parameter '%s' must be a string."
        raise error, catalog.msg(207, name)


# 2.9. Check that parameter is a string or None
#
# This is used for optional configuration parameters.

def check_string_or_none(config, name):
    param = getattr(config, name)
    if not (param == None or
            isinstance(param, types.StringType)):
        # "Configuration parameter '%s' must be None or a string."
        raise error, catalog.msg(208, name)


# 2.10. Check that parameter is an identifier
#
# Replicator and Perforce server identifiers must be from 1 to 32
# characters long, start with a letter or underscore, and consist only
# of letters, numbers and underscores.

def check_identifier(config, name):
    param = getattr(config, name)
    check_string(config, name)
    if (len(param) < 1 or len(param) > 32
        or not re.match('^[A-Za-z_][A-Za-z_0-9]*$', param)):
        # "Configuration parameter '%s' (value '%s') must be from 1 to
        # 32 characters long, start with a letter or number, and consist
        # of letters, numbers and underscores only."
        raise error, catalog.msg(209, (name, param))


# 2.11. Check that parameters is suitable for use as a changelist URL
#
# A changelist URL must contain exactly one instance of the %d format
# specifier.  Any other percentage signs must be doubled.

def check_changelist_url(config, name):
    param = getattr(config, name)
    if param == None:
        return
    check_string(config, name)
    i = 0
    found = 0
    while i < len(param):
        if param[i] == '%':
            i = i + 1
            if i >= len(param) or param[i] not in "%d":
                found = 0
                break
            if param[i] == 'd':
                found = found + 1
        i = i + 1
    if found != 1:
        # "Configuration parameter '%s' (value '%s') must contain
        # exactly one %%d format specifier, any number of doubled
        # percents, but no other format specifiers."
        raise error, catalog.msg(210, (name, param))


# 2.12. Check that parameter is suitable for use as a job URL
#
# A job URL must contain exactly one instance of the %s format
# specifier.  Any other percentage signs must be doubled.

def check_job_url(config, name):
    param = getattr(config, name)
    if param == None:
        return
    check_string(config, name)
    i = 0
    found = 0
    while i < len(param):
        if param[i] == '%':
            i = i + 1
            if i >= len(param) or param[i] not in "%s":
                found = 0
                break
            if param[i] == 's':
                found = found + 1
        i = i + 1
    if found != 1:
        # "Configuration parameter '%s' (value '%s') must contain
        # exactly one %%s format specifier, any number of doubled
        # percents, but no other format specifiers."
        raise error, catalog.msg(211, (name, param))


# A. REFERENCES
#
# [ISO 8601] "Representation of dates and times"; ISO; 1988-06-15.
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
# [RFC 822] "Standard for the format of ARPA Internet text messages";
# David H Crocker; 1982-08-13; <ftp://src.doc.ic.ac.uk/rfc/rfc822.txt>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-01-18 NB Moved from configure_bugzilla.py so we can share with
# other DTs.
#
# 2001-01-23 GDR Extended check_email so that it checks RFC822 address
# syntax.
#
# 2001-02-04 GDR Alphabetized.  Added check_date.
#
# 2001-02-16 NB Added check_function (for checking replicate_p
# parameter).
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-03-12 GDR Use messages when raising errors.
#
# 2001-03-14 GDR Formatted as a document; added references to
# requirements.  The check_date function checks the range of the date
# components.
#
# 2001-03-15 GDR Added check_identifier.
#
# 2001-03-24 GDR Added check_changelist_url.
#
# 2001-07-09 NB Add check_job_url.
#
# 2001-11-21 GDR check_function() allows methods as well as ordinary
# functions.  Check functions now take the module as the first argument
# instead of the parameter (this avoids duplicate of code and so reduces
# incorrect error messages).
#
# 2002-02-15 GDR Determine a function by the existence of a __call__
# method.
#
# 2003-11-25 NB Added check_list_of_string_pairs
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/check_config.py#1 $
