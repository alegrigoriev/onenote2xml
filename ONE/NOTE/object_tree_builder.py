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
from types import SimpleNamespace
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
		self.page_persistent_guid:GUID = None

		# Build all roles
		for role in self.revision.GetRootObjectRoles():
			oid = self.revision.GetRootObjectId(role)
			root_obj = self.GetObjectReference(oid)
			self.revision_roles[role] = root_obj

			if role == self.ROOT_ROLE_REVISION_METADATA:
				self.last_modified_timestamp = getattr(root_obj, 'LastModifiedTimeStamp', self.last_modified_timestamp)
			elif role == self.ROOT_ROLE_PAGE_METADATA:
				self.page_persistent_guid = str(getattr(root_obj, 'NotebookManagementEntityGuid', self.page_persistent_guid))
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
			print("%s (%d): GUID=%s, Author=%s" % (
				GetFiletime64Datetime(self.last_modified_timestamp),
				Filetime64ToUnixTimestamp(self.last_modified_timestamp),
				self.page_persistent_guid,
				self.last_modified_by,
				), file=fd)
		else:
			print("                                        GUID=%s, Author=%s" % (
				self.page_persistent_guid,
				self.last_modified_by,
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
		self.versions = [] # Sorted in ascending order of timestamp
		self.version_timestamps = []

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
			# Put history revisions in sorted order to the revisions and versions dictionaries
			self.revisions[revision_ctx.rid] = revision_ctx
			self.versions.append(revision_ctx)
			self.version_timestamps.append(revision_ctx.last_modified_timestamp)
			continue

		return

	def GetVersionByTimestamp(self, timestamp, lower_bound=False, upper_bound=False)->RevisionBuilderCtx:
		if upper_bound:
			# Returns a most recent version with last_modified_timestamp <= timestamp
			for rev in reversed(self.versions):
				if rev.last_modified_timestamp <= timestamp:
					return rev
				continue
		elif lower_bound:
			# Returns a least recent version with last_modified_timestamp >= timestamp
			for rev in self.versions:
				if rev.last_modified_timestamp >= timestamp:
					return rev
				continue
		else:
			# Returns a version with last_modified_timestamp == timestamp
			for rev in self.versions:
				if rev.last_modified_timestamp > timestamp:
					break
				if rev.last_modified_timestamp == timestamp:
					return rev
				continue
		return None

	def GetVersionTimestamps(self):
		return self.version_timestamps

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
		self.versions = None
		self.version_timestamps = []

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

		for version in self.GetVersions():
			print("\nVersion", GetFiletime64Datetime(version.LastModifiedTimeStamp), file=fd)
			for guid, page_ctx in version.directory.items():
				print(guid, page_ctx.gosid, file=fd)
		return

	def GetVersions(self):
		if self.versions is not None:
			return self.versions

		'''
		History is generated starting backwards from the current view,
		using the initial view from the root index. Each item in the root index has "topology created"
		timestamp. Inject these timestamps to the timestamp sequence to build.

		Changes in page index topology are saved in the history of the root object space.
		But revisions other than a root one are useless, because the revisions doesn't get timestamped properly,
		and the root object space doesn't have any history metadata.
		For example, if you move a page in the index, a new revision is created, but there's no new timestamp of the change.

		We'll build the tree starting from the oldest revision, using the root revision of the index
		'''

		self.versions = []
		rev = None

		timestamps = set()
		object_space_tree = {} # Indexed by OSID
		# Parse the root index page. Only one revision is really useful.
		root_object_space = self.object_spaces[self.root_gosid]
		index_revision = root_object_space.GetRootRevision()
		for page_series in getattr(index_revision.GetRootObject(), 'ElementChildNodes', ()):
			# MetaDataObjectsAboveGraphSpace = getattr(page_series, 'MetaDataObjectsAboveGraphSpace', ())
			# Because OneNote team doesn't have adult supervision,
			# there can be a stray item in MetaDataObjectsAboveGraphSpace.
			# Thus, we'll just use metadata from the root revision of the object space
			ChildGraphSpaceElementNodes = getattr(page_series, 'ChildGraphSpaceElementNodes', ())
			for object_space_id in ChildGraphSpaceElementNodes:
				object_space_ctx = self.object_spaces.get(object_space_id, None)
				if object_space_ctx is None:
					continue

				timestamps |= set(object_space_ctx.GetVersionTimestamps())

				object_space_tree[object_space_ctx.gosid] = object_space_ctx

		timestamps = sorted(timestamps)

		prev_version_tree_list = []
		for timestamp in timestamps:
			revision_ctx_list:list[RevisionBuilderCtx] = []
			for object_space_ctx in object_space_tree.values():
				revision_ctx = object_space_ctx.GetVersionByTimestamp(timestamp, upper_bound=True)
				if revision_ctx is not None:
					revision_ctx_list.append(revision_ctx)
				continue

			if not revision_ctx_list:
				continue

			revision_ctx_list.sort(key=lambda rev: rev.last_modified_timestamp)
			Author = revision_ctx_list[-1].last_modified_by
			version_timestamp = revision_ctx_list[-1].last_modified_timestamp

			version_tree = {}
			for revision_ctx in revision_ctx_list:
				guid = revision_ctx.page_persistent_guid
				if guid not in version_tree:
					version_tree[guid] = revision_ctx
					continue

				prev_revision_ctx = version_tree[guid]
				if prev_revision_ctx.last_modified_timestamp < revision_ctx.last_modified_timestamp:
					version_tree[guid] = revision_ctx
					for i in range(1,100):
						ext_guid = "%s-%d" % (guid, i)
						if ext_guid not in version_tree:
							break
						del version_tree[ext_guid]
						continue
				elif revision_ctx is not prev_revision_ctx:
					for i in range(1,100):
						ext_guid = "%s-%d" % (guid, i)
						if ext_guid not in version_tree:
							version_tree[ext_guid] = revision_ctx
							break
						continue

				continue

			# Re-sort the tree in object space order
			sorted_version_tree = sorted(version_tree.items(), key=lambda rev: rev[1].os_index)
			version_tree = {}
			for guid, revision_ctx in sorted_version_tree:
				version_tree[guid] = revision_ctx
				continue

			# Sort in GUID (first item in the tuples) order
			tree_list = sorted(*version_tree.items())

			# See if the previous version_tree is identical
			if prev_version_tree_list == tree_list:
				continue

			if rev is None \
				or version_timestamp != rev.LastModifiedTimeStamp \
				or (rev.Author is not None \
					and Author is not None \
					and rev.Author != Author):
				rev = SimpleNamespace(
									directory=version_tree,
									CreatedTimeStamp=version_timestamp,
									Author=Author,
									)
				self.versions.append(rev)
			else:
				rev.directory = version_tree

			rev.LastModifiedTimeStamp=version_timestamp
			prev_version_tree_list = tree_list
			continue

		return self.versions
