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

	def dump(self, fd, verbose=None):
		self.onestore.dump(fd, verbose)
		return

	def IsNotebookSection(self):
		return self.onestore.IsNotebookSection()

	def IsNotebookToc2(self):
		return self.onestore.IsNotebookToc2()

class OneNotebookSection(OneNote):

	def IsNotebookSection(self):
		assert (self.onestore.IsNotebookSection())
		return True

	def IsNotebookToc2(self):
		assert (not self.onestore.IsNotebookToc2())
		return False

	def GetPropertySetFactory(self):
		from .property_set_object_factory import OneNotebookPropertySetFactory as property_set_factory
		return property_set_factory

class OneNotebookToc2(OneNote):

	def IsNotebookSection(self):
		assert (not self.onestore.IsNotebookSection())
		return False

	def IsNotebookToc2(self):
		assert (self.onestore.IsNotebookToc2())
		return True

	def GetPropertySetFactory(self):
		from .property_set_object_factory import OneToc2PropertySetFactory as property_set_factory
		return property_set_factory
