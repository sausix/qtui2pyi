#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creates Python pyi stub files from QtDesigner ui files to add type annotations for IDEs and linters.
Applies to keeping Qt ui files as source instead of compiling them into py modules (uic, etc.).
"""

import os
import sys
import logging
import functools
import importlib
import json
import re

from datetime import datetime
from io import TextIOWrapper
from typing import Optional, Iterable, Generator
from pathlib import Path
from xml.dom.minidom import parse, Element, Document

__version__ = "0.1.1"
__github__ = "https://github.com/sausix/qtui2pyi"
__author__ = "sausix"


logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "WARNING").upper()
)

logger = logging.getLogger(__name__)


def print_help(as_error=False):
    """Prints command line help to STDOUT or STDERR."""
    pipe = sys.stderr if as_error else sys.stdout
    pipe.write(f"""{__doc__}\nUsage: {sys.argv[0]} UI_SRCFILE [OPTIONS]
Creates a Python pyi file based on a Qt Designer ui file.
OPTIONS:
    -p PACKAGE     Specifies Qt package name. Defaults to PySide6.
    -s             Use star imports instead of selective ones
    -o OUTFILE     Writes to specified file path. If ommited output directs to STDOUT.
    -f             Force recreation of output file even if timestamp seems up to date.
    -h             Print this help.
""")


class SelectiveQtImporter:
    """Handles class imports for the pyi file."""

    CACHE_DIR = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache") / "qtui2pyi"
    MODULES = "QtCore", "QtGui", "QtWidgets"
    RE_RELEVANT_ATTRIBUTE = re.compile(r"^Q[A-Z][^.]*$", re.DOTALL)

    def __init__(self, qt_package_name: str, invalidate_cache=False):
        self._qt_package_name = qt_package_name  # PySide6
        self._qt_package_qtcore = importlib.import_module(qt_package_name + ".QtCore")
        self._qt_version = self.detect_qt_version(self._qt_package_qtcore)

        self.package_cache = self.CACHE_DIR / qt_package_name
        self.package_cache.mkdir(mode=0o755, exist_ok=True, parents=True)

        # Cache is valid by Qt package name, package version and relevant qt package modules
        self.package_cache_file = (self.package_cache /
                                   f"{self._qt_version}_{'_'.join(self.MODULES)}.json")
        if invalidate_cache or not self.package_cache_file.exists():
            self.update_cache()

        self.cache: dict[str, list[str]] = self.read_cache()

    @staticmethod
    def detect_qt_version(p) -> str:
        """Detects the current Qt version of the selected package name."""
        if hasattr(p, "__version__"):
            return p.__version__

        if hasattr(p, "QT_VERSION_STR"):
            return p.QT_VERSION_STR

        return "unknown"

    def update_cache(self):
        """Updates the specific cache file on disk to avoid importing all sub modules."""
        cache = {}
        for m_str in self.MODULES:
            attrs = cache[m_str] = []
            m = importlib.import_module(f"{self._qt_package_name}.{m_str}")
            for attr in dir(m):
                if self.RE_RELEVANT_ATTRIBUTE.match(attr):
                    attrs.append(attr)

        with self.package_cache_file.open("wt") as fh:
            json.dump(cache, fh)

    def read_cache(self) -> dict[str, list[str]]:
        """Reads all modules' classes cache from file into dict"""
        with self.package_cache_file.open("rt") as fh:
            return json.load(fh)

    def get_import_lines(self, clss: set[str], star_imports=False) -> Generator[str, None, None]:
        """Yields relevant import statements"""

        if star_imports:
            # Star import (ok'ish for pyi)
            # from PySide6.QtCore import *
            for m_str in self.MODULES:
                yield f"from {self._qt_package_name}.{m_str} import *\n"
            return

        # from PySide6.QtCore import x, y, z
        # Selective imports
        all_classes = set(clss)
        for m_str in self.MODULES:
            module_classes = set(self.cache.get(m_str, []))
            matched = all_classes.intersection(module_classes)
            if matched:
                all_classes.difference_update(matched)
                yield f"from {self._qt_package_name}.{m_str} import {', '.join(sorted(matched))}\n"

        if all_classes:
            yield f"# Unknown class(es): {', '.join(sorted(all_classes))}\n"


