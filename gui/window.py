# coding:utf-8
"""
create on '11/14/15 9:43 PM'
"""
import ntpath
from cinter.parser import Parser
from gui.editor import CodeEditor
from ui_window import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import (QDir, pyqtSlot, QCoreApplication,
                          Qt, QFile, QModelIndex, QVariant, QAbstractItemModel)
from PyQt5.QtWidgets import (QMainWindow, QFileSystemModel,
                             QFileDialog, QAction, QApplication, QMessageBox)

__author__ = 'hejunjie'


class OutLog(object):
    def __init__(self, editor, color=None):
        self.editor = editor
        self.color = color

    def write(self, content):
        if self.color:
            self.editor.setTextColor(self.color)
        self.editor.moveCursor(QTextCursor.End)
        self.editor.insertPlainText(content)

    def close(self):
        pass


class TreeModel(QAbstractItemModel):
    def __init__(self, rootItem, parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = rootItem

    def index(self, row, column, parent=None, *args, **kwargs):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.childAt(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index=None):
        if not index.isValid():
            return QModelIndex()

        child = index.internalPointer()
        parent = child.parent

        if parent == self.rootItem:
            return QModelIndex()
        return self.createIndex(parent.indexInParent(), 0, parent)

    def rowCount(self, parent=None, *args, **kwargs):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def data(self, index, role=None):
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Left Browser tabs
        self.tabFiles = self.ui.tabWidgetBrowser.widget(0)
        self.tabToken = self.ui.tabWidgetBrowser.widget(1)
        self.tabSyntax = self.ui.tabWidgetBrowser.widget(2)
        self.ui.tabWidgetBrowser.removeTab(1)

        self.ui.tabWidgetBrowser.removeTab(1)
        self.ui.tabWidgetBrowser.setTabsClosable(True)
        self.ui.tabWidgetBrowser.tabCloseRequested.connect(self.closeBrowserTab)
        self.ui.tabWidgetBrowser.tabBarDoubleClicked.connect(self.maximizeBrowserTab)

        # File tree
        self.fileTreeModel = QFileSystemModel(self)
        self.fileTreeModel.setRootPath(QDir.currentPath())
        self.ui.treeViewFile.setModel(self.fileTreeModel)
        self.ui.treeViewFile.setRootIndex(self.fileTreeModel.index(QDir.currentPath()))
        self.ui.treeViewFile.hideColumn(1)
        self.ui.treeViewFile.hideColumn(2)
        self.ui.treeViewFile.hideColumn(3)
        self.ui.treeViewFile.setHeaderHidden(True)
        self.ui.treeViewFile.doubleClicked.connect(self.openFileFromTree)

        self.ui.treeViewSyntax.setHeaderHidden(True)
        self.ui.treeViewToken.setHeaderHidden(True)

        # Editor tabs
        self.currentEditor = self.ui.codeEditor
        self.currentEditor.file = None
        self.currentEditorTab = self.ui.tabEditor
        self.openedEditors = [self.currentEditor]
        self.openedEditorTabs = [self.currentEditorTab]
        self.currentEditor.setFocus()  # set focus
        self.ui.tabWidgetEditor.tabCloseRequested.connect(self.closeEditorTab)
        self.ui.tabWidgetEditor.tabBarClicked.connect(self.switchEditorTab)
        self.ui.tabWidgetEditor.tabBarDoubleClicked.connect(self.maximizeEditorTab)

        # Bottom output panel
        self.ui.tabWidgetOutput.hide()
        self.ui.tabWidgetOutput.setTabsClosable(True)
        self.ui.tabWidgetOutput.tabCloseRequested.connect(self.closeOutputTab)
        self.ui.tabWidgetOutput.tabBarDoubleClicked.connect(self.maximizeOutputTab)

        # Previous opened tabs
        self.preOpenedTabs = None

        # Initial size of inner splitter
        self.ui.splitterInner.setSizes([180, 459 * 2 - 180])

        # Menu "File"
        self.ui.actionOpen.triggered.connect(self.openFile)
        self.ui.actionNew.triggered.connect(self.newFile)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionSaveAs.triggered.connect(self.saveFileAs)
        self.ui.actionQuit.triggered.connect(self.close)

        # Menu "Edit"
        self.connectMenuEditSlots()

        # Menu "View"
        self.ui.menuView.triggered.connect(self.menuViewHandler)
        self.ui.actionAboutQt.triggered.connect(QApplication.aboutQt)

        self.ui.actionRunParser.triggered.connect(self.testParser)

    def testParser(self):
        if not self.saveFile():
            return

        stdin = open(self.currentEditor.file, 'r')
        stdout = OutLog(self.ui.textBrowserConsole)
        p = Parser(stdin, stdout=stdout, stderr=stdout)
        rootNode = p.parse()

        self.ui.tabWidgetOutput.show()
        self.ui.textBrowserConsole.clear()

        model = TreeModel(rootNode)
        self.ui.treeViewSyntax.setModel(model)
        self.ui.treeViewSyntax.setStyleSheet('QListView::item{background-color: red;}')
        self.ui.treeViewSyntax.setAnimated(True)

        self.ui.tabWidgetBrowser.addTab(self.tabSyntax, 'Syntax')
        index = self.ui.tabWidgetBrowser.indexOf(self.tabSyntax)
        self.ui.tabWidgetBrowser.setCurrentIndex(index)

    def closeEvent(self, event):
        """
        Override. When Close Event Triggered.
        Ask user for saving modified files
        :param event:
        :return:
        """
        for i in range(len(self.openedEditors)):
            editor = self.openedEditors[i]
            editorTab = self.openedEditorTabs[i]
            if editor.document().isModified():
                name = ntpath.basename(editor.file) if editor.file else 'New File'
                ret = QMessageBox.warning(
                    self, name,
                    'The document has been modified.\nDo you want to save your changes?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                if ret == QMessageBox.Save:
                    event.accept() if self.saveFile() else event.ignore()
                elif ret == QMessageBox.Discard:
                    index = self.ui.tabWidgetEditor.indexOf(editorTab)
                    self.ui.tabWidgetEditor.removeTab(index)
                    event.accept()
                else:
                    event.ignore()

    def connectMenuEditSlots(self):
        """
        set menu "Edit" signals connect to current editor slots
        :return:
        """
        self.ui.actionCopy.triggered.connect(self.currentEditor.copy)
        self.ui.actionCut.triggered.connect(self.currentEditor.cut)
        self.ui.actionPaste.triggered.connect(self.currentEditor.paste)
        self.ui.actionUndo.triggered.connect(self.currentEditor.undo)
        self.ui.actionRedo.triggered.connect(self.currentEditor.redo)
        self.ui.actionSelectAll.triggered.connect(self.currentEditor.selectAll)

    def disconnectMenuEditSlots(self):
        """
        disconnect menu "Edit" signals
        :return:
        """
        self.ui.actionCopy.triggered.disconnect(self.currentEditor.copy)
        self.ui.actionCut.triggered.disconnect(self.currentEditor.cut)
        self.ui.actionPaste.triggered.disconnect(self.currentEditor.paste)
        self.ui.actionUndo.triggered.disconnect(self.currentEditor.undo)
        self.ui.actionRedo.triggered.disconnect(self.currentEditor.redo)
        self.ui.actionSelectAll.triggered.disconnect(self.currentEditor.selectAll)

    def createEditorTab(self):
        """
        Create a new Editor tab and set as current editor
        Should reconnect the signal on menu 'Edit' actions
        :return:
        """
        # add a new editor
        self.currentEditorTab = QtWidgets.QWidget()
        horizontalLayout = QtWidgets.QHBoxLayout(self.currentEditorTab)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)
        horizontalLayout.setSpacing(6)
        codeEditor = CodeEditor(self.currentEditorTab)
        horizontalLayout.addWidget(codeEditor)
        self.ui.tabWidgetEditor.addTab(self.currentEditorTab, "")

        # disconnect signals
        self.disconnectMenuEditSlots()

        # change current tab and editors
        self.currentEditor = codeEditor
        self.currentEditor.file = None
        self.openedEditors.append(self.currentEditor)
        self.openedEditorTabs.append(self.currentEditorTab)

        # connect signals
        self.connectMenuEditSlots()

        # set tab closeable
        if len(self.openedEditorTabs) > 1:
            self.ui.tabWidgetEditor.setTabsClosable(True)

    @pyqtSlot(int)
    def switchEditorTab(self, index):
        """
        Switch current active editor tab to index
        Should reconnect the signal on menu 'Edit' actions
        :param index:
        :return:
        """
        self.disconnectMenuEditSlots()
        self.currentEditorTab = self.openedEditorTabs[index]
        self.currentEditor = self.openedEditors[index]
        self.connectMenuEditSlots()

    @pyqtSlot(int)
    def closeEditorTab(self, index):
        """
        Triggered when closing the editor tab at index requested
        :param index:
        :return:
        """
        self.ui.tabWidgetEditor.removeTab(index)
        self.openedEditorTabs.pop(index)
        self.openedEditors.pop(index)
        self.switchEditorTab(0)
        if len(self.openedEditorTabs) == 1:
            self.ui.tabWidgetEditor.setTabsClosable(False)

    @pyqtSlot(int)
    def closeBrowserTab(self, index):
        """
        Close Left Browser Tab at index
        :param index:
        :return:
        """
        w = self.ui.tabWidgetBrowser.widget(index)
        self.ui.tabWidgetBrowser.removeTab(index)
        if w == self.tabFiles:
            self.ui.actionFiles.setChecked(False)
        elif w == self.tabToken:
            self.ui.actionTokenTree.setChecked(False)
        else:
            self.ui.actionSystaxTree.setChecked(False)
        if self.ui.tabWidgetBrowser.count() == 0:
            self.ui.tabWidgetBrowser.hide()

    @pyqtSlot(int)
    def closeOutputTab(self, index):
        """
        Close(hide) the output tab widget
        :param index:
        :return:
        """
        self.ui.tabWidgetOutput.hide()
        self.ui.actionConsole.setChecked(False)

    def recoverTabWidgets(self):
        """
        recover tabs when cancel maximizing
        :return:
        """
        for tab in self.preOpenedTabs:
            tab.show()
        self.preOpenedTabs = None

    def storeOpenedTabs(self):
        """
        store tabs opened before maximize
        :return:
        """
        self.preOpenedTabs = []
        if not self.ui.tabWidgetOutput.isHidden():
            self.preOpenedTabs.append(self.ui.tabWidgetOutput)
        if not self.ui.tabWidgetEditor.isHidden():
            self.preOpenedTabs.append(self.ui.tabWidgetEditor)
        if not self.ui.tabWidgetBrowser.isHidden():
            self.preOpenedTabs.append(self.ui.tabWidgetBrowser)

    @pyqtSlot(int)
    def maximizeBrowserTab(self, index):
        if self.preOpenedTabs:
            self.recoverTabWidgets()
        else:
            self.storeOpenedTabs()
            self.ui.tabWidgetOutput.hide()
            self.ui.tabWidgetEditor.hide()

    @pyqtSlot(int)
    def maximizeEditorTab(self, index):
        if self.preOpenedTabs:
            self.recoverTabWidgets()
        else:
            self.storeOpenedTabs()
            self.ui.tabWidgetBrowser.hide()
            self.ui.tabWidgetOutput.hide()

    @pyqtSlot(int)
    def maximizeOutputTab(self, index):
        if self.preOpenedTabs:
            self.recoverTabWidgets()
        else:
            self.storeOpenedTabs()
            self.ui.tabWidgetBrowser.hide()
            self.ui.tabWidgetEditor.hide()

    @pyqtSlot(bool)
    def openFile(self, checked=True, path=None):
        """
        Open a new file.
        If current editor is associated with a file or its content is not null,
        Then create a new editor tab
        :return:
        """
        path = QFileDialog.getOpenFileName()[0] if not path else path
        if len(path) != 0:
            qfile = QFile(path)
            if not qfile.open(QFile.ReadOnly or QFile.Text):
                QMessageBox.warning(self, 'Application',
                                    'Cannot read file %s:\n%s.' % (path, qfile.errorString()))
                return
            with open(path, 'r') as _file:
                content = _file.read()

            if self.currentEditor.file or len(self.currentEditor.document().toPlainText()) > 0:
                self.createEditorTab()

            # associate file on disk with editor
            self.currentEditor.file = path

            # update tab name
            index = self.ui.tabWidgetEditor.indexOf(self.currentEditorTab)
            _translate = QCoreApplication.translate
            self.ui.tabWidgetEditor.setTabText(
                index, _translate("MainWindow", ntpath.basename(path)))
            self.ui.tabWidgetEditor.setCurrentIndex(index)
            self.currentEditor.setPlainText(content)

    @pyqtSlot(int)
    def openFileFromTree(self, index):
        f = self.fileTreeModel.fileInfo(index)
        if f.isFile():
            self.openFile(path=f.filePath())

    @pyqtSlot(bool)
    def newFile(self, checked):
        """
        create a new editor tab
        :param action:
        :return:
        """
        self.createEditorTab()
        index = self.ui.tabWidgetEditor.indexOf(self.currentEditorTab)
        _translate = QCoreApplication.translate
        self.ui.tabWidgetEditor.setTabText(
            index, _translate("MainWindow", 'New File'))
        self.ui.tabWidgetEditor.setCurrentIndex(index)

    @pyqtSlot(bool)
    def saveFile(self, checked=None):
        """
        Save file.
        If current editor is associated with a file on the disk,
        then save it. Or save file as...
        :param checked:
        :return: Saved or canceled
        """
        if self.currentEditor.file:
            if self.currentEditor.document().isModified():
                with open(self.currentEditor.file, 'w') as f:
                    f.write(self.currentEditor.document().toPlainText())
                self.currentEditor.document().setModified(False)
            return True
        else:
            return self.saveFileAs()

    @pyqtSlot(bool)
    def saveFileAs(self, checked=None):
        """
        Save File As...
        :param checked:
        :return: If saved or canceled
        """
        dialog = QFileDialog()
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        if dialog.exec_():
            filepath = dialog.selectedFiles()[0]
            with open(filepath, 'w') as f:
                f.write(self.currentEditor.document().toPlainText())
            self.currentEditor.document().setModified(False)
            return True
        else:
            return False

    @pyqtSlot(QAction)
    def menuViewHandler(self, action):
        """
        Handle the action on menu "View"
        :param action:
        :return:
        """
        if action == self.ui.actionToolbar:
            self.ui.toolBar.show() if action.isChecked() else self.ui.toolBar.hide()
        elif action == self.ui.actionConsole:
            self.ui.tabWidgetOutput.show() if action.isChecked() else self.ui.tabWidgetOutput.hide()
        else:
            if action == self.ui.actionFiles:
                widget = self.tabFiles
                name = 'File'
            elif action == self.ui.actionTokenTree:
                widget = self.tabToken
                name = 'Token'
            else:
                widget = self.tabSyntax
                name = 'Syntax'
            if action.isChecked():
                self.ui.tabWidgetBrowser.addTab(widget, name)
                self.ui.tabWidgetBrowser.show()

                # reset tab inner splitter size
                w = self.ui.tabWidgetBrowser.count() * 80
                self.ui.splitterInner.setSizes([w, self.ui.splitterInner.width() - w])
            else:
                self.ui.tabWidgetBrowser.removeTab(
                    self.ui.tabWidgetBrowser.indexOf(widget))
                if self.ui.tabWidgetBrowser.count() == 0:
                    self.ui.tabWidgetBrowser.hide()
