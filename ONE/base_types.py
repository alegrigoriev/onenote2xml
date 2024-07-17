#   Copyright 2024 Alexandre Grigoriev
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import annotations
import locale
from .exception import ArgumentException
from .STORE.reader import onestore_reader  # For annotations

'''
DEAR MICROSOFT DOCUMENTATION WRITER!

WHO THE FUCK THOUGHT IT'S A GOOD IDEA
TO SHOW THE LEAST SIGNIFICANT BIT FIRST
AND THE MOST SIGNIFICANT BIT LAST???

AND NOT EXPLICITLY EXPLAIN THAT CLUSTERFUCK ANYWHERE!!
'''

class CompactID:

	def __init__(self, reader:onestore_reader):
		'''
		The CompactID structure is a combination of two unsigned integers.
		A CompactID structure together with a global identification table (section 2.1.3)
		specifies an ExtendedGUID structure (section 2.2.1). This structure has the following format.

		n (8 bits): An unsigned integer that specifies the value of the ExtendedGUID.n field.
		guidIndex (24 bits): An unsigned integer that specifies the index in the global identification table.
		The GUID that corresponds to this index provides the value for the ExtendedGUID.guid field.
		'''
		word = reader.read_uint32()
		self.n = word & 0xFF
		self.guidIndex = word >> 8
		return

	def __str__(self):
		return "{%d},%d" % (self.guidIndex, self.n)

	def IsZero(self):
		return self.guidIndex == 0 and self.n == 0

def _IterBytesToWords(src:bytes):
	ii = iter(src)
	for c_low in ii:
		c_high = next(ii, None)
		if c_high is None:
			return
		yield c_low | (c_high << 8)
		continue
	return

def Utf16BytesToStr(src:bytes):
	ii = _IterBytesToWords(src)
	s = str()
	for wc in ii:
		# Convert from UTF-16 surrogate pair to UTF-32, if necessary
		if wc >= 0xD800 and wc <= 0xDFFF:
			if wc >= 0xDC00:
				# Surrogate Encoding error
				continue
			wc_low = next(ii, None)
			if wc_low is None:
				break
			if wc_low < 0xDC00 or wc_low > 0xDFFF:
				# Surrogate Encoding error
				continue
			wc = ((wc - 0xD800) << 10)|(wc_low - 0xDC00)

		# drop zero terminator:
		if wc == 0:
			break
		s += chr(wc)
		continue
	return s

LCID2Encoding = {}

def MbcsBytesToStr(src:bytes, lcid, charset):
	#encoding = LCID2Encoding.get(lcid, None)
	#if encoding is None:
	#	import win32api
	#	locale_name = win32api.LCIDToLocaleName(lcid, 0)
	#	prev_locale = locale.getlocale(locale.LC_CTYPE)
	#	locale.setlocale(locale.LC_CTYPE, str(lcid))
	#	encoding = locale.getpreferredencoding(do_setlocale=False)
	#	LCID2Encoding[lcid] = encoding
	#	locale.setlocale(locale.LC_CTYPE, prev_locale)
		# Get locale by lcid
	return str(src, encoding="mbcs")

def StringInStorageBuffer(reader:onestore_reader):
	'''
	cch (4 bytes): An unsigned integer that specifies the number of characters in the string.
	StringData (variable): An array of UTF-16 Unicode characters. The length of the array MUST be equal to the value specified by the cch field.
	'''

	length = reader.read_uint32()
	return Utf16BytesToStr(reader.read_bytes(length*2))

