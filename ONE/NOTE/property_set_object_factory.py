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
from ..STORE.property_set import PropertySet
from ..property_id import *
from enum import IntEnum
from hashlib import md5

class PropertySetObject:
	JCID = NotImplemented
	JCID_CLASS = PropertySetJCID
	from .property_object_factory import OneNotebookPropertyFactory as PROPERTY_FACTORY

	def __init__(self, jcid, oid):
		self._jcid:JCID = jcid
		self._oid = oid
		if self.JCID is NotImplemented:
			if jcid is not None:
				self._jcid_name = "jcid_%X" % (jcid.jcid,)
			else:
				self._jcid_name = "None"
		else:
			self._jcid_name = self.JCID.name
		self._display_name = self._jcid_name
		self._properties = {}
		return

	def __getattr__(self, name: str):
		try:
			return self._properties[name].get_object_value()
		except KeyError as e:
			raise AttributeError("'%s' object has no attribute '%s'" % (self._display_name, e.args[0]),self) from e

	def get(self, name:str, *default):
		return self._properties.get(name, *default)

	def make_object(self, revision_ctx, property_set:PropertySet):
		# parent revision contains oid->PropertySet table
		# object_table contains objects already built

		md5hash = md5(usedforsecurity=False)
		md5hash.update(self._jcid.jcid.to_bytes(4, byteorder='little', signed=False))

		for prop in property_set.Properties():
			prop_obj = self.PROPERTY_FACTORY(prop)
			if prop_obj is NotImplemented:
				continue

			prop_obj.make_object(self, revision_ctx)

			self._properties[prop_obj.key] = prop_obj
			prop_obj.update_hash(md5hash)
			continue

		self.md5 = md5hash.digest()

		return

	def __iter__(self):
		# Iterate over all attributes recursively
		for key, prop in self._properties.items():
			for path, objs in prop:
				yield (key, *path), (self, *objs)
				continue
			continue
		return

	def get_hash(self):
		return self.md5

class jcidReadOnlyPersistablePropertyContainerForAuthor(PropertySetObject):
	JCID = PropertySetJCID.jcidReadOnlyPersistablePropertyContainerForAuthor

class jcidSectionNode(PropertySetObject):
	JCID = PropertySetJCID.jcidSectionNode

class jcidPageSeriesNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageSeriesNode

class jcidPageNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageNode

class jcidOutlineNode(PropertySetObject):
	JCID = PropertySetJCID.jcidOutlineNode

class jcidOutlineElementNode(PropertySetObject):
	JCID = PropertySetJCID.jcidOutlineElementNode

class jcidRichTextOENode(PropertySetObject):
	JCID = PropertySetJCID.jcidRichTextOENode

	def make_object(self, revision_ctx, property_set:PropertySet):
		super().make_object(revision_ctx, property_set)

		RichEditTextUnicode = self.get('RichEditTextUnicode', None)
		TextExtendedAscii = self.get('TextExtendedAscii', None)
		text_run_index = getattr(self, 'TextRunIndex', [])
		text_run_data = iter(getattr(self, 'TextRunData', []))
		text_run_formatting = iter(getattr(self, 'TextRunFormatting', []))
		lcid = getattr(self, 'RichEditTextLangID', 1033)

		self.TextRunsArray = []
		prev_index = 0
		for next_index in *text_run_index, None:
			if RichEditTextUnicode is not None:
				if next_index is None: # last index
					next_index = len(RichEditTextUnicode.data)
					if next_index == 0:
						break
				else:
					next_index *= 2
				text = Utf16BytesToStr(RichEditTextUnicode.data[prev_index:next_index])
			elif TextExtendedAscii is not None:
				if next_index is None: # last index
					next_index = len(TextExtendedAscii.data)
					if next_index == 0:
						break
				# TODO: Find 'Charset' property in jcidParagraphStyleObject/jcidParagraphStyleObjectForText
				charset = 0
				text = MbcsBytesToStr(TextExtendedAscii.data[prev_index:next_index], lcid, charset)
			else:
				break

			run_data = next(text_run_data, None)
			run_formatting = next(text_run_formatting)
			self.TextRunsArray.append((text, run_formatting, run_data))
			prev_index = next_index
			continue

		return

