#             Perforce Defect Tracking Integration Project
#              <http://www.ravenbrook.com/project/p4dti/>
#
#                  PORTABLE.PY -- CROSS-PLATFORM PORTABILITY
#
#             Nick Barnes, Ravenbrook Limited, 2003-09-17
#
#
# 1. INTRODUCTION
#

# This Python module provides some utility routines which are
# portable across the set of platforms supported by the P4DTI.
# Python itself is quite portable; there are only a few exceptions.
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import os
import catalog

# 2. popen_read_binary()
# 
# we have to read command output in binary, but popen(cmd, 'rb')
# doesn't work on Posix systems.

def popen_read_binary(command):
    if os.name == 'nt':
        mode = 'rb'
    elif os.name == 'posix':
        mode = 'r'
    else:
        # "The P4DTI does not support the operating
        # system '%s'."
        raise error, catalog.msg(1021, os.name)
    return os.popen(command, mode)

# 3. protect_file()
#
# Make the named file readable and writable only by the current user
# (who is also the creator and owner of the file).  Surprisingly hard
# on Windows.  See the MSDN documentation on ACLs (e.g. [Nefcy 1994]).

if os.name=='posix':
    def protect_file(filename):
        os.chmod(filename, 0600)
else:
    import win32file
    import win32security
    import win32api

    def protect_file(filename):
        # get the SID for this user on this system.
        userName = win32api.GetUserName()
        systemName = '\\\\' + win32api.GetComputerName()
        userSID = win32security.LookupAccountName(systemName, userName)[0]

        # Initialize an SD.
        sd = win32security.SECURITY_DESCRIPTOR()

        # Initialize an ACL.  The magic number 128 is a buffer size,
        # based on some experimental code which suggested that 52
        # would be sufficient.  NB 2003-09-17.
        acl = win32security.ACL(128)

        # Add the user to the ACL.
        acl.AddAccessAllowedAce(win32file.FILE_ALL_ACCESS, userSID)

        # Set the DACL of the SD to the ACL we've created.
        sd.SetDacl(1, acl, 0)

        # Set the DACL of the file to the SD's DACL.
        try:
            win32security.SetFileSecurity(filename,
                                          win32security.DACL_SECURITY_INFORMATION,
                                          sd)
        except:
            # In some builds of the Python Extensions for Windows,
            # SetFileSecurity raises a bogus exception!
            pass

# A. REFERENCES
#
# 
# [Nefcy 1994] "Windows NT Security"; Christopher Nefcy; Microsoft
# Corporation; 1994-09;
# <http://msdn.microsoft.com/library/en-us/dnsecure/html/msdn_ntprog.asp>
#
# 
# B. DOCUMENT HISTORY
#
# 2003-09-17 NB Created.
#
#
# C. COPYRIGHT AND LICENSE
#
# This file is copyright (c) 2003 Perforce Software, Inc.  All rights
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/portable.py#1 $
