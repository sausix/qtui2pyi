# Qt6 example applications (PySide6 + PyQt6)

## Ui file
[MainWindow6.ui](MainWindow6.ui) is a demo ui created and editable by Qt6 Designer.  
Do not edit ui files with other Designer versions because some widgets have a
different property tree structure and behaviour.

## pyi creation
Run the qtui2pyi tool to generate the pyi. Use the designated Qt package name for the imports (`-p PySide6`).  

`./qtui2pyi.py MainWindow6.ui -p PySide6 -o PySide6/main.pyi`

## File structure and mapping
The module of your window class `main.py` has to match the pyi stem name: `main.pyi`.  
The top widget name and class in the ui designer file have to match the name and class:

![Designer top widget](designer_topwidget.png?raw=true)

```python
class MainWindow(QMainWindow):
    ...
```

Or a subclass of QMainWindow:

```python
class MainWindow(BasicMainWindow):
    ...
```


## class BasicMainWindow
BasicMainWindow is a helper subclass of QMainWindow to combine the features:
- Ui file loading.
- `QSettings` instance (`self.settings`) per window class or window class and instance name.
- Saving and loading window geometry into the `QSettings` instance.

You do not have to use `BasicMainWindow` for ui loading! See example in `uifileloader.py`.

## uifileloader.py
`uifileloader.load_ui()` function provides a uniform ui loading for each Qt package.  
PySide6 has a more complex loading mechanism than PyQt6.

`uifileloader` allows loading Designer files from various sources:
- Simple absolute and relative paths.
- Relative paths based on the main Python executable.
- Loading from Python package resources.
- Loading from Qt resources.

See comments in `uifileloader.py`.

## main.py
main.py files in the example folders feature a minimal Qt application window based on `BasicMainWindow`.  
See commented code in `main.py`.
