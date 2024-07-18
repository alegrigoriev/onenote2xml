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

from ..base_types import *
from .property import PropertyFactory

class PropertySet:
	'''
	cProperties (2 bytes): An unsigned integer that specifies the number of properties in this PropertySet structure.

	rgPrids (variable): An array of PropertyID structures (section 2.6.6).
	The number of elements in the array is equal to the value of the cProperties field.

	rgData (variable): A stream of bytes that specifies the data for each property specified by a rgPrids array.
	The total size, in bytes, of the rgData field is the sum of the sizes specified by the PropertyID.type field for each property in a rgPrids array.
	The total size of rgData MUST be zero if no property in a rgPrids array specifies that it contains data in the rgData field.
	'''

	def __init__(self, jcid:JCID, raw_data:bytes=None):
		self.properties = {}
		self.jcid = jcid
		self.oid = None
		self.raw_data = raw_data  # for read-only objects only, to verify they're immutable
		return

	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		cProperties = reader.read_uint16()
		prop_ids_reader = reader.extract(4*cProperties)
		for _ in range(cProperties):
			prop_id = prop_ids_reader.read_uint32()
			_property = PropertyFactory(prop_id)
			_property.read(reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs)
			self.properties[_property.key] = _property
			continue
		return

	def Properties(self):
		return self.properties.values()

	def dump(self, fd, verbose=None):
		if self.oid is not None:
			print("OID: %s" % (self.oid,), file=fd)

		jcid_type = getattr(verbose, 'pretty_jcid_type', None)
		jcid = self.jcid.jcid
		if jcid_type is not None:
			try:
				jcid_str = jcid_type(self.jcid.jcid).name
			except ValueError:
				jcid_str = "%06X" % (jcid,)
		else:
			jcid_str = "%06X" % (jcid,)
		print("JCID: %s" % (jcid_str,), file=fd)

		for _property in self.Properties():
			_property.dump(fd, verbose)
		return

class ObjectSpaceObjectStreamHeader:

	def __init__(self, reader):
		'''
		The ObjectSpaceObjectStreamHeader structure specifies the number of objects (see section 2.1.5)
		in a stream and whether there are more streams following the stream that contains this ObjectSpaceObjectStreamHeader structure.

		Count (24 bits): An unsigned integer that specifies the number of CompactID structures (section 2.2.2)
		in the stream that contains this ObjectSpaceObjectStreamHeader structure.
		Reserved (6 bits): MUST be zero, and MUST be ignored.
		A - ExtendedStreamsPresent (1 bit): A bit that specifies whether the ObjectSpaceObjectPropSet structure (section 2.6.1)
		contains any additional streams of data following this stream of data.
		B - OsidStreamNotPresent (1 bit): A bit that specifies whether the ObjectSpaceObjectPropSet
		structure does not contain OSIDs or ContextIDs fields.
		'''
		header = reader.read_uint32()
		self.Count = header & 0x00FFFFFF
		self.ExtendedStreamsPresent = 0 != (header & 0x40000000)
		self.OsidStreamNotPresent = 0 != (header & 0x80000000)
		return

class ObjectSpaceObjectStreamOfOIDs:

	def __init__(self, reader, global_id_table):
		'''
		header (4 bytes): An ObjectSpaceObjectStreamHeader structure (section 2.6.5)
		that specifies the number of elements in the body field and whether the
		ObjectSpaceObjectPropSet structure contains an OSIDs field and ContextIDs field.
		If the OSIDs field is present, the value of the header.OsidStreamNotPresent field MUST be false;
		otherwise, it MUST be true. If the ContextIDs field is present the value of the header.
		ExtendedStreamsPresent field MUST be true; otherwise, it MUST be false.

		body (variable): An array of CompactID structures (section 2.2.2) where each element
		in the array specifies the identity of an object.
		The number of elements is equal to the value of the header.Count field.
		'''
		header = ObjectSpaceObjectStreamHeader(reader)
		self.ExtendedStreamsPresent = header.ExtendedStreamsPresent
		self.OsidStreamNotPresent = header.OsidStreamNotPresent

		self.ObjectIDs = []
		for i in range(header.Count):
			compact_id = CompactID(reader)
			if compact_id.IsZero():
				oid = None
			else:
				oid = global_id_table[compact_id]
			self.ObjectIDs.append((compact_id, oid))
		return

	def __iter__(self):
		return iter(self.ObjectIDs)

