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
from ..STORE.property import PropertyTypeID
from ..NOTE.property_object_factory import PropertyID, Property
from xml.etree import ElementTree as ET

class xmlPropertyElementBase:
	# We'll make this the top __init__ method by using method dictionary
	def init(self, _property:Property, **kwargs):
		# Since we're using this class as a template,
		# the actual base class is not accessible to the default super() form
		super(type(self), self).__init__(_property, **kwargs)
		return

	def get_xml_text(self):
		return self.str_value

	def MakeXmlElement(self, revision_ctx):
		text = self.get_xml_text()

		element = ET.Element(self.key_string)
		if text is not None and type(text) is not str:
			text = str(text)
		element.text = text

		return element

	@classmethod
	def MakeClass(cls, base_class):
		new_class = type('xml' + base_class.__name__, (base_class, cls), {})
		new_class.__init__ = cls.init
		return new_class

class xmlBytesProperty(xmlPropertyElementBase): ...

class xmlBoolProperty(xmlPropertyElementBase): ...

class xmlGuidProperty(xmlPropertyElementBase): ...

class xmlIntProperty(xmlPropertyElementBase): ...

class xmlPrettyProperty(xmlPropertyElementBase):

	def get_xml_text(self):
		return self.display_value

class xmlArrayOfObjectIdProperty(xmlPropertyElementBase):

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self.key_string)

		# self.value is the array of child objects constructed by make_object
		for obj in self.value:
			if obj is not None:
				subelement = obj.MakeXmlElement(revision_ctx)
				if subelement is not None:
					element.append(subelement)
			continue

		return element

class xmlObjectIdProperty(xmlArrayOfObjectIdProperty): ...

class xmlArrayOfObjectSpaceIdProperty(xmlPropertyElementBase):

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self.key_string)

		# self.value is the array of child objects constructed by make_object
		for gosid in self.str_value:
			ET.SubElement(element, 'ObjectSpace', { "OSID" : gosid, })
		return element

class xmlObjectSpaceIdProperty(xmlArrayOfObjectSpaceIdProperty): ...

class xmlArrayOfContextIdProperty(xmlPropertyElementBase):

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self.key_string)

		for context_id in self.str_value:
			ET.SubElement(element, 'ContextId', { "CTXID" : context_id, })
		return element

class xmlContextIdProperty(xmlArrayOfContextIdProperty): ...

class xmlArrayOfPropertyValuesProperty(xmlObjectIdProperty):

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self.key_string)

		# self.value is the array of child objects constructed by make_object
		for obj in self.value:
			element.append(obj.MakeXmlElement(revision_ctx))

		return element

class xmlPropertyValueProperty(xmlArrayOfPropertyValuesProperty):  ...

# Make derived classes from property_factory and property_set_factory classes

OneNootebookPropertyElementBuilderTemplates = {
	int(PropertyID.NotebookManagementEntityGuid) : xmlGuidProperty,  # 0x1C001C30.
	0x1C0035CD : xmlGuidProperty,  # 0x1C0035CD
	0x1C005010 : xmlGuidProperty,  # 0x1C005010

	int(PropertyID.RgOutlineIndentDistance) : xmlPrettyProperty,  # 0x18001C65
	int(PropertyID.TextRunIndex) : xmlPrettyProperty,  # 0x18001C65
	int(PropertyID.TableColumnWidths) : xmlPrettyProperty,  # 0x18001C65
	int(PropertyID.TableColumnsLocked) : xmlPrettyProperty,  # 0x18001C65
}

DataTypeObjectXmlFactoryDict = {
	int(PropertyTypeID.NoData) : xmlPropertyElementBase, # 0x01
	int(PropertyTypeID.Bool) : xmlBoolProperty, # 0x02
	int(PropertyTypeID.OneByteOfData) : xmlIntProperty, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : xmlIntProperty, # 0x04
	int(PropertyTypeID.FourBytesOfData) : xmlIntProperty, # 0x05
	int(PropertyTypeID.EightBytesOfData) : xmlIntProperty, # 0x06
	int(PropertyTypeID.FourBytesOfLengthFollowedByData) : xmlPropertyElementBase, # 0x07
	int(PropertyTypeID.ObjectID) : xmlObjectIdProperty, # 0x08
	int(PropertyTypeID.ArrayOfObjectIDs) : xmlArrayOfObjectIdProperty, # 0x09
	int(PropertyTypeID.ObjectSpaceID) : xmlObjectSpaceIdProperty, # 0x0A
	int(PropertyTypeID.ArrayOfObjectSpaceIDs) : xmlArrayOfObjectSpaceIdProperty, # 0x0B
	int(PropertyTypeID.ContextID) : xmlContextIdProperty, # 0x0C
	int(PropertyTypeID.ArrayOfContextIDs) : xmlArrayOfContextIdProperty, # 0x0D
	int(PropertyTypeID.ArrayOfPropertyValues) : xmlArrayOfPropertyValuesProperty, # 0x10
	int(PropertyTypeID.PropertySet) : xmlPropertyValueProperty, # 0x11
	}

class XmlPropertyElementObjectFactory:
	def __init__(self, property_factory, template_dict:dict={}, default_class=xmlPropertyElementBase):
		self.property_factory = property_factory
		self.xml_property_template_dict = template_dict
		self.default_class = default_class
		self.xml_property_dict = { }  # Initially empty
		self.xml_class_dict = { }  # key: (id(base_class), id(template_class))
		return

	def make_property_xml_element_class(self, property_obj:Property):
		'''
		This creates a derived class to construct XML element for a property class
		'''
		# TODO: find if the class for same base class and template class already created
		base_class = self.property_factory.get_property_class(property_obj)
		base_xml_class = self.xml_property_template_dict.get(property_obj.property_id, None)
		if base_xml_class is None:
			# Get by property type
			base_xml_class = DataTypeObjectXmlFactoryDict.get(property_obj.data_type, self.default_class)

		key = (id(base_class), id(base_xml_class))
		new_class = self.xml_class_dict.get(key, None)
		if new_class is not None:
			return new_class

		new_class = base_xml_class.MakeClass(base_class)
		self.xml_class_dict[key] = new_class
		return new_class

	def get_property_class(self, property_obj:Property):
		property_class = self.xml_property_dict.get(property_obj.property_id, None)

		if property_class is None:
			# Build the class instance
			property_class = self.make_property_xml_element_class(property_obj)
			self.xml_property_dict[property_obj.property_id] = property_class

		return property_class

	def __call__(self, property_obj:Property, **kwargs):
		return self.get_property_class(property_obj)(property_obj, **kwargs)

from ..NOTE.property_object_factory import OneNotebookPropertyFactory
OneNotebookPropertyElementFactory = XmlPropertyElementObjectFactory(OneNotebookPropertyFactory,
																	OneNootebookPropertyElementBuilderTemplates)

OneToc2PropertyElementBuilderTemplates = {
}

from ..NOTE.property_object_factory import OneToc2PropertyFactory
OneToc2PropertyElementFactory = XmlPropertyElementObjectFactory(OneToc2PropertyFactory,
																OneToc2PropertyElementBuilderTemplates)
