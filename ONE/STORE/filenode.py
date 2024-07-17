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

from .reader import onestore_reader
from ..base_types import *
from ..exception import UnrecognizedFileNodeException, BaseTypeMismatchException, UnexpectedFileNodeException
from enum import IntEnum

'''
DEAR MICROSOFT DOCUMENTATION WRITER!

WHO THE FUCK THOUGHT IT'S A GOOD IDEA
TO SHOW THE LEAST SIGNIFICANT BIT FIRST
AND THE MOST SIGNIFICANT BIT LAST???

AND NOT EXPLICITLY EXPLAIN THAT CLUSTERFUCK ANYWHERE!!
'''

# FileNodeID values:
class FileNodeID(IntEnum):
	ObjectSpaceManifestRootFND = 0x004
	ObjectSpaceManifestListReferenceFND = 0x008
	ObjectSpaceManifestListStartFND = 0x00C
	RevisionManifestListReferenceFND = 0x010
	RevisionManifestListStartFND = 0x014
	RevisionManifestStart4FND = 0x01B
	RevisionManifestEndFND = 0x01C
	RevisionManifestStart6FND = 0x01E
	RevisionManifestStart7FND = 0x01F
	GlobalIdTableStartFNDX = 0x021
	GlobalIdTableStart2FND = 0x022
	GlobalIdTableEntryFNDX = 0x024
	GlobalIdTableEntry2FNDX = 0x025
	GlobalIdTableEntry3FNDX = 0x026
	GlobalIdTableEndFNDX = 0x028
	ObjectDeclarationWithRefCountFNDX = 0x02D
	ObjectDeclarationWithRefCount2FNDX = 0x02E
	ObjectRevisionWithRefCountFNDX = 0x041
	ObjectRevisionWithRefCount2FNDX = 0x042
	RootObjectReference2FNDX = 0x059
	RootObjectReference3FND = 0x05A
	RevisionRoleDeclarationFND = 0x05C
	RevisionRoleAndContextDeclarationFND = 0x05D
	ObjectDeclarationFileData3RefCountFND = 0x072
	ObjectDeclarationFileData3LargeRefCountFND = 0x073
	ObjectDataEncryptionKeyV2FNDX = 0x07C
	ObjectInfoDependencyOverridesFND = 0x084
	DataSignatureGroupDefinitionFND = 0x08C
	FileDataStoreListReferenceFND = 0x090
	FileDataStoreObjectReferenceFND = 0x094
	ObjectDeclaration2RefCountFND = 0x0A4
	ObjectDeclaration2LargeRefCountFND = 0x0A5
	ObjectGroupListReferenceFND = 0x0B0
	ObjectGroupStartFND = 0x0B4
	ObjectGroupEndFND = 0x0B8
	HashedChunkDescriptor2FND = 0x0C2
	ReadOnlyObjectDeclaration2RefCountFND = 0x0C4
	ReadOnlyObjectDeclaration2LargeRefCountFND = 0x0C5
	ChunkTerminatorFND = 0x0FF

class FileNode:
	BaseType = 0
	ID = NotImplemented
	NAME = NotImplemented

	def __init__(self, reader:onestore_reader):
		return

	def dump(self, fd):
		print("\n%s (0x%03X)" % (self.ID.name, self.ID.value), file=fd)
		return

class FileNode1(FileNode):
	BaseType = 1

class FileNode2(FileNode):
	BaseType = 2

class ObjectSpaceManifestRootFND(FileNode):
	ID = FileNodeID.ObjectSpaceManifestRootFND

	def __init__(self, reader:onestore_reader):
		self.gosidRoot = ExGUID().read(reader)
		return

class ObjectSpaceManifestListReferenceFND(FileNode2):
	ID = FileNodeID.ObjectSpaceManifestListReferenceFND

	def __init__(self, reader, ref):
		self.ref = ref
		self.gosid = ExGUID().read(reader)
		return

class ObjectSpaceManifestListStartFND(FileNode):
	ID = FileNodeID.ObjectSpaceManifestListStartFND

	def __init__(self, reader:onestore_reader):
		self.gosidRoot = ExGUID().read(reader)
		return

class RevisionManifestListReferenceFND(FileNode2):
	ID = FileNodeID.RevisionManifestListReferenceFND

	def __init__(self, reader, ref):
		self.ref = ref
		return

class RevisionManifestListStartFND(FileNode):
	ID = FileNodeID.RevisionManifestListStartFND

	def __init__(self, reader:onestore_reader):
		self.gosidRoot = ExGUID().read(reader)
		self.nInstance = reader.read_uint32()	# always ignored
		return

