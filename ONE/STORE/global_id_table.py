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

ID_GlobalIdTableEndFNDX = ID.GlobalIdTableEndFNDX.value
ID_GlobalIdTableEntryFNDX = ID.GlobalIdTableEntryFNDX.value
ID_GlobalIdTableEntry2FNDX = ID.GlobalIdTableEntry2FNDX.value
ID_GlobalIdTableEntry3FNDX = ID.GlobalIdTableEntry3FNDX.value

class GlobalIdTable:
	def __init__(self, node_iter, prev_global_id_table):
		self.table = {}
		node = next(node_iter)

		while node.ID != ID_GlobalIdTableEndFNDX:
			if node.ID == ID_GlobalIdTableEntryFNDX:
				self.table[node.index] = node.guid
			elif node.ID == ID_GlobalIdTableEntry2FNDX:
				self.table[node.iIndexMapTo] = prev_global_id_table.table[node.iIndexMapFrom]
			elif node.ID == ID_GlobalIdTableEntry3FNDX:
				iIndexCopyFrom = node.iIndexCopyFromStart
				cEntriesToCopy = node.cEntriesToCopy
				iIndexCopyTo = node.iIndexCopyToStart
				for _ in range(cEntriesToCopy):
					self.table[iIndexCopyTo] = prev_global_id_table.table[iIndexCopyFrom]
					iIndexCopyFrom += 1
					iIndexCopyTo += 1
			else:
				# The global ID table is present in the middle of a node stream,
				# we cannot rely on allowed nodes list to catch anomalies
				raise UnexpectedFileNodeException("Unexpected file node %03X in Global ID Table" % (node.ID,))
			node = next(node_iter)
			continue

		return

	def __getitem__(self, compact_id:CompactID):
		return ExGUID(self.table[compact_id.guidIndex].guid, compact_id.n)
