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
from .property_id import PropertyID, PropertyTypeID
from .STORE.property import Property
from .base_types import *

def BoolPropertyString(property_obj:Property):
	return property_obj.display_value

def NoDataPropertyString(property_obj:Property):
	return 'None'

def RgOutlineIndentDistanceDecode(data:bytes):
	value = []
	count = data[0]  # 3 bytes are ignored
	for i in range(4, count*4+4, 4):
		if i + 4 > len(data):
			break
		# Some OneNote versions incorrectly modify RgOutlineIndentDistance property,
		# which produced a random 'subnormal' floating point number,
		# for example 1.401298E-45, or very small number such as 2.723866E-19.
		if (data[i+3] & 0x7F) <= 0x20:
			value.append(0.0)
		else:
			value.append(UnpackFloat32(data[i:i+4]))
		continue

	return value

def TableColumnWidthsPropertyDecode(data:bytes):
	value = []
	count = data[0]  # Single byte count
	for i in range(1, count*4+1, 4):
		if i + 4 > len(data):
			break
		value.append(UnpackFloat32(data[i:i+4]))
		continue

	return value

def TableColumnsLockedPropertyDecode(data:bytes):
	value = []

	count = data[0]  # Single byte count
	word = int.from_bytes(data[1:], byteorder="little", signed=False)
	for _ in range(count):
		value.append(word & 1)
		word >>= 1
		continue

	return value

def TextRunIndexPropertyDecode(data:bytes):
	value = []
	for i in range(0, len(data), 4):
		if i + 4 > len(data):
			break
		value.append(int.from_bytes(data[i:i+4], byteorder="little", signed=False))
		continue

	return value

def ColorrefString(int_value):
	if int_value == 0xFF000000:
		return "%X (auto)" % (int_value,)

	return "R:%02X G:%02X B:%02X" % (
		int_value & 0xFF,
		(int_value >> 8) & 0xFF,
		(int_value >> 16) & 0xFF)

def ColorString(int_value):
	if int_value == 0xFFFFFFFF:
		return "%X (ignore)" % (int_value,)

	return "R:%02X G:%02X B:%02X A:%02X" % (
		int_value & 0xFF,
		(int_value >> 8) & 0xFF,
		(int_value >> 16) & 0xFF,
		(int_value >> 24) & 0xFF)

def LayoutAlignmentString(int_value):
	if int_value == 0 or (int_value & 0x80000000):
		return "%X (invalid)" % (int_value,)

	HorizontalAlignment = int_value & 7
	fHorizMargin = (int_value & 0x8) >> 3
	VerticalAlignment = (int_value & 0x10000) >> 16
	fVertMargin = (int_value & 0x80000) >> 19

	if HorizontalAlignment == 1:
		hor_align = "Left"
	elif HorizontalAlignment == 2:
		hor_align = "Center"
	elif HorizontalAlignment == 3:
		hor_align = "Right"
	elif HorizontalAlignment == 4:
		hor_align = "StartOfLine"
	elif HorizontalAlignment == 5:
		hor_align = "EndOfLine"
	else:
		hor_align = str(HorizontalAlignment)
	return "Hor:%s, HorMargin:%s, Vert:%s, VertMargin:%s" % (
		hor_align, "StartOfLine" if fHorizMargin else "EndOfLine",
		"Top" if VerticalAlignment else "Bottom",
		"Top" if fVertMargin else "Bottom",
		)

def FormatFloatArray(float_array:list):
	return list(("%#.7G" % (f,)) for f in float_array)

def FormatIntArray(int_array:list):
	return list(str(i) for i in int_array)

def RgOutlineIndentDistancePropertyString(property_obj:Property):
	float_array = RgOutlineIndentDistanceDecode(property_obj.data)
	return ','.join(FormatFloatArray(float_array))

def TableColumnWidthsPropertyString(property_obj:Property):
	float_array = TableColumnWidthsPropertyDecode(property_obj.data)
	return ','.join(FormatFloatArray(float_array))

def TableColumnsLockedPropertyString(property_obj:Property):
	int_array = TableColumnsLockedPropertyDecode(property_obj.data)
	return ','.join(FormatIntArray(int_array))

def TextRunIndexPropertyString(property_obj:Property):
	int_array = TextRunIndexPropertyDecode(property_obj.data)
	return ','.join(FormatIntArray(int_array))

def IntPropertyString(property_obj:Property):
	return str(property_obj.int_value)

def FiletimePropertyString(property_obj:Property):
	return str(GetFiletime64Datetime(property_obj.value))

def Time32PropertyString(property_obj:Property):
	return str(GetTime32Datetime(property_obj.value))

def FloatPropertyString(property_obj:Property):
	value = UnpackFloat32(property_obj.data)
	return '%#.7G' % (value,)

def WideStrPropertyString(property_obj:Property):
	value = Utf16BytesToStr(property_obj.data)
	return '"%s"' % (value,)

