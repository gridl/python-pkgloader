
import sys
import os
import os.path

from nose.tools import *

import pkgloader

# add test dir to path, in double
top = os.path.dirname(__file__)
sys.path.append(top)
sys.path.append(top)

def test_version():
    nonex = '/etc/non/exist/dir/modfoo-1.1'
    sys.path.append(nonex)

    pkgloader.require('modfoo', '2.0')
    import modfoo
    eq_(modfoo.__version__, '2.2')

    pkgloader.require('modfoo', '2.0')

    assert_raises(ImportError, pkgloader.require, 'modfoo', '3.0')

    assert_false(nonex in sys.path)

def test_unknown():
    pkgloader.require('unknown', '2.0')

def test_bad_ver():
    assert_raises(ImportError, pkgloader.require, 'mod_bad_ver', '4.1')

