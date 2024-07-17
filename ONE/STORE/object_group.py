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
from ..exception import UnexpectedFileNodeException
from .filenode import FileNodeID as ID
from .global_id_table import GlobalIdTable
from .filenode_list import FileNodeList

ID_ObjectGroupStartFND = ID.ObjectGroupStartFND.value
ID_GlobalIdTableStart2FND = ID.GlobalIdTableStart2FND.value
ID_DataSignatureGroupDefinitionFND = ID.DataSignatureGroupDefinitionFND.value
ID_ObjectDeclaration2RefCountFND = ID.ObjectDeclaration2RefCountFND.value
ID_ObjectDeclaration2LargeRefCountFND = ID.ObjectDeclaration2LargeRefCountFND.value
ID_ReadOnlyObjectDeclaration2RefCountFND = ID.ReadOnlyObjectDeclaration2RefCountFND.value
ID_ReadOnlyObjectDeclaration2LargeRefCountFND = ID.ReadOnlyObjectDeclaration2LargeRefCountFND.value
ID_ObjectDeclarationFileData3RefCountFND = ID.ObjectDeclarationFileData3RefCountFND.value
ID_ObjectDeclarationFileData3LargeRefCountFND = ID.ObjectDeclarationFileData3LargeRefCountFND.value
ID_ObjectGroupEndFND = ID.ObjectGroupEndFND.value
ID_GlobalIdTableEndFNDX = ID.GlobalIdTableEndFNDX.value
ID_GlobalIdTableEntryFNDX = ID.GlobalIdTableEntryFNDX.value

ObjectGroupListNodes = {
	ID_ObjectGroupStartFND,
	ID_GlobalIdTableStart2FND,
	ID_GlobalIdTableEntryFNDX,
	ID_GlobalIdTableEndFNDX,
	ID_DataSignatureGroupDefinitionFND,
	ID_ObjectDeclaration2RefCountFND,
	ID_ObjectDeclaration2LargeRefCountFND,
	ID_ObjectDeclarationFileData3LargeRefCountFND,
	ID_ReadOnlyObjectDeclaration2RefCountFND,
	ID_ReadOnlyObjectDeclaration2LargeRefCountFND,
	ID_ObjectDeclarationFileData3RefCountFND,
	ID_ObjectDeclarationFileData3LargeRefCountFND,
	ID_ObjectGroupEndFND,
	}

class ObjectGroup:
	def __init__(self, onestore, ref):
		self.DataSignature = None

		node_iter = FileNodeList(onestore, ref, allowed_nodes=ObjectGroupListNodes)

		node = next(node_iter)
		if node.ID != ID_ObjectGroupStartFND:
			raise UnexpectedFileNodeException("Unexpected file node %s in Object Group NodeList" % (node.ID.name,))
		self.ObjectGroupID = node.ogid

		node = next(node_iter)
		if node.ID != ID_GlobalIdTableStart2FND:
			raise UnexpectedFileNodeException("Unexpected file node %s in Object Group %s NodeList" % (node.ID.name, self.ObjectGroupID))
		self.global_id_table = GlobalIdTable(node_iter, None)

		for node in node_iter:
			nid = node.ID.value
			if nid == ID_DataSignatureGroupDefinitionFND:
				self.DataSignature = node.DataSignatureGroup
				continue
			elif nid == ID_ObjectDeclarationFileData3RefCountFND \
			  or nid == ID_ObjectDeclarationFileData3LargeRefCountFND:
				assert(node.jcid.IsFileData())
				# TODO: Read the file data object
				continue
			elif nid == ID_ObjectGroupEndFND:
				break

			if nid == ID_ObjectDeclaration2RefCountFND \
			  or nid == ID_ObjectDeclaration2LargeRefCountFND:
				# TODO: Read the property set
				assert(not node.body.jcid.IsReadOnly())
			elif nid == ID_ReadOnlyObjectDeclaration2RefCountFND \
			  or nid == ID_ReadOnlyObjectDeclaration2LargeRefCountFND:
				# TODO: Read the read-only property set
				assert(node.body.jcid.IsReadOnly())
			# FileNodeList will raise UnexpectedFileNodeException if any other node ID is read

			continue
		else:
			raise UnexpectedFileNodeException("Missing file node ObjectGroupEndFND in Object Group %s NodeList" % (self.ObjectGroupID))

		return

	def getExtguidByCompactID(self, compact_id:CompactID):
		return self.global_id_table[compact_id]

	def dump(self, fd):
		print("ObjectGroupID:", str(self.ObjectGroupID), file=fd)

		return
