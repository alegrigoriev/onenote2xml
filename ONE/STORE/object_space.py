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

from typing import Iterable
from ..base_types import ExGUID, NULL_ExGUID
from ..exception import UnexpectedFileNodeException
from .filenode import FileNodeID
from .filenode_list import FileNodeList
from .revision_manifest_list import RevisionManifestList, RevisionManifest

ID_ObjectSpaceManifestListStartFND = FileNodeID.ObjectSpaceManifestListStartFND.value
ID_RevisionManifestListReferenceFND = FileNodeID.RevisionManifestListReferenceFND.value

class ObjectSpace:
	def __init__(self, onestore, ref):
		self.revisions = {}

		manifest_ref = None
		node_iter = FileNodeList(onestore, ref,
			allowed_nodes=
			{
				ID_ObjectSpaceManifestListStartFND,
				ID_RevisionManifestListReferenceFND,
			})

		node = next(node_iter)
		if node.ID != ID_ObjectSpaceManifestListStartFND:
			raise UnexpectedFileNodeException("Unexpected file node %03X in Object Space NodeList" % (node.ID,))
		self.gosid = node.gosidRoot

		for node in node_iter:
			if node.ID != ID_RevisionManifestListReferenceFND:
				raise UnexpectedFileNodeException("Unexpected file node %03X in Object Space NodeList" % (node.ID,))

			# Only the last RevisionManifestListReferenceFND node in the list is valid
			manifest_ref = node.ref
			continue

		if manifest_ref is None:
			raise UnexpectedFileNodeException("Missing ManifestListReference in Object Space NodeList")

		# RevisionManifestList also calls SetContext() to pass context information by the side
		for revision in RevisionManifestList(self, onestore, manifest_ref):
			self.revisions[revision.rid] = revision

		if not self.revisions:
			raise UnexpectedFileNodeException("No revisions in Revision Manifest List")

		return

	def GetRevisionIds(self)->Iterable[ExGUID]:
		return self.revisions.keys()

	def GetRevision(self, rid)->RevisionManifest:
		return self.revisions.get(rid, None)

	def dump(self, fd):
		for revision in self.revisions.values():
			revision.dump(fd)
		for (gctxid, role), rid in self.contexts.items():
			print("Context %s:%d->revision %s" % (gctxid, role, rid), file=fd)

		return
