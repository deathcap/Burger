#!/usr/bin/env python
# -*- coding: utf8 -*-
__all__ = ['ManifestFile', 'ManifestError']

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ManifestError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


def _chunk_line(line, n):
    return [line[i:i + n] for i in range(0, len(line), n)]


class ManifestFile(object):
    """Parses, constructs, and validates MANIFEST.MF files."""
    def __init__(self, source=None):
        """
        Creates a new manifest file, optionally populating it from
        the string or file-like object `source`.
        """
        self._entries = {}
        self._header = {
            'Manifest-Version': '1.0',
        }

        if source:
            is_stringio = False
            if isinstance(source, basestring):
                source = StringIO(source)
                is_stringio = True

            is_header = True
            current_entry = None
            last_key = None
            tmp_entry = {}

            for line in source:
                # Is it the end of a section?
                if not line.strip():
                    if is_header:
                        is_header = False
                        self._header.update(tmp_entry)
                    elif not current_entry:
                        break
                    else:
                        self._entries[current_entry] = tmp_entry

                    tmp_entry = {}
                    current_entry = None

                    continue

                # Is this a continuation of the previous line?
                if line[0] == ' ':
                    if not last_key:
                        raise ManifestError('invalid manifest continuation')

                    tmp_entry[current_entry][last_key] += line[1:]
                else:
                    key, value = line.strip().split(':', 1)
                    if key == 'Name':
                        current_entry = value.lstrip()
                    tmp_entry[key] = value.lstrip()

            if is_stringio:
                source.close()

        else:
            self._header['Created-By'] = self.created_by

    @property
    def created_by(self):
        """
        Returns a human-readable string of what program has created or
        editted this JAR file. This should not be relied upon, as there
        is no convention to its format nor verification as to its
        authenticity.
        """
        return self._header.get('Created-By', '2.0.0 (Solum)')

    @created_by.setter
    def created_by(self, value):
        """
        Sets the 'Created-By' property of the manifest
        file.
        """
        if not self.is_valid_value(value):
            raise ManifestError('invalid value')

        self._header['Created-By'] = value

    def is_valid_value(self, value):
        """
        Returns `True` if the value complies with the Manifest Specification,
        else `False`.
        """
        if len(value) > 65535:
            return False

        return True

    @property
    def main_class(self):
        """Returns the name of main class in the Jar, if one is set."""
        return self._header.get('Main-Class')

    @main_class.setter
    def main_class(self, value):
        """Sets the main class in the jar."""
        if isinstance(value, basestring):
            value = value.replace('.', '/')
            value = value.replace('.class', '')
            value = value.strip()

        self._header['Main-Class'] = value

    def get_entry(self, name):
        """Returns the dictionary for the entry `name`."""
        ct = self._entries.get(name)
        return ct.copy() if ct is not None else None

    def get_header(self, field):
        """Returns a field from the header."""
        return self._header.get(field)

    def add_package(self, name, values):
        """
        Adds a new section to the manifest, populating it with `values`,
        which can be anything accepted to the dict() constructo.
        """
        self._entries[name] = dict(values)
        self._entries[name]['Name'] = name

    @property
    def packages(self):
        """Returns a (shallow) copy of all packages in the manifest."""
        return self._entries.copy()

    @property
    def headers(self):
        """Returns a (shallow) copy of the manifest header."""
        return self._header.copy()

    def build(self):
        """Returns the final, valid MANIFEST.MF file as a string."""
        output = []

        # Build the manifest header
        output.append('Manifest-Version: 1.0\n')
        for k, v in self._header.iteritems():
            # We only output V1 manifests, so ignore
            # this if it's set.
            if k == 'Manifest-Version':
                continue
            if v is None:
                continue
            output.append('%s: %s\n' % (k, v))
        output.append('\n')

        # Build the manifest sections
        for package_name, package_data in self._entries.iteritems():
            output.append('Name: %s\n' % package_name)
            for k, v in package_data.iteritems():
                if k == 'Name':
                    continue
                if v is None:
                    continue
                output.append('%s: %s\n' % (k, v))
            output.append('\n')

        # Chunk all the lines so none is more than
        # 72 characters, including colon, space,
        # and newline.
        final = []
        for i, line in enumerate(output):
            if len(line) <= 72:
                final.append(line)
                continue

            parts = _chunk_line(line, 72)
            last_line = parts.pop()
            final.append('%s\n' % parts.pop(0))
            for part in parts:
                final.append(' %s\n' % part)
            final.append(' %s' % last_line)

        return ''.join(final)
