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

from __future__ import annotations
from ..base_types import *
from .reader import onestore_reader
from ..exception import UnrecognizedFileFormatException
from ..exception import UnexpectedFileNodeException

class OneStoreFileHeader:

	def __init__(self, fd):
		self.guidFileType = GUID().read(fd)
		self.guidFile = GUID().read(fd)
		self.guidLegacyFileVersion = GUID().read(fd)
		self.guidFileFormat = GUID().read(fd)
		self.ffvLastCodeThatWroteToThisFile = fd.read_uint32()
		self.ffvOldestCodeThatHasWrittenToThisFile = fd.read_uint32()
		self.ffvNewestCodeThatHasWrittenToThisFile = fd.read_uint32()
		self.ffvOldestCodeThatMayReadThisFile = fd.read_uint32()
		self.fcrLegacyFreeChunkList = FileChunkReference32(fd)
		self.fcrLegacyTransactionLog = FileChunkReference32(fd)
		self.cTransactionsInLog = fd.read_uint32()
		self.cbLegacyExpectedFileLength = fd.read_uint32()
		self.rgbPlaceholder = fd.read_uint64()
		self.fcrLegacyFileNodeListRoot = FileChunkReference32(fd)
		self.cbLegacyFreeSpaceInFreeChunkList = fd.read_uint32()
		self.fNeedsDefrag = fd.read_uint8()
		self.fRepairedFile = fd.read_uint8()
		self.fNeedsGarbageCollect = fd.read_uint8()
		self.fHasNoEmbeddedFileObjects = fd.read_uint8()
		self.guidAncestor = GUID().read(fd)
		self.crcName = fd.read_uint32()
		self.fcrHashedChunkList = FileChunkReference64x32(fd)
		self.fcrTransactionLog = FileChunkReference64x32(fd)
		self.fcrFileNodeListRoot = FileChunkReference64x32(fd)
		self.fcrFreeChunkList = FileChunkReference64x32(fd)
		self.cbExpectedFileLength = fd.read_uint64()
		self.cbFreeSpaceInFreeChunkList = fd.read_uint64()
		self.guidFileVersion = GUID().read(fd)
		self.nFileVersionGeneration = fd.read_uint64()
		self.guidDenyReadFileVersion = GUID().read(fd)
		self.grfDebugLogFlags = fd.read_uint32()
		self.fcrDebugLog = FileChunkReference64x32(fd)
		self.fcrAllocVerificationFreeChunkList = FileChunkReference64x32(fd)
		self.bnCreated = fd.read_uint32()
		self.bnLastWroteToThisFile = fd.read_uint32()
		self.bnOldestWritten = fd.read_uint32()
		self.bnNewestWritten = fd.read_uint32()
		return

	def dump(self, fd):
		print("HEADER:", file=fd)
		print("guidFileType=%s" % (self.guidFileType,), file=fd)
		print("guidFile=%s" % (self.guidFile,), file=fd)
		print("guidLegacyFileVersion=%s" % (self.guidLegacyFileVersion,), file=fd)
		print("guidFileFormat=%s" % (self.guidFileFormat,), file=fd)
		print("guidFileVersion=%s" % (self.guidFileVersion,), file=fd)
		return

