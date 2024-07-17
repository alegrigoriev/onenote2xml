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

from types import SimpleNamespace
from ..property_id import *
from ..STORE.property import Property
from ..base_types import *
from ..property_pretty_print import *

class PropertyObject:
	PROPERTY_ID_CLASS = PropertyID

	def __init__(self, _property:Property, key = None, key_string=None, data=None, value=None, str_value=None, display_value=None):
		self.data_type:int = _property.data_type
		self.property_id:int = _property.property_id
		if key is None:
			property_id_class = type(self).PROPERTY_ID_CLASS
			if property_id_class is not NotImplemented:
				try:
					property_id = property_id_class(_property.property_id)
					key = property_id.name
				except ValueError:
					pass
		if key is None:
			key = _property.property_id
			if key_string is None:
				key_string = "Property_%X" % (key,)
		elif key_string is None:
			key_string = key
		self.key:str|int = key
		self.key_string:str = key_string

		if data is None:
			data = _property.data
		self.data:bytes = data	# raw data

		if value is None:
			value = _property.value
		self.value = value	# usable value or array of values from raw data

		if str_value is None:
			str_value = _property.str_value
		self.str_value:str|list[str] = str_value	# value or array of values in string form

		if display_value is None:
			display_value = _property.display_value
		self.display_value = display_value	# Single string to display the value

		return

	def make_object(self, property_set_obj, revision_ctx):
		'''
		property_set_obj is the parent property set
		'''
		return

	def get_object_value(self):
		# Used in property set __getattr__ method
		return self.value

	def __iter__(self):
		# Iterate over all attributes recursively
		yield (), self
		# By default there's no sub-objects
		return

class NoDataPropertyObject(PropertyObject): ...

class BoolPropertyObject(PropertyObject): ...

class PropertyObject1To8bytesData(PropertyObject):

	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.int_value = _property.value
		return

class IntPropertyObject(PropertyObject1To8bytesData): ...

class FourBytesOfLengthFollowedByDataPropertyObject(PropertyObject): ...

class ArrayOfObjectIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.oids = self.value
		return

	def make_object(self, property_set_obj, revision_ctx):
		self.value = []
		for oid in self.oids:
			# oid can be None
			obj = revision_ctx.GetObjectReference(oid)
			self.value.append(obj)
			# GetObjectReference returns None for None oid
		return

	def __iter__(self):
		# Iterate over all objects recursively
		for obj in self.value:
			if obj is not None:
				yield from obj
		return

class ObjectIDPropertyObject(ArrayOfObjectIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			return self.value[0]
		else:
			return None

class ArrayOfObjectSpaceIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.osids = self.value
		return

class ObjectSpaceIDPropertyObject(ArrayOfObjectSpaceIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

class ArrayOfContextIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.ctxids = self.value
		return

class ContextIDPropertyObject(ArrayOfContextIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

class ArrayOfPropertyValuesPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.propsets = self.value
		return

	def make_object(self, property_set_obj, revision_ctx):
		self.value = []
		for propset in self.propsets:
			self.value.append(revision_ctx.MakeObject(propset, None))
		return

class PropertySetPropertyObject(ArrayOfPropertyValuesPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

DataTypeObjectFactoryDict = {
	int(PropertyTypeID.NoData) : NoDataPropertyObject, # 0x01
	int(PropertyTypeID.Bool) : BoolPropertyObject, # 0x02
	int(PropertyTypeID.OneByteOfData) : PropertyObject1To8bytesData, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : PropertyObject1To8bytesData, # 0x04
	int(PropertyTypeID.FourBytesOfData) : PropertyObject1To8bytesData, # 0x05
	int(PropertyTypeID.EightBytesOfData) : PropertyObject1To8bytesData, # 0x06
	int(PropertyTypeID.FourBytesOfLengthFollowedByData) : FourBytesOfLengthFollowedByDataPropertyObject, # 0x07
	int(PropertyTypeID.ObjectID) : ObjectIDPropertyObject, # 0x08
	int(PropertyTypeID.ArrayOfObjectIDs) : ArrayOfObjectIDsPropertyObject, # 0x09
	int(PropertyTypeID.ObjectSpaceID) : ObjectSpaceIDPropertyObject, # 0x0A
	int(PropertyTypeID.ArrayOfObjectSpaceIDs) : ArrayOfObjectSpaceIDsPropertyObject, # 0x0B
	int(PropertyTypeID.ContextID) : ContextIDPropertyObject, # 0x0C
	int(PropertyTypeID.ArrayOfContextIDs) : ArrayOfContextIDsPropertyObject, # 0x0D
	int(PropertyTypeID.ArrayOfPropertyValues) : ArrayOfPropertyValuesPropertyObject, # 0x10
	int(PropertyTypeID.PropertySet) : PropertySetPropertyObject, # 0x11
	}

class PropertyObjectFactory:
	def __init__(self, property_dict:dict={}, property_id_class=PropertyID, default_class=PropertyObject):
		self.property_dict = property_dict
		self.property_id_class = property_id_class
		self.default_class = default_class
		return

	def get_property_id_class(self):
		return self.property_id_class

	def get_property_class(self, property_obj:Property):
		property_class = self.property_dict.get(property_obj.property_id, None)

		if property_class is None:
			property_class = DataTypeObjectFactoryDict.get(property_obj.data_type, self.default_class)
		return property_class

	def __call__(self, property_obj:Property, **kwargs):
		return self.get_property_class(property_obj)(property_obj, **kwargs)

OneNotebookPropertyFactory = PropertyObjectFactory()
