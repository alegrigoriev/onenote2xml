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
	CHILD_NODES_PROPERTY_ENUM = None

	def __init__(self, jcid, oid):
		self._jcid:JCID = jcid
		self._oid = oid
		if self.JCID is NotImplemented:
			if jcid is not None:
				self._jcid_name = "jcid_%X" % (jcid.jcid,)
			else:
				self._jcid_name = "None"
			self.min_verbosity = 5
		else:
			self._jcid_name = self.JCID.name
			self.min_verbosity = 4
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
		properties_verbosity = self.PROPERTIES_VERBOSITY
		properties_order = self.PROPERTIES_ORDER

		md5hash = md5(usedforsecurity=False)
		md5hash.update(self._jcid.jcid.to_bytes(4, byteorder='little', signed=False))

		for prop in sorted(property_set.Properties(), key=lambda k:properties_order.get(k.property_id, k.property_id)):
			prop_obj = self.PROPERTY_FACTORY(prop)
			if prop_obj is NotImplemented:
				continue

			prop_obj.min_verbosity = properties_verbosity.get(prop_obj.property_id, 5)
			# make_object can override prop_obj.min_verbosity

			prop_obj.make_object(self, revision_ctx)

			if self.min_verbosity > prop_obj.min_verbosity:
				self.min_verbosity = prop_obj.min_verbosity

			self._properties[prop_obj.key] = prop_obj
			if prop_obj.min_verbosity <= revision_ctx.verbosity:
				prop_obj.update_hash(md5hash)
			continue

		self.md5 = md5hash.digest()

		if self.CHILD_NODES_PROPERTY_ENUM is not None:
			ChildNodes = self.get(self.CHILD_NODES_PROPERTY_ENUM.name, None)
			if ChildNodes is not None:
				self.min_verbosity = ChildNodes.min_verbosity
			else:
				self.min_verbosity = properties_verbosity[self.CHILD_NODES_PROPERTY_ENUM.value]

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

	PROPERTIES_VERBOSITY = {
		# Values: minimum verbosity level
		int(PropertyID.LayoutTightLayout)               : 2,
		int(PropertyID.PageWidth)                       : 2,
		int(PropertyID.PageHeight)                      : 2,
		int(PropertyID.OutlineElementChildLevel)        : 0,
		int(PropertyID.Bold)                            : 0,
		int(PropertyID.Italic)                          : 0,
		int(PropertyID.Underline)                       : 0,
		int(PropertyID.Strikethrough)                   : 0,
		int(PropertyID.Superscript)                     : 0,
		int(PropertyID.Subscript)                       : 0,
		int(PropertyID.Font)                            : 0,
		int(PropertyID.FontSize)                        : 0,
		int(PropertyID.FontColor)                       : 0,
		int(PropertyID.Highlight)                       : 0,
		int(PropertyID.BodyTextAlignment)               : 4,
		int(PropertyID.OffsetFromParentHoriz)           : 2,
		int(PropertyID.OffsetFromParentVert)            : 2,
		int(PropertyID.NumberListFormat)                : 0,
		int(PropertyID.LayoutMaxWidth)                  : 2,
		int(PropertyID.LayoutMaxHeight)                 : 2,
		int(PropertyID.EnableHistory)                   : 2,
		int(PropertyID.ListNodes)                       : 0,
		int(PropertyID.OutlineElementRTL)               : 0,
		int(PropertyID.LanguageID)                      : 0,
		int(PropertyID.LayoutAlignmentSelf)             : 0,
		int(PropertyID.LayoutAlignmentInParent)         : 0,
		int(PropertyID.RgOutlineIndentDistance)         : 2,
		int(PropertyID.PictureContainer)                : 0,
		int(PropertyID.PageMarginTop)                   : 2,
		int(PropertyID.PageMarginBottom)                : 2,
		int(PropertyID.PageMarginLeft)                  : 2,
		int(PropertyID.PageMarginRight)                 : 2,
		int(PropertyID.ListFont)                        : 0,
		int(PropertyID.IsTitleTime)                     : 0,
		int(PropertyID.IsBoilerText)                    : 0,
		int(PropertyID.PageSize)                        : 2,
		int(PropertyID.PortraitPage)                    : 2,
		int(PropertyID.EnforceOutlineStructure)         : 0,
		int(PropertyID.EditRootRTL)                     : 0,
		int(PropertyID.CannotBeSelected)                : 2,
		int(PropertyID.IsTitleText)                     : 0,
		int(PropertyID.IsTitleDate)                     : 0,
		int(PropertyID.ListRestart)                     : 0,
		int(PropertyID.IsLayoutSizeSetByUser)           : 2,
		int(PropertyID.ListSpacingMu)                   : 0,
		int(PropertyID.LayoutOutlineReservedWidth)      : 2,
		int(PropertyID.LayoutResolveChildCollisions)    : 2,
		int(PropertyID.IsReadOnly)                      : 0,
		int(PropertyID.NoteOnlineParagraphStyle)        : 0,
		int(PropertyID.LayoutMinimumOutlineWidth)       : 2,
		int(PropertyID.LayoutCollisionPriority)         : 2,
		int(PropertyID.CachedTitleString)               : 0,
		int(PropertyID.DescendantsCannotBeMoved)        : 2,
		int(PropertyID.RichEditTextLangID)              : 0,
		int(PropertyID.LayoutTightAlignment)            : 2,
		int(PropertyID.Charset)                         : 0,
		int(PropertyID.Deletable)                       : 2,
		int(PropertyID.ListMSAAIndex)                   : 0,
		int(PropertyID.PageMarginOriginX)               : 2,
		int(PropertyID.PageMarginOriginY)               : 2,
		int(PropertyID.IsBackground)                    : 0,
		int(PropertyID.IRecordMedia)                    : 0,
		int(PropertyID.CachedTitleStringFromPage)       : 0,
		int(PropertyID.NotebookManagementEntityGuid)    : 0,
		int(PropertyID.TopologyCreationTimeStamp)       : 3,
		int(PropertyID.LastModifiedTimeStamp)           : 2,
		int(PropertyID.LastModifiedTime)                : 4,
		int(PropertyID.Author)                          : 0,
		int(PropertyID.AuthorMostRecent)                : 2,
		int(PropertyID.CreationTimeStamp)               : 3,
		int(PropertyID.AuthorOriginal)                  : 3,
		int(PropertyID.RowCount)                        : 0,
		int(PropertyID.ColumnCount)                     : 0,
		int(PropertyID.TableBordersVisible)             : 0,
		int(PropertyID.StructureElementChildNodes)      : 0,
		int(PropertyID.TableColumnWidths)               : 0,
		int(PropertyID.IsConflictPage)                  : 0,
		int(PropertyID.TableColumnsLocked)              : 0,
		int(PropertyID.PageLevel)                       : 0,
		int(PropertyID.IsConflictObjectForRender)       : 0,
		int(PropertyID.HasConflictPages)                : 0,
		int(PropertyID.EmbeddedFileContainer)           : 0,
		int(PropertyID.EmbeddedFileName)                : 0,
		int(PropertyID.SourceFilepath)                  : 0,
		int(PropertyID.ConflictingUserName)             : 0,
		int(PropertyID.ConflictingUserInitials)         : 3,
		int(PropertyID.ImageFilename)                   : 0,
		int(PropertyID.IsConflictObjectForSelection)    : 4,
		int(PropertyID.Hyperlink)                       : 0,
		int(PropertyID.UnderlineType)                   : 0,
		int(PropertyID.Hidden)                          : 0,
		int(PropertyID.HyperlinkProtected)              : 0,
		int(PropertyID.WzHyperlinkUrl)                  : 0,
		int(PropertyID.CellShadingColor)                : 0,
		int(PropertyID.ImageAltText)                    : 0,
		int(PropertyID.MathFormatting)                  : 0,
		int(PropertyID.ParagraphStyle)                  : 0,
		int(PropertyID.ParagraphSpaceBefore)            : 1,
		int(PropertyID.ParagraphSpaceAfter)             : 1,
		int(PropertyID.ParagraphLineSpacingExact)       : 1,
		int(PropertyID.TextRunIndex)                    : 1,
		int(PropertyID.RichEditTextUnicode)             : 1,
		int(PropertyID.TextExtendedAscii)               : 1,
		int(PropertyID.TextRunFormatting)               : 1,
		int(PropertyID.TextRunDataObject)               : 1,
		int(PropertyID.TextRunData)                     : 1,
		int(PropertyID.TextRunIsEmbeddedObject)         : 0,
		int(PropertyID.ParagraphStyleId)                : 0,
		int(PropertyID.HasVersionPages)                 : 2,
		int(PropertyID.ActionItemType)                  : 0,
		int(PropertyID.NoteTagShape)                    : 0,
		int(PropertyID.NoteTagHighlightColor)           : 0,
		int(PropertyID.NoteTagTextColor)                : 0,
		int(PropertyID.NoteTagPropertyStatus)           : 0,
		int(PropertyID.NoteTagLabel)                    : 0,
		int(PropertyID.NoteTagCreated)                  : 4,
		int(PropertyID.NoteTagCompleted)                : 4,
		int(PropertyID.NoteTagDefinitionOid)            : 4,
		int(PropertyID.NoteTagStates)                   : 4,
		int(PropertyID.ActionItemStatus)                : 0,
		int(PropertyID.ActionItemSchemaVersion)         : 0,
		int(PropertyID.ReadingOrderRTL)                 : 0,
		int(PropertyID.ParagraphAlignment)              : 0,
		int(PropertyID.DisplayedPageNumber)             : 0,
		int(PropertyID.SectionDisplayName)              : 0,
		int(PropertyID.SchemaRevisionInOrderToRead)     : 4,
		int(PropertyID.SchemaRevisionInOrderToWrite)    : 4,
		int(PropertyID.NextStyle)                       : 0,
		int(PropertyID.WebPictureContainer14)           : 0,
		int(PropertyID.ImageUploadState)                : 0,
		int(PropertyID.PictureWidth)                    : 0,
		int(PropertyID.PictureHeight)                   : 0,
		int(PropertyID.TaskTagDueDate)                  : 1,

		int(PropertyID.AsciiNumberListFormat_Undocumented) : 0,
		int(PropertyID.PredefinedParagraphStyles)       : 3,
		int(PropertyID.NotebookColor)                   : 0,
		int(PropertyID.TOCEntryIndex_OidIndex)          : 0,
		int(PropertyID.FileIdentityGuid)                : 0,
		int(PropertyID.NotebookElementOrderingID)       : 0,
		int(PropertyID.FolderChildFilename)             : 0,
		int(PropertyID.AuthorInitials)                  : 3,
		int(PropertyID.NotebookSectionName_Undocumented) : 0,
		int(PropertyID.ContentChildNodes)               : 0,
		# int(PropertyID.ContentChildNodesOfOutlineElement : 0,
		# int(PropertyID.ContentChildNodesOfPageManifest: 0,
		int(PropertyID.ElementChildNodes)               : 0,
		# int(PropertyID.ElementChildNodesOfSection)    : 0,
		# int(PropertyID.ElementChildNodesOfPage)       : 0,
		# int(PropertyID.ElementChildNodesOfTitle)      : 0,
		# int(PropertyID.ElementChildNodesOfOutline)    : 0,
		# int(PropertyID.ElementChildNodesOfOutlineElement : 0,
		# int(PropertyID.ElementChildNodesOfTable)      : 0,
		# int(PropertyID.ElementChildNodesOfTableRow    : 0,
		# int(PropertyID.ElementChildNodesOfTableCell   : 0,
		# int(PropertyID.ElementChildNodesOfVersionHistory : 0,
		int(PropertyID.VersionHistoryGraphSpaceContextNodes) : 4,
		int(PropertyID.AudioRecordingGuid)              : 0,
		int(PropertyID.AudioRecordingGuids)             : 0,
		int(PropertyID.AudioRecordingDuration)          : 0,
	}

	@staticmethod
	def MakePropertiesOrder(properties_verbosity:set|dict):
		prop_order_dict = {}
		i = 1
		for prop_id in properties_verbosity:
			prop_order_dict[prop_id] = i
			i += 1
			continue
		return prop_order_dict

	PROPERTIES_ORDER = MakePropertiesOrder(PROPERTIES_VERBOSITY)

