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

class PropertySetJCID(IntEnum):
	'''
	JCID codes with 0x00100000 bit set are read-only objects.
	All objects with same ID in all revisions of an object space will have same value.
	All JCID codes below have 0x00020000 bit set, which means they all are property set objects.
	0x00040000 bit means IsGraphNode, which is only advisory. It means rendered contents.
	metadata and style objects don't have bit 0x00040000 set.
	'''
	jcidReadOnlyPersistablePropertyContainerForAuthor = 0x00120001 # Read Only
	jcidSectionNode                      = 0x00060007
	jcidPageSeriesNode                   = 0x00060008
	jcidPageNode                         = 0x0006000B
	jcidOutlineNode                      = 0x0006000C
	jcidOutlineElementNode               = 0x0006000D
	jcidRichTextOENode                   = 0x0006000E
	jcidImageNode                        = 0x00060011
	jcidNumberListNode                   = 0x00060012
	jcidOutlineGroup                     = 0x00060019
	jcidTableNode                        = 0x00060022
	jcidTableRowNode                     = 0x00060023
	jcidTableCellNode                    = 0x00060024
	jcidTitleNode                        = 0x0006002C
	jcidPageMetaData                     = 0x00020030
	jcidSectionMetaData                  = 0x00020031
	jcidEmbeddedFileNode                 = 0x00060035
	jcidEmbeddedFileContainer            = 0x00080036
	jcidPageManifestNode                 = 0x00060037
	jcidConflictPageMetaData             = 0x00020038
	jcidPictureContainer14               = 0x00080039
	jcidVersionHistoryContent            = 0x0006003C
	jcidVersionProxy                     = 0x0006003D
	jcidNoteTagSharedDefinitionContainer = 0x00120043 # Read Only
	jcidRevisionMetaData                 = 0x00020044
	jcidVersionHistoryMetaData           = 0x00020046
	jcidParagraphStyleObject             = 0x0012004D # Read Only
	#jcidParagraphStyleObjectForText     = 0x0012004D
	jcidReadOnlyAuthor                   = 0x00120051

class NoteOnlineParagraphStylePropertySetJCID(IntEnum):
	jcidNoteOnlineParagraphStyle = 0x00020001

class TocSectionPropertySetJCID(IntEnum):
	jcidPersistablePropertyContainerForTOCSection = 0x00020001

class TocPropertySetJCID(IntEnum):
	jcidPersistablePropertyContainerForTOC = 0x00020001

