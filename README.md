# qtui2pyi

## What?
This tool creates Python pyi files from various Qt Designer ui files which
hint IDEs and linters to correct types. This primarily allows IDEs to
show you dropdowns and auto completion features.

![Example of having code completion in PyCharm](example_annotated.png?raw=true)

## But there is uic / pyuic for that!
In fact the onboard tools of PyQt and PySide allow compiling your ui
files directly into Python modules. This is totally fine and that includes types and
auto completion without any pyi files.  

But some people still prefer using ui files as direct origin for GUI
initialization for good reasons:
- Ui files can be stored in Python resources and in Qt resource files or anywhere on a disk.
- Changes in ui files are reflected direclty after restarting the program.
- Compile tools add special functions like setupUI or similar.
- Ui files allow dynamic loading or nesting for example multiple ui files into pages of a single TabWidget or other nested widgets.

This tool solves the biggest disadvantage of having no type annotations.

## Tool state
Alpha? This is the first release and problems are expected. Ui files can
be special. PySide and PyQt may have different handlings and classes like "pyqtProperty".

## Requirements
- The tool runs fine on Python 3.9+ (and could be modified to support Python 3.6+)
- No external packages, except the wanted Qt packages you are working with.

## Usage example
(python3) `qtui2pyi.py -p PySide6 sourcefile.ui -o sourcefile.pyi`

Also see: `qtui2pyi -h`  

Example folders also feature some full applications to show usage.

## How does it work
The ui files are simple xml files and being parsed by xml.dom.minidom.  
The submodules and classes of the Qt package (specified by -p 'PySide2|PyQt5|...' defaults to 'PySide6') will be be imported, processed and stored into a json cache file matching the version. 
Some meta information, import statements and the class body a written to the output file or to STDOUT for piping.
Time stamps of the original ui file are monitored and actual recreation of the pyi depends on a newer file modification date.

## Version history
- 0.1.1 Fix missing top level widget class import
- 0.1.0 First release (alpha)

## TODO
- Get feedback and love as motivation
- Testing
- Add Qt5/Qt2 examples
- Add argparser (maybe)
- Packaging and CLI entrypoints
