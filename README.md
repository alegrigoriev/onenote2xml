py1note package
---------------

The package contains Python (3.9+) modules for reading and parsing Microsoft OneNote files (`.one` sections and `.onetoc2` notebooks).

## Contents

All OneNote parser code is in [ONE](ONE/README.md) directory and its subdirectories.

Command line applications are provided to invoke the parser.

## Command line applications

The following command line applications are provided:

[parse1note.py](#parse1note) just loads an OneNote file and dumps all its structures to the log file.

[1note2xml.py](#1note2xml) command line application generates an XML file from the provided OneNote section or notebook file.

[1note2json.py](#1note2json) command line application generates a JSON file from the provided OneNote section or notebook file.

### `parse1note.py`{#parse1note}

`parse1note.py` application is invoked with the following command line:

```
python parse1note.py <OneNote filename> [common options] [--raw]
```

The following option is specific to `parse1note.py` only:

`--raw` (`-w`)
- Dump raw structures to the log file. The default is to dump pretty decoded attributes and objects.

### `1note2xml.py`{#1note2xml}

[1note2xml.py](1note2xml.py) application is invoked with the following command line:

```
python 1note2xml.py <OneNote filename> [common options]
```

### `1note2json.py`{#1note2json}

[1note2json.py](1note2json.py) application is invoked with the following command line:

```
python 1note2json.py <OneNote filename> [common options]
```

### Common options

`--log <log filename>` (`-L <log filename>`) options gives the file name to write the parser log.

`--output <filename>` (`-O <filename`)
- the file name to write the XML or JSON file.
The file will contain the most current revision of all pages stored in the source OneNote file.
To produce a complete file with all revisions, add `--all-revisions` command line option.

`--all-revisions` (`-A`)
- include all page revisions to the generated file, not just the most recent versions.

`--include-oids` (`-o`)
- tag all structures with object IDs (extended GUIDs) in the generated files.
It allows to match the generated elements against the raw object contents in the log file.
It's only useful for debugging OneNote file structure.

`--verbose <verbosity>` (`-v <verbosity>`) sets the level of data issued into the generated XML and JSON files.

The following verbosity levels are defined:

`0` - only objects and attributes relevant for content and history parsing.
Rich text objects are converted from separate text run index and style arrays, and the text string,
to a single array of text run elements. Empty text objects and *outlines* are dropped.  
`1` - only objects and attributes relevant for content and history parsing.
Rich text objects are left as is.  
`2` - page layout attributes are included.  
`3` - some extra author and timestamp attributes included.  
`4` - all objects and attributes, except for those with undocumented IDs.  
`5` - all objects and attributes, including those with undocumented IDs.
