# ONE.STORE namespace

This namespace contains modules to support parsing of
[[MS-ONESTORE]](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-onestore/ae670cd2-4b38-4b24-82d1-87cfb2cc3725)
file format.

The structure of ONESTORE format is briefly described in [ONESTORE format](#ONESTORE)

## `reader.py`

This module defines class `onestore_reader` which provides sequential reading of data items of various types from the a chunk of the source file.

## `onestore.py`

This module provides class `OneStoreFile` which encapsulates functionality for parsing the upper level of the MS-ONESTORE file format,
and invoking the rest of function to parse the complete structure.

## `filenode.py`

This module provides IntEnum subclass `FileNodeID` which declares codes for file node types.
It also defines classes for each of file node structures, and exports `FileNodeFactory` function to read and build file node objects.

## `filenode_list.py`

This module exports `FileNodeList` function, which works as a filenode object generator, given the `onestore` instance,
and the chunk reference for the file list.

## `global_id_table.py`

This module exports `GlobalIdTable` class, which builds a table from a sequence of file nodes, for mapping `CompactId` indices to 128 bit GUIDs.

## `object_group.py`

This module exports class `ObjectGroup`, which parses a group of objects,
referred by ObjectGroupListReferenceFND structure. An object group is used by `.one` files.

## `object_space.py`

This module exports class `ObjectSpace`,
which invokes loading of a single revision manifest list (which is a sequence of revision manifests).

## `revision_manifest_list.py`

This module exports a function `RevisionManifestList`, called by `ObjectSpace`,
which parses a file node list containing a sequence of revision manifests,
each represented by class `RevisionManifest`.

# ONESTORE format{#ONESTORE}

The most current format is used for `.one` files. `.onetoc2` (Notebook Table Of Contents) files uses a legacy format.

## Header

The header (of fixed size at offset 0000000 of the file) contains some format versioning information,
and pointers (chunk references) to root filenode list and transaction list.

Root filenode list contains pointers to the object space manifest list, ID of the root object space,
and a pointer to file data store list (optional, `.one` files only).

The transaction list was intended to implement safe updates of the file lists.
Unfortunately, the files I've looked at seem to have the transaction list corrupted.
It might have been deprecated altogether.

File data store list keeps pointers to data (pictures, other multimedia) files embedded in ONESTORE file.
Bigger picture/multimedia files are kept outside the ONESTORE file in `onefiles/` directory.

## Filenode list

Most other data is kept as or described by `filenode lists`.
A filenode list is a sequence of `filenodes` which are basic structures,
identified by 10 bit type ID. As the list grows, it can be split into multiple chunks.

## Object space

All higher level data structures are kept as *property sets* (objects) in *object spaces*.
Objects in one space can point at each other. Objects refer to each other by and Object ID (OID),
which is an *extended GUID*,
which is combination of a 128 bit *Globally Unique ID (GUID)* and an 8 bit sequence number.

To reduce storage size, Object IDs are kept as a *compact ID* with 24 bit index and 8 bit sequence.
The index refers to a GUID in a slot in the *global ID table*, which is not really global, but kept per `revision`.
A zero compact id is an equivalent of `null`, it doesn't refer to any OID.

Note that same OID can refer to different versions of an object in different revisions.

NOTE: An object space might have been conceived as a container for the given page's revisions.
Unfortunately, it seems to be associated with a slot in the page array/tree, instead.
When you insert a page, other pages revisions may get shuffled into different object spaces.
A page is uniquely identified by `NotebookManagementEntityGuid` attribute, instead.

One object space is designated in ONESTORE file as `root`.
In `.onetoc2` file this object space contains pointers (GUIDs) to all sections of a notebook (collection of sections).
In `.one` file (a section of a notebook) the root space is the table of pages. Each slot refers to a non-root object space.

## Revisions

An object space keeps a list of *revisions*, which are not just revisions of a given page.
As said above, a particular page may get shuffled from one object space to another.

To describe history, an object space keeps a special *meta-revision*,
with a jcidVersionHistoryContent object (property set) as its root object.

An object space can have multiple root objects, per their `roles`.
Role **1** is *contents*, role **2** is *page metadata* which basically duplicates the metadata in the table of pages,
role **4** is *version metadata* which duplicates the page version information
in the history meta-revision (which itself doesn't have role 4).

One revision in the object space is designated as `root`.
It's the most recent page version for rendering. The root revision is not listed in the history meta-revision.

Revisions are labeled by *Context IDs*, which are Extended GUIDs, with an additional role label, which is always 1.
The root revision is always labeled with Context ID {{00000000-0000-0000-0000-000000000000},1}.
The history meta-revision is always labeled with Context ID {{7111497F-1B6B-4209-9491-C98B04CF4C5A},1}.

## Objects

Most objects are *property sets* which is an equivalent of a structure.
There are also file data objects, which can refer to a file data store item (embedded file),
or a file in `onestore/` directory.

A property set is a collection of *attributes*. An attribute has an ID,
which is one of pre-defined 31 bit constants, and value, which can be one of predefined types:
bool, 1/2/4/8 bytes integer, bytes, array of pointers to objects (through object ID),
array of pointers to other objects spaces, array of Context IDs, array of property sets.

Integer value is interpreted depending on the ID, as just a number, or a floating point number,
or a timestamp, or RGB color.
Bytes value is interpreted depending on the ID, as an Unicode or MBCS string, an array of ints or floats,
or a custom structure.