class RevisionManifestStart4FND(FileNode):
	ID = FileNodeID.RevisionManifestStart4FND

	def __init__(self, reader:onestore_reader):
		self.rid = ExGUID().read(reader)
		self.ridDependent = ExGUID().read(reader)
		self.timeCreation = reader.read_uint64()	# always ignored
		self.RevisionRole = reader.read_uint32()
		self.odcsDefault = reader.read_uint16()	# always ignored
		return

class RevisionManifestStart6FND(FileNode):
	ID = FileNodeID.RevisionManifestStart6FND

	def __init__(self, reader:onestore_reader):
		self.rid = ExGUID().read(reader)
		self.ridDependent = ExGUID().read(reader)
		self.RevisionRole = reader.read_uint32()
		# 0 - unencrypted;
		# 2 - encrypted. Property sets within this revision manifest MUST be ignored and MUST NOT be altered.
		self.odcsDefault = reader.read_uint16()
		return

class RevisionManifestStart7FND(RevisionManifestStart6FND):
	ID = FileNodeID.RevisionManifestStart7FND

	def __init__(self, reader):
		super().__init__(reader)
		self.gctxid = ExGUID().read(reader)
		return

class GlobalIdTableStartFNDX(FileNode):
	ID = FileNodeID.GlobalIdTableStartFNDX

	def __init__(self, reader:onestore_reader):
		self.Reserved = reader.read_bytes(1)
		return

class GlobalIdTableEntryFNDX(FileNode):
	ID = FileNodeID.GlobalIdTableEntryFNDX

	def __init__(self, reader:onestore_reader):
		self.index = reader.read_uint32()
		self.guid = GUID().read(reader)
		return

class GlobalIdTableEntry2FNDX(FileNode):
	ID = FileNodeID.GlobalIdTableEntry2FNDX

	def __init__(self, reader:onestore_reader):
		self.iIndexMapFrom = reader.read_uint32()
		self.iIndexMapTo = reader.read_uint32()
		return

class GlobalIdTableEntry3FNDX(FileNode):
	ID = FileNodeID.GlobalIdTableEntry3FNDX

	def __init__(self, reader:onestore_reader):
		self.iIndexCopyFromStart = reader.read_uint32()
		self.cEntriesToCopy = reader.read_uint32()
		self.iIndexCopyToStart = reader.read_uint32()
		return

class ObjectRevisionWithRefCountFNDX(FileNode1):
	ID = FileNodeID.ObjectRevisionWithRefCountFNDX

	def __init__(self, reader, ref):
		self.jcid = None
		self.ref = ref
		self.coid = CompactID(reader)
		b = reader.read_uint8()
		self.fHasOidReferences = (b & 1) != 0
		self.fHasOsidReferences = (b & 2) != 0
		self.prop_set = None
		self.cRef = b >> 2
		# Object's JCID is inherited from the existing definition
		return

class ObjectRevisionWithRefCount2FNDX(FileNode1):
	ID = FileNodeID.ObjectRevisionWithRefCount2FNDX

	def __init__(self, reader, ref):
		self.jcid = None
		self.ref = ref
		self.coid = CompactID(reader)
		b = reader.read_uint32()
		self.fHasOidReferences = (b & 1) != 0
		self.fHasOsidReferences = (b & 2) != 0
		self.cRef = reader.read_uint32()
		self.prop_set = None
		return

class RootObjectReference2FNDX(FileNode):
	ID = FileNodeID.RootObjectReference2FNDX

	def __init__(self, reader:onestore_reader):
		self.coidRoot = CompactID(reader)
		self.RootRole = reader.read_uint32()
		return

class RootObjectReference3FND(FileNode):
	ID = FileNodeID.RootObjectReference3FND

	def __init__(self, reader:onestore_reader):
		self.oidRoot = ExGUID().read(reader)
		self.RootRole = reader.read_uint32()
		return

class RevisionRoleDeclarationFND(FileNode):
	ID = FileNodeID.RevisionRoleDeclarationFND

	def __init__(self, reader:onestore_reader):
		self.rid = ExGUID().read(reader)
		self.RevisionRole = reader.read_uint32()
		return

class RevisionRoleAndContextDeclarationFND(RevisionRoleDeclarationFND):
	ID = FileNodeID.RevisionRoleAndContextDeclarationFND

	def __init__(self, reader):
		super().__init__(reader)
		self.gctxid = ExGUID().read(reader)
		return

