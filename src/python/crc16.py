#!/usr/bin/env python

# crc16.py by Bryan G. Olson, 2005
# This module is free software and may be used and
# distributed under the same terms as Python itself.

"""
     CRC-16 in Python, as standard as possible. This is
     the 'reflected' version, which is usually what people
     want. See Ross N. Williams' /A Painless Guide to
     CRC error detection algorithms/.
"""

from array import array


def crc16(string, value=0):
     """ Single-function interface, like gzip module's crc32
     """
     for ch in string:
         value = table[ord(ch) ^ (value & 0xff)] ^ (value >> 8)
     return value


class CRC16(object):
     """ Class interface, like the Python library's cryptographic
         hash functions (which CRC's are definitely not.)
     """

     def __init__(self, string=''):
         self.val = 0
         if string:
             self.update(string)

     def update(self, string):
         self.val = crc16(string, self.val)

     def checksum(self):
         return chr(self.val >> 8) + chr(self.val & 0xff)

     def hexchecksum(self):
         return '%04x' % self.val

     def copy(self):
         clone = CRC16()
         clone.val = self.val
         return clone


# CRC-16 poly: p(x) = x**16 + x**12 + x**5 + 1
# top bit implicit, reflected
poly = 0x1021
table = array('H')
for byte in range(256):
     crc = 0
     for bit in range(8):
         if (byte ^ crc) & 1:
             crc = (crc >> 1) ^ poly
         else:
             crc >>= 1
         byte >>= 1
     table.append(crc)

crc = CRC16()
crc.update("123456789")
#print crc.hexchecksum()
#assert crc.checksum() == '\xf3\xf2'

