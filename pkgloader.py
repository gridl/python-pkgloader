"""Loader for versioned modules.

Primary idea is to allow several major versions to co-exists.
Secondary idea - allow checking minimal minor version.

Based on idea from pygtk.  Assume you have directory
like this in python path::

    site-packages/
        gtk/
          __init__.py
        gtk-2.0/
            gtk/
              __init__.py
        gtk-3.0/
            gtk/
              __init__.py

Then

    import pkgloader
    pkgloader.require('gtk', '2.0')
    import gtk

Should loader 'gtk' module under gtk-2.0 directory and not
from any other.

"""

from __future__ import division, absolute_import, print_function

import sys
import os
import os.path
import re

__all__ = ['require']

_pkg_cache = None
_import_cache = {}
_pat = re.compile(r'^([a-z_]+)-([0-9]+)\.([0-9]+)$')


def _str2ver(vstr):
    parts = tuple([int(n) for n in vstr.split('.')] + [0, 0])
    return parts[:2]


def _ver2str(parts):
    return '.'.join([str(n) for n in parts])


def _load_pkg_cache():
    global _pkg_cache
    if _pkg_cache is not None:
        return _pkg_cache
    _pkg_cache = {}
    seen = set()
    for topdir in sys.path:
        if not os.path.isdir(topdir):
            continue
        for dirname in os.listdir(topdir):
            m = _pat.match(dirname)
            if not m:
                continue
            if dirname in seen:
                continue
            fullpath = os.path.join(topdir, dirname)
            if not os.path.isdir(fullpath):
                continue
            modname = m.group(1)
            modver = (int(m.group(2)), int(m.group(3)))
            _pkg_cache.setdefault(modname, []).append((modver, fullpath))
            seen.add(dirname)
    for vlist in _pkg_cache.values():
        vlist.sort(reverse=True)
    return _pkg_cache


def _install_path(pkg, newpath):
    for p in sys.path:
        pname = os.path.basename(p)
        m = _pat.match(pname)
        if m and m.group(1) == pkg:
            sys.path.remove(p)
    sys.path.insert(0, newpath)


def require(pkg, reqver):
    # parse arg
    need = _str2ver(reqver)

    # check if we already have one installed
    if pkg in _import_cache:
        got = _import_cache[pkg]
        if need[0] != got[0] or need > got:
            raise ImportError("Request for package '%s' ver '%s', have '%s'" % (
                              pkg, reqver, _ver2str(got)))
        return

    # pick best ver from available ones
    cache = _load_pkg_cache()
    if pkg not in cache:
        return

    for pkgver, pkgdir in cache[pkg]:
        if pkgver[0] == need[0] and pkgver >= need:
            # install the best one
            _install_path(pkg, pkgdir)
            break

    inst_ver = need

    # now import whatever is available
    mod = __import__(pkg)

    # check if it is actually useful
    ver_str = getattr(mod, '__version__') or ''
    ver_str = re.sub('^([0-9.]+).*', r'\1', ver_str)
    full_ver = _str2ver(ver_str)
    if full_ver[0] != need[0] or need > full_ver:
        raise ImportError("Request for package '%s' ver '%s', have '%s'" % (
                          pkg, reqver, _ver2str(full_ver)))
    inst_ver = full_ver

    # remember full version
    _import_cache[pkg] = inst_ver

    return mod

