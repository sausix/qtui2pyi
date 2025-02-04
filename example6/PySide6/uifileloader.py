# -*- coding: utf-8 -*-

"""
Example for loading a Qt Designer ui file into a QMainWindow (or similar) using PySide6.

Why not compiling into Python code with uic?
It allows editing the ui file during development and having an "explicit origin".
The only disadvantage is not haing type hints of the widgets.

This is a rewrite of old code and not yet tested enough.
Especially the loading from Python package resources.
"Posting untested now before forgetting later" principle.
Should also work on child QWidgets but its not tested yet either.
The code is still ugly and may contain major bugs. I will fix it later™.

Example use:

from uifileloader import load_ui

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)  # I hate super() btw. It also violates the zen of Python.

        # Load relative to the main python file
        load_ui("PY:/res/ui/main.ui", self)

        # Load from Qt ressource
        # load_ui(":/ui/main.ui", self)

        # Load from Python package resources (the deployment method)
        # Untested!
        # load_ui("RES:/myproject:main.ui", self)

        # Plain loading which is dangerous on variable working directories
        # which are not always on your project root.
        # load_ui("ui/main.ui", self)
"""

import re
import sys

from typing import Optional
from pathlib import Path
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QMetaObject, QFile, QFileDevice
from PySide6.QtWidgets import QWidget


class UiFileLoader(QUiLoader):
    _RE_PYREL = re.compile(r"^PY:/(.+)")
    _RE_PKGRES = re.compile(r"^RES:/([a-zA-Z_]+):(.+)")
    _RE_QRES = re.compile(r"^(:/.+)")

    def __init__(self):
        self._parent_widget: Optional[QWidget] = None
        QUiLoader.__init__(self)

    def createWidget(self, classname, parent=None, name=""):
        # Forgot the exact purpose and source of this snippet. Sorry.
        if parent is None and self._parent_widget is not None:
            widget = self._parent_widget
        else:
            widget = QUiLoader.createWidget(self, classname, parent, name)
            if self._parent_widget is not None:
                setattr(self._parent_widget, name, widget)
        return widget

    def load_ui(self, ui_file: str | Path, parent_widget: QWidget) -> QWidget:
        # Todo: Fix file handling into QFile directly.
        ui_str = str(ui_file)

        if m := self._RE_PYREL.match(ui_str):
            # Relative to the main python module file
            # "PY:/gui.ui"
            if sys.argv[0] in {"", "-c"}:
                # Non file based execution
                #   python -c "code"
                #   echo "code" | python
                uifile = Path.cwd() / m.group(1)  # Use current directory
            else:
                # File based execution
                # python main_file.py
                uifile = Path(sys.argv[0]).resolve().absolute().parent / m.group(1)

        elif m := self._RE_PKGRES.match(ui_str):
            # ui file from Python resource
            # "RES:/packagename:pyth"
            from pkg_resources import resource_filename
            uifile = Path(resource_filename(*m.groups()))

        elif m := self._RE_QRES.match(ui_str):
            # ui file from Qt resource
            # ":/qres/path"
            uifile = QFile(m.group(1))

        else:
            uifile = Path(ui_str)

        if isinstance(uifile, Path) and not uifile.is_file():
            raise ValueError(f"ui file does not exists: {uifile}")

        if isinstance(uifile, QFileDevice) and not uifile.exists():
            raise ValueError(f"ui file does not exists: {uifile.fileName()}")

        self._parent_widget = parent_widget

        widget = self.load(uifile)

        # Connect signals to actual code.
        QMetaObject.connectSlotsByName(widget)

        return widget


def load_ui(ui_file: str | Path, parent_widget: QWidget) -> QWidget:
    """
    Short hand function to use the UiFileLoader class.

    :param ui_file: The ui file containing a compatible UI. QWidget/QMainWindow/QWindow etc.
                    Supported protocols:
                        "PY:/gui.ui":  Relative to main Python file
                        "RES:/packagename:gui.ui":  From Python package resource (untested)
                        ":/ui/gui.ui":  From Qt resource

                        Dangerous:
                        "gui.ui" Relative path to CWD
                        "/path/gui.ui" Absolute path
    :param parent_widget: The existing widget to load the ui into.
    :return: Undocumented in Qt? Returns the parent widget.
    """
    loader = UiFileLoader()
    return loader.load_ui(ui_file, parent_widget)
