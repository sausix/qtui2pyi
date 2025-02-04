# -*- coding: utf-8 -*-

"""
Minimal basic Qt window application. PySide6 version.
"""

import sys

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from basicmainwindow import BasicMainWindow


class MainWindow(BasicMainWindow):
    """Basic MainWindow using the BasicMainWindow helper class"""

    # pyi for this class created by:
    # ../../qtui2pyi.py ../MainWindow6.ui -p PySide6 -o main.pyi

    # You can define the ui file on class level.
    UI_FILE = "../MainWindow6.ui"
    # __init__ argument uifile takes precedence.

    def __init__(self):
        BasicMainWindow.__init__(self)
        #  BasicMainWindow.__init__(self, "../MainWindow6.ui")
        #  super().__init__()  # For super() fans.

        # Connecting signals
        # Manually connect to action trigger
        #  self.actionShowDialog.triggered.connect(self.show_msgbox)

        # Manually connect to pushButton connect
        #  self.pushButtonDialog.clicked.connect(self.show_msgbox)

    # Or use slot "on_objectName_signal" scheme to connect events:
    @Slot()
    def on_pushButtonDialog_clicked(self):
        self.show_msgbox()

    @Slot()
    def on_actionShowDialog_triggered(self):
        self.show_msgbox()

    def show_msgbox(self):
        msgbox = QMessageBox()
        msgbox.setText("Hello there! This is a QMessageBox example.")
        msgbox.setWindowTitle(self.windowTitle())
        msgbox.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setOrganizationName("Example")
    app.setOrganizationDomain("example.com")
    app.setApplicationName("example.PySide6")

    main_win = MainWindow()
    main_win.show()

    sys.exit(app.exec())
