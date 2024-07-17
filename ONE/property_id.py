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

class PropertyTypeID(IntEnum):
	'''
	type (5 bits): An unsigned integer that specifies the property type and the size and location of the data for this property.
	MUST be one of the following values:
	'''
	NoData                          = 0x01 # 0x04xxxxxx
	Bool                            = 0x02 # 0x08xxxxxx
	OneByteOfData                   = 0x03 # 0x0Cxxxxxx
	TwoBytesOfData                  = 0x04 # 0x10xxxxxx
	FourBytesOfData                 = 0x05 # 0x14xxxxxx
	EightBytesOfData                = 0x06 # 0x18xxxxxx
	FourBytesOfLengthFollowedByData = 0x07 # 0x1Cxxxxxx
	ObjectID                        = 0x08 # 0x20xxxxxx
	ArrayOfObjectIDs                = 0x09 # 0x24xxxxxx
	ObjectSpaceID                   = 0x0A # 0x28xxxxxx
	ArrayOfObjectSpaceIDs           = 0x0B # 0x2Cxxxxxx
	ContextID                       = 0x0C # 0x30xxxxxx
	ArrayOfContextIDs               = 0x0D # 0x34xxxxxx
	ArrayOfPropertyValues           = 0x10 # 0x40xxxxxx
	PropertySet                     = 0x11 # 0x44xxxxxx