class jcidReadOnlyPersistablePropertyContainerForAuthor(PropertySetObject):
	JCID = PropertySetJCID.jcidReadOnlyPersistablePropertyContainerForAuthor

class jcidSectionNode(PropertySetObject):
	JCID = PropertySetJCID.jcidSectionNode

	PROPERTIES_VERBOSITY = {
		int(PropertyID.NotebookManagementEntityGuid)    : 2,
		int(PropertyID.TopologyCreationTimeStamp)       : 3,
		int(PropertyID.ElementChildNodes)  : 0,
		}
	PROPERTIES_ORDER = PropertySetObject.MakePropertiesOrder(PROPERTIES_VERBOSITY)

class jcidPageSeriesNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageSeriesNode

	PROPERTIES_VERBOSITY = {
		int(PropertyID.NotebookManagementEntityGuid)    : 2,
		int(PropertyID.MetaDataObjectsAboveGraphSpace)  : 0,
		int(PropertyID.ChildGraphSpaceElementNodes)     : 0,
		int(PropertyID.LastModifiedTime)                : 2,
		int(PropertyID.TopologyCreationTimeStamp)       : 3,
		}
	PROPERTIES_ORDER = PropertySetObject.MakePropertiesOrder(PROPERTIES_VERBOSITY)

class jcidPageNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageNode
	CHILD_NODES_PROPERTY_ENUM = PropertyID.ElementChildNodes

class jcidOutlineNode(PropertySetObject):
	JCID = PropertySetJCID.jcidOutlineNode
	CHILD_NODES_PROPERTY_ENUM = PropertyID.ElementChildNodes

class jcidOutlineElementNode(PropertySetObject):
	JCID = PropertySetJCID.jcidOutlineElementNode
	CHILD_NODES_PROPERTY_ENUM = PropertyID.ContentChildNodes

class jcidRichTextOENode(PropertySetObject):
	JCID = PropertySetJCID.jcidRichTextOENode

	PROPERTIES_VERBOSITY = {
		int(PropertyID.LastModifiedTime)                : 3,
		int(PropertyID.ParagraphStyle)                  : 0,
		int(PropertyID.ParagraphSpaceBefore)            : 0,
		int(PropertyID.ParagraphSpaceAfter)             : 0,
		int(PropertyID.ParagraphLineSpacingExact)       : 0,
		int(PropertyID.ParagraphAlignment)              : 0,
		int(PropertyID.IsBoilerText)                    : 0,
		int(PropertyID.IsTitleText)                     : 0,
		int(PropertyID.IsTitleDate)                     : 0,
		int(PropertyID.IsTitleTime)                     : 0,
		int(PropertyID.Deletable)                       : 2,
		int(PropertyID.LayoutAlignmentInParent)         : 0,
		int(PropertyID.LayoutAlignmentSelf)             : 0,
		int(PropertyID.IsReadOnly)                      : 0,
		int(PropertyID.RichEditTextLangID)              : 0,
		int(PropertyID.ReadingOrderRTL)                 : 0,
		int(PropertyID.TextRunIndex)                    : 1,
		int(PropertyID.TextRunFormatting)               : 1,
		int(PropertyID.RichEditTextUnicode)             : 1,
		int(PropertyID.TextExtendedAscii)               : 1,
		int(PropertyID.TextRunDataObject)               : 1,
		int(PropertyID.TextRunData)                     : 1,
		int(PropertyID.LayoutTightLayout)               : 2,
		int(PropertyID.NoteTagStates)                   : 4,
		int(PropertyID.IsConflictObjectForRender)       : 0,
		int(PropertyID.IsConflictObjectForSelection)    : 4,
		}
	PROPERTIES_ORDER = PropertySetObject.MakePropertiesOrder(PROPERTIES_VERBOSITY)

	def make_object(self, revision_ctx, property_set:PropertySet):
		super().make_object(revision_ctx, property_set)
		TextRunFormattingVerbosity = self.PROPERTIES_VERBOSITY[int(PropertyID.TextRunFormatting)]
		if revision_ctx.verbosity >= TextRunFormattingVerbosity:
			self.TextRunsArray = None
			return self

		# The super-object only hashed attributes not ignored by verbosity level
		# We heedn to hash the hext here
		md5hash = md5(self.md5, usedforsecurity=False)
		for prop_obj in self._properties.values():
			if prop_obj.min_verbosity == TextRunFormattingVerbosity:
				prop_obj.update_hash(md5hash)
			continue
		self.md5 = md5hash.digest()

		RichEditTextUnicode = self.get('RichEditTextUnicode', None)
		TextExtendedAscii = self.get('TextExtendedAscii', None)
		text_run_index = getattr(self, 'TextRunIndex', [])
		text_run_data = iter(getattr(self, 'TextRunData', []))
		text_run_formatting = iter(getattr(self, 'TextRunFormatting', []))
		lcid = getattr(self, 'RichEditTextLangID', 1033)

		# By default, do not show this text element
		self.min_verbosity = TextRunFormattingVerbosity
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

			if text:
				# Do not discard this property set, because it has non-empty text
				self.min_verbosity = 0
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

	PROPERTIES_VERBOSITY = {
		int(PropertyID.PageLevel)                       : 0,
		int(PropertyID.CachedTitleString)               : 0,
		int(PropertyID.IsDeletedGraphSpaceContent)      : 0,
		int(PropertyID.NotebookManagementEntityGuid)    : 1,
		int(PropertyID.HasConflictPages)                : 0,

		int(PropertyID.HasVersionPages)                 : 2,
		int(PropertyID.TopologyCreationTimeStamp)       : 3,

		int(PropertyID.SchemaRevisionInOrderToRead)     : 4,
		int(PropertyID.SchemaRevisionInOrderToWrite)    : 4,
		}
	PROPERTIES_ORDER = PropertySetObject.MakePropertiesOrder(PROPERTIES_VERBOSITY)

