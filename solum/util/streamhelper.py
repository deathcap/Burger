#!/usr/bin/env python
# -*- coding: utf8 -*-
__all__ = ['StreamReader']

import struct


class StreamReader(object):
    def __init__(self, source):
        self.source = source

    def read(self, fmt):
        return struct.unpack(fmt,
            self.source.read(struct.calcsize(fmt))
        )
