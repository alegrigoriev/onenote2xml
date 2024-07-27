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

from enum import IntEnum
from ..base_types import *
from ..property_set_jcid import *
from xml.etree import ElementTree as ET

class PropertySetXmlElementBase:
	READONLY_SPACE = NotImplemented

	# We'll make this the top __init__ method by using method dictionary
	def init(self, jcid, oid):
		# Since we're using this class as a template,
		# the actual base class is not accessible to the default super() form
		super(type(self), self).__init__(jcid, oid)
		# TODO: Add initialization here
		return

	def is_read_only(self):
		return self._jcid.IsReadOnly()

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self._jcid_name)

		for prop in self._properties.values():
			prop_element = prop.MakeXmlElement(revision_ctx)
			if prop_element is not None:
				element.append(prop_element)
			continue
		return element

	@classmethod
	def MakeClass(cls, base_class, xml_property_element_factory):
		new_class = type('xml' + base_class.__name__.removeprefix('jcid'), (base_class, cls), {})
		new_class.__init__ = cls.init
		new_class.PROPERTY_FACTORY = xml_property_element_factory
		return new_class

class xmlReadOnlyPersistablePropertyContainerForAuthor(PropertySetXmlElementBase):
	READONLY_SPACE = 'Authors'

class xmlReadOnlyAuthor(xmlReadOnlyPersistablePropertyContainerForAuthor): ...

class xmlNoteTagSharedDefinitionContainer(PropertySetXmlElementBase):
	READONLY_SPACE = 'NoteTags'

class xmlParagraphStyleObject(PropertySetXmlElementBase):
	READONLY_SPACE = 'ParagraphStyles'

from ..NOTE.property_set_object_factory import PropertySetFactory

class XmlPropertySetFactory:
	def __init__(self, property_set_factory:PropertySetFactory,
					xml_property_element_factory,
					xml_property_set_template_dict:dict={}):
		self.xml_property_set_template_dict = xml_property_set_template_dict
		self.property_set_factory = property_set_factory
		self.xml_property_element_factory = xml_property_element_factory
		self.jcid_class = property_set_factory.get_jcid_class()
		self.xml_property_set_dict = { }  # Initially empty
		return

	def get_jcid_class(self):
		return self.jcid_class

	def make_property_set_xml_element_class(self, jcid):
		'''
		This creates a custom class to construct XML element for a property class
		'''
		base_class = self.property_set_factory.get_property_set_class(jcid)
		base_xml_class = self.xml_property_set_template_dict.get(jcid.jcid, PropertySetXmlElementBase)

		return base_xml_class.MakeClass(base_class, self.xml_property_element_factory)

	def get_property_set_class(self, jcid:JCID):
		property_set_class = self.xml_property_set_dict.get(jcid.jcid, None)
		if property_set_class is None:
			# Build the class instance
			property_set_class = self.make_property_set_xml_element_class(jcid)
			self.xml_property_set_dict[jcid.jcid] = property_set_class

		return property_set_class

	def __call__(self, jcid:JCID, oid:ExGUID):
		return self.get_property_set_class(jcid)(jcid, oid)

OneNootebookPropertySetElementBuilderTemplates = {
	PropertySetJCID.jcidReadOnlyPersistablePropertyContainerForAuthor.value :
						xmlReadOnlyPersistablePropertyContainerForAuthor,
	PropertySetJCID.jcidParagraphStyleObject.value: xmlParagraphStyleObject,
	PropertySetJCID.jcidNoteTagSharedDefinitionContainer.value: xmlNoteTagSharedDefinitionContainer,
	PropertySetJCID.jcidReadOnlyAuthor.value: xmlReadOnlyAuthor,
}

from ..NOTE.property_set_object_factory import OneNotebookPropertySetFactory
from .property_element_factory import OneNotebookPropertyElementFactory
OneNotebookXmlPropertySetFactory = XmlPropertySetFactory(OneNotebookPropertySetFactory,
												OneNotebookPropertyElementFactory,
												OneNootebookPropertySetElementBuilderTemplates)


# Upper directory level object: jcidPersistablePropertyContainerForTOC structures
from ..NOTE.property_set_object_factory import OneToc2PropertySetFactory

class xmlPersistablePropertyContainerForTOC(PropertySetXmlElementBase):
	JCID = TocPropertySetJCID.jcidPersistablePropertyContainerForTOC
	JCID_CLASS:IntEnum = TocPropertySetJCID

PropertyContainerForTOCTemplates = {
	TocPropertySetJCID.jcidPersistablePropertyContainerForTOC.value :
						xmlPersistablePropertyContainerForTOC,
}

from .property_element_factory import OneToc2PropertyElementFactory

OneToc2XmlPropertySetFactory = XmlPropertySetFactory(OneToc2PropertySetFactory,
													 OneToc2PropertyElementFactory,
													 PropertyContainerForTOCTemplates)
