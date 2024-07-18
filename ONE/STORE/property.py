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

from ..exception import UnrecognizedPropertyDataTypeException
from ..property_id import PropertyTypeID

class Property:

	def __init__(self, prop_id, data=None, value=None, str_value=None, display_value=None):
		self.data_type = (prop_id & 0x7C000000) >> 26
		self.property_id = prop_id & 0x7FFFFFFF
		self.key = self.property_id
		self.key_string = "Property_%X" % (self.property_id,)	# String to use as a key in the prop dictionary
		self.data = data	# raw data
		self.value = value	# usable value or array of values from raw data
		self.str_value = str_value or str(value)	# value or array of values in string form
		self.display_value = display_value or str_value	# Single string to display the value
		return

	def read(self, reader, *args):
		return self

	def get_property_name(self, verbose):
		prop_type = getattr(verbose, 'pretty_prop_type', None)
		if prop_type is not None:
			try:
				return prop_type(self.property_id).name
			except ValueError:
				pass
		return self.key_string

	def get_pretty_print_string(self, verbose):
		if not getattr(verbose, 'pretty_print_properties', False):
			return self.display_value

		from ..property_pretty_print import PropertyPrettyPrintString
		pretty_str = PropertyPrettyPrintString(self, verbose)
		if pretty_str is not None:
			return pretty_str
		return self.display_value

	def dump(self, fd, verbose=None):
		print("%s=%s" % (self.get_property_name(verbose),
					self.get_pretty_print_string(verbose)), file=fd)

		return

class NoDataProperty(Property): ...

class BoolProperty(Property):
	def __init__(self, prop_id):
		super().__init__(prop_id)
		self.value = 0 != (prop_id & 0x80000000)
		self.str_value = str(self.value)
		self.display_value = self.str_value
		return

class Property1To8bytesData(Property):
	def read(self, reader, *args):
		data_type = self.data_type

		if data_type == PropertyTypeID.FourBytesOfData:
			self.data = reader.read_bytes(4)
		elif data_type == PropertyTypeID.OneByteOfData:
			self.data = reader.read_bytes(1)
		elif data_type == PropertyTypeID.TwoBytesOfData:
			self.data = reader.read_bytes(2)
		elif data_type == PropertyTypeID.EightBytesOfData:
			self.data = reader.read_bytes(8)
		self.value = int.from_bytes(self.data, byteorder="little", signed=False)
		self.str_value = str(self.value)
		self.display_value = self.str_value
		return self

class FourBytesOfLengthFollowedByDataProperty(Property):
	def read(self, reader, *args):
		length = reader.read_uint32()
		self.data = reader.read_bytes(length)
		self.str_value = self.data.hex()
		self.display_value = "%d bytes: %s" % (len(self.data), self.str_value)
		return self

class ObjectIDProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		# To simplify usage of single/array variants, we always put it in an array
		coid, oid = next(iterObjectIDs)
		self.data = [coid]
		self.value = [oid]
		self.str_value = [str(oid)]
		return self

	def dump(self, fd, verbose=None):
		print("%s=OID: %s" % (self.get_property_name(verbose), self.str_value[0]), file=fd)
		return

class ArrayOfObjectIDsProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		count = reader.read_uint32()
		self.data = []
		self.value = []
		self.str_value = []
		for _ in range(count):
			coid, oid = next(iterObjectIDs)
			self.data.append(coid)
			self.value.append(oid)
			self.str_value.append(str(oid))
		return self

	def dump(self, fd, verbose=None):
		print("%s: Array of %d OIDs:" % (self.get_property_name(verbose), len(self.value)), file=fd)
		for oid_str in self.str_value:
			print("   ", oid_str, file=fd)
		return

class ObjectSpaceIDProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		# To simplify usage of single/array variants, we always put it in an array
		coid, osid = next(iterObjectSpaceIDs)
		self.data = [coid]
		self.value = [osid]
		self.str_value = [str(osid)]
		return self

	def dump(self, fd, verbose=None):
		print("%s=OSID: %s" % (self.get_property_name(verbose), self.str_value[0]), file=fd)
		return

class ArrayOfObjectSpaceIDsProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		count = reader.read_uint32()
		self.data = []
		self.value = []
		self.str_value = []
		for _ in range(count):
			coid, osid = next(iterObjectSpaceIDs)
			self.data.append(coid)
			self.value.append(osid)
			self.str_value.append(str(osid))
		return self

	def dump(self, fd, verbose=None):
		print("%s: Array of %d OSIDs:" % (self.get_property_name(verbose), len(self.data)), file=fd)
		for osid_str in self.str_value:
			print("   ", osid_str, file=fd)
		return

class ContextIDProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		# To simplify usage of single/array variants, we always put it in an array
		coid, ctxid = next(iterContextIDs)
		self.data = [coid]
		self.value = [ctxid]
		self.str_value = [str(ctxid)]
		return self

	def dump(self, fd, verbose=None):
		print("%s=CTXID: %s" % (self.get_property_name(verbose), self.str_value[0]), file=fd)
		return

class ArrayOfContextIDsProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		count = reader.read_uint32()
		self.data = []
		self.value = []
		self.str_value = []
		for _ in range(count):
			coid, ctxid = next(iterContextIDs)
			self.data.append(coid)
			self.value.append(ctxid)
			self.str_value.append(str(ctxid))
		return self

	def dump(self, fd, verbose=None):
		print("%s: Array of %d CTXIDs:" % (self.get_property_name(verbose), len(self.data)), file=fd)
		for ctxid_str in self.str_value:
			print("   ", ctxid_str, file=fd)
		return

class PropertySetProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		from .property_set import PropertySet
		from ..base_types import JCID
		# To simplify usage of single/array variants, we always put it in an array
		property_set = PropertySet(JCID(0x20000))
		property_set.read(reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs)
		self.value = [property_set]
		return self

	def dump(self, fd, verbose=None):
		print("%s: PropertySet" % (self.get_property_name(verbose),), file=fd)
		self.value[0].dump(fd, verbose)
		return

class ArrayOfPropertyValuesProperty(Property):
	def read(self, reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs):
		from .property_set import PropertySet
		from ..base_types import JCID
		self.value = []
		count = reader.read_uint32()
		if count == 0:
			return self

		data_type = reader.read_uint32()
		assert(((data_type & 0x7C000000) >> 26) == PropertyTypeID.PropertySet)
		for _ in range(count):
			property_set = PropertySet(JCID(0x20000))
			property_set.read(reader, iterObjectIDs, iterObjectSpaceIDs, iterContextIDs)
			self.value.append(property_set)
		return self

	def dump(self, fd, verbose=None):
		print("%s: ArrayOfPropertyValues" % (self.get_property_name(verbose),), file=fd)
		for propset in self.value:
			propset.dump(fd, verbose)
		return

DataTypeFactoryDict = {
	int(PropertyTypeID.NoData) : NoDataProperty, # 0x01
	int(PropertyTypeID.Bool) : BoolProperty, # 0x02
	int(PropertyTypeID.OneByteOfData) : Property1To8bytesData, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : Property1To8bytesData, # 0x04
	int(PropertyTypeID.FourBytesOfData) : Property1To8bytesData, # 0x05
	int(PropertyTypeID.EightBytesOfData) : Property1To8bytesData, # 0x06
	int(PropertyTypeID.FourBytesOfLengthFollowedByData) : FourBytesOfLengthFollowedByDataProperty, # 0x07
	int(PropertyTypeID.ObjectID) : ObjectIDProperty, # 0x08
	int(PropertyTypeID.ArrayOfObjectIDs) : ArrayOfObjectIDsProperty, # 0x09
	int(PropertyTypeID.ObjectSpaceID) : ObjectSpaceIDProperty, # 0x0A
	int(PropertyTypeID.ArrayOfObjectSpaceIDs) : ArrayOfObjectSpaceIDsProperty, # 0x0B
	int(PropertyTypeID.ContextID) : ContextIDProperty, # 0x0C
	int(PropertyTypeID.ArrayOfContextIDs) : ArrayOfContextIDsProperty, # 0x0D
	int(PropertyTypeID.ArrayOfPropertyValues) : ArrayOfPropertyValuesProperty, # 0x10
	int(PropertyTypeID.PropertySet) : PropertySetProperty, # 0x11
	}

def PropertyFactory(property_header):

	data_type = (property_header & 0x7C000000) >> 26
	property_class = DataTypeFactoryDict.get(data_type, None)
	if property_class is None:
		raise UnrecognizedPropertyDataTypeException("Unrecognized type %02X in property %X"
											  % (data_type, property_header & 0x7FFFFFFF))
	return property_class(property_header)
