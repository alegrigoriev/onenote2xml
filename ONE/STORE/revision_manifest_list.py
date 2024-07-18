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
from ..exception import RevisionMismatchException
from .property_set import ObjectSpaceObjectPropSet
from .filenode import FileNodeID as ID
from .filenode import ObjectInfoDependencyOverrideData
from .object_group import ObjectGroup
from .global_id_table import GlobalIdTable
from .filenode_list import FileNodeList

ID_RevisionManifestListStartFND = ID.RevisionManifestListStartFND.value
ID_RevisionRoleDeclarationFND = ID.RevisionRoleDeclarationFND.value
ID_RevisionRoleAndContextDeclarationFND = ID.RevisionRoleAndContextDeclarationFND.value
ID_RevisionManifestStart4FND = ID.RevisionManifestStart4FND.value
ID_RevisionManifestStart6FND = ID.RevisionManifestStart6FND.value
ID_RevisionManifestStart7FND = ID.RevisionManifestStart7FND.value
ID_RevisionManifestEndFND = ID.RevisionManifestEndFND.value
ID_ObjectGroupListReferenceFND = ID.ObjectGroupListReferenceFND.value
ID_ObjectInfoDependencyOverridesFND = ID.ObjectInfoDependencyOverridesFND.value
ID_RootObjectReference2FNDX = ID.RootObjectReference2FNDX.value
ID_RootObjectReference3FND = ID.RootObjectReference3FND.value
ID_GlobalIdTableStart2FND = ID.GlobalIdTableStart2FND.value
ID_GlobalIdTableStartFNDX = ID.GlobalIdTableStartFNDX.value
ID_DataSignatureGroupDefinitionFND = ID.DataSignatureGroupDefinitionFND.value
ID_ObjectDeclarationWithRefCountFNDX = ID.ObjectDeclarationWithRefCountFNDX.value
ID_ObjectDeclarationWithRefCount2FNDX = ID.ObjectDeclarationWithRefCount2FNDX.value
ID_ObjectRevisionWithRefCountFNDX = ID.ObjectRevisionWithRefCountFNDX.value
ID_ObjectRevisionWithRefCount2FNDX = ID.ObjectRevisionWithRefCount2FNDX.value
ID_ObjectDataEncryptionKeyV2FNDX = ID.ObjectDataEncryptionKeyV2FNDX.value

ID_GlobalIdTableEndFNDX = ID.GlobalIdTableEndFNDX.value
ID_GlobalIdTableEntryFNDX = ID.GlobalIdTableEntryFNDX.value
ID_GlobalIdTableEntry2FNDX = ID.GlobalIdTableEntry2FNDX.value
ID_GlobalIdTableEntry3FNDX = ID.GlobalIdTableEntry3FNDX.value

NotebookRevisionManifestListNodes = {
	ID_RevisionManifestListStartFND,
	ID_RevisionRoleDeclarationFND,
	ID_RevisionRoleAndContextDeclarationFND,
	ID_RevisionManifestStart6FND,
	ID_RevisionManifestStart7FND,
	ID_ObjectGroupListReferenceFND,
	ID_ObjectInfoDependencyOverridesFND,
	ID_RootObjectReference2FNDX,
	ID_RootObjectReference3FND,
	ID_GlobalIdTableStartFNDX,
	ID_GlobalIdTableStart2FND,
	ID_GlobalIdTableEntryFNDX,
	ID_GlobalIdTableEndFNDX,
	ID_DataSignatureGroupDefinitionFND,
	ID_ObjectDataEncryptionKeyV2FNDX,
	ID_RevisionManifestEndFND,
	}

Toc2RevisionManifestListNodes = {
	ID_RevisionManifestListStartFND,
	ID_RevisionRoleDeclarationFND,
	ID_RevisionManifestStart4FND,
	ID_ObjectInfoDependencyOverridesFND,
	ID_RootObjectReference2FNDX,
	ID_GlobalIdTableStartFNDX,
	ID_GlobalIdTableEntryFNDX,
	ID_GlobalIdTableEntry2FNDX,
	ID_GlobalIdTableEntry3FNDX,
	ID_GlobalIdTableEndFNDX,
	ID_DataSignatureGroupDefinitionFND,
	ID_ObjectDeclarationWithRefCountFNDX,
	ID_ObjectDeclarationWithRefCount2FNDX,
	ID_ObjectRevisionWithRefCountFNDX,
	ID_ObjectRevisionWithRefCount2FNDX,
	ID_RevisionManifestEndFND,
	}

