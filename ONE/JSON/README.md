# ONE.JSON namespace

This namespace contains the following modules for building and writing JSON object tree from OneNote files:

## `json_tree_builder.py`

This module adds JSON-specific functionality to `object_tree_builder.py` tree builder classes.

## `json_property_factory.py`

This module defines a set of custom classes which add JSON-specific functionality to `property_object_factory.py` classes,
and also exports several *object factories* to create instances of property-specific classes.

### `class jsonPropertyBase`

The base class for building a JSON-compatible value from a property object.
Valid JSON-compatible types are `dict`, `list`, `int`, `str`, `float`, `None`.

The JSON value is built by `MakeJsonValue()` function; the default implementation returns `self.value`.

`MakeClass` *classmethod* function builds a class object from the provided base class
(`PropertyObject` or derived, returned by `PropertyObjectFactory.get_property_class()`).

This class and its derived classes are not used by themselves,
but serve as a base class for class objects created on runtime,
by combining with a class returned by `PropertyObjectFactory.get_property_class()` member function.

### `class JsonPropertyObjectFactory`

An instance of this class serves as a *property object factory*,
which creates an instance of a property-specific class.
The class is created as necessary for the given property ID, or a previously created class object is reused.

The module exports `OneNotebookJsonPropertyFactory` and `OneToc2JsonPropertyFactory` instances of
`class JsonPropertyObjectFactory`.

## `json_property_set_factory.py`

This module defines a set of custom classes which add JSON-specific functionality to `property_set_object_factory.py` classes,
and also exports several *object factories* to create instances of property-set-specific classes.

### `class jsonPropertySetBase`

The base class for building a JSON dictionary object from a property set object.
The element is built by `MakeJsonTree()` function. 
The default implementation of the function makes a dictionary from its properties
by calling their `MakeJsonValue()` function.

`MakeClass` *classmethod* function builds a class object from the provided base class (`PropertySetObject` or derived,
returned by `PropertySetObjectFactory.get_property_set_class()`).

This class and its derived classes are not used by themselves,
but serve as a base class for class objects created on runtime,
by combining with a class returned by `PropertySetObjectFactory.get_property_set_class()` member function.

### `class JsonPropertySetFactory`

An instance of this class serves as a *property set object factory*,
which creates an instance of a property-set-specific class.
The class is created as necessary for the given property set JCID ID, or a previously created class object is reused.

The module exports `OneNotebookJsonPropertySetFactory` and `OneToc2JsonPropertySetFactory` instances of
`class JsonPropertySetFactory`.