class ObjectDataEncryptionKeyV2FNDX(FileNode1):
	ID = FileNodeID.ObjectDataEncryptionKeyV2FNDX

	def __init__(self, reader, ref):
		self.ref = ref
		return

class ObjectInfoDependencyOverride8:

	def __init__(self, reader:onestore_reader):
		self.coid = CompactID(reader)
		self.cRef = reader.read_uint8()
		return

class ObjectInfoDependencyOverride32:

	def __init__(self, reader:onestore_reader):
		self.coid = CompactID(reader)
		self.cRef = reader.read_uint32()
		return

class ObjectInfoDependencyOverrideData:

	def __init__(self, reader:onestore_reader):
		c8BitOverrides = reader.read_uint32()
		c32BitOverrides = reader.read_uint32()
		self.crc = reader.read_uint32()

		self.overrides = []
		for _ in range(c8BitOverrides):
			o = ObjectInfoDependencyOverride8(reader)
			self.overrides.append(o)
		for _ in range(c32BitOverrides):
			o = ObjectInfoDependencyOverride32(reader)
			self.overrides.append(o)

		return

class ObjectInfoDependencyOverridesFND(FileNode1):
	ID = FileNodeID.ObjectInfoDependencyOverridesFND

	def __init__(self, reader, ref):
		self.ref = ref
		if self.ref.isNil():
			self.overrides = ObjectInfoDependencyOverrideData(reader)
		else:
			self.overrides = None   # TODO: Read from the root reader
		return

class FileDataStoreListReferenceFND(FileNode2):
	ID = FileNodeID.FileDataStoreListReferenceFND

	def __init__(self, reader, ref):
		self.ref = ref
		return

class FileDataStoreObjectReferenceFND(FileNode1):
	ID = FileNodeID.FileDataStoreObjectReferenceFND

	def __init__(self, reader, ref):
		self.ref = ref
		self.guidReference = GUID().read(reader)
		self.data_store_object = None
		return

class ObjectDeclarationWithRefCountBody:

	def __init__(self, reader:onestore_reader):
		self.coid = CompactID(reader)

		w = reader.read_uint16()
		jci = w & 0x3FF
		assert(jci == 1)
		# When only index is specified, the other fields of JCID MUST be implied as set to:
		#  JCID.IsBinary = "false",
		#  JCID.IsPropertySet = "true",
		#  JCID.IsGraphNode = "false",
		#  JCID.IsFileData = "false",
		#  and JCID.IsReadOnly = "false".
		self.jcid = JCID(jci | 0x00020000)
		self.odcs = w & 0x3C00
		w = reader.read_uint32()
		self.fHasOidReferences = (w & 1) != 0
		self.fHasOsidReferences = (w & 2) != 0
		return

class ObjectDeclarationWithRefCountFNDX(FileNode1):
	ID = FileNodeID.ObjectDeclarationWithRefCountFNDX
	cRefReadFunc = onestore_reader.read_uint8

	def __init__(self, reader, ref):
		self.ObjectRef = ref
		self.body = ObjectDeclarationWithRefCountBody(reader)
		self.cRef = type(self).cRefReadFunc(reader)
		self.prop_set = None
		return

class ObjectDeclarationWithRefCount2FNDX(ObjectDeclarationWithRefCountFNDX):
	ID = FileNodeID.ObjectDeclarationWithRefCount2FNDX
	cRefReadFunc = onestore_reader.read_uint32

class HashedChunkDescriptor2FND(FileNode1):
	ID = FileNodeID.HashedChunkDescriptor2FND

	def __init__(self, reader, ref):
		self.BlobRef = ref
		self.guidHash = GUID().read(reader)
		return

class ObjectDeclaration2Body:

	def __init__(self, reader:onestore_reader):
		self.coid = CompactID(reader)
		self.jcid = JCID().read(reader)

		w = reader.read_uint8()
		self.fHasOidReferences = (w & 1) != 0
		self.fHasOsidReferences = (w & 2) != 0
		return

class ObjectDeclaration2RefCountFND(FileNode1):
	ID = FileNodeID.ObjectDeclaration2RefCountFND
	cRefReadFunc = onestore_reader.read_uint8

	def __init__(self, reader, ref):
		self.BlobRef = ref
		self.body = ObjectDeclaration2Body(reader)
		self.cRef = type(self).cRefReadFunc(reader)
		self.md5Hash = None
		self.prop_set = None
		return

