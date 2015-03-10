#!/usr/bin/env python
# -*- coding: utf8 -*-
__all__ = ['ConstantError']

from collections import namedtuple

from ..util import StreamReader
from ..descriptor import method_descriptor, field_descriptor


class ConstantType(object):
    CLASS = 7
    FIELD = 9
    METHOD = 10
    INTERFACE = 11
    STRING = 8
    INTEGER = 3
    FLOAT = 4
    LONG = 5
    DOUBLE = 6
    NAME_AND_TYPE = 12
    UTF8 = 1

Constant = namedtuple('Constant', 'tag disk_index')
ConstantClass = namedtuple('ConstantClass', Constant._fields + ('name',))
ConstantString = namedtuple('ConstantString', Constant._fields + ('value',))
ConstantInteger = namedtuple('ConstantInteger', Constant._fields + ('value',))
ConstantFloat = namedtuple('ConstantFloat', Constant._fields + ('value',))
ConstantLong = namedtuple('ConstantLong', Constant._fields + ('value',))
ConstantDouble = namedtuple('ConstantDouble', Constant._fields + ('value',))
ConstantMethod = namedtuple('ConstantMethod',
        Constant._fields + ('class_name', 'name', 'takes', 'returns'))
ConstantField = namedtuple('ConstantField',
        Constant._fields + ('class_name', 'name', 'of_type'))
ConstantInterface = namedtuple('ConstantInterface',
        Constant._fields + ('class_name', 'name', 'of_type'))


class ConstantPool(object):
    def __init__(self, source=None, collect_stats=True):
        """
        Constructs a new constants pool, optionally
        loading it from the given `source`.
        """
        self._constants = []

        if source is not None:
            self.read_from_file(source)

    def read_from_file(self, source):
        """
        Reads in a constant pool from `source`, assuming the
        cursor is positioned at the pool length prelude.
        """
        sr = StreamReader(source)

        # Get the number of entries in the constant pool, with
        # each long and double counting as two entries.
        pool_count = sr.read('>H')[0]
        position = 1

        # Store our temporary indices to be remapped after
        # loading from the stream.
        temporary_map = {}

        while position < pool_count:
            tag, = sr.read('>B')
            tmp = dict(tag=tag)

            # All three of these have the same on-disk structure.
            if tag in (ConstantType.METHOD,
                    ConstantType.FIELD, ConstantType.INTERFACE):
                tmp['class_index'], tmp['type_index'] = sr.read('>HH')
            elif tag == ConstantType.CLASS:
                tmp['name_index'], = sr.read('>H')
            elif tag == ConstantType.STRING:
                tmp['string_index'], = sr.read('>H')
            elif tag == ConstantType.INTEGER:
                tmp['value'], = sr.read('>i')
            elif tag == ConstantType.FLOAT:
                tmp['value'], = sr.read('>f')
            elif tag == ConstantType.LONG:
                tmp['value'], = sr.read('>q')
            elif tag == ConstantType.DOUBLE:
                tmp['value'], = sr.read('>d')
            elif tag == ConstantType.NAME_AND_TYPE:
                tmp.update(zip(
                    ['name_index', 'descriptor_index'],
                    sr.read('>HH')
                ))
            elif tag == ConstantType.UTF8:
                length, = sr.read('>H')
                tmp['value'], = sr.read('>%ss' % length)

            temporary_map[position] = tmp
            position += 2 if tag in (ConstantType.DOUBLE,
                    ConstantType.LONG) else 1

        # Now that we have the complete map, we can create our
        # internal constants and get rid of the cruft.
        for index, constant in temporary_map.iteritems():
            tag = constant['tag']
            if tag == ConstantType.CLASS:
                name = temporary_map[constant['name_index']]['value']
                name = name.replace('/', '.')
                tmp = ConstantClass(tag, index, name)
            elif tag == ConstantType.STRING:
                value = temporary_map[constant['string_index']]['value']
                tmp = ConstantString(tag, index, value)
            elif tag == ConstantType.INTEGER:
                tmp = ConstantInteger(tag, index, constant['value'])
            elif tag == ConstantType.FLOAT:
                tmp = ConstantFloat(tag, index, constant['value'])
            elif tag == ConstantType.LONG:
                tmp = ConstantLong(tag, index, constant['value'])
            elif tag == ConstantType.DOUBLE:
                tmp = ConstantDouble(tag, index, constant['value'])
            elif tag == ConstantType.NAME_AND_TYPE:
                # Will be inlined by anything that needs it.
                continue
            elif tag == ConstantType.UTF8:
                # Will be inlined by anything that needs it.
                continue
            elif tag in (9, 10, 11):
                class_ = temporary_map[constant['class_index']]
                name = temporary_map[class_['name_index']]['value']
                name = name.replace('/', '.')
                type_ = temporary_map[constant['type_index']]
                type_name = temporary_map[type_['name_index']]['value']
                descriptor = temporary_map[type_['descriptor_index']]['value']

                if tag == ConstantType.METHOD:
                    args, returns = method_descriptor(descriptor)
                    tmp = ConstantMethod(tag, index, name, type_name, args,
                        returns)
                elif tag == ConstantType.FIELD:
                    of_type = field_descriptor(descriptor)
                    tmp = ConstantField(tag, index, name, type_name, of_type)
                elif tag == ConstantType.INTERFACE:
                    args, returns = method_descriptor(descriptor)
                    tmp = ConstantInterface(tag, index, name, type_name, args,
                        returns)
            else:
                raise RuntimeError('Invalid constant type.')

            self.add(tmp)

    def add(self, constant):
        """Adds a Constant object to our internal mechanism."""
        self._constants.append(constant)

    def remove(self, tag=None, f=None):
        """
        Removes all matching constants from the pool that match
        the criteria.
        """
        def keep(constant):
            if tag is not None and constant.tag != tag:
                return False

            if f is not None and not f(constant):
                return False

            return True

        self._constants[:] = [c for c in self._constants if keep(c)]

    def remove_one(self, tag=None, f=None, instance=None):
        """
        Removes the first constant from the pool that matches the given
        criteria, returning it.
        """
        for i, constant in enumerate(self._constants):
            if instance is not None and constant is instance:
                return self._constants.pop(i)

            if tag is not None and constant.tag != tag:
                continue

            if f is not None and not f(constant):
                continue

            return self._constants.pop(i)

    def find(self, tag=None, f=None):
        """
        Yields all constants from the pool that match the criteria.
        """
        for constant in self._constants:
            if tag is not None and constant.tag != tag:
                continue

            if f is not None and not f(constant):
                continue

            yield constant

    def find_one(self, tag=None, f=None):
        """
        Returns the first matching constant from the pool,
        or `None` if there were no matches.
        """
        for constant in self._constants:
            if tag is not None and constant.tag != tag:
                continue

            if f is not None and not f(constant):
                continue

            return constant

        return None
