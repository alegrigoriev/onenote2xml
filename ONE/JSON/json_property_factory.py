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
from ..base_types import *
from ..property_id import *
from ..STORE.property import Property

class jsonPropertyBase:

	# We'll make this the top __init__ method by using method dictionary
	def init(self, _property:Property, **kwargs):
		# Since we're using this class as a template,
		# the actual base class is not accessible to the default super() form
		super(type(self), self).__init__(_property, **kwargs)
		return

	def MakeJsonValue(self, revision_ctx):
		return self.value

	@classmethod
	def MakeClass(cls, base_class):
		new_class = type('json' + base_class.__name__, (base_class, cls), {})
		new_class.__init__ = cls.init
		return new_class

class jsonPropertyNone(jsonPropertyBase):

	def MakeJsonValue(self, revision_ctx):
		return None

class jsonBoolProperty(jsonPropertyBase): ...

class jsonBytesProperty(jsonPropertyBase): ...

class jsonStringProperty(jsonPropertyBase):
	def MakeJsonValue(self, revision_ctx):
		return self.str_value

class jsonGuidProperty(jsonStringProperty): ...

class jsonIntProperty(jsonPropertyBase):
	def MakeJsonValue(self, revision_ctx):
		return self.int_value

class jsonArrayOfObjectIdProperty(jsonPropertyBase):

	def MakeJsonValue(self, revision_ctx):
		array = []

		# self.value is the array of child objects constructed by make_object
		for obj in self.value:
			if obj is None:
				array.append(None)
				continue
			if obj.min_verbosity > revision_ctx.verbosity:
				continue

			value = obj.MakeJsonNode(revision_ctx)
			if value is not NotImplemented:
				array.append(value)
			continue

		return array

class jsonObjectIdProperty(jsonArrayOfObjectIdProperty):
	def MakeJsonValue(self, revision_ctx):
		array = super().MakeJsonValue(revision_ctx)
		if array:
			return array[0]
		return None

class jsonArrayOfObjectSpaceIdProperty(jsonPropertyBase):

	def MakeJsonValue(self, revision_ctx):
		array = []

		for osid in self.str_value:
			array.append({ "PageID" : osid, })

		return array

class jsonObjectSpaceIdProperty(jsonArrayOfObjectSpaceIdProperty):
	def MakeJsonValue(self, revision_ctx):
		array = super().MakeJsonValue(revision_ctx)
		if array:
			return array[0]
		return None

class jsonArrayOfContextIdProperty(jsonPropertyBase):

	def MakeJsonValue(self, revision_ctx):
		array = []

		if revision_ctx.verbosity == 0:
			for rid in self.rids:
				array.append(str(rid))
				continue
			return array

		for context_id in self.str_value:
			array.append({ "CTXID" : context_id, })
		return array

class jsonContextIdProperty(jsonArrayOfContextIdProperty):
	def MakeJsonValue(self, revision_ctx):
		array = super().MakeJsonValue(revision_ctx)
		if array:
			return array[0]
		return None

class jsonArrayOfPropertyValuesProperty(jsonObjectIdProperty):

	def MakeJsonValue(self, revision_ctx):
		array = []

		# self.value is the array of child objects constructed by make_object
		for obj in self.value:
			array.append(obj.MakeJsonValue(revision_ctx))
		return array

class jsonPropertyValueProperty(jsonArrayOfPropertyValuesProperty):
	def MakeJsonValue(self, revision_ctx):
		array = super().MakeJsonValue(revision_ctx)
		if array:
			return array[0]
		return None

class jsonNoteOnlineParagraphStyleProperty(jsonObjectIdProperty):

	def make_object(self, property_set_obj, revision_ctx):
		prev_property_set_factory = revision_ctx.property_set_factory

		from .json_property_set_factory import NoteOnlineParagraphStyleJsonFactory
		revision_ctx.property_set_factory = NoteOnlineParagraphStyleJsonFactory

		super(type(self), self).make_object(property_set_obj, revision_ctx)
		revision_ctx.property_set_factory = prev_property_set_factory
		return

	@classmethod
	def MakeClass(cls, base_class):
		new_class = jsonObjectIdProperty.MakeClass(base_class)
		new_class.make_object = cls.make_object
		return new_class

class jsonColorrefProperty(jsonStringProperty): ...

class jsonColorProperty(jsonColorrefProperty): ...

class jsonLayoutAlignmentProperty(jsonPropertyBase):

	def MakeJsonValue(self, revision_ctx):
		alignment = self.value
		if alignment is None:
			return None
		attrs = {}
		if alignment.HorizontalAlignment == 1:
			hor_align = "Left"
		elif alignment.HorizontalAlignment == 2:
			hor_align = "Center"
		elif alignment.HorizontalAlignment == 3:
			hor_align = "Right"
		elif alignment.HorizontalAlignment == 4:
			hor_align = "StartOfLine"
		elif alignment.HorizontalAlignment == 5:
			hor_align = "EndOfLine"
		else:
			hor_align = str(alignment.HorizontalAlignment)
		attrs['HorizontalAlignment'] = hor_align
		attrs['fHorizMargin'] = "StartOfLine" if alignment.fHorizMargin else "EndOfLine"
		attrs['VerticalAlignment'] = "Top" if alignment.VerticalAlignment else "Bottom"
		attrs['fVertMargin'] = "Top" if alignment.fVertMargin else "Bottom"
		return attrs