class jcidImageNode(PropertySetObject):
	JCID = PropertySetJCID.jcidImageNode

class jcidNumberListNode(PropertySetObject):
	JCID = PropertySetJCID.jcidNumberListNode

class jcidOutlineGroup(PropertySetObject):
	JCID = PropertySetJCID.jcidOutlineGroup
	# Insert break line between outline groups?

class jcidTableNode(PropertySetObject):
	JCID = PropertySetJCID.jcidTableNode

class jcidTableRowNode(PropertySetObject):
	JCID = PropertySetJCID.jcidTableRowNode

class jcidTableCellNode(PropertySetObject):
	JCID = PropertySetJCID.jcidTableCellNode

class jcidTitleNode(PropertySetObject):
	JCID = PropertySetJCID.jcidTitleNode

class jcidPageMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidPageMetaData

class jcidSectionMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidSectionMetaData

class jcidEmbeddedFileNode(PropertySetObject):
	JCID = PropertySetJCID.jcidEmbeddedFileNode

class jcidPageManifestNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageManifestNode

class jcidConflictPageMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidConflictPageMetaData

class jcidVersionHistoryContent(PropertySetObject):
	JCID = PropertySetJCID.jcidVersionHistoryContent

class jcidVersionProxy(PropertySetObject):
	JCID = PropertySetJCID.jcidVersionProxy

class jcidNoteTagSharedDefinitionContainer(PropertySetObject):
	JCID = PropertySetJCID.jcidNoteTagSharedDefinitionContainer

class jcidRevisionMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidRevisionMetaData

class jcidVersionHistoryMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidVersionHistoryMetaData

class jcidParagraphStyleObject(PropertySetObject):
	JCID = PropertySetJCID.jcidParagraphStyleObject

class jcidReadOnlyAuthor(PropertySetObject):
	JCID = PropertySetJCID.jcidReadOnlyAuthor

class jcidEmbeddedFileContainer(PropertySetObject):
	JCID = PropertySetJCID.jcidEmbeddedFileContainer

class jcidPictureContainer14(jcidEmbeddedFileContainer):
	JCID = PropertySetJCID.jcidPictureContainer14

OneNotebookPropertySetFactoryDict = {
	int(PropertySetJCID.jcidReadOnlyPersistablePropertyContainerForAuthor) :
						jcidReadOnlyPersistablePropertyContainerForAuthor,
	int(PropertySetJCID.jcidSectionNode): jcidSectionNode,
	int(PropertySetJCID.jcidPageSeriesNode): jcidPageSeriesNode,
	int(PropertySetJCID.jcidPageNode): jcidPageNode,
	int(PropertySetJCID.jcidOutlineNode): jcidOutlineNode,
	int(PropertySetJCID.jcidOutlineElementNode): jcidOutlineElementNode,
	int(PropertySetJCID.jcidRichTextOENode): jcidRichTextOENode,
	int(PropertySetJCID.jcidImageNode): jcidImageNode,
	int(PropertySetJCID.jcidNumberListNode): jcidNumberListNode,
	int(PropertySetJCID.jcidOutlineGroup): jcidOutlineGroup,
	int(PropertySetJCID.jcidTableNode): jcidTableNode,
	int(PropertySetJCID.jcidTableRowNode): jcidTableRowNode,
	int(PropertySetJCID.jcidTableCellNode): jcidTableCellNode,
	int(PropertySetJCID.jcidTitleNode): jcidTitleNode,
	int(PropertySetJCID.jcidPageMetaData): jcidPageMetaData,
	int(PropertySetJCID.jcidSectionMetaData): jcidSectionMetaData,
	int(PropertySetJCID.jcidEmbeddedFileNode): jcidEmbeddedFileNode,
	int(PropertySetJCID.jcidPageManifestNode): jcidPageManifestNode,
	int(PropertySetJCID.jcidConflictPageMetaData): jcidConflictPageMetaData,
	int(PropertySetJCID.jcidVersionHistoryContent): jcidVersionHistoryContent,
	int(PropertySetJCID.jcidVersionProxy): jcidVersionProxy,
	int(PropertySetJCID.jcidNoteTagSharedDefinitionContainer):
										jcidNoteTagSharedDefinitionContainer,
	int(PropertySetJCID.jcidRevisionMetaData): jcidRevisionMetaData,
	int(PropertySetJCID.jcidVersionHistoryMetaData): jcidVersionHistoryMetaData,
	int(PropertySetJCID.jcidParagraphStyleObject): jcidParagraphStyleObject,
	int(PropertySetJCID.jcidReadOnlyAuthor): jcidReadOnlyAuthor,
	int(PropertySetJCID.jcidEmbeddedFileContainer): jcidEmbeddedFileContainer,
	int(PropertySetJCID.jcidPictureContainer14): jcidPictureContainer14,
	}

