# ONE.NOTE namespace

This namespace contains modules to support parsing of
Microsoft [ONE](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-one/73d22548-a613-4350-8c23-07d15576be50)
file structure.

## `onenote.py`

This module defines class `OneNote` which is encapsulates a non-specific OneNote file, and two specialized derived classes:
`OneNotebookSection` and `OneNotebookToc2`.

`OneNote` class provides a generic `open()` function, which also supports Python context (entry/exit) semantics.
