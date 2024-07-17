py1note package
---------------

The package contains Python (3.9+) modules for reading and parsing Microsoft OneNote files (`.one` sections and `.onetoc2` notebooks).

## Contents

All OneNote parser code is in [ONE](ONE/README.md) directory and its subdirectories.

Command line applications are provided to invoke the parser.

## Command line applications

The following command line applications are provided:

[parse1note.py](#parse1note) just loads an OneNote file and dumps all its structures to the log file.

### `parse1note.py`{#parse1note}

`parse1note.py` application is invoked with the following command line:

```
python parse1note.py <OneNote filename> [common options]
```

### Common options

`--log <log filename>` (`-L <log filename>`) options gives the file name to write the parser log.