class UIDesingerFile:
    """Represents a Designer ui file with can be converted into a pyi file."""
    INDENT = 4 * " "  # You're strange if you want to change this.
    RE_PYI_SRCFILE_MTIME = re.compile(r".*\[mtime:([0-9.]+)\]", re.DOTALL)

    def __init__(self, source_uixml: Path, qt_package="PySide6"):
        self._input_file = Path(source_uixml)
        self._ouput_file: Optional[Path] = None
        self._qt_package = qt_package

        # Open and parse ui file.
        with self._input_file.open("rt", encoding="utf-8") as fh:
            self.doc: Document = parse(fh)

        # Get and check root element
        self.root_element: Element = self.doc.documentElement
        if self.root_element.tagName != "ui":
            raise TypeError("root's tagname in xml file should be 'ui'.")

        # File handle for file output
        self._output_fh: Optional[TextIOWrapper] = None
        self._force_recreate_file = False

    def redirect_close(self):
        """Stop redirecting to a file (if doing) and close the handle.
        Further outputs will be printed to STDOUT."""
        if self._output_fh is None:
            return

        if not self._output_fh.closed:
            self._output_fh.close()

        self._output_fh = None

    def redirect_to_file(self, file: Optional[Path]):
        """Output result into a specific file"""
        self.redirect_close()
        self._ouput_file = file
        self._output_fh = file.open("wt")

    def _write(self, s: str):
        """Write a string to selected output method."""
        dest = self._output_fh or sys.stdout
        dest.write(s)

    def import_section(self, results: dict[str, str], star_imports=False):
        """Writes the whole import section."""
        selective_imports = SelectiveQtImporter(self._qt_package)

        for line in selective_imports.get_import_lines(set(results.values()), star_imports):
            self._write(line)

    @functools.cached_property
    def ui_top_widget(self) -> Element:
        """Returns the top widget of the ui file: <ui><widget class="QMainWindow" name="Main">"""
        nodes = self.root_element.getElementsByTagName("widget")
        if len(nodes) == 0:
            raise ValueError("Missing widget node in ui file.")
        return nodes[0]

    @functools.cached_property
    def ui_top_widget_class(self) -> str:
        """Returns the top widget class, for example 'QMainWindow'."""
        return self.ui_top_widget.getAttribute("class")

    @functools.cached_property
    def ui_top_widget_name(self) -> str:
        """Returns the top widget objectName, for example 'Main'.
        This has to match your Python class name."""
        return self.ui_top_widget.getAttribute("name")

    def subnodes(self, tagnames: Iterable[str]) -> Generator[Element, None, None]:
        """Interates over all given tagnames below the root element and returns all Elements."""
        for tagname in tagnames:
            for el in self.root_element.getElementsByTagName(tagname):
                if isinstance(el, Element):
                    yield el

    def get_name_type_mapping(self, elements: Iterable[Element]) -> dict[str, str]:
        """Creates a dictionary containing all widgets names and types:
        {"my_widget_name": "QWidgetClass"}"""

        result = {}
        for n in elements:
            w_name = n.getAttribute("name")
            if w_name in result:
                raise NameError("Duplicate element name in file: " + w_name)

            if n.tagName == "action":
                w_class = "QAction"
            else:
                w_class = n.getAttribute("class")

            result[w_name] = w_class

        return result

    def get_elements(self) -> Generator[Element, None, None]:
        """Creates a list containing all relevant xml Elements:"""

        names = set()

        for n in self.subnodes(["widget", "layout", "action"]):
            w_name = n.getAttribute("name")
            if w_name in names:
                raise NameError("Duplicate element name in file: " + w_name)
            names.add(w_name)
            yield n


    def check_outputfile_is_uptodate(self, dest_file: Path) -> bool:
        """Returns False if the destination file is missing
        or too old compared to the source file's timestamp."""
        if not dest_file.is_file():
            # Missing file. Creation needed.
            return False

        with dest_file.open("rt", encoding="utf-8") as fh:
            header = fh.readline()

        if dst_mtime_match := self.RE_PYI_SRCFILE_MTIME.match(header):
            src_mtime = self._input_file.stat().st_mtime
            dst_mtime = float(dst_mtime_match.group(1))
            return src_mtime < dst_mtime + 1

        # No or invalid header found. Recreation needed.
        return False

    def without_ui_top_widget(self, elements: Iterable[Element]) -> Generator[Element, None, None]:
        for e in elements:
            if e is not self.ui_top_widget:
                yield e

    def write_pyi(self, star_imports=True):
        """Writes the pyi file"""

        # Info header
        self._write(f"# PYI created on {datetime.now().isoformat()} from "
                    f"'{self._input_file}'[mtime:{self._input_file.stat().st_mtime}]\n")

        if self._output_fh:
            # Write to file. Filename known.
            self._write(f"# Suitable for '{self._ouput_file.stem}.py':")
        else:
            # Write to STDOUT. Filename unknown.
            self._write(f"# Pipe mode: pyi file should have the same stem name as the py file.")

        self._write(f" Must contain the class {self.ui_top_widget_name}"
                    f"({self.ui_top_widget_class})\n")

        # Fetch all widgets and classes
        all_elements = list(self.get_elements())
        
        # Create name and type mapping dict
        import_dict = self.get_name_type_mapping(all_elements)
        self.import_section(import_dict, star_imports)

        elements_dict = self.get_name_type_mapping(self.without_ui_top_widget(all_elements))

        self._write(f"\nclass {self.ui_top_widget_name}({self.ui_top_widget_class}):\n")
        if elements_dict:
            # At least one element
            for w_name, w_class in elements_dict.items():
                self._write(f"{self.INDENT}{w_name}: {w_class}\n")
        else:
            # No elements yet
            self._write(f"{self.INDENT}pass\n")

        if self._output_fh is not None:
            self._output_fh.close()
            self._output_fh = None

    def __del__(self):
        self.redirect_close()


