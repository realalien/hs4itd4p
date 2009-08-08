#                Perforce Defect Tracking Integration Project
#                 <http://www.ravenbrook.com/project/p4dti/>
#
#             CONFIG_LOADER.PY -- LOCATE AND LOAD CONFIGURATION
#
#                Nick Levine, Ravenbrook Limited, 2001-11-07
#
#
# 1. INTRODUCTION
#
# This module locates and loads the P4DTI configuration.
#
# If the environment variable P4DTI_CONFIG is specified, then load the
# configuration from that file (this is so we can support multiple P4DTI
# instances using multiple configuration files, either for testing, or
# when there are multiple Perforce servers -- requirement 96).
#
# Don't load the P4DTI configuration if the config module is already
# loaded, regardless of the P4DTI_CONFIG environment variable.  This is
# so that a test harness can substitute its own preferred configuration.
# See [GDR 2001-03-14, 2.2].
#
# After loading this file you will typically want to import config, to
# gain direct access to that module's namespace.  (It's better to write
# "from config_loader import config" since you only want the latter.)
#
# The intended readership of this document is project developers.
#
# This document is not confidential.

import imp
import os
import sys

if (not sys.modules.has_key('config')
    and os.environ.has_key('P4DTI_CONFIG')):
    file = open(os.environ['P4DTI_CONFIG'])
    try:
        imp.load_source('config', os.environ['P4DTI_CONFIG'], file)
    finally:
        file.close()

# Need this so we can write "from config_loader import config".
import config


# A. REFERENCES
#
# [GDR 2001-03-14] "test_p4dti.py -- Test the P4DTI"; Gareth Rees;
# Ravenbrook Limited; 2001-03-14;
# <http://www.ravenbrook.com/project/p4dti/version/2.4/test/test_p4dti.py>.
#
#
# B. Document History
#
# 2001-11-07 NDL Created, extracting code from init.py so that it can
# be shared by service.py
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
# $Id: //info.ravenbrook.com/project/p4dti/version/2.4/code/replicator/config_loader.py#2 $
