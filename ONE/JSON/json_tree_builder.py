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
from ..NOTE.object_tree_builder import *

class JsonRevisionTreeBuilderCtx(RevisionBuilderCtx):
	def __init__(self, property_set_factory, revision, object_space_ctx):
		super().__init__(property_set_factory, revision, object_space_ctx)
		return

	def MakeJsonTree(self):
		# All roles are included in the tree
		obj = {}

		for role in self.revision_roles:
			role_tree = self.GetRootObject(role)
			obj.update(role_tree.MakeJsonNode(self))

		return obj

class JsonObjectSpaceBuilderCtx(ObjectSpaceBuilderCtx):
	REVISION_BUILDER = JsonRevisionTreeBuilderCtx

	def MakeRootJsonTree(self):
		return self.root_revision_ctx.MakeJsonTree()

class JsonTreeBuilder(ObjectTreeBuilder):
	OBJECT_SPACE_BUILDER = JsonObjectSpaceBuilderCtx

	def BuildJsonTree(self, root_tree_name:str, options):
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
