#!/usr/bin/env python
# -*- coding: utf8 -*-
__all__ = ['ClassFile', 'ClassError']

import struct

from .constants import ConstantPool


class ClassError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class ClassFile(object):
    def __init__(self, source=None):
        self._this = None
        self._version = (0x31, 0)

        if source and isinstance(source, basestring):
            self._load_from_path(source)
        elif source:
            self._load_from_file(source)

    def _load_from_file(self, source):
        def read(fmt):
            return struct.unpack(fmt, source.read(struct.calcsize(fmt)))

        magic_number, = read(">I")
        if magic_number != 0xCAFEBABE:
            raise ClassError('not a valid classfile')

        ver_min, ver_maj = read(">HH")
        self._version = (ver_maj, ver_min)

        self._cp = ConstantPool(source)

    def _load_from_path(self, path):
        sin = open(path, 'rb')
        self._load_from_file(sin)
        sin.close()

    @staticmethod
    def is_classfile(source):
        """
        Returns `True` if `source` is a valid ClassFile, False otherwise.
        If the source does not exist, an exception will be raised.
        """
        def check_stream(stream):
            if struct.unpack('>I', stream.read(4))[0] == 0xCAFEBABE:
                return True
            return False

        if isinstance(source, basestring):
            tmp = open(source, 'rb')
            result = check_stream(tmp)
            tmp.close()
        else:
            result = check_stream(source)
            try:
                source.seek(0, 0)
            except IOError:
                pass

        return result

    @property
    def constants(self):
        """Returns the class constant pool."""
        return self._cp

    @property
    def version(self):
        """Returns a tuple of (major_version, minor_version)."""
        return self._version

    @property
    def version_string(self):
        """
        Returns a human-readable string representing the version of Java used
        to construct this ClassFile.
        """
        return {
            0x2D: "JDK 1.1",
            0x2E: "JDK 1.2",
            0x2F: "JDK 1.3",
            0x30: "JDK 1.4",
            0x31: "J2SE 5.0",
            0x32: "J2SE 6.0"
        }.get(self.version[0], "unknown")