def main(args: list[str]) -> int:
    """CLI main entry function."""
    # Defaults
    file_output: Optional[Path] = None
    qt_package = "PySide6"
    star_imports = False
    force_recreate_file = False

    # TODO: Argparse?
    if "-h" in args:
        print_help(as_error=False)
        return 0

    if "-s" in args:
        star_imports = True
        args.remove("-s")

    if "-f" in args:
        force_recreate_file = True
        args.remove("-f")

    if "-o" in args:
        index = args.index("-o")
        args.pop(index)
        file_output = Path(args.pop(index))

    if "-p" in args:
        index = args.index("-p")
        args.pop(index)
        qt_package = args.pop(index)

    if len(args) != 1:
        logger.error("Wrong arguments.")
        print_help(as_error=True)
        return 1

    src = Path(args[0])
    if not src.is_file():
        logger.error("Source ui file not found: %s", args[0])
        return 1

    logger.info("- Star imports" if star_imports else "- Selective imports")
    logger.info("- Forcing recreation" if force_recreate_file else "- Only recreate if outdated")
    logger.info("- Creating pyi file for %s", qt_package)
    logger.info("- Writing to %s", file_output or "STDOUT")

    pyi = UIDesingerFile(src, qt_package)

    if file_output and not force_recreate_file and pyi.check_outputfile_is_uptodate(file_output):
        logger.info("Output file is already up to date. Use -f to force recreation.")
        return 0

    # Select destination
    if file_output:
        pyi.redirect_to_file(file_output)
    else:
        pyi.redirect_close()

    try:
        pyi.write_pyi(star_imports=star_imports)
        logger.info("> SUCCESS.")
        return 0
    except Exception as exc:
        logger.error(exc, exc_info=True)
        logger.info("> FAIL.")
        return 1
    finally:
        pyi.redirect_close()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))

    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)
