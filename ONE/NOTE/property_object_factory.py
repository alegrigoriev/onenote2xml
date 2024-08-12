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
from ..property_id import *
from ..STORE.property import Property
from ..base_types import *
from ..property_pretty_print import *

class PropertyObject:
	PROPERTY_ID_CLASS = PropertyID

	def __init__(self, _property:Property, key = None, key_string=None, data=None, value=None, str_value=None, display_value=None):
		self.data_type:int = _property.data_type
		self.property_id:int = _property.property_id
		if key is None:
			property_id_class = type(self).PROPERTY_ID_CLASS
			if property_id_class is not NotImplemented:
				try:
					property_id = property_id_class(_property.property_id)
					key = property_id.name
				except ValueError:
					pass
		if key is None:
			key = _property.property_id
			if key_string is None:
				key_string = "Property_%X" % (key,)
		elif key_string is None:
			key_string = key
		self.key:str|int = key
		self.key_string:str = key_string

		if data is None:
			data = _property.data
		self.data:bytes = data	# raw data

		if value is None:
			value = _property.value
		self.value = value	# usable value or array of values from raw data

		if str_value is None:
			str_value = _property.str_value
		self.str_value:str|list[str] = str_value	# value or array of values in string form

		if display_value is None:
			display_value = _property.display_value
		self.display_value = display_value	# Single string to display the value

		return

	def make_object(self, property_set_obj, revision_ctx):
		'''
		property_set_obj is the parent property set
		'''
		return

	def get_object_value(self):
		# Used in property set __getattr__ method
		return self.value

	def __iter__(self):
		# Iterate over all attributes recursively
		yield (), self
		# By default there's no sub-objects
		return
	def update_hash(self, md5hash):
		md5hash.update(self.property_id.to_bytes(4, byteorder='little', signed=False))
		return

class NoDataPropertyObject(PropertyObject): ...

class BoolPropertyObject(PropertyObject):

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(b'\1' if self.value else b'\0')
		return

class PropertyObject1To8bytesData(PropertyObject):

	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.int_value = _property.value
		return

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.data).to_bytes(4, byteorder='little', signed=False))
		md5hash.update(self.data)
		return

class IntPropertyObject(PropertyObject1To8bytesData): ...

class FourBytesOfLengthFollowedByDataPropertyObject(PropertyObject):
	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.data).to_bytes(4, byteorder='little', signed=False))
		md5hash.update(self.data)
		return

class ArrayOfObjectIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.oids = self.value
		return

	def make_object(self, property_set_obj, revision_ctx):
		self.value = []
		min_verbosity = None
		for oid in self.oids:
			# oid can be None
			obj = revision_ctx.GetObjectReference(oid)
			self.value.append(obj)
			# GetObjectReference returns None for None oid
			if obj is not None and \
				(min_verbosity is None or min_verbosity > obj.min_verbosity):
				# Find lowest verbosity of the child elements
				min_verbosity = obj.min_verbosity

		if min_verbosity is None:
			# empty
			self.min_verbosity = 4
		elif self.min_verbosity < min_verbosity:
			# Only increase this attribute min_verbosity level
			self.min_verbosity = min_verbosity
		return

	def __iter__(self):
		# Iterate over all objects recursively
		for obj in self.value:
			if obj is not None:
				yield from obj
		return

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.value).to_bytes(4, byteorder='little', signed=False))
		for obj in self.value:
			if obj is not None and obj.min_verbosity <= self.min_verbosity:
				md5hash.update(obj.get_hash())
		return

class ObjectIDPropertyObject(ArrayOfObjectIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			return self.value[0]
		else:
			return None

class ArrayOfObjectSpaceIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.osids = self.value
		return

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.value).to_bytes(4, byteorder='little', signed=False))
		return

class ObjectSpaceIDPropertyObject(ArrayOfObjectSpaceIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

class ArrayOfContextIDsPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.ctxids = self.value
		return

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.value).to_bytes(4, byteorder='little', signed=False))
		return

