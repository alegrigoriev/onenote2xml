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
import sys
from typing import Iterable
from types import SimpleNamespace
from ..base_types import *
from ..exception import CircularObjectReferenceException, ObjectNotFoundException
from ..STORE.revision_manifest_list import RevisionManifest
from ..STORE.onestore import OneStoreFile
from pathlib import Path

def GetTopologyCreationTimeStamps(obj):
	timestamps = []
	# Get all property sets with TopologyCreationTimeStamp property
	for paths, props in obj:
		if paths[-1] == 'TopologyCreationTimeStamp':
			timestamps.append(props[-2])
		continue
	return sorted(timestamps, key=lambda t:t.TopologyCreationTimeStamp, reverse=True)

class DataFileCtx:
	def __init__(self, filename, data):
		self.data = data
		self.filename = filename
		self.page_persistent_guid = filename
		return

	def MakeFile(self, directory, guid):
		full_path = Path(directory, self.filename)
		full_path.write_bytes(self.data)
		return

	def IsFile(self):
		return True

	def GetFilename(self):
		return self.filename

	def GetHash(self):
		return b''

	def GetData(self):
		return self.data

	def GetTitle(self):
		return None

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
		self.is_encrypted = revision.IsEncrypted()

		self.last_modified_timestamp = None
		self.last_modified_by = None

		self.revision_roles = {}
		self.obj_dict = {}
		self.data_objects = {}
		self.page_persistent_guid:GUID = None
		self.filename = None
		self.page_title = 'notitle'
		self.page_level = None
		self.page_hash = b''
		self.conflict_author = None
		self.conflicts = {}

		# Build all roles
		for role in self.revision.GetRootObjectRoles():
			oid = self.revision.GetRootObjectId(role)
			root_obj = self.GetObjectReference(oid)
			self.revision_roles[role] = root_obj

			if role == self.ROOT_ROLE_REVISION_METADATA:
				if not self.conflict_author:
					self.last_modified_timestamp = getattr(root_obj, 'LastModifiedTimeStamp', self.last_modified_timestamp)
				last_modified_by = getattr(root_obj, 'AuthorMostRecent', None)
				self.last_modified_by = getattr(last_modified_by, 'Author', None)
				# Not part of page_hash
			elif role == self.ROOT_ROLE_PAGE_METADATA:
				self.page_persistent_guid = str(getattr(root_obj, 'NotebookManagementEntityGuid', ""))
				self.page_title = getattr(root_obj, 'CachedTitleString', self.page_title)
				self.page_level = getattr(root_obj, 'PageLevel', None)
				self.page_hash += root_obj.get_hash()
				self.has_conflict_pages = getattr(root_obj, 'HasConflictPages', False)
				self.conflict_author = getattr(root_obj, 'ConflictingUserName', None)
				if self.conflict_author:
					# For conflict pages, an actual usable timestamp is in TopologyCreationTimeStamp
					self.last_modified_timestamp = getattr(root_obj, 'TopologyCreationTimeStamp', self.last_modified_timestamp)
			elif role == self.ROOT_ROLE_CONTENTS:
				self.page_hash += root_obj.get_hash()
				if root_obj._jcid_name == 'jcidSectionNode':
					self.page_title = 'Section root'
					# If this is a root page, find the most recent TopologyCreationTimeStamp
					if self.last_modified_timestamp is None:
						topology_creation_timestamps = GetTopologyCreationTimeStamps(root_obj)
						if topology_creation_timestamps:
							self.last_modified_timestamp = topology_creation_timestamps[0].TopologyCreationTimeStamp

				ChildGraphSpaceElementNodes = getattr(root_obj, 'ChildGraphSpaceElementNodes', None)
				if not ChildGraphSpaceElementNodes:
					continue
				# The metadata object OID is made from OSID in ChildGraphSpaceElementNodes by XOR with GUID
				# { 0x22a8c031, 0x3600, 0x42ee, { 0xb7, 0x14, 0xd7, 0xac, 0xda, 0x24, 0x35, 0xe8 } },
				# or {22a8c031-3600-42ee-b714-d7acda2435e8}.
				seed_guid = ExGUID(b'\x31\xC0\xA8\x22\x00\x36\xEE\x42\xb7\x14\xD7\xAC\xDA\x24\x35\xE8', 0)
				metadata_objects = {}
				MetaDataObjectsAboveGraphSpace = getattr(root_obj, 'MetaDataObjectsAboveGraphSpace', ())
				for metadata_obj in MetaDataObjectsAboveGraphSpace:
					metadata_objects[metadata_obj._oid ^ seed_guid] = metadata_obj
					continue

				for conflict_space in ChildGraphSpaceElementNodes:
					self.conflicts[conflict_space] = metadata_objects.get(conflict_space, None)
					continue
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

	def GetDataStoreObject(self, guid, extension):
		filename = str(guid) + extension
		obj = self.data_objects.get(filename, None)
		if obj is None:
			obj = DataFileCtx(filename, self.onestore.GetDataStoreObjectData(guid))
			obj.os_index = self.os_index
			self.data_objects[filename] = obj
		return obj

	def ReadOnefile(self, onefilename, extension):
		filename = onefilename + extension
		obj = self.data_objects.get(filename, None)
		if obj is None:
			obj = DataFileCtx(filename, self.onestore.ReadOnefile(onefilename))
			obj.os_index = self.os_index
			self.data_objects[filename] = obj
		return obj

	def IsFile(self):
		return False

	def GetFilename(self):
		return self.filename or self.page_persistent_guid

	def GetTitle(self):
		return self.page_title

	def GetPageLevel(self):
		return self.page_level

	def GetHash(self):
		return self.page_hash

	def dump(self, fd, verbose=None):
		if self.conflict_author:
			print("%s (%d): GUID=%s, Level=%s, Author=%s, ConflictAuthor=%s, title=%s" % (
				GetFiletime64Datetime(self.last_modified_timestamp),
				Filetime64ToUnixTimestamp(self.last_modified_timestamp),
				self.page_persistent_guid,
				self.page_level,
				self.last_modified_by,
				self.conflict_author,
				self.page_title,
				), file=fd)
		elif self.last_modified_timestamp is not None:
			print("%s (%d): GUID=%s, Level=%s, Author=%s, title=%s" % (
				GetFiletime64Datetime(self.last_modified_timestamp),
				Filetime64ToUnixTimestamp(self.last_modified_timestamp),
				self.page_persistent_guid,
				self.page_level,
				self.last_modified_by,
				self.conflict_author,
				self.page_title,
				), file=fd)
		else:
			print("                                        GUID=%s, Author=%s, title=%s" % (
				self.page_persistent_guid,
				self.page_level,
				self.last_modified_by,
				self.page_title,
				), file=fd)

		for gosid, metadata in self.conflicts.items():
			print("\tConflict page GOSID=%s GUID=%s author=%s" %
					(gosid, metadata.NotebookManagementEntityGuid,metadata.ConflictingUserName), file=fd)
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
		self.is_conflict_space = False

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
		if history_revision_ctx is not None and not history_revision_ctx.is_encrypted:
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

		for revision_ctx in sorted(versions, key=lambda ver: ver.last_modified_timestamp if ver.last_modified_timestamp is not None else 0):
			# Put history revisions in sorted order to the revisions and versions dictionaries
			self.revisions[revision_ctx.rid] = revision_ctx
			if revision_ctx.is_encrypted:
				continue

			self.versions.append(revision_ctx)
			self.version_timestamps.append(revision_ctx.last_modified_timestamp)
			if revision_ctx.conflict_author:
				self.is_conflict_space = True
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
		print("\nObject Space %s%s" % (self.gosid, " CONFLICT" if self.is_conflict_space else ""), file=fd)
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
		# The option value is in minutes
		self.combine_revisions_time_span = getattr(options, 'combine_revisions', 0)
		# Convert to 100 ns units of Windows FILETIME
		self.combine_revisions_time_span *= 60 * 1000 * 10000

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
				assert(not object_space_ctx.is_conflict_space)

				timestamps |= set(object_space_ctx.GetVersionTimestamps())

				object_space_tree[object_space_ctx.gosid] = object_space_ctx

		for object_space_ctx in self.object_spaces.values():
			if object_space_ctx.is_conflict_space:
				timestamps |= set(object_space_ctx.GetVersionTimestamps())
			continue

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
				elif revision_ctx.GetHash() != prev_revision_ctx.GetHash():
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

				# Add conflict pages
				for gosid in revision_ctx.conflicts:
					obj_space_ctx = self.object_spaces[gosid]
					conflict_ctx = obj_space_ctx.GetVersionByTimestamp(revision_ctx.last_modified_timestamp, upper_bound=True)
					if conflict_ctx is not None:
						ext_guid = "%s-conflict-%s" % (guid, conflict_ctx.page_persistent_guid)
						version_tree[ext_guid] = conflict_ctx
					continue

				for guid, data_obj in revision_ctx.data_objects.items():
					version_tree[guid] = data_obj

				continue

			# Sort in GUID (first item in the tuples) order
			tree_list = sorted((guid, item_ctx.GetHash()) for guid, item_ctx in version_tree.items())

			# See if the previous version_tree is identical
			if prev_version_tree_list == tree_list:
				continue

			if rev is None \
				or (version_timestamp != rev.LastModifiedTimeStamp \
					and version_timestamp - rev.CreatedTimeStamp >= self.combine_revisions_time_span) \
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

	def _WriteVersionFiles(self, version, directory, prev_directory={}, incremental=False):
		changed = []

		for guid, item_ctx in version.directory.items():
			prev_item = prev_directory.get(guid, None)
			if prev_item is not None:
				if prev_item.GetHash() != item_ctx.GetHash():
					changed.append(item_ctx)
				elif incremental:
					continue

			item_ctx.MakeFile(directory, guid)
			continue

		with open(Path(directory, 'index.txt'), 'wt') as pages_file:
			for item_ctx in version.directory.values():
				if item_ctx.IsFile():
					continue
				print("%s%s:%s" % ('\t' * (item_ctx.GetPageLevel()-1), item_ctx.GetFilename(), item_ctx.GetTitle()), file=pages_file)
		return changed

	def MakeVersionFiles(self, directory, options):
		directory = Path(directory)
		if directory.is_dir():
			# Check if it's not empty
			for _ in directory.iterdir():
				print("WARNING: Versions directory %s is not empty: will not clean it." % (str(directory)), file=sys.stderr)
				break
		else:
			directory.mkdir(parents=True)

		if not getattr(options, 'all_revisions', False):
			timestamp = getattr(options, 'timestamp', None)
			if timestamp is not None:
				version = self.GetVersionByTimestamp(timestamp, upper_bound=True)
				if version is None:
					return
			else:
				version = self.GetVersions()[-1]
			return self._WriteVersionFiles(version, directory)

		incremental = getattr(options, 'incremental', False)

		versions_list = []

		versions_file = open(Path(directory, 'versions.txt'), 'wt')
		prev_directory = {}
		for version in self.GetVersions():
			timestamp = version.LastModifiedTimeStamp
			datetime = GetFiletime64Datetime(timestamp, local=False)
			version_str = datetime.isoformat().replace(':', '-').removesuffix('+00-00')
			print("Edited on %s by %s" % (version_str, version.Author), file=sys.stderr)
			version_dir = Path(directory, version_str)
			version_dir.mkdir(exist_ok=True)

			changed = self._WriteVersionFiles(version, version_dir, prev_directory, incremental)

			print('[version "v%d"]' % (timestamp), file=versions_file)
			print('\tAUTHOR =', version.Author, file=versions_file)
			print('\tTIMESTAMP = %d' % (Filetime64ToUnixTimestamp(timestamp),), file=versions_file)
			print('\tDIRECTORY =', version_str, file=versions_file)

			def sort_key(rev):
				return (rev.os_index, rev.page_persistent_guid)

			added = sorted((version.directory[guid] for guid in set(version.directory) - set(prev_directory)),
							key=sort_key)
			deleted = sorted((prev_directory[guid] for guid in set(prev_directory) - set(version.directory)),
							key=sort_key)
			# messages will contain tuples of (guid, msg)
			messages = []

			for item_ctx in added:
				print('\tADDED = %s' + item_ctx.GetFilename(), file=versions_file)
				if title := item_ctx.GetTitle():
					messages.append((item_ctx, 'Added page: ' + title))
				continue

			for item_ctx in changed:
				print('\tMODIFIED = ' + item_ctx.GetFilename(), file=versions_file)
				if title := item_ctx.GetTitle():
					messages.append((item_ctx, 'Modified page: ' + title))
				continue

			for item_ctx in deleted:
				print('\tDELETED = ' + item_ctx.GetFilename(), file=versions_file)
				if title := item_ctx.GetTitle():
					messages.append((item_ctx, 'Deleted page: ' + title))
				continue

			if len(messages) == 1:
				title = messages[0][1]
				messages.clear()
			else:
				if added:
					title = "Added"
					if changed:
						title += ", modified"
				elif changed:
					title = "Modified"

				if deleted:
					title += ", deleted" if title else "Deleted"
				title += ' pages'
			print('\tTITLE = ' + title, file=versions_file)

			for _, msg in sorted(messages, key=lambda rev: rev[0].os_index):
				print('\tMESSAGE = ' + msg, file=versions_file)

			print(file=versions_file)

			versions_list.append((timestamp, version_str))
			prev_directory = version.directory
			continue

		print('[versions]', file=versions_file)
		if incremental:
			print('\tincremental = true', file=versions_file)

		for timestamp, section in versions_list:
			print('\tv%d = %s' % (timestamp, section), file=versions_file)
		versions_file.close()

		return

	def GetVersionByTimestamp(self, timestamp, lower_bound=False, upper_bound=False):
		if upper_bound:
			# Returns a most recent version with CreatedTimeStamp <= timestamp
			for ver in reversed(self.GetVersions()):
				if ver.CreatedTimeStamp <= timestamp:
					return ver
				continue
		elif lower_bound:
			# Returns a least recent version with CreatedTimeStamp >= timestamp
			for ver in self.GetVersions():
				if ver.CreatedTimeStamp >= timestamp:
					return ver
				continue
		else:
			# Returns a version with CreatedTimeStamp == timestamp
			for ver in self.GetVersions():
				if ver.CreatedTimeStamp > timestamp:
					break
				if ver.CreatedTimeStamp == timestamp:
					return ver
				continue
		return None
