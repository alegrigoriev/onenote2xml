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
from ..property_set_jcid import *
from enum import IntEnum

class jsonPropertySetBase:

	# We'll make this the top __init__ method by using method dictionary
	def init(self, jcid, oid):
		# Since we're using this class as a template,
		# the actual base class is not accessible to the default super() form
		super(type(self), self).__init__(jcid, oid)
		# TODO: Add initialization here
		return

	def MakeJsonNode(self, revision_ctx):
		obj = {}
		for prop in self._properties.values():

			subobj = prop.MakeJsonValue(revision_ctx)
			if subobj is NotImplemented:
				continue

			obj[prop.key_string] = subobj
			continue
		return obj

	@classmethod
	def MakeClass(cls, base_class, json_property_element_factory):
		new_class = type('json' + base_class.__name__.removeprefix('jcid'), (base_class, cls), {})
		new_class.__init__ = cls.init
		new_class.PROPERTY_FACTORY = json_property_element_factory
		return new_class

class jsonReadOnlyPersistablePropertyContainerForAuthor(jsonPropertySetBase):
	...

class jsonPersistablePropertyContainerForTOC(jsonPropertySetBase):
	...

class jsonSectionNode(jsonPropertySetBase):
	...

class jsonPageSeriesNode(jsonPropertySetBase):
	...

class jsonPageNode(jsonPropertySetBase):
	...

class jsonOutlineNode(jsonPropertySetBase):
	...

class jsonOutlineElementNode(jsonPropertySetBase):
	...

class jsonRichTextOENode(jsonPropertySetBase):
	...

	def MakeJsonNode(self, revision_ctx):

		content = []
		for text_run in self.TextRunsArray:
			if not text_run[0]:
				continue

			text_run_obj = {
				'text' : text_run[0],
				'attr' : text_run[1].MakeJsonNode(revision_ctx)
				}
			content.append(text_run_obj)
			continue

		if not content:
			return None
		root = {
			'type' : 'paragraph',
			'content' : content
			}

		paragraph_style = getattr(self, 'ParagraphStyle', None)
		if paragraph_style is not None:
			root['style'] = paragraph_style.MakeJsonNode(revision_ctx)
		# TODO: add other elements
		return root

class jsonImageNode(jsonPropertySetBase):
	...

class jsonNumberListNode(jsonPropertySetBase):
	...

class jsonOutlineGroup(jsonPropertySetBase):
	...

class jsonTableNode(jsonPropertySetBase):
	...

class jsonTableRowNode(jsonPropertySetBase):
	...

class jsonTableCellNode(jsonPropertySetBase):
	...

class jsonTitleNode(jsonPropertySetBase):
	...

class jsonPageMetaData(jsonPropertySetBase):
	...

class jsonSectionMetaData(jsonPropertySetBase):
	...

class jsonEmbeddedFileNode(jsonPropertySetBase):
	...

class jsonPageManifestNode(jsonPropertySetBase):
	...

class jsonConflictPageMetaData(jsonPropertySetBase):
	...

class jsonVersionHistoryContent(jsonPropertySetBase):
	...

class jsonVersionProxy(jsonPropertySetBase):
	...

class jsonNoteTagSharedDefinitionContainer(jsonPropertySetBase):
	...

class jsonRevisionMetaData(jsonPropertySetBase):
	...

class jsonVersionHistoryMetaData(jsonPropertySetBase):
	...

class jsonParagraphStyleObject(jsonPropertySetBase):
	def MakeJsonNode(self, revision_ctx):

		attrs = {}
		value = getattr(self, 'ParagraphStyleId', '')
		if value: attrs['id'] = value

		for prop_name, json_name in (
						('Bold', 'bold'),
						('Italic', 'italic'),
						('Underline', 'underline'),
						('Strikethrough', 'strikethrough'),
						('Subscript', 'subscript'),
						('Superscript', 'superscript'),
						('Hidden', 'hidden'),
						('Hyperlink', 'hyperlink'),
						('HyperlinkProtected', 'hyperlink_protected'),
						('MathFormatting', 'math'),
						('Font', 'font'),
						('FontSize', 'font_size'),
						('LanguageID', 'language_id'),
						('Charset', 'charset'),
						('FontColor', 'font_color'),
						('Highlight', 'highlight'),
						):
			prop = self.get(prop_name, None)
			if prop is not None:
				attrs[json_name] = prop.MakeJsonValue(revision_ctx)

		return attrs