class ObjectDeclaration2LargeRefCountFND(ObjectDeclaration2RefCountFND):
	ID = FileNodeID.ObjectDeclaration2LargeRefCountFND
	cRefReadFunc = onestore_reader.read_uint32

class ReadOnlyObjectDeclaration2RefCountFND(ObjectDeclaration2RefCountFND):
	ID = FileNodeID.ReadOnlyObjectDeclaration2RefCountFND

	def __init__(self, reader, ref):
		super().__init__(reader, ref)
		assert(self.body.jcid.IsPropertySet)
		assert(self.body.jcid.IsReadOnly)
		self.md5Hash = reader.read_bytes(16)
		return

class ReadOnlyObjectDeclaration2LargeRefCountFND(ReadOnlyObjectDeclaration2RefCountFND):
	ID = FileNodeID.ReadOnlyObjectDeclaration2LargeRefCountFND
	cRefReadFunc = onestore_reader.read_uint32

class ObjectDeclarationFileData3RefCountFND(FileNode):
	ID = FileNodeID.ObjectDeclarationFileData3RefCountFND
	cRefReadFunc = onestore_reader.read_uint8

	def __init__(self, reader:onestore_reader):
		self.data_store_object = None
		self.coid = CompactID(reader)
		self.jcid = JCID().read(reader)
		self.cRef = type(self).cRefReadFunc(reader)
		self.FileDataReference = StringInStorageBuffer(reader)
		self.Extension = StringInStorageBuffer(reader)
		return

class ObjectDeclarationFileData3LargeRefCountFND(ObjectDeclarationFileData3RefCountFND):
	ID = FileNodeID.ObjectDeclarationFileData3LargeRefCountFND
	cRefReadFunc = onestore_reader.read_uint32

class ObjectGroupListReferenceFND(FileNode2):
	ID = FileNodeID.ObjectGroupListReferenceFND

	def __init__(self, reader, ref):
		self.ref = ref
		self.ObjectGroupID = ExGUID().read(reader)
		return

class ObjectGroupStartFND(FileNode):
	ID = FileNodeID.ObjectGroupStartFND

	def __init__(self, reader:onestore_reader):
		self.ogid = ExGUID().read(reader)
		return

class DataSignatureGroupDefinitionFND(FileNode):
	ID = FileNodeID.DataSignatureGroupDefinitionFND

	def __init__(self, reader:onestore_reader):
		self.DataSignatureGroup = ExGUID().read(reader)
		return

class RevisionManifestEndFND(FileNode):
	ID = FileNodeID.RevisionManifestEndFND

class GlobalIdTableStart2FND(FileNode):
	ID = FileNodeID.GlobalIdTableStart2FND

class GlobalIdTableEndFNDX(FileNode):
	ID = FileNodeID.GlobalIdTableEndFNDX

class ObjectGroupEndFND(FileNode):
	ID = FileNodeID.ObjectGroupEndFND

class ChunkTerminatorFND(FileNode):
	ID = FileNodeID.ChunkTerminatorFND