def NumberListFormatPropertyString(property_obj:Property):
	# Unlike WideStrPropertyObject, the first byte specifies number of characters
	# Note that 0x2022 codepoint is a bullet character,
	# 0x25CB codepoint is a white ring character,
	num_chars = property_obj.data[0] + property_obj.data[1] * 256
	value = Utf16BytesToStr(property_obj.data[2:2+num_chars*2])
	return '"%s"' % (value,)

def MultibyteStrPropertyString(property_obj:Property):
	value = MbcsBytesToStr(property_obj.data, 1033, 0)
	return '"%s"' % (value,)

def GuidPropertyString(property_obj:Property):
	return str(GUID(property_obj.data))

def ExGuidPropertyString(property_obj:Property):
	return str(ExGUID(property_obj.data[0:16],
		int.from_bytes(property_obj.data[16:20], byteorder="little", signed=False)))

def ColorrefPropertyString(property_obj:Property):
	return ColorrefString(property_obj.value)

def ColorPropertyString(property_obj:Property):
	return ColorString(property_obj.value)

def LayoutAlignmentPropertyString(property_obj:Property):
	return LayoutAlignmentString(property_obj.value)

OneNotePropertyStringDict = {
	int(PropertyID.PageWidth) : FloatPropertyString,  # 0x14001C01
	int(PropertyID.PageHeight) : FloatPropertyString,  # 0x14001C02
	int(PropertyID.Font) : WideStrPropertyString,  # 0x1C001C0A
	int(PropertyID.FontColor) : ColorrefPropertyString,  # 0x14001C0C
	int(PropertyID.Highlight) : ColorrefPropertyString,  # 0x14001C0D
	int(PropertyID.RgOutlineIndentDistance) : RgOutlineIndentDistancePropertyString,  # 0x1C001C12
	int(PropertyID.OffsetFromParentHoriz) : FloatPropertyString,  # 0x14001C14
	int(PropertyID.OffsetFromParentVert) : FloatPropertyString,  # 0x14001C15
	int(PropertyID.NumberListFormat) : NumberListFormatPropertyString,  # 0x1C001C1A
	int(PropertyID.LayoutMaxWidth) : FloatPropertyString,  # 0x14001C1B
	int(PropertyID.LayoutMaxHeight) : FloatPropertyString,  # 0x14001C1C
	int(PropertyID.RichEditTextUnicode) : WideStrPropertyString,  # 0x1C001C22  Hyperlink target starts with code point 0xFDDF, then "HYPERLINK "
	# NotebookManagementEntityGuid:
	# The GUID can be used to construct a hyperlink to a page (section 1.3.2).
	# It MUST NOT be used to construct a hyperlink to a section (section 1.3.1).
	int(PropertyID.NotebookManagementEntityGuid) : GuidPropertyString,  # 0x1C001C30.
	int(PropertyID.LayoutAlignmentInParent) : LayoutAlignmentPropertyString,  # 0x14001C3E
	int(PropertyID.PageMarginTop) : FloatPropertyString,  # 0x14001C4C
	int(PropertyID.PageMarginBottom) : FloatPropertyString,  # 0x14001C4D
	int(PropertyID.PageMarginLeft) : FloatPropertyString,  # 0x14001C4E
	int(PropertyID.PageMarginRight) : FloatPropertyString,  # 0x14001C4F
	int(PropertyID.ListFont) : WideStrPropertyString,  # 0x1C001C52
	int(PropertyID.TopologyCreationTimeStamp) : FiletimePropertyString,  # 0x18001C65
	int(PropertyID.LayoutAlignmentSelf) : LayoutAlignmentPropertyString,  # 0x14001C84
	int(PropertyID.ListSpacingMu) : FloatPropertyString,  # 0x14001CCB
	int(PropertyID.LayoutOutlineReservedWidth) : FloatPropertyString,  # 0x14001CDB
	int(PropertyID.LayoutMinimumOutlineWidth) : FloatPropertyString,  # 0x14001CEC
	int(PropertyID.CachedTitleString) : WideStrPropertyString,  # 0x1C001CF3
	int(PropertyID.CreationTimeStamp) : Time32PropertyString,  # 0x14001D09
	int(PropertyID.CachedTitleStringFromPage) : WideStrPropertyString,  # 0x1C001D3C
	int(PropertyID.TableColumnWidths) : TableColumnWidthsPropertyString,  # 0x1C001D66
	int(PropertyID.Author) : WideStrPropertyString,  # 0x1C001D75
	0x1C001E5D : WideStrPropertyString,
	int(PropertyID.LastModifiedTimeStamp) : FiletimePropertyString,  # 0x18001D77
	int(PropertyID.LastModifiedTime) : Time32PropertyString,  # 0x14001D7A
	int(PropertyID.TableColumnsLocked) : TableColumnsLockedPropertyString,  # 0x1C001D7D
	int(PropertyID.EmbeddedFileName) : WideStrPropertyString,  # 0x1C001D9C
	int(PropertyID.SourceFilepath) : WideStrPropertyString,  # 0x1C001D9D
	int(PropertyID.ConflictingUserName) : WideStrPropertyString,  # 0x1C001D9E
	int(PropertyID.ConflictingUserInitials) : WideStrPropertyString,  # 0x1C001D9F
	int(PropertyID.ImageFilename) : WideStrPropertyString,  # 0x1C001DD7
	int(PropertyID.TextRunIndex) : TextRunIndexPropertyString,  # 0x1C001E12
	int(PropertyID.CellShadingColor) : ColorrefPropertyString,  # COLORREF 0x14001e26
	int(PropertyID.ImageAltText) : WideStrPropertyString,  # 0x1C001E58
	int(PropertyID.ParagraphSpaceBefore) : FloatPropertyString,  # 0x1400342E
	int(PropertyID.ParagraphSpaceAfter) : FloatPropertyString,  # 0x1400342F
	int(PropertyID.ParagraphLineSpacingExact) : FloatPropertyString,  # 0x14003430
	int(PropertyID.ParagraphStyleId) : WideStrPropertyString,  # 0x1C00345A
	int(PropertyID.NoteTagHighlightColor) : ColorrefPropertyString,  # COLORREF 0x14003465
	int(PropertyID.NoteTagTextColor) : ColorrefPropertyString,  # COLORREF 0x14003466
	int(PropertyID.NoteTagLabel) : WideStrPropertyString,  # 0x1C003468
	int(PropertyID.NoteTagCreated) : Time32PropertyString,  # Time32 0x1400346E
	int(PropertyID.NoteTagCompleted) : Time32PropertyString,  # Time32 0x1400346F
	int(PropertyID.SectionDisplayName) : WideStrPropertyString,  # 0x1C00349B
	int(PropertyID.NextStyle) : WideStrPropertyString,  # 0x1C00348A
	int(PropertyID.TextExtendedAscii) : MultibyteStrPropertyString,  # 0x1C003498, uses preceding RichEditTextLangID
	0x1C0035CD : ExGuidPropertyString,  # 0x1C0035CD
	int(PropertyID.PictureWidth) : FloatPropertyString,  # 0x140034CD
	int(PropertyID.PictureHeight) : FloatPropertyString,  # 0x140034CE
	int(PropertyID.PageMarginOriginX) : FloatPropertyString,  # 0x14001D0F
	int(PropertyID.PageMarginOriginY) : FloatPropertyString,  # 0x14001D10
	int(PropertyID.WzHyperlinkUrl) : WideStrPropertyString,  # 0x1C001E20
	int(PropertyID.TaskTagDueDate) : Time32PropertyString,  # 0x1400346B
	0x1C005010 : ExGuidPropertyString,  # 0x1C005010
	#int(PropertyID.IsDeletedGraphSpaceContent) : Property,  # 0x1C001DE9 - Bytes with count
	0x1C001E30 : WideStrPropertyString,  # Azure account XML metadata?
	0x1C001E5B : WideStrPropertyString,
	0x14001C9E : FloatPropertyString,
	0x14001C9F : FloatPropertyString,
	0x14001CA0 : FloatPropertyString,
	0x14001CA1 : FloatPropertyString,
	int(PropertyID.AsciiNumberListFormat_Undocumented) : NumberListFormatPropertyString,
	int(PropertyID.AuthorInitials) : WideStrPropertyString, # 0x1C001D94
	int(PropertyID.NotebookSectionName_Undocumented) : WideStrPropertyString, # 0x1C001D69
	int(PropertyID.FileIdentityGuid) : GuidPropertyString, # 0x1C001D94
	int(PropertyID.FolderChildFilename) : WideStrPropertyString, # 0x1C001D6B
	int(PropertyID.NotebookColor): ColorPropertyString, # 0x14001CBE
	}

DataTypeObjectFactoryDict = {
	int(PropertyTypeID.NoData) : NoDataPropertyString, # 0x01
	int(PropertyTypeID.Bool) : BoolPropertyString, # 0x02
	int(PropertyTypeID.OneByteOfData) : IntPropertyString, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : IntPropertyString, # 0x04
	int(PropertyTypeID.FourBytesOfData) : IntPropertyString, # 0x05
	int(PropertyTypeID.EightBytesOfData) : IntPropertyString, # 0x06
	}

def PropertyPrettyPrintString(property_obj:Property, verbose=None):
	pretty_print_func = OneNotePropertyStringDict.get(property_obj.property_id, None)

	if pretty_print_func is None:
		pretty_print_func = DataTypeObjectFactoryDict.get(property_obj.property_id, None)
		if pretty_print_func is None:
			return None

	return pretty_print_func(property_obj)
