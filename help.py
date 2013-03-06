# Routines borrowed from mayavi2
# Authors: Gael Varoquaux <gael.varoquaux[at]normalesup.org>
#          Prabhu Ramachandran
# Copyright (c) 2007-2008, Enthought, Inc.
# License: BSD Style.

import os, sys

# To find the html documentation directory, first look under the
# standard place.  If that directory doesn't exist, assume you
# are running from the source.
local_dir = os.path.dirname(sys.argv[0])
LOCAL_HELP_DIR = os.path.join(local_dir, 'docs/_build/html')
if not os.path.exists(LOCAL_HELP_DIR):
    LOCAL_HELP_DIR = None


def browser_open(url):
    if sys.platform == 'darwin':
        os.system('open %s &' % url)
    else:
        import webbrowser
        if webbrowser._iscommand('firefox'):
            # Firefox is installed, let's use it, we know how to make it chromeless.
            firefox = webbrowser.get('firefox')
            firefox._invoke(['-chrome', url], remote=False, autoraise=True)
        else:
            webbrowser.open(url)


def open_help_index():
    ''' Open the user manual index in a browser. '''
    # If the HTML_DIR was found, bring up the documentation in a
    # web browser.  Otherwise, try the interwebs.
    if LOCAL_HELP_DIR is not None:
        path_pieces = LOCAL_HELP_DIR.split('\\')
        browser_open('/'.join(['file://'] + path_pieces + ['index.html']))
#        browser_open(os.path.join('file:///', LOCAL_HELP_DIR, 'index.html'))
    else:
        browser_open('http://sinspect.readthedocs.org')
