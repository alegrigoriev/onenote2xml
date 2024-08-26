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

'''

Section->[PageSeriesNode,...]

PageSeriesNode->[Page ObjectSpace]

Page ObjectSpace->jcidPageManifestNode (content, 1)
Page ObjectSpace->jcidPageMetaData (metadata, 2)
Page ObjectSpace->jcidRevisionMetaData (version metadata, 2)

jcidPageMetaData->PageLevel (1...3)
jcidPageManifestNode->[jcidPageNode, ...]
jcidPageManifestNode->ChildGraphSpaceElementNodes->[Page ObjectSpace] for conflict pages

jcidPageNode->StructureElementChildNodes->[jcidTitleNode]
jcidPageNode->ElementChildNodesOfPage->[jcidOutlineNode|jcidImageNode|jcidEmbeddedFileNode]


jcidTitleNode->ElementChildNodesOfTitle->[jcidOutlineNode|jcidOutlineGroup]

jcidOutlineNode->ElementChildNodesOfOutline[jcidOutlineGroup|jcidOutlineElementNode]

jcidOutlineElementNode->ElementChildNodesOfOutlineElement->[jcidOutlineGroup|jcidOutlineElementNode]
jcidOutlineElementNode->ContentChildNodesOfOutlineElement->[jcidRichTextOENode|jcidTableNode|jcidImageNode|jcidEmbeddedFileNode]
jcidOutlineElementNode->ListNodes->[jcidNumberListNode...]

jcidTableNode->RowCount
jcidTableNode->ColumnCount
jcidTableNode->TableColumnWidths[]
jcidTableNode->ElementChildNodesOfTable->jcidTableRowNode[RowCount]

jcidTableRowNode->ElementChildNodesOfTableRow->jcidTableCellNode[ColumnCount]

jcidTableCellNode->ElementChildNodesOfTableCell->[jcidOutlineElementNode...]     jcidOutlineGroup SHOULD NOT be used
jcidTableCellNode->OutlineElementChildLevel == 0x01

'''

from ..base_types import *
from ..NOTE.object_tree_builder import *

class JsonRevisionTreeBuilderCtx(RevisionBuilderCtx):
	def __init__(self, property_set_factory, revision, object_space_ctx):
		self.include_oids = getattr(object_space_ctx.options, 'include_oids', False)
		self.filename = None
		self.full_path = None
		self.file_data = None
		super().__init__(property_set_factory, revision, object_space_ctx)
		return

	def MakeJsonTree(self):
		# All roles are included in the tree
		obj = {}

		for role in self.revision_roles:
			role_tree = self.GetRootObject(role)
			obj.update(role_tree.MakeJsonNode(self))

		if self.is_encrypted:
			obj['IsEncrypted'] = True

		return obj

	def MakeFile(self, directory, guid):
		from pathlib import Path
		import json

		if self.full_path is not None:
			assert(self.filename == guid + '.json')
			if self.file_data is None:
				self.file_data = self.full_path.read_bytes()

			Path(directory, self.filename).write_bytes(self.file_data)
			return

		self.filename = guid + '.json'
		self.full_path = Path(directory, self.filename)

		obj_tree = self.MakeJsonTree()

		with open(self.full_path, 'wt') as file:
			json.dump(obj_tree, file, indent='\t')
		return

	def GetFilename(self):
		return self.filename

class JsonObjectSpaceBuilderCtx(ObjectSpaceBuilderCtx):
	REVISION_BUILDER = JsonRevisionTreeBuilderCtx

	def MakeRootJsonTree(self):
		return self.root_revision_ctx.MakeJsonTree()

	def MakeAllRevisionsJsonTree(self):
		# 'self' is object_space_factory_context from object_spaces dictionary
		# Root object is always role 1 of the NULL context
		# Other revision root objects are referred by contexts
		# Child elements:
		# RootRevision - ID of the root revision (forced first in Revisions)
		# Revisions - array of revisions (only those referred from the tree and contexts)

		revisions_dict = {}
		object_space_dict = {
			'type' : 'page',
			'revisions' : revisions_dict,
			}

		for revision_ctx in reversed(self.GetRevisions()):
			# These are only revisions referred by the root or contexts
			root_tree = revision_ctx.MakeJsonTree()
			if revision_ctx is self.root_revision_ctx:
				root_tree['root_revision'] = True
			revisions_dict[str(revision_ctx.rid)] = root_tree
			continue

		return object_space_dict

class JsonTreeBuilder(ObjectTreeBuilder):
	OBJECT_SPACE_BUILDER = JsonObjectSpaceBuilderCtx

	def BuildJsonTree(self, root_tree_name:str, options):
		'''
		Since a notebook can contain a collection of pages
		with nesting, the generated tree is an extension
		of Atlassian Document Format, with custom 'type' attributes.
		The tree will be massaged to a collection of Atlassian pages and media
		upon upload.
		'''

		if getattr(options, 'all_revisions', False):
			return self.BuildAllRevisionsJsonTree(root_tree_name)

		timestamp = getattr(options, 'timestamp', None)
		if timestamp is not None:
			return self.BuildRevisionJsonTree(root_tree_name, timestamp)

		pages = {}

		root_dict = {
			'type' : root_tree_name,
			'pages' : pages,
			}

		for gosid, object_space_ctx in self.object_spaces.items():
			# Add nondefault context nodes for non-root object spaces
			if gosid == self.root_gosid:
				continue
			pages[str(gosid)] = object_space_ctx.MakeRootJsonTree()
			continue
		return root_dict

	def BuildRevisionJsonTree(self, root_tree_name, timestamp):
		version = self.GetVersionByTimestamp(timestamp, upper_bound=True)
		if version is None:
			return None

		pages = {}
		root_dict = {
			'type' : root_tree_name,
			'pages' : pages,
			}

		for guid, item_ctx in version.directory.items():

			if item_ctx.IsFile():
				... # item_ctx.MakeFile(directory, guid)
			else:
				pages[str(guid)] = item_ctx.MakeJsonTree()
			continue

		return root_dict

	def BuildAllRevisionsJsonTree(self, root_tree_name:str):
		pages = {}

		root_object_space_ctx = self.object_spaces[self.root_gosid]
		root_page = root_object_space_ctx.MakeJsonTree()
		root_dict = {
			'type' : root_tree_name,
			'pageIndex' : root_page,
			'pages' : pages,
			}

		for gosid, object_space_ctx in self.object_spaces.items():
			# Add nondefault context nodes for non-root object spaces
			if gosid == self.root_gosid:
				continue
			pages[str(gosid)] = object_space_ctx.MakeAllRevisionsJsonTree()
			continue
		return root_dict

	@staticmethod
	def Validate(obj):
		import sys
		if obj is None:
			return True
		objtype = type(obj)
		if objtype is str \
			or objtype is int \
			or objtype is float \
			or objtype is bool:
			return True
		elif objtype is dict:
			for key,subobj in obj.items():
				if type(key) is not str:
					print("Type of key %s is %s, should be str" % (key, type(key).__name__), file=sys.stderr)
					return False
				if not JsonTreeBuilder.Validate(subobj):
					return False
		elif objtype is list or objtype is tuple:
			for subobj in obj:
				if not JsonTreeBuilder.Validate(subobj):
					return False
		else:
			print("Object type is %s" % (objtype.__name__), file=sys.stderr)
			return False
		return True
