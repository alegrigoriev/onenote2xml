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
from ..base_types import *

class OneNote:
	ROOT_NODE_NAME = None

	def __init__(self, onestore=None, filename=None, options=None, log_file=None):
		self.onestore = onestore
		self.filename = filename
		self.options = options
		self.log_file = log_file
		return

	@staticmethod
	def open(filename, options, log_file=None)->OneNote:
		from ..STORE.onestore import OneStoreFile
		onefile = OneStoreFile.open(filename, options, log_file=log_file)
		if onefile.IsNotebookSection():
			return OneNotebookSection(onefile, filename, options, log_file=log_file)
		elif onefile.IsNotebookToc2():
			return OneNotebookToc2(onefile, filename, options, log_file=log_file)

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, exception_traceback):
		return False

	def GetDefaultTreeBuilder(self, options):
		from ..NOTE.object_tree_builder import ObjectTreeBuilder
		tree_builder = ObjectTreeBuilder(onestore=self.onestore,
			property_set_factory=self.GetPropertySetFactory(), options=options)

		return tree_builder

	def MakeObjectTree(self, options=None):
		builder = self.GetDefaultTreeBuilder(options)
		if self.log_file is not None:
			builder.dump(self.log_file, self.options.verbose)
		return builder

	def MakeXmlFile(self, filename, options):
		from xml.etree import ElementTree as ET
		xml_tree = self.MakeXmlTree(options)

		element_tree = ET.ElementTree(xml_tree)
		ET.indent(element_tree, '  ')
		with open(filename, 'wb') as file:  # element_tree.write does its own encoding
			element_tree.write(file,
						# Use default 'ascii' encoding to encode extended characters as escape sequences
						encoding='ascii',
						xml_declaration=True,
						short_empty_elements=getattr(options, 'short_empty_elements', True))
		return

	def MakeXmlRevisions(self, directory, options):
		xml_builder = self.GetXmlBuilder(options)
		xml_builder.MakeVersionFiles(directory, options)
		return

	def MakeXmlTree(self, options):
		xml_builder = self.GetXmlBuilder(options)
		if self.log_file is not None:
			xml_builder.dump(self.log_file, self.options.verbose)
		return xml_builder.BuildXmlTree(self.ROOT_NODE_NAME, options)

	def GetXmlBuilder(self, options=None):
		from ..XML.xml_tree_builder import XmlTreeBuilder

		return XmlTreeBuilder(self.onestore,
							self.GetXmlPropertySetFactory(), options=options)

	def GetJsonBuilder(self, options):
		from ..JSON.json_tree_builder import JsonTreeBuilder

		return JsonTreeBuilder(self.onestore,
							self.GetJsonPropertySetFactory(), options=options)

	def MakeJsonFile(self, filename, options=None):
		obj_tree = self.MakeJsonTree(options)
		import json

		with open(filename, 'wt') as file:
			json.dump(obj_tree, file, indent='\t')
		return

	def MakeJsonTree(self, options):
		json_builder = self.GetJsonBuilder(options)
		if self.log_file is not None:
			json_builder.dump(self.log_file, options.verbose)
		root = json_builder.BuildJsonTree(self.ROOT_NODE_NAME, options)
		return root

	def MakeJsonRevisions(self, directory, options):
		json_builder = self.GetJsonBuilder(options)
		json_builder.MakeVersionFiles(directory, options)
		return

	def dump(self, fd, verbose=None):
		self.onestore.dump(fd, verbose)
		return

	def IsNotebookSection(self):
		return self.onestore.IsNotebookSection()

	def IsNotebookToc2(self):
		return self.onestore.IsNotebookToc2()

	def GetVersions(self):
		return self.GetDefaultTreeBuilder().GetVersions()

	def PrintVersions(self, fd, human_friendly=True):
		for version in self.GetVersions():

			if human_friendly:
				print("Edited at %s by %s" % (
					GetFiletime64Datetime(version.LastModifiedTimeStamp),
					version.Author,
					), file=fd)
			else:
				print("%d %d\t%s" % (
					version.LastModifiedTimeStamp,
					Filetime64ToUnixTimestamp(version.LastModifiedTimeStamp),
					version.Author,
					), file=fd)

		return

class OneNotebookSection(OneNote):
	ROOT_NODE_NAME = "NotebookSection"

	def IsNotebookSection(self):
		assert (self.onestore.IsNotebookSection())
		return True

	def IsNotebookToc2(self):
		assert (not self.onestore.IsNotebookToc2())
		return False

	def GetPropertySetFactory(self):
		from .property_set_object_factory import OneNotebookPropertySetFactory as property_set_factory
		return property_set_factory

	def GetXmlPropertySetFactory(self):
		from ..XML.property_set_element_factory import OneNotebookXmlPropertySetFactory as property_set_element_factory
		return property_set_element_factory

	def GetJsonPropertySetFactory(self):
		from ..JSON.json_property_set_factory import OneNotebookJsonPropertySetFactory as property_set_factory
		return property_set_factory

class OneNotebookToc2(OneNote):
	ROOT_NODE_NAME = "NotebookToc2"

	def IsNotebookSection(self):
		assert (not self.onestore.IsNotebookSection())
		return False

	def IsNotebookToc2(self):
		assert (self.onestore.IsNotebookToc2())
		return True

	def GetPropertySetFactory(self):
		from .property_set_object_factory import OneToc2PropertySetFactory as property_set_factory
		return property_set_factory

	def GetXmlPropertySetFactory(self):
		from ..XML.property_set_element_factory import OneToc2XmlPropertySetFactory as property_set_element_factory
		return property_set_element_factory

	def GetJsonPropertySetFactory(self):
		from ..JSON.json_property_set_factory import OneToc2JsonPropertySetFactory as property_set_factory
		return property_set_factory
