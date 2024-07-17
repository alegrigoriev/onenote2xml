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
from typing import Iterable
from ..base_types import *
from ..exception import CircularObjectReferenceException, ObjectNotFoundException
from ..STORE.revision_manifest_list import RevisionManifest
from ..STORE.onestore import OneStoreFile

class RevisionBuilderCtx:
	ROOT_ROLE_CONTENTS = RevisionManifest.ROOT_ROLE_CONTENTS
	ROOT_ROLE_PAGE_METADATA = RevisionManifest.ROOT_ROLE_PAGE_METADATA
	ROOT_ROLE_REVISION_METADATA = RevisionManifest.ROOT_ROLE_REVISION_METADATA

	def __init__(self, property_set_factory,
				revision:RevisionManifest, object_space_ctx:ObjectSpaceBuilderCtx):
		self.property_set_factory = property_set_factory
		self.onestore = object_space_ctx.onestore
		self.gosid = object_space_ctx.gosid
		self.os_index = object_space_ctx.os_index

		self.revision = revision
		self.rid:ExGUID = revision.rid

		self.revision_roles = {}
		self.obj_dict = {}

		# Build all roles
		for role in self.revision.GetRootObjectRoles():
			oid = self.revision.GetRootObjectId(role)
			root_obj = self.GetObjectReference(oid)
			self.revision_roles[role] = root_obj

			continue

		return

	def GetRootObject(self, role=ROOT_ROLE_CONTENTS):
		return self.revision_roles.get(role, None)

	def GetObjectReference(self, oid):
		if oid is None:
			return None

		obj = self.obj_dict.get(oid, None)
		if obj is NotImplemented:
			# Circular reference, unexpected
			raise CircularObjectReferenceException("Circular reference to object %s" % (oid,))

		if obj is not None:
			# Already built
			return obj

		self.obj_dict[oid] = NotImplemented

		prop_set = self.revision.GetObjectById(oid)
		if prop_set is None:
			raise ObjectNotFoundException("Object %s not found in revision %s" % (oid, self.rid))

		obj = self.MakeObject(prop_set, oid)	# Never None
		self.obj_dict[oid] = obj
		return obj

	def MakeObject(self, prop_set, oid=None):
		obj = self.property_set_factory(prop_set.jcid, oid)	# Never None
		obj.make_object(self, prop_set)
		return obj

	def dump(self, fd, verbose=None):
		# Empty
		return

class ObjectSpaceBuilderCtx:
	REVISION_BUILDER = RevisionBuilderCtx
	'''
	This structure describes a context for building an object tree from ONESTORE properties trees
	for a single object space.
	'''

	def __init__(self, onestore:OneStoreFile, property_set_factory, object_space, index:int, options):
		self.options = options
		self.onestore = onestore
		self.gosid = object_space.gosid
		self.object_space = object_space
		self.os_index = index
		self.root_revision_id = object_space.GetDefaultContextRevisionId()

		self.revisions = {}  # All revisions, including meta-revisions

		revisions = {}
		for rid in object_space.GetRevisionIds():
			revision = object_space.GetRevision(rid)
			revisions[rid] = self.REVISION_BUILDER(property_set_factory, revision, self)
			continue

		self.root_revision_ctx = revisions.pop(self.root_revision_id, None)

		self.revisions = revisions

		# After all other revisions
		self.revisions[self.root_revision_id] = self.root_revision_ctx

		return

	def GetRevisions(self)->Iterable[RevisionBuilderCtx]:
		return self.revisions.values()

	def GetRootRevision(self):
		return self.root_revision_ctx

	def dump(self, fd, verbose=None):
		print("\nObject Space %s" % (self.gosid,), file=fd)
		#for revision in self.revisions.values():
		for revision in self.revisions.values():
			revision.dump(fd, verbose)
		return

class ObjectTreeBuilder:
	'''
	This structure describes a context for building an object tree from ONESTORE properties trees.

	'property_set_factory' is a callable with a single 'jcid' argument, to return
	a property set object instance, which then needs a make_object(prop_set, self)
	call to finish construction.

	'onestore' is an instance of ONE.STORE.onestore.OneStoreFile object with loaded file contents.

	'parent_revision' is an instance of ONE.STORE.revision_manifest_list.RevisionManifest object,
	with a loaded contents of one revision. The tree is currently being built for this revision.
	Use this revision to resolve object references.

	'object_space' the ONE.STORE.object_space.ObjectSpace object of 'parent_revision'.

	'object_spaces' is a dictionary of ObjectTreeBuilder objects, keyed with ExGUID Object Space ID.

	'''

	OBJECT_SPACE_BUILDER = ObjectSpaceBuilderCtx
	def __init__(self, onestore, property_set_factory, options=None):
		self.object_spaces:dict[ExGUID, ObjectSpaceBuilderCtx] = {}
		self.root_gosid = onestore.GetRootObjectSpaceId()

		# Derived classes MUST do their initialization _before_ invoking super().__init__()
		os_index = 0
		for gosid in onestore.GetObjectSpaces():
			object_space = onestore.GetObjectSpace(gosid)
			self.object_spaces[gosid] = self.OBJECT_SPACE_BUILDER(onestore, property_set_factory, object_space, os_index, options)
			os_index += 1
			continue

		return

	def dump(self, fd, verbose):
		for object_space in self.object_spaces.values():
			object_space.dump(fd, verbose)

		return
