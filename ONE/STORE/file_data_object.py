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
from ..exception import UnrecognizedFileDataException
from .property_set import PropertySet

class FileDataObject(PropertySet):
	def __init__(self, onestore, node):
		super().__init__(node.jcid)
		self.data = None
		self.guid = None
		self.extension = node.Extension
		self.filename = None
		self.data_filename = None
		self.reference = node.FileDataReference
		if self.reference.startswith('<file>'):
			# A file in the onefiles folder
			self.filename = self.reference.removeprefix('<file>')
			# The file is located in onefiles folder:
			'''
			onefiles folder: A folder that stores file data objects for a OneNote revision store file.
			It is located in the same directory as the revision store file and the folder name maps to the name of the revision store file.
			For example, if the revision store file is named "section.one" the onefiles folder is named "section_onefiles".
			'''
			self.data_filename = self.filename + self.extension
			# Read data from the referred file
			# The file extension shall be .onebin
			# The actual extension is self.extension
		elif self.reference.startswith('<ifndf>'):
			# FileDataStoreObject
			self.guid = GUID(self.reference.removeprefix('<ifndf>'))
			self.data_filename = str(self.guid) + self.extension
			# DataFileStoreList haven't been loaded yet at this time
		elif self.reference.startswith('<invfdo>'):
			# Invalid data, ignore
			return
		else:
			raise UnrecognizedFileDataException('Unrecognized FileDataReference in ObjectDeclarationFileData3 structure: "%s"' % (self.reference))
		return

	def GetFilename(self):
		return self.data_filename

	def dump(self, fd, verbose=None):
		super().dump(fd, verbose)

		print("Reference: %s" % (self.reference,), file=fd)
		print("Extension: %s" % (self.extension,), file=fd)
		return
