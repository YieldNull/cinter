# coding:utf-8
"""
Main window.

Show ui and handle events.

create on '11/14/15 9:43 PM'
"""
import ntpath

from cinter.inter import Interpreter
from cinter.parser import Parser
from gui.editor import CodeEditor
from ui_window import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor, QColor, QFont
from PyQt5.QtCore import (QDir, pyqtSlot, QCoreApplication,
                          Qt, QFile, QModelIndex, QVariant, QAbstractItemModel, pyqtSignal, QThread, QObject, QMutex,
                          QWaitCondition)
from PyQt5.QtWidgets import (QMainWindow, QFileSystemModel,
                             QFileDialog, QAction, QApplication, QMessageBox)

__author__ = 'hejunjie'


class Console(QObject):
    """
    The stream-like-object to redirect stream to Qt editor document
    """
    update = pyqtSignal(str)  # something is writen to console

    def __init__(self, editor, color=None, parent=None, waitCond=None):
        """
        :param editor: QTextBrowser or QPlainTextEditor etc.
        :param color: text color
        :return:
        """
        super(Console, self).__init__(parent)

        self.editor = editor
        self.color = color
        if self.color:
            self.editor.setTextColor(self.color)

        self.mutex = QMutex()
        self.waitCond = waitCond
        self.input = None

    def write(self, content):
        """
        Append to editor's document
        :param content:
        :return:
        """
        self.update.emit(content)

    def read(self):
        self.editor.setReadOnly(False)

        self.mutex.lock()
        self.waitCond.wait(self.mutex)
        self.mutex.unlock()
        return self.input

    def close(self):
        pass

    @pyqtSlot(str)
    def receivedInput(self, content):
        self.input = content


class ExecuteThread(QThread):
    """
    A thread for execute Intermediate Code
    """

    def __init__(self, work, parent=None):
        super(ExecuteThread, self).__init__(parent)
        self.work = work

    def run(self):
        self.work()


