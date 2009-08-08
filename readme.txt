PERFORCE DEFECT TRACKING INTEGRATION README FOR RELEASE 2.4.5

Richard Brooksby, Ravenbrook Limited

$Date: 2009/05/07 $


CONTENTS

  1. Introduction
  2. Installation
    2.1. Upgrading from an old release of the P4DTI
    2.2. Installing the Bugzilla integration on Linux
    2.3. Installing the Bugzilla integration on Solaris
    2.4. Installing the Bugzilla integration on Windows 2000
    2.5. Installing the Integration Kit
  A. References
  B. Document history
  C. Copyright and license

1. INTRODUCTION

This is release 2.4.5 of the Perforce Defect Tracking Integration
(P4DTI).

The P4DTI connects your defect tracking system to Perforce, so that you
don't have to switch between them and enter duplicate information about
your work.  It also links changes made in Perforce with defect tracker
issues, making it easy to find out why a change was made, find the work
that was done to resolve an issue, or generate reports relating issues
to files or codelines.

For supported configurations, contact information, and what's new in
this release, see the release notes (release-notes.txt).

If you are planning to modify, adapt, or extend the P4DTI, please
download and unpack the P4DTI Integration Kit.  See section 2.5.

The readership of this document is anyone who wants to download and use
the Perforce Defect Tracking Integration.

This document is not confidential.


2. INSTALLATION


2.1. Upgrading from an old release of the P4DTI

If you're running an old release of the P4DTI, then you must follow
these steps when upgrading to this release:

  1. Stop the replicator.

  2. Make a copy of your configuration file config.py in a safe place.

  3. (Bugzilla only.)  Remove the old Bugzilla patch.  Go to the Bugzilla
installation directory and run the command:

     patch -R < /opt/p4dti/bugzilla-VERSION-patch

where VERSION is the version of Bugzilla (for example, 3.0).  (If
you didn't install the Bugzilla integration as an RPM, then the patch
file will be wherever you installed it, not necessarily in
/opt/p4dti.)

  4. If your old release was installed as an RPM, run the following
command as root to uninstall it:

     rpm -e p4dti

  5. Install the P4DTI as normal (see sections 2.2 to 2.4 below).

  6. Copy your old configuration file as config.py in the new P4DTI
installation directory.


2.2. Installing the Bugzilla integration on Linux

The integration is distributed as an RPM called
"p4dti-2.4.5-1.i386.rpm".  Transfer this to the Bugzilla server machine,
then run the following command as root:

  rpm -i p4dti-2.4.5-1.i386.rpm

This will install the P4DTI files into /opt/p4dti and a startup script
in the /etc/rc.d/init.d directory.

Then consult the Administrator's Guide (installed as
"/usr/doc/p4dti-2.4.5/ag/index.html") for further instructions.

If you prefer not to use RPMs, you can follow the procedure in section
2.3.


2.3. Installing the Bugzilla integration on Solaris

The integration is distributed as a gzipped tar file called
"p4dti-bugzilla-2.4.5.tar.gz".  Unpack this tarball on the Bugzilla
server machine, using the command

  gunzip -c p4dti-bugzilla-2.4.5.tar.gz | tar xvf -

Then consult the Administrator's Guide (installed as
"p4dti-bugzilla-2.4.5/ag/index.html") for further instructions.


2.4. Installing the Bugzilla integration on Windows 2000 or Windows NT

On the Bugzilla Windows machine, run the "p4dti-bugzilla-2.4.5.exe"
installer program that came with this document.  This will unpack the
integration.  We recommend installing the integration in "C:\Program
Files\P4DTI-2.4.5\" but you can ask the installer to put it somewhere
else.

Then consult the Administrator's Guide (installed by default in
"C:\Program Files\P4DTI-2.4.5\ag\index.html") for further instructions.


2.5. Installing the integration kit

The P4DTI integration kit is a complete set of P4DTI sources and
documentation to enable third parties to develop new integrations.
You should only install it if you are planning to modify, adapt, or
extend the P4DTI.

For Windows, the integration kit is distributed as the ZIP archive
"p4dti-kit-2.4.5.zip".  Unpack it using WinZip.

For Unix, the integration kit is distributed as the tarball
"p4dti-kit-2.4.5.tar.gz".  Unpack it using the command "gunzip -c
p4dti-kit-2.4.5.tar.gz | tar xvf -".

Then consult the Integration Kit readme file
(p4dti-kit-2.4.5/kit-readme.txt) for further instructions.


A. REFERENCES

None.


B. DOCUMENT HISTORY

2007-08-16 NB Updated for release 2.4.1

2007-09-25 NB Updated for release 2.4.2

2009-03-03 NB Updated for release 2.4.3

2009-04-14 NB Updated for release 2.4.4

2009-05-07 NB Updated for release 2.4.5

C. COPYRIGHT AND LICENSE

This document is copyright (C) 2001 Perforce Software, Inc.  All rights
reserved.

Redistribution and use of this document in any form, with or without
modification, is permitted provided that redistributions of this
document retain the above copyright notice, this condition and the
following disclaimer.

THIS DOCUMENT IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDERS AND CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
DOCUMENT, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

$Id: //info.ravenbrook.com/project/p4dti/version/2.4/readme.txt#7 $
