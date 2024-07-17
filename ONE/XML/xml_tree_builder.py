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
from ..NOTE.object_tree_builder import RevisionBuilderCtx,ObjectSpaceBuilderCtx, ObjectTreeBuilder
from xml.etree import ElementTree as ET

class XmlRevisionBuilderCtx(RevisionBuilderCtx):
	def __init__(self, property_set_factory, revision, object_space_ctx):
		self.compact = getattr(object_space_ctx.options, 'compact', False)
		super().__init__(property_set_factory, revision, object_space_ctx)
		return

	def GetRevisionXmlTree(self, tag):

		revision_tree = self.GetXmlTree(tag)

		return revision_tree

	def GetXmlTree(self, tag):
		# All roles are included in the tree
		revision_element = ET.Element(tag)

		for role in self.revision_roles:
			role_tree = self.GetRootObject(role)
			root_element = ET.SubElement(revision_element, 'Root',
									{ 'Role' : str(role)})

			element = role_tree.MakeXmlElement(self)
			root_element.append(element)
			continue

		return revision_element

class XmlObjectSpaceBuilderCtx(ObjectSpaceBuilderCtx):
	REVISION_BUILDER = XmlRevisionBuilderCtx

	def GetRootRevisionXmlTree(self, tag):
		return self.root_revision_ctx.GetRevisionXmlTree(tag)

class XmlTreeBuilder(ObjectTreeBuilder):
	OBJECT_SPACE_BUILDER = XmlObjectSpaceBuilderCtx

	def BuildXmlTree(self, root_tree_name:str, options):

		root_tree = ET.Element(root_tree_name)

		for gosid, object_space_ctx in self.object_spaces.items():
			# Add nondefault context nodes for non-root object spaces
			if gosid == self.root_gosid:
				continue
			object_space_tree = object_space_ctx.GetRootRevisionXmlTree('Page')
			root_tree.append(object_space_tree)
			continue
		return root_tree