# Make derived classes from property_factory and property_set_factory classes

OneNootebookPropertyJsonBuilderTemplates = {
	int(PropertyID.NotebookManagementEntityGuid) : jsonGuidProperty,  # 0x1C001C30.
	0x1C0035CD : jsonGuidProperty,  # 0x1C0035CD
	0x1C005010 : jsonGuidProperty,  # 0x1C005010

	int(PropertyID.FontColor) : jsonColorrefProperty,
	int(PropertyID.Highlight) : jsonColorrefProperty,
	int(PropertyID.CellShadingColor) : jsonColorrefProperty,
	int(PropertyID.NoteTagHighlightColor) : jsonColorrefProperty,
	int(PropertyID.NoteTagTextColor) : jsonColorrefProperty,
	int(PropertyID.CellShadingColor) : jsonColorrefProperty,
	int(PropertyID.NotebookColor) : jsonColorProperty,
	int(PropertyID.LayoutAlignmentInParent) : jsonLayoutAlignmentProperty,
	int(PropertyID.LayoutAlignmentSelf) : jsonLayoutAlignmentProperty,
	int(PropertyID.NoteOnlineParagraphStyle): jsonNoteOnlineParagraphStyleProperty,
}

DataTypeObjectJsonFactoryDict = {
	int(PropertyTypeID.NoData) : jsonPropertyNone, # 0x01
	int(PropertyTypeID.Bool) : jsonBoolProperty, # 0x02
	int(PropertyTypeID.OneByteOfData) : jsonIntProperty, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : jsonIntProperty, # 0x04
	int(PropertyTypeID.FourBytesOfData) : jsonIntProperty, # 0x05
	int(PropertyTypeID.EightBytesOfData) : jsonIntProperty, # 0x06
	int(PropertyTypeID.FourBytesOfLengthFollowedByData) : jsonBytesProperty, # 0x07
	int(PropertyTypeID.ObjectID) : jsonObjectIdProperty, # 0x08
	int(PropertyTypeID.ArrayOfObjectIDs) : jsonArrayOfObjectIdProperty, # 0x09
	int(PropertyTypeID.ObjectSpaceID) : jsonObjectSpaceIdProperty, # 0x0A
	int(PropertyTypeID.ArrayOfObjectSpaceIDs) : jsonArrayOfObjectSpaceIdProperty, # 0x0B
	int(PropertyTypeID.ContextID) : jsonContextIdProperty, # 0x0C
	int(PropertyTypeID.ArrayOfContextIDs) : jsonArrayOfContextIdProperty, # 0x0D
	int(PropertyTypeID.ArrayOfPropertyValues) : jsonArrayOfPropertyValuesProperty, # 0x10
	int(PropertyTypeID.PropertySet) : jsonPropertyValueProperty, # 0x11
	}

class JsonPropertyObjectFactory:
	def __init__(self, property_factory, template_dict:dict={}, default_class=jsonPropertyBase):
		self.property_factory = property_factory
		self.json_property_template_dict = template_dict
		self.default_class = default_class
		self.json_property_dict = { }  # Initially empty
		self.json_class_dict = { }  # key: (id(base_class), id(template_class))
		return

	def make_property_doc_class(self, property_obj:Property):
		'''
		This creates a derived class to construct XML element for a property class
		'''
		# TODO: find if the class for same base class and template class already created
		base_class = self.property_factory.get_property_class(property_obj)
		base_json_class = self.json_property_template_dict.get(property_obj.property_id, None)
		if base_json_class is None:
			# Get by property type
			base_json_class = DataTypeObjectJsonFactoryDict.get(property_obj.data_type, self.default_class)

		key = (id(base_class), id(base_json_class))
		new_class = self.json_class_dict.get(key, None)
		if new_class is not None:
			return new_class

		new_class = base_json_class.MakeClass(base_class)
		self.json_class_dict[key] = new_class
		return new_class

	def get_property_class(self, property_obj:Property):
		property_class = self.json_property_dict.get(property_obj.property_id, None)

		if property_class is None:
			# Build the class instance
			property_class = self.make_property_doc_class(property_obj)
			self.json_property_dict[property_obj.property_id] = property_class

		return property_class

	def __call__(self, property_obj:Property, **kwargs):
		return self.get_property_class(property_obj)(property_obj, **kwargs)

from ..NOTE.property_object_factory import OneNotebookPropertyFactory
OneNotebookJsonPropertyFactory = JsonPropertyObjectFactory(OneNotebookPropertyFactory,
																	OneNootebookPropertyJsonBuilderTemplates)

OneToc2PropertyJsonBuilderTemplates = {
	int(PropertyID.FileIdentityGuid) : jsonGuidProperty,
	int(PropertyID.NotebookColor) : jsonColorProperty,
}

from ..NOTE.property_object_factory import OneToc2PropertyFactory
OneToc2JsonPropertyFactory = JsonPropertyObjectFactory(OneToc2PropertyFactory,
																OneToc2PropertyJsonBuilderTemplates)