class ContextIDPropertyObject(ArrayOfContextIDsPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

class ArrayOfPropertyValuesPropertyObject(PropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.propsets = self.value
		return

	def update_hash(self, md5hash):
		super().update_hash(md5hash)
		md5hash.update(len(self.value).to_bytes(4, byteorder='little', signed=False))
		for obj in self.value:
			if obj.min_verbosity <= self.min_verbosity:
				md5hash.update(obj.get_hash())
		return

	def make_object(self, property_set_obj, revision_ctx):
		self.value = []
		for propset in self.propsets:
			self.value.append(revision_ctx.MakeObject(propset, None))
		return

class PropertySetPropertyObject(ArrayOfPropertyValuesPropertyObject):
	def get_object_value(self):
		if self.value:
			assert(len(self.value) == 1)
			return self.value[0]
		else:
			return None

class RgOutlineIndentDistance(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = RgOutlineIndentDistanceDecode(self.data)
		self.str_value = FormatFloatArray(self.value)
		self.display_value = ','.join(self.str_value)
		return

class TableColumnWidthsPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = TableColumnWidthsPropertyDecode(self.data)
		self.str_value = FormatFloatArray(self.value)
		self.display_value = ','.join(self.str_value)
		return

class TableColumnsLockedPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = TableColumnsLockedPropertyDecode(self.data)
		self.str_value = FormatIntArray(self.value)
		self.display_value = ','.join(self.str_value)
		return

class TextRunIndexProperty(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = TextRunIndexPropertyDecode(self.data)
		self.str_value = FormatIntArray(self.value)
		self.display_value = ','.join(self.str_value)
		return

class FiletimePropertyObject(PropertyObject1To8bytesData):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.display_value = str(GetFiletime64Datetime(self.value))
		return

class Time32PropertyObject(PropertyObject1To8bytesData):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.display_value = str(GetTime32Datetime(self.value))
		return

class FloatPropertyObject(PropertyObject1To8bytesData):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = UnpackFloat32(self.data)
		self.int_value = self.value
		self.str_value = '%#.7G' % (self.value,)
		self.display_value = self.str_value
		return

class WideStrPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = Utf16BytesToStr(self.data)
		self.str_value = self.value
		self.display_value = '"%s"' % (self.str_value,)
		return

class NumberListFormatProperty(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		# Unlike WideStrPropertyObject, the first byte specifies number of characters
		num_chars = self.data[0] + self.data[1] * 256
		# Note that 0x2022 codepoint is a bullet character,
		# 0x25CB codepoint is a white ring character,
		self.value = Utf16BytesToStr(self.data[2:2+num_chars*2])
		self.str_value = self.value
		self.display_value = '"%s"' % (self.value,)
		return

class MultibyteStrProperty(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = MbcsBytesToStr(self.data, 1033, 0) #prop_set[PropertyID.RichEditTextLangID])
		self.str_value = self.value
		self.display_value = '"%s"' % (self.value,)
		return

class GuidPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = GUID(self.data)
		self.str_value = str(self.value)
		self.display_value = self.str_value
		return

class GuidArrayPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = []
		for i in range(0, len(self.data), 16):
			self.value.append(GUID(self.data[i:i+16]))
		self.str_value = str(self.value)
		self.display_value = self.str_value
		return

class ExGuidPropertyObject(FourBytesOfLengthFollowedByDataPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)

		self.value = ExGUID(self.data[0:16], int.from_bytes(self.data[16:20], byteorder="little", signed=False))
		self.str_value = str(self.value)
		self.display_value = self.str_value
		return

class ColorrefPropertyObject(IntPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		int_value = self.int_value

		if int_value == 0xFF000000:
			self.value = None
			self.str_value = None
		else:
			self.value = SimpleNamespace(
				R=int_value & 0xFF,
				G=(int_value >> 8) & 0xFF,
				B=(int_value >> 16) & 0xFF,
				)
			self.str_value = '#%06x' % (int_value & 0xFFFFFF)

		self.display_value = ColorrefString(int_value)
		return

class ColorPropertyObject(IntPropertyObject):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		int_value = self.int_value

		if int_value == 0xFFFFFFFF:
			self.value = None
			self.str_value = None
		else:
			self.value = SimpleNamespace(
				R=int_value & 0xFF,
				G=(int_value >> 8) & 0xFF,
				B=(int_value >> 16) & 0xFF,
				A=(int_value >> 24) & 0xFF,
				)
			self.str_value = '#%08x' % (int_value & 0xFFFFFF)

		self.display_value = ColorString(int_value)
		return

class LayoutAlignmentProperty(PropertyObject1To8bytesData):
	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		int_value = self.int_value

		if int_value == 0 or (int_value & 0x80000000):
			self.value = None
		else:
			self.value = SimpleNamespace(
				HorizontalAlignment=int_value & 7,
				fHorizMargin=(int_value & 0x8) >> 3,
				VerticalAlignment=(int_value & 0x10000) >> 16,
				fVertMargin=(int_value & 0x80000) >> 19,
				)
		self.display_value = LayoutAlignmentString(int_value)
		return

class LayoutAlignmentInParentProperty(LayoutAlignmentProperty):

	def make_object(self, property_set_obj, revision_ctx):
		if hasattr(property_set_obj, 'LayoutAlignmentSelf'):
			self.min_verbosity = 4
		return

from win32api import GetUserDefaultLangID
DefaultLangID = GetUserDefaultLangID()
class LanguageIDObject(IntPropertyObject):

	def __init__(self, _property:Property, **kwargs):
		super().__init__(_property, **kwargs)
		self.str_value = "0x%X" % (self.int_value,)
		self.display_value = self.str_value
		return

	def make_object(self, property_set_obj, revision_ctx):
		if self.int_value == DefaultLangID:
			self.min_verbosity = 4
		return

class RichEditTextLangIDObject(LanguageIDObject): ...

class CharsetObject(IntPropertyObject):

	def make_object(self, property_set_obj, revision_ctx):
		if self.int_value == 1:  # DEFAULT_CHARSET
			self.min_verbosity = 4
		return

OneNotebookPropertyFactoryDict = {
	int(PropertyID.PageWidth) : FloatPropertyObject,  # 0x14001C01
	int(PropertyID.PageHeight) : FloatPropertyObject,  # 0x14001C02
	int(PropertyID.Font) : WideStrPropertyObject,  # 0x1C001C0A
	int(PropertyID.FontColor) : ColorrefPropertyObject,  # 0x14001C0C
	int(PropertyID.Highlight) : ColorrefPropertyObject,  # 0x14001C0D
	int(PropertyID.RgOutlineIndentDistance) : RgOutlineIndentDistance,  # 0x1C001C12
	int(PropertyID.OffsetFromParentHoriz) : FloatPropertyObject,  # 0x14001C14
	int(PropertyID.OffsetFromParentVert) : FloatPropertyObject,  # 0x14001C15
	int(PropertyID.NumberListFormat) : NumberListFormatProperty,  # 0x1C001C1A
	int(PropertyID.LayoutMaxWidth) : FloatPropertyObject,  # 0x14001C1B
	int(PropertyID.LayoutMaxHeight) : FloatPropertyObject,  # 0x14001C1C
	int(PropertyID.RichEditTextUnicode) : WideStrPropertyObject,  # 0x1C001C22  Hyperlink target starts with code point 0xFDDF, then "HYPERLINK "
	# NotebookManagementEntityGuid:
	# The GUID can be used to construct a hyperlink to a page (section 1.3.2).
	# It MUST NOT be used to construct a hyperlink to a section (section 1.3.1).
	int(PropertyID.NotebookManagementEntityGuid) : GuidPropertyObject,  # 0x1C001C30.
	int(PropertyID.LayoutAlignmentInParent) : LayoutAlignmentInParentProperty,  # 0x14001C3E
	int(PropertyID.PageMarginTop) : FloatPropertyObject,  # 0x14001C4C
	int(PropertyID.PageMarginBottom) : FloatPropertyObject,  # 0x14001C4D
	int(PropertyID.PageMarginLeft) : FloatPropertyObject,  # 0x14001C4E
	int(PropertyID.PageMarginRight) : FloatPropertyObject,  # 0x14001C4F
	int(PropertyID.ListFont) : WideStrPropertyObject,  # 0x1C001C52
	int(PropertyID.TopologyCreationTimeStamp) : FiletimePropertyObject,  # 0x18001C65
	int(PropertyID.LayoutAlignmentSelf) : LayoutAlignmentProperty,  # 0x14001C84
	int(PropertyID.ListSpacingMu) : FloatPropertyObject,  # 0x14001CCB
	int(PropertyID.LayoutOutlineReservedWidth) : FloatPropertyObject,  # 0x14001CDB
	int(PropertyID.LayoutMinimumOutlineWidth) : FloatPropertyObject,  # 0x14001CEC
	int(PropertyID.CachedTitleString) : WideStrPropertyObject,  # 0x1C001CF3
	int(PropertyID.CreationTimeStamp) : Time32PropertyObject,  # 0x14001D09
	int(PropertyID.CachedTitleStringFromPage) : WideStrPropertyObject,  # 0x1C001D3C
	int(PropertyID.TableColumnWidths) : TableColumnWidthsPropertyObject,  # 0x1C001D66
	int(PropertyID.Author) : WideStrPropertyObject,  # 0x1C001D75
	0x1C001E5D : WideStrPropertyObject,
	int(PropertyID.LastModifiedTimeStamp) : FiletimePropertyObject,  # 0x18001D77
	int(PropertyID.LastModifiedTime) : Time32PropertyObject,  # 0x14001D7A
	int(PropertyID.TableColumnsLocked) : TableColumnsLockedPropertyObject,  # 0x1C001D7D
	int(PropertyID.EmbeddedFileName) : WideStrPropertyObject,  # 0x1C001D9C
	int(PropertyID.SourceFilepath) : WideStrPropertyObject,  # 0x1C001D9D
	int(PropertyID.ConflictingUserName) : WideStrPropertyObject,  # 0x1C001D9E
	int(PropertyID.ConflictingUserInitials) : WideStrPropertyObject,  # 0x1C001D9F
	int(PropertyID.ImageFilename) : WideStrPropertyObject,  # 0x1C001DD7
	int(PropertyID.TextRunIndex) : TextRunIndexProperty,  # 0x1C001E12
	int(PropertyID.CellShadingColor) : ColorrefPropertyObject,  # COLORREF 0x14001e26
	int(PropertyID.ImageAltText) : WideStrPropertyObject,  # 0x1C001E58
	int(PropertyID.ParagraphSpaceBefore) : FloatPropertyObject,  # 0x1400342E
	int(PropertyID.ParagraphSpaceAfter) : FloatPropertyObject,  # 0x1400342F
	int(PropertyID.ParagraphLineSpacingExact) : FloatPropertyObject,  # 0x14003430
	int(PropertyID.ParagraphStyleId) : WideStrPropertyObject,  # 0x1C00345A
	int(PropertyID.NoteTagHighlightColor) : ColorrefPropertyObject,  # COLORREF 0x14003465
	int(PropertyID.NoteTagTextColor) : ColorrefPropertyObject,  # COLORREF 0x14003466
	int(PropertyID.NoteTagLabel) : WideStrPropertyObject,  # 0x1C003468
	int(PropertyID.NoteTagCreated) : Time32PropertyObject,  # Time32 0x1400346E
	int(PropertyID.NoteTagCompleted) : Time32PropertyObject,  # Time32 0x1400346F
	int(PropertyID.SectionDisplayName) : WideStrPropertyObject,  # 0x1C00349B
	int(PropertyID.NextStyle) : WideStrPropertyObject,  # 0x1C00348A
	int(PropertyID.TextExtendedAscii) : MultibyteStrProperty,  # 0x1C003498, uses preceding RichEditTextLangID
	0x1C0035CD : ExGuidPropertyObject,  # 0x1C0035CD
	int(PropertyID.PictureWidth) : FloatPropertyObject,  # 0x140034CD
	int(PropertyID.PictureHeight) : FloatPropertyObject,  # 0x140034CE
	int(PropertyID.PageMarginOriginX) : FloatPropertyObject,  # 0x14001D0F
	int(PropertyID.PageMarginOriginY) : FloatPropertyObject,  # 0x14001D10
	int(PropertyID.WzHyperlinkUrl) : WideStrPropertyObject,  # 0x1C001E20
	int(PropertyID.TaskTagDueDate) : Time32PropertyObject,  # 0x1400346B
	int(PropertyID.RichEditTextLangID) : RichEditTextLangIDObject,  # 0x10001CFE
	int(PropertyID.LanguageID) : LanguageIDObject,  # 0x14001C3B
	int(PropertyID.Charset) : CharsetObject,  # 0x0C001D01
	int(PropertyID.AudioRecordingGuid): GuidPropertyObject,
	int(PropertyID.AudioRecordingGuids): GuidArrayPropertyObject,
	0x1C001C98 : GuidPropertyObject,
	0x1C005010 : ExGuidPropertyObject,  # 0x1C005010
	#int(PropertyID.IsDeletedGraphSpaceContent) : Property,  # 0x1C001DE9 - Bytes with count
	0x1C001E30 : WideStrPropertyObject,  # Azure account XML metadata?
	0x1C001E5B : WideStrPropertyObject,
	0x14001C9E : FloatPropertyObject,
	0x14001C9F : FloatPropertyObject,
	0x14001CA0 : FloatPropertyObject,
	0x14001CA1 : FloatPropertyObject,
	int(PropertyID.AsciiNumberListFormat_Undocumented) : NumberListFormatProperty,
	int(PropertyID.AuthorInitials) : WideStrPropertyObject, # 0x1C001D94
	int(PropertyID.NotebookSectionName_Undocumented) : WideStrPropertyObject, # 0x1C001D69
	int(PropertyID.NotebookColor): ColorPropertyObject, # 0x14001CBE
	int(PropertyID.VersionHistoryGraphSpaceContextNodes) : ObjectSpaceIDPropertyObject, # Treat as a single pointer
	}

DataTypeObjectFactoryDict = {
	int(PropertyTypeID.NoData) : NoDataPropertyObject, # 0x01
	int(PropertyTypeID.Bool) : BoolPropertyObject, # 0x02
	int(PropertyTypeID.OneByteOfData) : PropertyObject1To8bytesData, # 0x03
	int(PropertyTypeID.TwoBytesOfData) : PropertyObject1To8bytesData, # 0x04
	int(PropertyTypeID.FourBytesOfData) : PropertyObject1To8bytesData, # 0x05
	int(PropertyTypeID.EightBytesOfData) : PropertyObject1To8bytesData, # 0x06
	int(PropertyTypeID.FourBytesOfLengthFollowedByData) : FourBytesOfLengthFollowedByDataPropertyObject, # 0x07
	int(PropertyTypeID.ObjectID) : ObjectIDPropertyObject, # 0x08
	int(PropertyTypeID.ArrayOfObjectIDs) : ArrayOfObjectIDsPropertyObject, # 0x09
	int(PropertyTypeID.ObjectSpaceID) : ObjectSpaceIDPropertyObject, # 0x0A
	int(PropertyTypeID.ArrayOfObjectSpaceIDs) : ArrayOfObjectSpaceIDsPropertyObject, # 0x0B
	int(PropertyTypeID.ContextID) : ContextIDPropertyObject, # 0x0C
	int(PropertyTypeID.ArrayOfContextIDs) : ArrayOfContextIDsPropertyObject, # 0x0D
	int(PropertyTypeID.ArrayOfPropertyValues) : ArrayOfPropertyValuesPropertyObject, # 0x10
	int(PropertyTypeID.PropertySet) : PropertySetPropertyObject, # 0x11
	}

OneToc2PropertyFactoryDict = {
	int(PropertyID.FileIdentityGuid) : GuidPropertyObject, # 0x1C001D94
	int(PropertyID.FolderChildFilename) : WideStrPropertyObject, # 0x1C001D6B
	int(PropertyID.NotebookColor): ColorPropertyObject, # 0x14001CBE
	}

class PropertyObjectFactory:
	def __init__(self, property_dict:dict={}, property_id_class=PropertyID, default_class=PropertyObject):
		self.property_dict = property_dict
		self.property_id_class = property_id_class
		self.default_class = default_class
		return

	def get_property_id_class(self):
		return self.property_id_class

	def get_property_class(self, property_obj:Property):
		property_class = self.property_dict.get(property_obj.property_id, None)

		if property_class is None:
			property_class = DataTypeObjectFactoryDict.get(property_obj.data_type, self.default_class)
		return property_class

	def __call__(self, property_obj:Property, **kwargs):
		return self.get_property_class(property_obj)(property_obj, **kwargs)

OneNotebookPropertyFactory = PropertyObjectFactory(OneNotebookPropertyFactoryDict)
# For both TOC directory (upper level) and TOC sections:
OneToc2PropertyFactory = PropertyObjectFactory(OneToc2PropertyFactoryDict)
