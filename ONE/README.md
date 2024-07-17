# ONE namespace

This namespace contains the following child namespaces:

- [STORE/](STORE/README.md) - modules to support parsing of
[[MS-ONESTORE]](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-onestore/ae670cd2-4b38-4b24-82d1-87cfb2cc3725)
file format;
- [NOTE/](NOTE/README.md) - parsing of
Microsoft [ONE](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-one/73d22548-a613-4350-8c23-07d15576be50)
file structure;

and basic support modules:
`property_set_jcid.py`,
`property_id.py`,
`property_pretty_print.py`,
`exception.py`,
and `base_types.py`.

## `property_set_jcid.py`

This module contains definitions of object IDs (JCID).

## `property_id.py`

This module contains definitions of property IDs.

## `property_pretty_print.py`

This module contains functions and a factory function to make human-readable strings from property data.

## `exception.py`

This module defines the base exception class `OneException`. All other exception classes defined in this module are derived from it.

## `base_types.py`

This module contains classes and functions to support data types used in
[[MS-ONESTORE]](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-onestore/ae670cd2-4b38-4b24-82d1-87cfb2cc3725) files:

- `CompactID` - 32 bit ID consisting of 24 bit index to a GUID table, and 8 bit sequence number for the GUID, to make an extended GUID;
- `FileNodeChunkReference`, `FileChunkReference32`, `FileChunkReference64x32`, `FileChunkReference64` - file
structures containing a reference to a chink in `MS ONESTORE` file with the starting position of various or variable size,
and chunk size of variable size;
- `JCID` - type identifier for various object types in the file. See [[MS-ONE]](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-one/73d22548-a613-4350-8c23-07d15576be50) document for more details;
- `GUID` - 128 bit Global Unique Identifier;
- `ExGUID` -  a GUID, extended with 8 bit sequence index. Used to identify various objects in the file.