class jcidSectionMetaData(PropertySetObject):
	JCID = PropertySetJCID.jcidSectionMetaData

class jcidEmbeddedFileNode(PropertySetObject):
	JCID = PropertySetJCID.jcidEmbeddedFileNode

class jcidPageManifestNode(PropertySetObject):
	JCID = PropertySetJCID.jcidPageManifestNode
	CHILD_NODES_PROPERTY_ENUM = PropertyID.ContentChildNodes

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

	def __init__(self, jcid, oid):
		super().__init__(jcid, oid)
		self._data:bytes = None
		self._guid = None
		self._filename = None
		return

	def make_object(self, revision_ctx, file_data_object):
		# file_data_object is a FileDataObject object, not PropertySet
		# Locate binary data either in onestore.FileDataStoreList,
		# or from a file in onefiles directory
		md5hash = md5(usedforsecurity=False)
		md5hash.update(self._jcid.jcid.to_bytes(4, byteorder='little', signed=False))

		self._guid = str(file_data_object.guid)
		self._extension = file_data_object.extension
		if file_data_object.guid is not None:
			data_ctx = revision_ctx.GetDataStoreObject(file_data_object.guid, file_data_object.extension)
		elif self._filename is not None:
			data_ctx = revision_ctx.ReadOnefile(file_data_object.filename, file_data_object.extension)
		else:
			data_ctx = None

		if data_ctx is not None:
			self._data = data_ctx.GetData()
			self._filename = data_ctx.GetFilename()
			md5hash.update(self._filename.encode())

		if self._data:
			self.min_verbosity = 0
			md5hash.update(len(self._data).to_bytes(4, byteorder='little', signed=False))
			md5hash.update(self._data)

		self.md5 = md5hash.digest()
		return

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
