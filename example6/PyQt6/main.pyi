# PYI created on 2025-02-04T18:36:50.845050 from 'MainWindow6.ui'[mtime:1738689626.7610867]
# Suitable for 'main.py': Must contain the class MainWindow(QMainWindow)
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QDockWidget, QHBoxLayout, QMainWindow, QMdiArea, QMenu, QMenuBar, QPushButton, QStatusBar, QTextEdit, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    MainWindow: QMainWindow
    centralwidget: QWidget
    mdiArea: QMdiArea
    menubar: QMenuBar
    menuFile: QMenu
    statusbar: QStatusBar
    dockTools: QDockWidget
    dockWidgetToolsContents: QWidget
    pushButtonDialog: QPushButton
    dockLog: QDockWidget
    dockWidgetLogContents: QWidget
    textLog: QTextEdit
    verticalLayout: QVBoxLayout
    horizontalLayout_2: QHBoxLayout
    horizontalLayout: QHBoxLayout
    actionShowDialog: QAction
