# -*- coding: utf-8 -*-

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow

from uifileloader import load_ui


class BasicMainWindow(QMainWindow):
    """
    Extends QMainWindow to offer some basic features like
    ui loading,
    settings bound to the window (+instance name)
    and windows geometry persistence.

    Derive your class from BasicMainWindow instead from QMainWindow and call
    this __init__ function with the associated uifile.
    Or define UI_FILE in your own class.
    """

    UI_FILE = ""

    def __init__(self, uifile: str = None, settings_instance: str = None):
        QMainWindow.__init__(self)

        if not uifile:
            # Use class default
            uifile = self.UI_FILE

        if not uifile:
            # Guess. Use class name.
            uifile = self.__class__.__name__ + ".ui"

        # Load the ui
        load_ui(uifile, self)

        self.settings = QSettings()
        self.settings.beginGroup(self.__class__.__name__ +
                                 ("" if settings_instance is None else "/" + settings_instance))

        self.restore_settings()

    def closeEvent(self, event):
        """Windows closing. Save settings before closing"""
        self.save_settings()
        QMainWindow.closeEvent(self, event)

    def save_settings(self):
        """Save window geometry and state."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())

    def restore_settings(self):
        """Restore window geometry and state."""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)

        if state := self.settings.value("state"):
            self.restoreState(state)
