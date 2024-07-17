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
from ..property_set_jcid import *
from ..STORE.property_set import PropertySet

class PropertySetObject:
	JCID = NotImplemented
	JCID_CLASS = PropertySetJCID
	from .property_object_factory import OneNotebookPropertyFactory as PROPERTY_FACTORY

	def __init__(self, jcid, oid):
		self._jcid:JCID = jcid
		self._oid = oid
		if self.JCID is NotImplemented:
			if jcid is not None:
				self._jcid_name = "jcid_%X" % (jcid.jcid,)
			else:
				self._jcid_name = "None"
		else:
			self._jcid_name = self.JCID.name
		self._display_name = self._jcid_name
		self._properties = {}
		return

	def __getattr__(self, name: str):
		try:
			return self._properties[name].get_object_value()
		except KeyError as e:
			raise AttributeError("'%s' object has no attribute '%s'" % (self._display_name, e.args[0]),self) from e

	def get(self, name:str, *default):
		return self._properties.get(name, *default)

	def make_object(self, revision_ctx, property_set:PropertySet):
		# parent revision contains oid->PropertySet table
		# object_table contains objects already built
		for prop in property_set.Properties():
			prop_obj = self.PROPERTY_FACTORY(prop)
			if prop_obj is NotImplemented:
				continue

			prop_obj.make_object(self, revision_ctx)

			self._properties[prop_obj.key] = prop_obj
			continue
		return

	def __iter__(self):
		# Iterate over all attributes recursively
		for key, prop in self._properties.items():
			for path, objs in prop:
				yield (key, *path), (self, *objs)
				continue
			continue
		return

class PropertySetFactory:
	def __init__(self, property_set_dict:dict={}, jcid_class=PropertySetJCID, default_class=PropertySetObject):
		self.property_set_dict = property_set_dict
		self.default_class = default_class
		self.jcid_class = jcid_class
		return

	def get_jcid_class(self):
		return self.jcid_class

	def get_property_set_class(self, jcid:JCID):
		return self.property_set_dict.get(jcid.jcid, self.default_class)

	def __call__(self, jcid:JCID, oid:ExGUID):
		return self.get_property_set_class(jcid)(jcid, oid)

OneNotebookPropertySetFactory = PropertySetFactory()
OneToc2PropertySetFactory = PropertySetFactory()
