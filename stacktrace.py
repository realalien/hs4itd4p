#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#       STACKTRACE.PY -- FORMAT A TRACEBACK WITH LOCAL VARIABLES
#
#             Nick Barnes, Ravenbrook Limited, 2001-01-19
#
#
# 1. INTRODUCTION
#
# This module defines a function format_exception.  This takes the same
# arguments as the built-in function traceback.format_exception [Python
# 2.0 Library, 3.9] and returns a result in a similar format, namely a
# list of strings describing the exception and tracing the stack that
# were passed as arguments to the function.  The result is the result of
# traceback.format_exception with the addition of the local variables in
# each stack frame.
#
# This function is intended to
#
#  1. Allow administrators to debug their configuration [Requirements,
# 63] by by providing as much information as possible when an error
# occurs.
#
#  2. Allow developers to debug modifications of the P4DTI
# [Requirements, 25] ditto.
#
#  3. Help Perforce support to assist administrators [Requirements, 33,
# 34, 35] ditto.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import traceback

def format_frame_locals(frame):
    locals = ['    locals:\n']
    for key, value in frame.f_locals.items():
        locals.append ("      " + key + ": " + repr(value) + '\n')
    return locals

def format_locals(tb):
    locals = []
    while tb != None:
        locals.append(format_frame_locals(tb.tb_frame))
        tb = tb.tb_next
    return locals

def format_exception(exc_type, exc_value, tb):
    try:
        exception = traceback.format_exception_only(exc_type, exc_value)
        locations = traceback.format_tb(tb)
        locals = format_locals(tb)
        formatted = (['Exception:\n'] +
                     exception +
                     ['Traceback (innermost last):\n'])
        while locations != []:
            formatted.append(locations[0])
            formatted = formatted + locals[0]
            del locations[0]
            del locals[0]
        return formatted
    except:
        formatted = (["Couldn't print detailed traceback.\n"] +
                     traceback.format_exception(exc_type, exc_value,
                                                tb))
        return formatted

# A. REFERENCES
#
# [Requirements] "Perforce Defect Tracking Integration Project
# Requirements"; Gareth Rees; Ravenbrook Limited; 2000-05-24;
# <http://www.ravenbrook.com/project/p4dti/req/>.
#
# [Python 2.0 Library] "Python 2.0 Library Reference"; Guido van Rossum;
# 2000-10-16; <http://www.python.org/doc/2.0/lib/lib.html>.
#
#
# B. DOCUMENT HISTORY
#
# 2001-01-19 NB Wrote after a bug report arrived and we realized that a
# traceback without local variables isn't as much use to us as one with
# them.
#
# 2001-03-02 RB Transferred copyright to Perforce under their license.
#
# 2001-04-29 GDR Formatted as a document.  Added Introduction.
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/stacktrace.py#1 $