class jsonEmbeddedFileContainer(jsonPropertySetBase):
	...

class jsonPictureContainer14(jsonEmbeddedFileContainer): ...

from ..NOTE.property_set_object_factory import PropertySetFactory

class JsonPropertySetFactory:
	def __init__(self, property_set_factory:PropertySetFactory,
					json_property_factory,
					template_dict:dict={}):
		self.template_dict = template_dict
		self.property_set_factory = property_set_factory
		self.json_property_factory = json_property_factory
		self.jcid_class = property_set_factory.get_jcid_class()
		self.json_property_set_dict = { }  # Initially empty
		return

	def get_jcid_class(self):
		return self.jcid_class

	def make_json_property_set_class(self, jcid):
		'''
		This creates a custom class to construct json object for a property class
		'''
		base_class = self.property_set_factory.get_property_set_class(jcid)
		base_json_class = self.template_dict.get(jcid.jcid, jsonPropertySetBase)

		return base_json_class.MakeClass(base_class, self.json_property_factory)

	def get_json_property_set_class(self, jcid:JCID):
		property_set_class = self.json_property_set_dict.get(jcid.jcid, None)
		if property_set_class is None:
			# Build the class instance
			property_set_class = self.make_json_property_set_class(jcid)
			self.json_property_set_dict[jcid.jcid] = property_set_class

		return property_set_class

	def __call__(self, jcid:JCID, oid:ExGUID):
		return self.get_json_property_set_class(jcid)(jcid, oid)

OneNootebookJsonPropertySetDocBuilderTemplates = {
	PropertySetJCID.jcidReadOnlyPersistablePropertyContainerForAuthor.value :
						jsonReadOnlyPersistablePropertyContainerForAuthor,
	PropertySetJCID.jcidParagraphStyleObject.value: jsonParagraphStyleObject,
	PropertySetJCID.jcidNoteTagSharedDefinitionContainer.value: jsonNoteTagSharedDefinitionContainer,
	PropertySetJCID.jcidImageNode.value: jsonImageNode,
	PropertySetJCID.jcidNumberListNode.value: jsonNumberListNode,
	PropertySetJCID.jcidOutlineGroup.value: jsonOutlineGroup,
	PropertySetJCID.jcidTableNode.value: jsonTableNode,
	PropertySetJCID.jcidTableRowNode.value: jsonTableRowNode,
	PropertySetJCID.jcidTableCellNode.value: jsonTableCellNode,
	PropertySetJCID.jcidTitleNode.value: jsonTitleNode,
	PropertySetJCID.jcidPageSeriesNode.value: jsonPageSeriesNode,
	PropertySetJCID.jcidPageNode.value: jsonPageNode,
	PropertySetJCID.jcidOutlineNode.value: jsonOutlineNode,
	PropertySetJCID.jcidRichTextOENode.value: jsonRichTextOENode,
	PropertySetJCID.jcidEmbeddedFileContainer.value: jsonEmbeddedFileContainer,
	PropertySetJCID.jcidPictureContainer14.value: jsonPictureContainer14,
	PropertySetJCID.jcidReadOnlyAuthor.value: jsonReadOnlyPersistablePropertyContainerForAuthor,
}

from ..NOTE.property_set_object_factory import OneNotebookPropertySetFactory
from .json_property_factory import OneNotebookJsonPropertyFactory
OneNotebookJsonPropertySetFactory = JsonPropertySetFactory(OneNotebookPropertySetFactory,
												OneNotebookJsonPropertyFactory,
												OneNootebookJsonPropertySetDocBuilderTemplates)

from ..NOTE.property_set_object_factory import OneToc2PropertySetFactory
TocPropertySetJCID = OneToc2PropertySetFactory.get_jcid_class()

class jsonPersistablePropertyContainerForTOC(jsonPropertySetBase):
	JCID = TocPropertySetJCID.jcidPersistablePropertyContainerForTOC
	JCID_CLASS:IntEnum = TocPropertySetJCID

PropertyContainerForJsonTOCTemplates = {
	TocPropertySetJCID.jcidPersistablePropertyContainerForTOC.value :
						jsonPersistablePropertyContainerForTOC,
}

# Directory sections: jcidPersistablePropertyContainerForTOCSection
from .json_property_factory import OneToc2JsonPropertyFactory
OneToc2JsonPropertySetFactory = JsonPropertySetFactory(OneToc2PropertySetFactory,
														OneToc2JsonPropertyFactory,
														PropertyContainerForJsonTOCTemplates)
