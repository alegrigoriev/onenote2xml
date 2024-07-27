# ONE.XML namespace

This namespace contains the following modules for building XML element tree from OneNote files:

## `xml_tree_builder.py`

This module adds XML-specific functionality to `object_tree_builder.py` tree builder classes.

## `property_element_factory.py`

This module defines a set of custom classes to add XML-specific functionality to `property_object_factory.py` classes,
and also exports several *object factories* to create instances of property-specific classes.

### `class xmlPropertyElementBase`

The base class for building an XML element from a property object. The element is built by `MakeXmlElement()` function.
The default implementation of the function makes an element with the property name as the element tag,
and sets the text to the value returned by `get_xml_text()` member function.
Most derived classes only need to override `get_xml_text()` function.

`MakeXmlComment()` function generates an optional comment string for the XML element.

`MakeClass` *classmethod* function builds a class object from the provided base class (`PropertyObject` or derived,
returned by `PropertyObjectFactory.get_property_class()`).

This class and its derived classes are not used by themselves,
but serve as a base class for class objects created on runtime,
by combining with a class returned by `PropertyObjectFactory.get_property_class()` member function.

### `class XmlPropertyElementObjectFactory`

An instance of this class serves as a *property object factory*,
which creates an instance of a property-specific class.
The class is created as necessary for the given property ID, or a previously created class object is reused.

The module exports `OneNotebookPropertyElementFactory` and `OneToc2PropertyElementFactory` instances of
`class XmlPropertyElementObjectFactory`.

## `property_set_element_factory.py`

This module defines a set of custom classes to provide XML-specific functionality to `property_set_object_factory.py` classes,
and also exports several *object factories* to create instances of property-set-specific classes.

### `class xmlPropertySetElementBase`

The base class for building an XML element from a property set object. The element is built by `MakeXmlElement()` function.
The default implementation of the function makes an element with the property set JCID name as the element tag,
and makes the child sub-elements from its properties by calling their `MakeXmlElement()` function.

`MakeXmlComment()` function generates an optional comment string for the XML element.

`MakeClass` *classmethod* function builds a class object from the provided base class (`PropertySetObject` or derived,
returned by `PropertySetObjectFactory.get_property_set_class()`).

This class and its derived classes are not used by themselves,
but serve as a base class for class objects created on runtime,
by combining with a class returned by `PropertySetObjectFactory.get_property_set_class()` member function.

### `class XmlPropertySetFactory`

An instance of this class serves as a *property set object factory*,
which creates an instance of a property-set-specific class.
The class is created as necessary for the given property set JCID ID, or a previously created class object is reused.

The module exports `OneNotebookXmlPropertySetFactory` and `OneToc2XmlPropertySetFactory` instances of
`class XmlPropertySetFactory`.
