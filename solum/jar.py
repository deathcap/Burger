#!/usr/bin/env python
# -*- coding: utf8 -*-
__all__ = ['JarFile', 'JarError']

import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from .manifest import ManifestFile
from .core import ClassFile


class JarError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class JarFile(object):
    def __init__(self, source=None):
        self._files = {}
        self._cache_class_count = None

        if source and zipfile.is_zipfile(source):
            source_ = zipfile.ZipFile(source, 'r')
            # TODO: Can we creatively patch ZipFile to allow us to
            # safely pass ZipInfo on Python < 2.6?
            for zi in source_.infolist():
                self._files[zi.filename] = source_.read(zi.filename)
            source_.close()
        elif source:
            raise JarError('source is not a valid zip file')

        self._manifest = ManifestFile(
            self._files.pop('META-INF/MANIFEST.MF', None)
        )

    def read(self, filename):
        """Returns the contents of the file `filename`."""
        return self._files.get(filename)

    def open(self, filename):
        """
        Opens and returns a file-like object for `filename`. The caller
        is responsible for closing this resource when finished.
        """
        contents = self.read(filename)
        if not contents:
            raise JarError('file does not exist')
        return StringIO(contents)

    def open_class(self, filename):
        """
        Opens and returns a ClassFile object for the given `filename`.
        If the filename is missing the .class suffix, it will be added.
        """
        if not filename.endswith('.class'):
            filename = filename.replace('.', '/')
            filename = '%s.class' % filename

        return ClassFile(self.open(filename))

    def write(self, filename, contents):
        """
        Creates or overwrites `filename` with `contents`. This has
        no effect on-disk until `save()` is called.
        """
        self._cache_class_count = None
        self._files[filename] = contents

    def remove(self, filename):
        """
        Removes the file `filename` if it exists. Returns `True` if the file
        was removed, `False` otherwise.
        """
        if filename in self._files:
            self._cache_class_count = None
            del self._files[filename]
            return True
        return False

    @property
    def class_count(self):
        """Returns the number of classes in the JAR."""
        if self._cache_class_count is not None:
            return self._cache_class_count

        tally = 0
        for file_ in self._files.iterkeys():
            if file_.endswith('.class'):
                tally += 1

        self._cache_class_count = tally
        return tally

    def save(self, output):
        """
        Saves the JAR into the file at `output`, which will be overwritten
        if it exists.

        WARNING: This is far from perfect, and information may be lost. It
        is advised to keep a copy of any source JAR.
        """
        if not self._files:
            # Trying to write empty ZIPs with ZipFile will produce
            # invalid archives (missing central directory).
            raise JarError('cannot save an empty JAR')

        out = zipfile.ZipFile(output, 'w')

        # Make sure the manifest (if it exists) is the first record
        # in the JAR for legacy reasons.
        out.writestr('META-INF/MANIFEST.MF', self.manifest.build())
        for filename, filedata in self._files.iteritems():
            out.writestr(filename, filedata)
        out.close()

    @property
    def manifest(self):
        """Returns the underlying JAR MANIFEST.MF."""
        return self._manifest