import datetime
GregorianEpoch = datetime.datetime(1601, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

def GetFiletime64Datetime(filetime:int, local=True):
	date = GregorianEpoch + datetime.timedelta(seconds=filetime / 10000000.)
	if local:
		# Convert to local timezone
		date = date.astimezone()
	return date

# Note that unlike Unix epoch (which starts from 1970), this starts from 1980
Time32Epoch = datetime.datetime(1980, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
def GetTime32Datetime(time32:int, local=True):
	date = Time32Epoch + datetime.timedelta(seconds=float(time32))
	if local:
		# Convert to local timezone
		date = date.astimezone()
	return date

def Filetime64ToUnixTimestamp(filetime:int):
	date = GregorianEpoch + datetime.timedelta(seconds=filetime / 10000000.)
	return int(date.timestamp())

def Time32ToUnixTimestamp(time32:int):
	date = Time32Epoch + datetime.timedelta(seconds=float(time32))
	return int(date.timestamp())

class FileNodeChunkReference:
	'''
	'''

	def __init__(self, reader:onestore_reader, StpFormat, CbFormat):
		if StpFormat == 0:
			self.stp = reader.read_uint64()
		elif StpFormat == 1:
			self.stp = reader.read_uint32()
		elif StpFormat == 2:
			self.stp = reader.read_uint16() * 8
		elif StpFormat == 3:
			self.stp = reader.read_uint32() * 8
		else:
			raise ArgumentException("Invalid chunk position format %d" % (StpFormat,))

		if CbFormat == 0:
			self.cb = reader.read_uint32()
		elif CbFormat == 1:
			self.cb = reader.read_uint64()
		elif CbFormat == 2:
			self.cb = reader.read_uint8() * 8
		elif CbFormat == 3:
			self.cb = reader.read_uint16() * 8
		else:
			raise ArgumentException("Invalid chunk size format %d" % (CbFormat,))

		if self.cb != 0:
			return

		# Convert to 64 bit Nil from smaller formats
		if StpFormat == 1:
			if self.stp == 0xFFFFFFFF:
				self.stp = 0xFFFFFFFFFFFFFFFF
		elif StpFormat == 2:
			if self.stp == 0xFFFF*8:
				# Convert to 64 bit Nil
				self.stp = 0xFFFFFFFFFFFFFFFF
		elif StpFormat == 3:
			if self.stp == 0xFFFFFFFF*8:
				# Convert to 64 bit Nil
				self.stp = 0xFFFFFFFFFFFFFFFF
		return

	def isZero(self):
		return self.stp == 0 and self.cb == 0

	def isNil(self):
		return self.stp == 0xFFFFFFFFFFFFFFFF and self.cb == 0

	def __str__(self):
		return "%X:%X" % (self.stp, self.cb)

class FileChunkReference32(FileNodeChunkReference):

	def __init__(self, reader:onestore_reader):
		self.stp = reader.read_uint32()
		self.cb = reader.read_uint32()

		# Convert to 64 bit Nil from 32 bit
		if self.cb == 0 and self.stp == 0xFFFFFFFF:
			self.stp = 0xFFFFFFFFFFFFFFFF
		return

class FileChunkReference64x32(FileNodeChunkReference):

	def __init__(self, reader:onestore_reader):
		self.stp = reader.read_uint64()
		self.cb = reader.read_uint32()
		return

class FileChunkReference64(FileNodeChunkReference):

	def __init__(self, reader:onestore_reader):
		self.stp = reader.read_uint64()
		self.cb = reader.read_uint64()
		return

class JCID:
	def __init__(self, jcid:int=0):
		self.jcid = jcid
		return

	def read(self, reader:onestore_reader):
		self.jcid = reader.read_uint32()
		return self

	def index(self):
		return self.jcid & 0xFFFF

	def IsBinary(self):
		return (self.jcid & 0x10000) != 0

	def IsPropertySet(self):
		return (self.jcid & 0x20000) != 0

	def IsGraphNode(self):
		return (self.jcid & 0x40000) != 0	# Unspecified

	def IsFileData(self):
		return (self.jcid & 0x80000) != 0

	def IsReadOnly(self):
		return (self.jcid & 0x100000) != 0

class GUID:
	def __init__(self, guid:bytes|str=None):
		if type(guid) is str:
			import re
			m = re.fullmatch(r'\{([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})\}', guid)
			if not m:
				raise ArgumentException("Invalid GUID:" + guid)
			guid = bytes(reversed(bytes.fromhex(m[3]) + bytes.fromhex(m[2]) + bytes.fromhex(m[1])))
			guid += bytes.fromhex(m[4]) + bytes.fromhex(m[5])
		elif guid is not None:
			assert(type(guid) is bytes)
			assert(len(guid) == 16)
		self.guid:bytes = guid
		return

	def read(self, reader:onestore_reader):
		self.guid:bytes = reader.read_bytes(16)
		return self

	def __str__(self):
		return "{%02X%02X%02X%02X-%02X%02X-%02X%02X-%02X%02X-%02X%02X%02X%02X%02X%02X}" % (
			self.guid[3], self.guid[2], self.guid[1], self.guid[0],
			self.guid[5], self.guid[4], self.guid[7], self.guid[6],
			self.guid[8], self.guid[9], self.guid[10], self.guid[11],
			self.guid[12], self.guid[13], self.guid[14], self.guid[15],
			)
	# Define methods to allow use as a dictionary key
	def __hash__(self) -> int:
		return self.guid.__hash__()

	def __repr__(self):
		return self.__str__()

	def __eq__(self, value: object) -> bool:
		return self.guid == value.guid

	def _xor_guid(self, other):
		return bytes(self.guid[i] ^ other.guid[i] for i in range(16))

	def __xor__(self, other):
		return GUID(self._xor_guid(other))

class ExGUID(GUID):
	def __init__(self, guid:bytes=None, n:int=None):
		super().__init__(guid)
		self.n:int = n
		return

	def read(self, reader:onestore_reader):
		super().read(reader)
		self.n:int = reader.read_uint32()
		return self

	def __str__(self):
		return "{%s,%d}" % (super().__str__(), self.n)

	# Define methods to allow use as a dictionary key
	def __hash__(self) -> int:
		return self.guid.__hash__() ^ self.n.__hash__()

	def __eq__(self, value: object) -> bool:
		return self.guid == value.guid and self.n == value.n

	def __xor__(self, other):
		return ExGUID(self._xor_guid(other), self.n ^ other.n)

NULL_GUID = GUID(b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
NULL_ExGUID = ExGUID(b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0', 0)

def UnpackFloat32(data:bytes):
	assert(len(data) == 4)
	import struct
	f, = struct.unpack("<f", data)
	return f