def RevisionManifestList(obj_space, onestore, ref):
	revisions = {}

	if onestore.IsNotebookSection():
		allowed_nodes = NotebookRevisionManifestListNodes
	elif onestore.IsNotebookToc2():
		allowed_nodes = Toc2RevisionManifestListNodes
	else:
		allowed_nodes = None

	node_iter = FileNodeList(onestore, ref, allowed_nodes)

	node = next(node_iter)
	if node.ID.value != ID_RevisionManifestListStartFND:
		raise UnexpectedFileNodeException("Unexpected file node %s in Revision Manifest List NodeList" % (node.ID,))
	assert(obj_space.gosid == node.gosidRoot)

	for node in node_iter:
		nid = node.ID.value
		if nid == ID_RevisionManifestStart4FND \
			or nid == ID_RevisionManifestStart6FND \
			or nid == ID_RevisionManifestStart7FND:
			revision = RevisionManifest(onestore, node_iter, node, revisions)

			revisions[revision.rid] = revision
			yield revision

		elif nid != ID_RevisionRoleDeclarationFND and \
				nid != ID_RevisionRoleAndContextDeclarationFND:
			raise UnexpectedFileNodeException("Unexpected file node %s in Revision Manifest NodeList" % (node.ID,))

		# revision Context ID:
		gctxid = getattr(node, 'gctxid', NULL_ExGUID)
		obj_space.SetContext(node.rid, gctxid, node.RevisionRole)
		continue

	return