class TreeModel(QAbstractItemModel):
    """
    The tree model to show token tree or syntax tree in QTreeView
    Functions are all overrode
    """

    def __init__(self, rootItem, parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = rootItem

    def index(self, row, column, parent=None, *args, **kwargs):
        """
        Returns the index of the item in the model
        specified by the given row, column and parent index.
        """
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
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.
        """
        if not index.isValid():
            return QModelIndex()

        child = index.internalPointer()
        parent = child.parent

        if parent == self.rootItem:
            return QModelIndex()
        return self.createIndex(parent.indexInParent(), 0, parent)

    def rowCount(self, parent=None, *args, **kwargs):
        """
        Returns the number of rows under the given parent.
        When the parent is valid it means that
        rowCount is returning the number of children of parent.
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def columnCount(self, parent=None, *args, **kwargs):
        """
        Returns the number of columns for the children of the given parent.
        """
        return 1

    def data(self, index, role=None):
        """
        Returns the data stored under the
        given role for the item referred to by the index.
        """
        if not index.isValid():
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return item.data()


class MainWindow(QMainWindow):
    inputReceived = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Left Browser tabs
        self.ui.tabWidgetBrowser.removeTab(1)
        self.ui.tabWidgetBrowser.removeTab(1)
        self.ui.tabWidgetBrowser.setTabsClosable(True)
        self.ui.tabWidgetBrowser.tabCloseRequested.connect(self.closeBrowserTab)
        self.ui.tabWidgetBrowser.tabBarDoubleClicked.connect(lambda: self.maximizeTabs(self.ui.tabWidgetBrowser))

        # Left tree views
        self.fileTreeModel = QFileSystemModel(self)
        self.fileTreeModel.setRootPath(QDir.currentPath() + QDir.separator() + 'test')
        self.ui.treeViewFile.setModel(self.fileTreeModel)
        self.ui.treeViewFile.setRootIndex(self.fileTreeModel.index(QDir.currentPath() + QDir.separator() + 'test'))
        self.ui.treeViewFile.hideColumn(1)
        self.ui.treeViewFile.hideColumn(2)
        self.ui.treeViewFile.hideColumn(3)
        self.ui.treeViewFile.doubleClicked.connect(self.openFileFromTree)

        self.ui.treeViewFile.setAnimated(True)
        self.ui.treeViewSyntax.setAnimated(True)
        self.ui.treeViewToken.setAnimated(True)

        self.ui.treeViewFile.setHeaderHidden(True)
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
        self.ui.tabWidgetEditor.tabBarDoubleClicked.connect(lambda: self.maximizeTabs(self.ui.tabWidgetEditor))

        # Bottom console
        font = QFont()
        font.setFamily("Courier")
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.ui.console.setFont(font)
        self.ui.console.setReadOnly(True)
        self.waitInputCond = QWaitCondition()
        self.oldConsoleText = None

        # Bottom output tabs
        self.ui.tabWidgetOutput.hide()
        self.ui.tabWidgetOutput.tabCloseRequested.connect(self.closeOutputTab)
        self.ui.tabWidgetOutput.tabBarDoubleClicked.connect(lambda: self.maximizeTabs(self.ui.tabWidgetOutput))
        self.ui.tabWidgetOutput.setTabText(0, 'Console')

        # Previous opened tabs,for maximizing
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
        self.ui.menuView.triggered.connect(self.manageMenuView)
        self.ui.actionAboutQt.triggered.connect(QApplication.aboutQt)

        # Menu "Run"
        self.ui.actionRun.triggered.connect(self.run)
        self.ui.actionBuild.triggered.connect(self.runCompile)
        self.ui.actionShowStable.triggered.connect(self.runSemantic)
        self.ui.actionRunParser.triggered.connect(self.runParser)
        self.ui.actionRunLexer.triggered.connect(self.runLexer)

    @pyqtSlot(bool)
    def runLexer(self, checked):
        """
        Run lexer and present result on self.ui.tabToken Tree
        :return:
        """
        p = self.genParser(Parser.mode_lexer)
        tokenNode = p.lexse() if p else None
        if not tokenNode:
            self.endEcho(False)
            return

        self.showBrowserTree(self.ui.tabToken, tokenNode)
        self.endEcho(True)

    @pyqtSlot(bool)
    def runParser(self, checked):
        """
        Run parser and present result on self.ui.tabSyntax Tree
        :return:
        """
        # Begin parse
        p = self.genParser(Parser.mode_parser)
        result = p.parse() if p else None
        if not result:
            self.endEcho(False)
            return

        syntaxNode, tokenNode = result

        # self.showBrowserTree(self.ui.tabToken, tokenNode)
        self.ui.treeViewToken.setModel(TreeModel(tokenNode))
        self.showBrowserTree(self.ui.tabSyntax, syntaxNode)
        self.endEcho(True)

    @pyqtSlot(bool)
    def runSemantic(self, checked):
        """
        run semantics analysing and print symbol table
        :return:
        """
        p = self.genParser(Parser.mode_stable)
        result = p.semantic() if p else None
        if not result:
            self.endEcho(False)
            return

        stable, syntaxNode, tokenNode = result

        self.ui.treeViewToken.setModel(TreeModel(tokenNode))
        self.ui.treeViewSyntax.setModel(TreeModel(syntaxNode))
        self.endEcho(True)

    @pyqtSlot(bool)
    def runCompile(self, checked):
        """
        Run compiler and print Intermediate code
        :return:
        """
        p = self.genParser(Parser.mode_compile)
        result = p.compile() if p else None
        if not result:
            self.endEcho(False)
            return

        codes, stable, syntaxNode, tokenNode = result
        self.ui.treeViewToken.setModel(TreeModel(tokenNode))
        self.ui.treeViewSyntax.setModel(TreeModel(syntaxNode))
        self.endEcho(True)

    @pyqtSlot(bool)
    def run(self, checked):
        """
        compile and run the source code

        compile in main thread and run in a worker thread
        """
        p = self.genParser(Parser.mode_execute)
        result = p.compile() if p else None
        if not result:
            self.endEcho(False)
            return

        codes, stable, syntaxNode, tokenNode = result
        self.ui.treeViewToken.setModel(TreeModel(tokenNode))
        self.ui.treeViewSyntax.setModel(TreeModel(syntaxNode))

        console = Console(self.ui.console, parent=self, waitCond=self.waitInputCond)
        console.update.connect(self.updateOutput)
        self.inputReceived.connect(console.receivedInput)
        self.ui.console.blockCountChanged.connect(self.waitInput)

        interp = Interpreter(codes, stdin=console, stdout=console, stderr=console)
        thread = ExecuteThread(interp.inter, self)
        thread.start()

    def genParser(self, mode=Parser.mode_execute):
        """
        Generate a parser instance
        :param mode:
        :return:
        """
        if not self.saveFile():
            return
        self.showOutputPanel()
        self.ui.actionViewConsole.setChecked(True)
        self.beginEcho()

        stdin = open(self.currentEditor.file, 'r')
        console = Console(self.ui.console, parent=self)
        console.update.connect(self.updateOutput)

        return Parser(stdin, stdout=console, stderr=console, mode=mode)

    def beginEcho(self):
        self.updateOutput('%s\n' % self.currentEditor.file)

    def endEcho(self, success=True):
        msg = 'successfully' if success else 'unsuccessfully'
        self.updateOutput('Process finished %s\n' % msg)

    @pyqtSlot(str)
    def updateOutput(self, content):
        """
        Update bottom text browser when content is writen to it.
        :param content:
        :return:
        """
        self.ui.console.moveCursor(QTextCursor.End)
        self.ui.console.insertPlainText('%s' % content)
        self.oldConsoleText = self.ui.console.toPlainText()

    @pyqtSlot(int)
    def waitInput(self, newBlockCount):
        """
        :param newBlockCount: line count
        :return:
        """
        if not self.ui.console.isReadOnly():
            self.inputReceived.emit(self.ui.console.toPlainText()
                                    .replace(self.oldConsoleText, ''))
            self.waitInputCond.wakeAll()
            self.ui.console.setReadOnly(True)

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

    def showOutputPanel(self):
        """
        Clear previous output and show the ouput panel
        :return:
        """
        self.ui.console.clear()
        self.ui.tabWidgetOutput.show()

    def showBrowserTree(self, tab, rootNode):
        """
        Show treeView on tabWidgetBrowser
        :param tab:
        :param rootNode:
        """
        model = TreeModel(rootNode)

        if tab == self.ui.tabSyntax:
            treeView = self.ui.treeViewSyntax
            name = 'Syntax'
            self.ui.actionViewSystaxTree.setChecked(True)
        else:
            treeView = self.ui.treeViewToken
            name = 'Token'
            self.ui.actionViewTokenTree.setChecked(True)

        treeView.setModel(model)

        # show the tab
        index = self.ui.tabWidgetBrowser.indexOf(tab)
        if index == -1:
            self.ui.tabWidgetBrowser.addTab(tab, name)
            index = self.ui.tabWidgetBrowser.indexOf(tab)
        self.ui.tabWidgetBrowser.setCurrentIndex(index)

        self.addjustBrowserWidth()

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
        self.switchEditorTab(0)  # choose the beginning tab as current active
        if len(self.openedEditorTabs) == 1:
            self.ui.tabWidgetEditor.setTabsClosable(False)

    @pyqtSlot(int)
    def closeBrowserTab(self, index):
        """
        Close Left Browser Tab at index
        :param index:
        :return:
        """
        # make menu "View" corresponding
        w = self.ui.tabWidgetBrowser.widget(index)
        if w == self.ui.tabFile:
            self.ui.actionViewFiles.setChecked(False)
        elif w == self.ui.tabToken:
            self.ui.actionViewTokenTree.setChecked(False)
        else:
            self.ui.actionViewSystaxTree.setChecked(False)

        # remove tab
        self.ui.tabWidgetBrowser.removeTab(index)
        if self.ui.tabWidgetBrowser.count() == 0:
            self.ui.tabWidgetBrowser.hide()

    @pyqtSlot(int)
    def closeOutputTab(self, index):
        """
        Close(hide) the output tab widget
        :param index:
        """

        # make menu "View" corresponding
        self.ui.actionViewConsole.setChecked(False)

        self.ui.tabWidgetOutput.hide()

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

    def maximizeTabs(self, widget):
        if self.preOpenedTabs:
            self.recoverTabWidgets()
        else:
            self.storeOpenedTabs()
            for w in [self.ui.tabWidgetBrowser, self.ui.tabWidgetOutput, self.ui.tabWidgetEditor]:
                if w != widget:
                    w.hide()

    @pyqtSlot(QAction)
    def manageMenuView(self, action):
        """
        Handle the action on menu "View"
        :param action:
        :return:
        """
        if action == self.ui.actionViewToolbar:
            self.ui.toolBar.show() if action.isChecked() else self.ui.toolBar.hide()
            return

        pair = {
            self.ui.actionViewFiles: (self.ui.tabWidgetBrowser, self.ui.tabFile, 'File'),
            self.ui.actionViewTokenTree: (self.ui.tabWidgetBrowser, self.ui.tabToken, 'Token'),
            self.ui.actionViewSystaxTree: (self.ui.tabWidgetBrowser, self.ui.tabSyntax, 'Syntax'),
            self.ui.actionViewConsole: (self.ui.tabWidgetOutput, self.ui.tabConsole, 'Console'),
        }
        p = pair[action]
        widget = p[0]
        tab = p[1]
        name = p[2]

        if action.isChecked():
            widget.addTab(tab, name)
            widget.setCurrentWidget(tab)

            if widget == self.ui.tabWidgetBrowser:  # reset tab inner splitter size
                self.addjustBrowserWidth()

            if widget.isHidden():
                widget.show()
        else:
            widget.removeTab(
                    widget.indexOf(tab))
            if widget.count() == 0:
                widget.hide()

    def addjustBrowserWidth(self):
        w = self.ui.tabWidgetBrowser.count() * 80
        self.ui.splitterInner.setSizes([w, self.ui.splitterInner.width() - w])

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
            self.currentEditor.file = filepath
            return True
        else:
            return False