class jcidPersistablePropertyContainerForTOCSection(PropertySetObject):
	JCID = TocSectionPropertySetJCID.jcidPersistablePropertyContainerForTOCSection
	JCID_CLASS:IntEnum = TocSectionPropertySetJCID
	from .property_object_factory import OneToc2PropertyFactory as PROPERTY_FACTORY

OneToc2PropertySetSectionFactoryDict = {
	int(TocSectionPropertySetJCID.jcidPersistablePropertyContainerForTOCSection) :
								jcidPersistablePropertyContainerForTOCSection,
}

class jcidPersistablePropertyContainerForTOC(PropertySetObject):
	JCID = TocPropertySetJCID.jcidPersistablePropertyContainerForTOC
	JCID_CLASS:IntEnum = TocPropertySetJCID
	from .property_object_factory import OneToc2PropertyFactory as PROPERTY_FACTORY

OneToc2PropertySetFactoryDict = {
	int(TocPropertySetJCID.jcidPersistablePropertyContainerForTOC) :
						jcidPersistablePropertyContainerForTOC,
}

class jcidNoteOnlineParagraphStyle(PropertySetObject):
	JCID_CLASS:IntEnum = NoteOnlineParagraphStylePropertySetJCID
	JCID = NoteOnlineParagraphStylePropertySetJCID.jcidNoteOnlineParagraphStyle

NoteOnlineParagraphStyleFactoryDict = {
	int(NoteOnlineParagraphStylePropertySetJCID.jcidNoteOnlineParagraphStyle) :
						jcidNoteOnlineParagraphStyle,
}

class PropertySetFactory:
	def __init__(self, property_set_dict:dict={}, jcid_class=PropertySetJCID, default_class=PropertySetObject):
		self.property_set_dict = property_set_dict
		self.default_class = default_class
		self.jcid_class = jcid_class
		return

	def get_jcid_class(self):
		return self.jcid_class

	def get_property_set_class(self, jcid:JCID):
		return self.property_set_dict.get(jcid.jcid, self.default_class)

	def __call__(self, jcid:JCID, oid:ExGUID):
		return self.get_property_set_class(jcid)(jcid, oid)

NoteOnlineParagraphStyleObjectFactory = PropertySetFactory(NoteOnlineParagraphStyleFactoryDict, NoteOnlineParagraphStylePropertySetJCID)

OneNotebookPropertySetFactory = PropertySetFactory(OneNotebookPropertySetFactoryDict)

# Section descriptors:
OneToc2SectionPropertySetFactory = PropertySetFactory(OneToc2PropertySetSectionFactoryDict, TocSectionPropertySetJCID)

# Top level directory
OneToc2PropertySetFactory = PropertySetFactory(OneToc2PropertySetFactoryDict, TocPropertySetJCID)