class RevisionManifest:
	ROOT_ROLE_CONTENTS = 1
	ROOT_ROLE_PAGE_METADATA = 2
	ROOT_ROLE_REVISION_METADATA = 4

	def __init__(self, onestore, node_iter, node, revisions):
		self.DataSignatureGroup = None
		self.objects = {}
		self.global_id_table = None
		self.object_groups = {}
		self.root_objects = {}

		self.rid = node.rid
		self.ridDependent = node.ridDependent
		self.odcsDefault = node.odcsDefault

		if node.ridDependent != NULL_ExGUID:
			# Contrary to [MS-ONESTORE] doc, this revision may not be immediately following the dependent revision
			# Thus, we should not just take the previous revision and see if its RID matched the dependent.
			dep_revision = revisions.get(node.ridDependent, None)
			if dep_revision is None:
				raise RevisionMismatchException("Dependent revision not present, expected: %s"
											% (node.ridDependent,))
			# Transfer objects from the previous revision
			assert(self.odcsDefault == dep_revision.odcsDefault) # TODO: raise an exception instead
			self.dep_revision = dep_revision
			prev_global_id_table = dep_revision.global_id_table
			self.root_objects = dep_revision.root_objects.copy()
		else:
			self.dep_revision = None
			prev_global_id_table = None

		node = next(node_iter)
		if node.ID.value == ID_ObjectDataEncryptionKeyV2FNDX:
			node = next(node_iter)

		while (nid := node.ID) != ID_RevisionManifestEndFND:

			if nid == ID_ObjectGroupListReferenceFND:
				if self.odcsDefault != 0:
					# Can't read encrypted objects.
					continue
				obj_group = ObjectGroup(onestore, node.ref, self)
				assert(obj_group.ObjectGroupID == node.ObjectGroupID)
				self.object_groups[node.ObjectGroupID] = obj_group
			elif nid == ID_ObjectInfoDependencyOverridesFND:
				# For read-only purposes, reference counts don't matter
				if node.overrides is None:
					node.overrides = ObjectInfoDependencyOverrideData(onestore.get_chunk(node.ref))
				# TODO: The overrides data uses CompactIds resolved by the obj_group GlobalObjectIdTable
			elif nid == ID_RootObjectReference2FNDX:
				self.root_objects[node.RootRole] = obj_group.getExtguidByCompactID(node.coidRoot)
			else:
				break

			node = next(node_iter)
			continue

		if nid == ID_GlobalIdTableStart2FND \
			 or nid == ID_GlobalIdTableStartFNDX:
			self.global_id_table = GlobalIdTable(node_iter, prev_global_id_table)

			node = next(node_iter)

		while (nid := node.ID) != ID_RevisionManifestEndFND:

			if nid == ID_ObjectInfoDependencyOverridesFND:
				# For read-only purposes, reference counts don't matter
				if node.overrides is None:
					node.overrides = ObjectInfoDependencyOverrideData(onestore.get_chunk(node.ref))
				# TODO: The overrides data uses CompactIds resolved by the self.global_id_table
			elif nid == ID_RootObjectReference3FND:
				self.root_objects[node.RootRole] = node.oidRoot
			elif nid == ID_DataSignatureGroupDefinitionFND:
				self.DataSignatureGroup = node.DataSignatureGroup
			elif nid == ID_ObjectDeclarationWithRefCountFNDX \
			  or nid == ID_ObjectDeclarationWithRefCount2FNDX:
				oid = self.global_id_table[node.body.coid]
				obj = ObjectSpaceObjectPropSet(onestore, node.ObjectRef, node.body.jcid, self.global_id_table)
				node.prop_set = obj
				self.AddObject(oid, obj)
			elif nid == ID_ObjectRevisionWithRefCountFNDX \
			  or nid == ID_ObjectRevisionWithRefCount2FNDX:
				oid = self.global_id_table[node.coid]
				# Object's JCID is inherited from the existing definition
				prev_object = self.GetObjectById(oid)
				obj = ObjectSpaceObjectPropSet(onestore, node.ref, prev_object.jcid, self.global_id_table)
				node.prop_set = obj
				self.AddObject(oid, obj)
			elif nid == ID_RootObjectReference2FNDX:
				# [ONESTORE] document doesn't specify that RootObjectReference2FNDX may be after Global ID table
				self.root_objects[node.RootRole] = self.getExtguidByCompactID(node.coidRoot)
			else:
				raise UnexpectedFileNodeException("Unexpected file node %03X in Revision Manifest NodeList Global Table" % (nid,))

			node = next(node_iter)
			continue

		return

	def GetRootObjectId(self, role:int=ROOT_ROLE_CONTENTS):
		return self.root_objects.get(role, None)

	def GetRootObjectRoles(self):
		return self.root_objects.keys()

	def getExtguidByCompactID(self, compact_id:CompactID):
		return self.global_id_table[compact_id]

	def AddObject(self, oid, obj, md5Hash=None):
		obj.oid = oid
		if not obj.jcid.IsReadOnly():
			self.objects[oid] = obj
			return

		# See if there is a previous object with same ID:
		prev_obj = self.GetObjectById(oid)
		if prev_obj is not None:
			# compare data
			assert(prev_obj.jcid.IsReadOnly())
			assert(obj.raw_data == prev_obj.raw_data)
			# The object is also put in this revision object table
		# md5Hash never matches, perhaps Microsoft uses a strange flavor of it (without appending length with padding?)
		elif False and md5Hash is not None:
			from hashlib import md5
			obj_hash = md5(obj.raw_data, usedforsecurity=False)
			# Pad the data to multiple of 8?
			for _ in range(7 & -len(obj.raw_data)):
				obj_hash.update(b'\0')
			digest = obj_hash.digest()
			assert(digest == md5Hash)

		self.objects[oid] = obj
		return

	def GetObjectById(self, oid):
		revision = self
		while revision is not None:
			obj = revision.objects.get(oid, None)
			if obj is not None:
				return obj
			revision = revision.dep_revision
			continue
		return None

	def dump(self, fd, verbose=None):
		print("\nRevision:", self.rid, file=fd)
		if self.dep_revision is not None:
			print(" PrevRevision:", self.dep_revision.rid, file=fd)
		for role, obj_id in self.root_objects.items():
			print(" Root object: %s, role: %d" % (obj_id, role), file=fd)
		for object_group in self.object_groups.values():
			object_group.dump(fd, verbose)

		if not getattr(verbose, 'dump_nodelists', False):
			for extid, obj in self.objects.items():
				print("\nObjectID:", str(extid), file=fd)
				obj.dump(fd, verbose)
		# else the objects will be dumped along the filenodes
		return
