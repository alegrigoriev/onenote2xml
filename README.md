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
