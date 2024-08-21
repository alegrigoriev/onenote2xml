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

def MakeReadonlyXmlTree(read_only_types_dict):
	readonly_element = ET.Element('ReadonlyObjects')

	# Generate these items in stable sorted order, to be version control friendly
	for read_only_type, read_only_type_dict in sorted(read_only_types_dict.items(), key=lambda k: k[0]):
		readonly_subelement = ET.SubElement(readonly_element, read_only_type)
		for key, subelement in sorted(read_only_type_dict.items(), key=lambda k: k[0]):
			subelement.set('ID', key)
			readonly_subelement.append(subelement)
	return readonly_element

class XmlRevisionBuilderCtx(RevisionBuilderCtx):
	def __init__(self, property_set_factory, revision, object_space_ctx):
		self.compact = getattr(object_space_ctx.options, 'compact', False)
		self.include_oids = getattr(object_space_ctx.options, 'include_oids', False)
		super().__init__(property_set_factory, revision, object_space_ctx)
		return

	def GetRevisionXmlTree(self, tag):

		read_only_types_dict = {}
		revision_tree = self.GetXmlTree(tag, read_only_types_dict)
		revision_tree.append(MakeReadonlyXmlTree(read_only_types_dict))

		return revision_tree

	def GetXmlTree(self, tag, read_only_types_dict):
		# All roles are included in the tree
		revision_element = ET.Element(tag)

		self.read_only_types_dict = read_only_types_dict

		if self.verbosity < 4:
			for role in reversed(self.revision_roles):
				role_tree = self.GetRootObject(role)
				element = role_tree.MakeXmlElement(self)

				# Below verbosity 4, all roles are appended to the root element
				if element:
					revision_element.append(element)
				continue
		else:
			for role in self.revision_roles:
				role_tree = self.GetRootObject(role)

				root_element = ET.SubElement(revision_element, 'Root',
										{ 'Role' : str(role)})

				element = role_tree.MakeXmlElement(self)
				root_element.append(element)
				continue

		self.read_only_types_dict = None

		return revision_element

	def AppendXmlElementReference(self, parent_element, propset_obj):
		if propset_obj is None:
			return
		if propset_obj.min_verbosity > self.verbosity:
			return

		if propset_obj.is_read_only():
			# Use one from the read-only object cache (per object space)
			readonly_space = propset_obj.READONLY_SPACE
			if readonly_space is NotImplemented:
				readonly_space = propset_obj._jcid_name
			read_only_dict = self.read_only_types_dict.setdefault(readonly_space, {})
			key = str(GUID(propset_obj.get_hash()))
			if key not in read_only_dict:
				read_only_dict[key] = propset_obj.MakeXmlElement(self)

			element = ET.Element(propset_obj._jcid_name, { "ID" : key, })
		else:
			element = propset_obj.MakeXmlElement(self)

		if element is not None:
			comment:str = propset_obj.MakeXmlComment()
			if comment:
				parent_element.append(ET.Comment(' ' + comment + ' '))
			parent_element.append(element)
		return

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