FileNodeFactoryDict = {
	int(FileNodeID.ObjectSpaceManifestRootFND) : ObjectSpaceManifestRootFND,
	int(FileNodeID.ObjectSpaceManifestListReferenceFND) : ObjectSpaceManifestListReferenceFND,
	int(FileNodeID.ObjectSpaceManifestListStartFND) : ObjectSpaceManifestListStartFND,
	int(FileNodeID.RevisionManifestListReferenceFND) : RevisionManifestListReferenceFND,
	int(FileNodeID.RevisionManifestListStartFND) : RevisionManifestListStartFND,
	int(FileNodeID.RevisionManifestStart4FND) : RevisionManifestStart4FND,
	int(FileNodeID.RevisionManifestEndFND) : RevisionManifestEndFND,
	int(FileNodeID.RevisionManifestStart6FND) : RevisionManifestStart6FND,
	int(FileNodeID.RevisionManifestStart7FND) : RevisionManifestStart7FND,
	int(FileNodeID.GlobalIdTableStartFNDX) : GlobalIdTableStartFNDX,
	int(FileNodeID.GlobalIdTableStart2FND) : GlobalIdTableStart2FND,
	int(FileNodeID.GlobalIdTableEntryFNDX) : GlobalIdTableEntryFNDX,
	int(FileNodeID.GlobalIdTableEntry2FNDX) : GlobalIdTableEntry2FNDX,
	int(FileNodeID.GlobalIdTableEntry3FNDX) : GlobalIdTableEntry3FNDX,
	int(FileNodeID.GlobalIdTableEndFNDX) : GlobalIdTableEndFNDX,
	int(FileNodeID.ObjectDeclarationWithRefCountFNDX) : ObjectDeclarationWithRefCountFNDX,
	int(FileNodeID.ObjectDeclarationWithRefCount2FNDX) : ObjectDeclarationWithRefCount2FNDX,
	int(FileNodeID.ObjectRevisionWithRefCountFNDX) : ObjectRevisionWithRefCountFNDX,
	int(FileNodeID.ObjectRevisionWithRefCount2FNDX) : ObjectRevisionWithRefCount2FNDX,
	int(FileNodeID.RootObjectReference2FNDX) : RootObjectReference2FNDX,
	int(FileNodeID.RootObjectReference3FND) : RootObjectReference3FND,
	int(FileNodeID.RevisionRoleDeclarationFND) : RevisionRoleDeclarationFND,
	int(FileNodeID.RevisionRoleAndContextDeclarationFND) : RevisionRoleAndContextDeclarationFND,
	int(FileNodeID.ObjectDeclarationFileData3RefCountFND) : ObjectDeclarationFileData3RefCountFND,
	int(FileNodeID.ObjectDeclarationFileData3LargeRefCountFND) : ObjectDeclarationFileData3LargeRefCountFND,
	int(FileNodeID.ObjectDataEncryptionKeyV2FNDX) : ObjectDataEncryptionKeyV2FNDX,
	int(FileNodeID.ObjectInfoDependencyOverridesFND) : ObjectInfoDependencyOverridesFND,
	int(FileNodeID.DataSignatureGroupDefinitionFND) : DataSignatureGroupDefinitionFND,
	int(FileNodeID.FileDataStoreListReferenceFND) : FileDataStoreListReferenceFND,
	int(FileNodeID.FileDataStoreObjectReferenceFND) : FileDataStoreObjectReferenceFND,
	int(FileNodeID.ObjectDeclaration2RefCountFND) : ObjectDeclaration2RefCountFND,
	int(FileNodeID.ObjectDeclaration2LargeRefCountFND) : ObjectDeclaration2LargeRefCountFND,
	int(FileNodeID.ObjectGroupListReferenceFND) : ObjectGroupListReferenceFND,
	int(FileNodeID.ObjectGroupStartFND) : ObjectGroupStartFND,
	int(FileNodeID.ObjectGroupEndFND) : ObjectGroupEndFND,
	int(FileNodeID.HashedChunkDescriptor2FND) : HashedChunkDescriptor2FND,
	int(FileNodeID.ReadOnlyObjectDeclaration2RefCountFND) : ReadOnlyObjectDeclaration2RefCountFND,
	int(FileNodeID.ReadOnlyObjectDeclaration2LargeRefCountFND) : ReadOnlyObjectDeclaration2LargeRefCountFND,
	int(FileNodeID.ChunkTerminatorFND) : ChunkTerminatorFND,
	}

def FileNodeFactory(reader:onestore_reader, allowed_nodes:set=None):
	start_offset = reader.get_offset()
	hdr = reader.read_uint32()

	if (hdr & 0x80000000) == 0:
		return None

	file_node_id = hdr & 0x3FF
	Size = (hdr >> 10) & 0x1FFF
	StpFormat = (hdr >> 23) & 0x3
	CbFormat = (hdr >> 25) & 0x3
	BaseType = (hdr >> 27) & 0xF

	FileNodeClass = FileNodeFactoryDict.get(file_node_id, None)
	if FileNodeClass is None:
		raise UnrecognizedFileNodeException("File node ID %03X unrecognized" % (file_node_id,))

	assert(FileNodeClass.ID.value == file_node_id)
	if FileNodeClass.BaseType != BaseType:
		raise BaseTypeMismatchException("File node ID %s expects BaseType %d, but came with %d" %
										(FileNodeClass.ID.name, FileNodeClass.BaseType, BaseType))
	assert(Size >= 4)

	if allowed_nodes is not None and file_node_id not in allowed_nodes \
		and file_node_id != FileNodeID.ChunkTerminatorFND.value:
		raise UnexpectedFileNodeException("File node %s not allowed" % (FileNodeClass.ID.name))

	if BaseType == 0:
		file_node_object = FileNodeClass(reader)
	else:
		# First item in the structure is FileNodeChunkReference
		ref = FileNodeChunkReference(reader, StpFormat, CbFormat)
		file_node_object = FileNodeClass(reader, ref)

	assert(start_offset + Size == reader.get_offset())
	return file_node_object
