# ONE.NOTE namespace

This namespace contains modules to support parsing of
Microsoft [ONE](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-one/73d22548-a613-4350-8c23-07d15576be50)
file structure.

## `onenote.py`

This module defines class `OneNote` which is encapsulates a non-specific OneNote file, and two specialized derived classes:
`OneNotebookSection` and `OneNotebookToc2`.

`OneNote` class provides a generic `open()` function, which also supports Python context (entry/exit) semantics.

## `object_tree_builder.py`

This module defines a set of classes to iterate through object spaces and their revisions to build a structured tree out of OneNote objects (property sets).

## `property_object_factory.py`

This module defines a set of classes to build various kinds of object properties out of raw OneStore property,
and also exports several *object factories* to create instances of property-specific classes.

### `class PropertyObject`

The base class for building a higher level object from a raw ONESTORE [property object](../STORE/README.md#property).
The object is constructed by `__init__()` function, and then can be post-processed by `make_object()` member function.

The default implementation of the `__init__()` function makes an object
with the property name extracted from the property ID enumeration class,
specified by `PROPERTY_ID_CLASS` class member (default `PropertyID`),
and copies `data`, `value`, `str_value`, `display_value` members
from the source raw property object.

Most derived classes only override the `make_object()` function, though some also override the `__init__()` function.

`get_object_value()` member function provides a value for the `__getattr__()` method of the parent property set object.

### `class PropertyObjectFactory`

An instance of this class serves as a *property object factory*,
which creates an instance of a property-specific class.

The module exports `OneNotebookPropertyFactory` and `OneToc2PropertyFactory` instances of
`class PropertyObjectFactory`.

## `property_set_object_factory.py`

This module defines a set of classes to encapsulate various kinds of objects out of raw OneStore property sets,
and also exports several *object factories* to create instances of property-set-specific classes.

### `class PropertySetObject`

The base class for building a higher level object from a raw ONESTORE [property set object](../STORE/README.md#property_set).
The object is initialized by `__init__()` function, and then constructed by `make_object()` member function.

The default implementation of the `__init__()` function makes an object
with the property set name extracted from the property set JCID enumeration class,
specified by `JCID_CLASS` class member (default `PropertySetJCID`),
and makes `_jcid_name`, `_display_name` members from the source raw property set object.

The default implementation of the `make_object()` function fills the `_properties` dictionary with
property objects, which are built from the raw properties of the source raw property set object.

Most derived classes only extend the `make_object()` function, though some also override the `__init__()` function.

`__getattr__()` member function allows to refer to the property set properties as Python object attributes,
using the dot-notation. The values it returns are provided by `get_object_value()` function of the property objects.

### `class PropertySetObjectFactory`

An instance of this class serves as a *property set object factory*,
which creates an instance of a property-set-specific class.

The module exports `OneNotebookPropertySetFactory` and `OneToc2PropertySetFactory` instances of
`class PropertySetObjectFactory`.