class PropertyID(IntEnum):
	'''
	id (26 bits): An unsigned integer that specifies the identity of this property.
	The meanings of the id field values are specified in [MS-ONE] section 2.1.12.
	'''
	LayoutTightLayout                = 0x08001C00
	PageWidth                        = 0x14001C01
	PageHeight                       = 0x14001C02
	OutlineElementChildLevel         = 0x0C001C03
	Bold                             = 0x08001C04
	Italic                           = 0x08001C05
	Underline                        = 0x08001C06
	Strikethrough                    = 0x08001C07
	Superscript                      = 0x08001C08
	Subscript                        = 0x08001C09
	Font                             = 0x1C001C0A
	FontSize                         = 0x10001C0B
	FontColor                        = 0x14001C0C
	Highlight                        = 0x14001C0D
	RgOutlineIndentDistance          = 0x1C001C12
	BodyTextAlignment                = 0x0C001C13
	OffsetFromParentHoriz            = 0x14001C14
	OffsetFromParentVert             = 0x14001C15
	NumberListFormat                 = 0x1C001C1A
	LayoutMaxWidth                   = 0x14001C1B
	LayoutMaxHeight                  = 0x14001C1C
	ContentChildNodes                = 0x24001C1F
	# ContentChildNodesOfOutlineElement = 0x24001C1F
	# ContentChildNodesOfPageManifest= 0x24001C1F
	ElementChildNodes                = 0x24001C20
	# ElementChildNodesOfSection     = 0x24001C20
	# ElementChildNodesOfPage        = 0x24001C20
	# ElementChildNodesOfTitle       = 0x24001C20
	# ElementChildNodesOfOutline     = 0x24001C20
	# ElementChildNodesOfOutlineElement = 0x24001C20
	# ElementChildNodesOfTable       = 0x24001C20
	# ElementChildNodesOfTableRow    = 0x24001C20
	# ElementChildNodesOfTableCell   = 0x24001C20
	# ElementChildNodesOfVersionHistory = 0x24001C20
	EnableHistory                    = 0x08001E1E
	RichEditTextUnicode              = 0x1C001C22
	ListNodes                        = 0x24001C26
	NotebookManagementEntityGuid     = 0x1C001C30
	OutlineElementRTL                = 0x08001C34
	LanguageID                       = 0x14001C3B
	LayoutAlignmentInParent          = 0x14001C3E
	PictureContainer                 = 0x20001C3F
	PageMarginTop                    = 0x14001C4C
	PageMarginBottom                 = 0x14001C4D
	PageMarginLeft                   = 0x14001C4E
	PageMarginRight                  = 0x14001C4F
	ListFont                         = 0x1C001C52
	TopologyCreationTimeStamp        = 0x18001C65
	LayoutAlignmentSelf              = 0x14001C84
	IsTitleTime                      = 0x08001C87
	IsBoilerText                     = 0x08001C88
	PageSize                         = 0x14001C8B
	PortraitPage                     = 0x08001C8E
	EnforceOutlineStructure          = 0x08001C91
	EditRootRTL                      = 0x08001C92
	CannotBeSelected                 = 0x08001CB2
	IsTitleText                      = 0x08001CB4
	IsTitleDate                      = 0x08001CB5
	ListRestart                      = 0x14001CB7
	IsLayoutSizeSetByUser            = 0x08001CBD
	ListSpacingMu                    = 0x14001CCB
	LayoutOutlineReservedWidth       = 0x14001CDB
	LayoutResolveChildCollisions     = 0x08001CDC
	IsReadOnly                       = 0x08001CDE
	NoteOnlineParagraphStyle         = 0x20001CE2
	LayoutMinimumOutlineWidth        = 0x14001CEC
	LayoutCollisionPriority          = 0x14001CF1
	CachedTitleString                = 0x1C001CF3
	DescendantsCannotBeMoved         = 0x08001CF9
	RichEditTextLangID               = 0x10001CFE
	LayoutTightAlignment             = 0x08001CFF
	Charset                          = 0x0C001D01
	CreationTimeStamp                = 0x14001D09
	Deletable                        = 0x08001D0C
	ListMSAAIndex                    = 0x10001D0E
	PageMarginOriginX                = 0x14001D0F
	PageMarginOriginY                = 0x14001D10
	IsBackground                     = 0x08001D13
	IRecordMedia                     = 0x14001D24
	CachedTitleStringFromPage        = 0x1C001D3C
	RowCount                         = 0x14001D57
	ColumnCount                      = 0x14001D58
	TableBordersVisible              = 0x08001D5E
	StructureElementChildNodes       = 0x24001D5F
	ChildGraphSpaceElementNodes      = 0x2C001D63
	TableColumnWidths                = 0x1C001D66
	Author                           = 0x1C001D75
	LastModifiedTimeStamp            = 0x18001D77
	AuthorOriginal                   = 0x20001D78
	AuthorMostRecent                 = 0x20001D79
	LastModifiedTime                 = 0x14001D7A
	IsConflictPage                   = 0x08001D7C
	TableColumnsLocked               = 0x1C001D7D
	SchemaRevisionInOrderToRead      = 0x14001D82
	IsConflictObjectForRender        = 0x08001D96
	HasConflictPages                 = 0x08001D97
	EmbeddedFileContainer            = 0x20001D9B
	EmbeddedFileName                 = 0x1C001D9C
	SourceFilepath                   = 0x1C001D9D
	ConflictingUserName              = 0x1C001D9E
	ConflictingUserInitials          = 0x1C001D9F
	ImageFilename                    = 0x1C001DD7
	IsConflictObjectForSelection     = 0x08001DDB
	IsDeletedGraphSpaceContent       = 0x1C001DE9
	PageLevel                        = 0x14001DFF
	TextRunIndex                     = 0x1C001E12
	TextRunFormatting                = 0x24001E13
	Hyperlink                        = 0x08001E14
	UnderlineType                    = 0x0C001E15
	Hidden                           = 0x08001E16
	HyperlinkProtected               = 0x08001E19
	WzHyperlinkUrl                   = 0x1C001E20
	TextRunIsEmbeddedObject          = 0x08001E22
	CellShadingColor                 = 0x14001E26
	ImageAltText                     = 0x1C001E58
	MathFormatting                   = 0x08003401
	ParagraphStyle                   = 0x2000342C
	ParagraphSpaceBefore             = 0x1400342E
	ParagraphSpaceAfter              = 0x1400342F
	ParagraphLineSpacingExact        = 0x14003430
	MetaDataObjectsAboveGraphSpace   = 0x24003442
	TextRunDataObject                = 0x24003458
	TextRunData                      = 0x40003499
	ParagraphStyleId                 = 0x1C00345A
	HasVersionPages                  = 0x08003462
	ActionItemType                   = 0x10003463
	NoteTagShape                     = 0x10003464
	NoteTagHighlightColor            = 0x14003465
	NoteTagTextColor                 = 0x14003466
	NoteTagPropertyStatus            = 0x14003467
	NoteTagLabel                     = 0x1C003468
	NoteTagCreated                   = 0x1400346E
	NoteTagCompleted                 = 0x1400346F
	NoteTagDefinitionOid             = 0x20003488
	NoteTagStates                    = 0x04003489
	ActionItemStatus                 = 0x10003470
	ActionItemSchemaVersion          = 0x0C003473
	ReadingOrderRTL                  = 0x08003476
	ParagraphAlignment               = 0x0C003477
	VersionHistoryGraphSpaceContextNodes = 0x3400347B
	DisplayedPageNumber              = 0x14003480
	SchemaRevisionInOrderToWrite     = 0x1400348B
	SectionDisplayName               = 0x1C00349B
	NextStyle                        = 0x1C00348A
	WebPictureContainer14            = 0x200034C8
	ImageUploadState                 = 0x140034CB
	TextExtendedAscii                = 0x1C003498
	PictureWidth                     = 0x140034CD
	PictureHeight                    = 0x140034CE
	TaskTagDueDate                   = 0x1400346B

	AsciiNumberListFormat_Undocumented = 0x1C001CDA
	PredefinedParagraphStyles        = 0x240034D8 # Need to drop from XML
	NotebookColor                    = 0x14001CBE
	TOCEntryIndex_OidIndex           = 0x24001CF6
	FileIdentityGuid                 = 0x1C001D94
	NotebookElementOrderingID        = 0x14001CB9
	FolderChildFilename              = 0x1C001D6B
	AuthorInitials                   = 0x1C001DF8
	NotebookSectionName_Undocumented = 0x1C001D69
	AudioRecordingGuid               = 0x1C001C97
	AudioRecordingGuids              = 0x1C001CA3
	AudioRecordingDuration           = 0x14001CFD
