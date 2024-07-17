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

from ..base_types import FileChunkReference64x32
from .filenode import FileNodeFactory, FileNodeID

class FileNodeListHeader:

	def __init__(self, reader):
		self.uintMagic = reader.read_uint64()
		assert(self.uintMagic == 0xA4567AB1F5F7F4C4)
		self.FileNodeListID = reader.read_uint32()
		self.nFragmentSequence = reader.read_uint32()
		return

def FileNodeList(onestore, ChunkReference, allowed_nodes:set=None):
	'''The FileNodeListFragment structure specifies a sequence of file nodes from a file node list (section 2.4).
	The size of the FileNodeListFragment structure is specified by the structure that references it.
	All fragments in the same file node list MUST have the same FileNodeListFragment.header.FileNodeListID field.
	header (16 bytes): A FileNodeListHeader structure (section 2.4.2).
	rgFileNodes (variable): A stream of bytes that contains a sequence of FileNode structures (section 2.4.3).

	The stream is terminated when any of the following conditions is met:
	- The number of bytes between the end of the last read FileNode and the nextFragment field is less than 4 bytes.
	- A FileNode structure with a FileNodeID field value equal to 0x0FF (ChunkTerminatorFND structure, section 2.4.3) is read.
	If a ChunkTerminatorFND structure is present, the value of the nextFragment field MUST be
	a valid FileChunkReference64x32 structure (section 2.2.4.4) to the next FileNodeListFragment structure.

	- The number of FileNode structures read for the containing file node list is equal
	to the number of nodes specified for the list by the transaction log (section 2.3.3)
	in the last TransactionEntry (section 2.3.3.2) that modified the list. In this case the nextFragment field MUST be ignored.

	padding (variable): An optional array of bytes between the last FileNode structure in the rgFileNodes field and the nextFragment field. Undefined and MUST be ignored.
	nextFragment (12 bytes): A FileChunkReference64x32 structure (section 2.2.4.4) that specifies
	whether there are more fragments in this file node list, and if so, the location and size of the next fragment.
	If this is the last fragment, the value of the nextFragment field MUST be "fcrNil" (see section 2.2.4).
	Otherwise the value of the nextFragment.stp field MUST specify the location of a valid FileNodeListFragment structure,
	and the value of the nextFragment.cb field MUST be equal to the size of the referenced fragment including the
	FileNodeListFragment.header field and the FileNodeListFragment.footer field.

	The location of the nextFragment field is calculated by adding the size of this FileNodeListFragment structure
	minus the size of the nextFragment and footer fields to the location of this FileNodeListFragment structure.

	footer (8 bytes): An unsigned integer; MUST be "0x8BC215C38233BA4B". Specifies the end of the FileNodeListFragment structure.
	'''

	prev_header = None

	while not ChunkReference.isNil():
		reader = onestore.get_chunk(ChunkReference)

		header = FileNodeListHeader(reader)
		if prev_header is not None:
			assert(header.FileNodeListID == prev_header.FileNodeListID)
			assert(header.nFragmentSequence == prev_header.nFragmentSequence+1)
		else:
			assert(header.nFragmentSequence == 0)

		prev_header = header

		tail_reader = reader.extract(-20)
		ChunkReference = FileChunkReference64x32(tail_reader)
		footer = tail_reader.read_uint64()
		assert(footer == 0x8BC215C38233BA4B)

		while reader.remaining() >= 4:
			file_node = FileNodeFactory(reader, allowed_nodes)
			if file_node is None:
				# Invalid data begun
				return

			if file_node.ID == FileNodeID.ChunkTerminatorFND.value:
				assert(not ChunkReference.isNil())
				break

			yield file_node
			# Some file lists are terminated by their own end node ID,
			# and may have an invalid garbage after it.
			# We can't read ahead, or read all nodes in advance
			continue

		continue

	return