class OneStoreFile:
	'''
	The header (section 2.3.1) is the first 1024 bytes of the file. It contains references to the other structures in the file as well as metadata about the file.
	The free chunk list (section 2.3.2) defines where there are free spaces in the file where data can be written.
	The transaction log (section 2.3.3) stores the state and length of each file node list (section 2.4) in the file.
	The hashed chunk list (section 2.3.4) stores read-only objects in the file that can be referenced by multiple revisions (section 2.1.8).
	The root file node list (section 2.1.14) is the file node list that is the root of the tree of all file node lists in the file.
	All of the file node lists that contain user data.
	'''
	one_section_file_type_guid = GUID('{7B5C52E4-D88C-4DA7-AEB1-5378D02996D3}')
	onenote2_file_type_guid = GUID('{43FF2FA1-EFD9-4C76-9EE2-10EA5722765F}')
	_one_section = 1
	_one_toc2 = 2

	def __init__(self, filename, data:bytes, options=None, log_file=None):

		self.filename = filename
		self.data = data
		self.options = options
		self.log_file = log_file
		self.RootObjectSpaceId = None
		self.ObjectSpaces = {}

		self.header = OneStoreFileHeader(onestore_reader(data, 1024, 0))

		if self.header.guidFileType == self.one_section_file_type_guid:
			self.file_format = self._one_section
		elif self.header.guidFileType == self.onenote2_file_type_guid:
			self.file_format = self._one_toc2
		else:
			raise UnrecognizedFileFormatException("Unrecognised guidFileType: %s" % (self.header.guidFileType,))

		try:
			self.ReadRootFileNodeList(self.header)
		except UnexpectedFileNodeException as e:
			if self.IsNotebookSection():
				e.args = (str(e) + ' in ".one" file',)
			elif self.IsNotebookToc2():
				e.args = (str(e) + ' in ".onetoc2" file',)
			raise
		return

	def ReadRootFileNodeList(self, header):
		'''The root file node list is a file node list (section 2.4)
		that specifies the set of all object spaces (section 2.1.4) contained in this file.
		It also specifies which object space is the root.
		The root file node list MUST begin with the FileNodeListFragment structure (section 2.4.1)
		specified by the Header.fcrFileNodeListRoot field (section 2.3.1).
		The root file node list MUST consist of the following FileNode structures (section 2.4.3),
		and MUST NOT contain any others:
		- One or more FileNode structures with FileNodeID field values equal to 0x008
		  (ObjectSpaceManifestListReferenceFND structure, section 2.5.2).
		- One FileNode structure with a FileNodeID field value equal to 0x004
		  (ObjectSpaceManifestRootFND structure, section 2.5.1).
		- Zero or one FileNode structure with FileNodeID field values equal to 0x090
		  (FileDataStoreListReferenceFND structure, section 2.5.21).
		'''

		from .filenode import FileNodeID as ID
		from .filenode_list import FileNodeList

		allowed_nodes= {
			ID.ObjectSpaceManifestListReferenceFND.value,
			ID.ObjectSpaceManifestRootFND.value,
		}
		if self.IsNotebookSection():
			allowed_nodes.add(ID.FileDataStoreListReferenceFND.value)

		for node in FileNodeList(self, header.fcrFileNodeListRoot, allowed_nodes):
			nid = node.ID
			if nid == ID.ObjectSpaceManifestListReferenceFND:
				from .object_space import ObjectSpace
				object_space = ObjectSpace(self, node.ref)
				assert(node.gosid == object_space.gosid)
				self.ObjectSpaces[node.gosid] = object_space
			elif nid == ID.FileDataStoreListReferenceFND.value:
				pass # TODO: read file data store list
			elif nid == ID.ObjectSpaceManifestRootFND:
				assert(self.RootObjectSpaceId is None)
				self.RootObjectSpaceId = node.gosidRoot
			# FileNodeList will raise UnexpectedFileNodeException if any other node ID is read
			continue

		assert(self.RootObjectSpaceId is not None)
		assert(len(self.ObjectSpaces) != 0)
		return

	def IsNotebookSection(self):
		return self.file_format is self._one_section

	def IsNotebookToc2(self):
		return self.file_format is self._one_toc2

	def get_chunk(self, chunk_ref:FileNodeChunkReference)->onestore_reader:
		return onestore_reader(self.data, chunk_ref.cb, chunk_ref.stp)

	def GetObjectSpaces(self):
		return self.ObjectSpaces.keys()

	def GetObjectSpace(self, osid:ExGUID):
		return self.ObjectSpaces.get(osid, None)

	def GetRootObjectSpaceId(self):
		return self.RootObjectSpaceId

	@staticmethod
	def open(filename, options, log_file=None)->OneStoreFile:
		with open(filename, 'rb') as fd:
			return OneStoreFile(filename, fd.read(), options, log_file=log_file)

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, exception_traceback):
		return False

	def dump(self, fd):
		self.header.dump(fd)
		print("\nRootObjectSpaceId=%s" % (self.RootObjectSpaceId,), file=fd)
		for gosid, space in self.ObjectSpaces.items():
			print("\nObjectSpaceID=%s" % (gosid,), file=fd)
			space.dump(fd)
		return
