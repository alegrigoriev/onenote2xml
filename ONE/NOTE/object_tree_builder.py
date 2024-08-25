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

def GetTopologyCreationTimeStamps(obj):
	timestamps = []
	# Get all property sets with TopologyCreationTimeStamp property
	for paths, props in obj:
		if paths[-1] == 'TopologyCreationTimeStamp':
			timestamps.append(props[-2])
		continue
	return sorted(timestamps, key=lambda t:t.TopologyCreationTimeStamp, reverse=True)

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
		self.verbosity = object_space_ctx.verbosity

		self.revision = revision
		self.rid:ExGUID = revision.rid

		self.last_modified_timestamp = None

		self.revision_roles = {}
		self.obj_dict = {}

		# Build all roles
		for role in self.revision.GetRootObjectRoles():
			oid = self.revision.GetRootObjectId(role)
			root_obj = self.GetObjectReference(oid)
			self.revision_roles[role] = root_obj

			if role == self.ROOT_ROLE_REVISION_METADATA:
				self.last_modified_timestamp = getattr(root_obj, 'LastModifiedTimeStamp', self.last_modified_timestamp)
			elif role == self.ROOT_ROLE_CONTENTS:
				if root_obj._jcid_name == 'jcidSectionNode':
					# If this is a root page, find the most recent TopologyCreationTimeStamp
					if self.last_modified_timestamp is None:
						topology_creation_timestamps = GetTopologyCreationTimeStamps(root_obj)
						if topology_creation_timestamps:
							self.last_modified_timestamp = topology_creation_timestamps[0].TopologyCreationTimeStamp
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
		if self.last_modified_timestamp is not None:
			print("%s (%d)" % (
				GetFiletime64Datetime(self.last_modified_timestamp),
				Filetime64ToUnixTimestamp(self.last_modified_timestamp),
				), file=fd)
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

		self.verbosity = getattr(options, 'verbosity', 0)

		self.revisions = {}  # All revisions, including meta-revisions

		revisions = {}
		for rid in object_space.GetRevisionIds():
			revision = object_space.GetRevision(rid)
			revisions[rid] = self.REVISION_BUILDER(property_set_factory, revision, self)
			continue

		versions = []
		# The root (current) revision typically is not in the history metadata
		# Need to pop it in advance before processing the history revision
		self.root_revision_ctx = revisions.pop(self.root_revision_id, None)

		history_rid = self.object_space.GetContextRevisionId(ExGUID("{7111497F-1B6B-4209-9491-C98B04CF4C5A}", 1))
		history_revision_ctx = revisions.pop(history_rid, None)
		if history_revision_ctx is not None:
			# Revision history goes first
			self.revisions[history_rid] = history_revision_ctx

			# An initial jcidVersionProxy object can be empty and not have 'ElementChildNodes' property
			for jcidVersionProxy in getattr(history_revision_ctx.GetRootObject(), 'ElementChildNodes', ()):
				ctxid = jcidVersionProxy.VersionHistoryGraphSpaceContextNodes
				rid = self.object_space.GetContextRevisionId(ctxid)
				revision_ctx = revisions.pop(rid, None)
				if revision_ctx is not None:
					versions.append(revision_ctx)
				continue

		if self.root_revision_ctx is not None:
			versions.append(self.root_revision_ctx)

		# Add the remaining non-timestamped revisions to the dictionary
		self.revisions.update(revisions)

		for revision_ctx in sorted(versions, key=lambda ver: ver.last_modified_timestamp):
			# Put timestamped revisions in sorted order to the dictionary
			self.revisions[revision_ctx.rid] = revision_ctx
			continue

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
