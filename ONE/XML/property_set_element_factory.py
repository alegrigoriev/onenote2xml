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

	def MakeXmlComment(self)->str:
		return None

	def MakeXmlElement(self, revision_ctx):
		element = ET.Element(self._jcid_name)
		if revision_ctx.include_oids and self._oid is not None:
			element.set('OID', str(self._oid))

		for prop in self._properties.values():
			if prop.min_verbosity > revision_ctx.verbosity:
				continue

			prop_element = prop.MakeXmlElement(revision_ctx)
			if prop_element is not None:
				comment:str = prop.MakeXmlComment()
				if comment:
					element.append(ET.Comment(' ' + comment + ' '))
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

	def MakeXmlComment(self):
		comment = 'Author:' + self.Author
		try:
			comment += ', Initials:' + self.AuthorInitials
		except:
			pass
		return comment

class xmlReadOnlyAuthor(xmlReadOnlyPersistablePropertyContainerForAuthor): ...

class xmlNoteTagSharedDefinitionContainer(PropertySetXmlElementBase):
	READONLY_SPACE = 'NoteTags'

class xmlParagraphStyleObject(PropertySetXmlElementBase):
	READONLY_SPACE = 'ParagraphStyles'

	def MakeXmlComment(self):
		comments = []

		prop = getattr(self, 'ParagraphStyleId', None)
		if prop:
			comments.append(('Style', prop))

		for prop_name in (
						'Bold',
						'Italic',
						'Underline',
						'Strikethrough',
						'Subscript',
						'Superscript',
						'Hidden',
						'Hyperlink',
						'HyperlinkProtected',
						):

			prop = getattr(self, prop_name, False)
			if prop:
				comments.append((prop_name, '1'))

		prop = getattr(self, 'MathFormatting', False)
		if prop:
			comments.append(('Math', '1'))

		for prop_name in (
						'Font',
						'FontSize',
						'LanguageID',
						'Charset',
						'FontColor',
						'Highlight',
						):
			prop = self.get(prop_name, None)
			if prop is not None \
				and prop.min_verbosity <= self.min_verbosity \
				and prop.value is not None:
				comments.append((prop_name, prop.str_value))

		for prop_name in (
						('ParagraphSpaceBefore', 'SpaceBefore'),
						('ParagraphSpaceAfter', 'SpaceAfter'),
						('ParagraphLineSpacingExact', 'LineSpacingExact'),
						):
			prop = self.get(prop_name[0], None)
			if prop is not None \
				and prop.min_verbosity <= self.min_verbosity \
				and prop.value != 0.0:
				comments.append((prop_name[1], prop.str_value))

		return ', '.join('%s:%s' % name_value_tuple for name_value_tuple in comments)

class xmlRichTextOENode(PropertySetXmlElementBase):

	def MakeXmlElement(self, revision_ctx):
		element = super().MakeXmlElement(revision_ctx)

		if self.TextRunsArray is None:
			return element

		text_runs_element = ET.SubElement(element, 'TextRuns')
		for text_run in self.TextRunsArray:
			subelement = ET.SubElement(text_runs_element, 'TextRun')
			TextElement = ET.SubElement(subelement, 'Text')
			TextElement.text = text_run[0]
			revision_ctx.AppendXmlElementReference(subelement, text_run[1])
			if text_run[2] is not None:
				RunData = text_run[2].MakeXmlElement(revision_ctx)
				RunData.tag = 'RunData'
				if RunData:
					# Not empty
					subelement.append(RunData)
			continue

		return element

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
	PropertySetJCID.jcidRichTextOENode.value: xmlRichTextOENode,
}

from ..NOTE.property_set_object_factory import OneNotebookPropertySetFactory
from .property_element_factory import OneNotebookPropertyElementFactory
OneNotebookXmlPropertySetFactory = XmlPropertySetFactory(OneNotebookPropertySetFactory,
												OneNotebookPropertyElementFactory,
												OneNootebookPropertySetElementBuilderTemplates)


from ..NOTE.property_set_object_factory import NoteOnlineParagraphStyleObjectFactory
class xmlNoteOnlineParagraphStyle(xmlParagraphStyleObject):
	def is_read_only(self): return True

NoteOnlineParagraphStyleTemplates = {
	NoteOnlineParagraphStylePropertySetJCID.jcidNoteOnlineParagraphStyle.value :
						xmlNoteOnlineParagraphStyle,
}

NoteOnlineParagraphStyleXmlFactory = XmlPropertySetFactory(NoteOnlineParagraphStyleObjectFactory,
												OneNotebookPropertyElementFactory,
												NoteOnlineParagraphStyleTemplates)

# Upper directory level object: jcidPersistablePropertyContainerForTOC structures
from ..NOTE.property_set_object_factory import OneToc2PropertySetFactory

class xmlPersistablePropertyContainerForTOC(PropertySetXmlElementBase):
	JCID = TocPropertySetJCID.jcidPersistablePropertyContainerForTOC
	JCID_CLASS:IntEnum = TocPropertySetJCID

	def make_object(self, revision_ctx, property_set):
		prev_property_set_factory = revision_ctx.property_set_factory

		revision_ctx.property_set_factory = OneToc2SectionPropertySetXmlFactory

		super(type(self), self).make_object(revision_ctx, property_set)

		revision_ctx.property_set_factory = prev_property_set_factory
		return

	@staticmethod
	def MakeClass(cls, base_class, xml_property_element_factory):
		new_class = PropertySetXmlElementBase.MakeClass(base_class, xml_property_element_factory)
		new_class.make_object = cls.make_object
		return new_class

PropertyContainerForTOCTemplates = {
	TocPropertySetJCID.jcidPersistablePropertyContainerForTOC.value :
						xmlPersistablePropertyContainerForTOC,
}

# Directory sections: jcidPersistablePropertyContainerForTOCSection
from ..NOTE.property_set_object_factory import OneToc2SectionPropertySetFactory
from .property_element_factory import OneToc2PropertyElementFactory
OneToc2SectionPropertySetXmlFactory = XmlPropertySetFactory(OneToc2SectionPropertySetFactory,
															OneToc2PropertyElementFactory)

OneToc2XmlPropertySetFactory = XmlPropertySetFactory(OneToc2PropertySetFactory,
													 OneToc2PropertyElementFactory,
													 PropertyContainerForTOCTemplates)