class ObjectSpaceObjectStreamOfOSIDs:

	def __init__(self, reader, global_id_table):
		'''
		header (4 bytes): An ObjectSpaceObjectStreamHeader structure (section 2.6.5)
		that specifies the number of elements in the body field and whether the
		ObjectSpaceObjectPropSet structure contains an OSIDs field and ContextIDs field.
		If the OSIDs field is present, the value of the header.OsidStreamNotPresent field MUST be false;
		otherwise, it MUST be true. If the ContextIDs field is present the value of the header.
		ExtendedStreamsPresent field MUST be true; otherwise, it MUST be false.

		body (variable): An array of CompactID structures (section 2.2.2) where each element
		in the array specifies the identity of an object.
		The number of elements is equal to the value of the header.Count field.
		'''
		header = ObjectSpaceObjectStreamHeader(reader)
		self.ExtendedStreamsPresent = header.ExtendedStreamsPresent
		self.OsidStreamNotPresent = header.OsidStreamNotPresent

		self.ObjectSpaceIDs = []
		for i in range(header.Count):
			compact_id = CompactID(reader)
			osid = global_id_table[compact_id]
			self.ObjectSpaceIDs.append((compact_id, osid))
		return

	def __iter__(self):
		return iter(self.ObjectSpaceIDs)

class ObjectSpaceObjectStreamOfContextIDs:
	'''
	header (4 bytes): An ObjectSpaceObjectStreamHeader structure (section 2.6.5)
	that specifies the number of elements in the body field and whether the
	ObjectSpaceObjectPropSet structure contains an OSIDs field and ContextIDs field.
	If the OSIDs field is present, the value of the header.OsidStreamNotPresent field MUST be false;
	otherwise, it MUST be true. If the ContextIDs field is present the value of the header.
	ExtendedStreamsPresent field MUST be true; otherwise, it MUST be false.

	body (variable): An array of CompactID structures (section 2.2.2) where each element
	in the array specifies the identity of an object.
	The number of elements is equal to the value of the header.Count field.
	'''

	def __init__(self, reader, global_id_table):

		header = ObjectSpaceObjectStreamHeader(reader)
		self.ExtendedStreamsPresent = header.ExtendedStreamsPresent
		self.OsidStreamNotPresent = header.OsidStreamNotPresent

		self.ContextIDs = []
		for i in range(header.Count):
			compact_id = CompactID(reader)
			ctxid = global_id_table[compact_id]
			self.ContextIDs.append((compact_id, ctxid))
		return

	def __iter__(self):
		return iter(self.ContextIDs)

from .onestore import OneStoreFile
def ObjectSpaceObjectPropSet(onestore:OneStoreFile, ref, jcid, global_id_table):
	''' OIDs (variable): An ObjectSpaceObjectStreamOfOIDs (section 2.6.2)
	that specifies the count and list of objects that are referenced by this ObjectSpaceObjectPropSet.
	The count of referenced objects is calculated as the number of properties specified by the body field,
	with PropertyID equal to 0x8 plus the number of referenced objects specified by properties with PropertyID equal to 0x9, 0x10, and 0x11.
	This count MUST be equal to the value of OIDs.header.Count field.
	Properties that reference other objects MUST be matched with the CompactID structures (section 2.2.2) from OIDs.
	body field in the same order as the properties are listed in the body.rgPrids field.
	'''

	reader = onestore.get_chunk(ref)
	if jcid.IsReadOnly():
		raw_data = reader.read_bytes_at(0, ref.cb)
	else:
		raw_data = None

	property_set = PropertySet(jcid, raw_data)

	OIDs = ObjectSpaceObjectStreamOfOIDs(reader, global_id_table)
	iterObjectIDs = iter(OIDs)
	if not OIDs.OsidStreamNotPresent:
		OSIDs = ObjectSpaceObjectStreamOfOSIDs(reader, global_id_table)
		iterObjectSpaceIDs = iter(OSIDs)
		if OSIDs.ExtendedStreamsPresent:
			ContextIDs = ObjectSpaceObjectStreamOfContextIDs(reader, global_id_table)
			iterContextIDs = iter(ContextIDs)
		else:
			iterContextIDs = None
	else:
		iterObjectSpaceIDs = None
		iterContextIDs = None

	property_set.read(reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs)

	return property_set
