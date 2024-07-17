# ONE.STORE namespace

This namespace contains modules to support parsing of
[[MS-ONESTORE]](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-onestore/ae670cd2-4b38-4b24-82d1-87cfb2cc3725)
file format.

## `reader.py`

This module defines class `onestore_reader` which provides sequential reading of data items of various types from the a chunk of the source file.

## `onestore.py`

This module provides class `OneStoreFile` which encapsulates functionality for parsing the upper level of the MS-ONESTORE file format,
and invoking the rest of function to parse the complete structure.
