# coding:utf-8
"""
create on '11/14/15 11:51 AM'
"""
from PyQt5.QtCore import pyqtSlot, QSize, QRect, Qt
from PyQt5.QtGui import QColor, QTextFormat, QPainter, QFont, QFontMetrics
from PyQt5.QtWidgets import QWidget, QTextEdit
from PyQt5.QtWidgets import QPlainTextEdit
from gui.highlighter import Highlighter

__author__ = 'hejunjie'


class LineNumArea(QWidget):
    """
    The line number area
    """

    def __init__(self, editor):
        super(LineNumArea, self).__init__(editor)
        self.editor = editor

    def sizeHint(self):
        """
        Override. Provide the size hint
        :return:
        """
        return QSize(self.editor.lineNumWidth(), 0)

    def paintEvent(self, event):
        """
        Override. Like onDraw() on android
        :param event:
        :return:
        """
        self.editor.numPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.numArea = LineNumArea(self)

        # Binding signals to slots
        self.blockCountChanged.connect(self.updateNumWidth)
        self.updateRequest.connect(self.updateNum)
        self.cursorPositionChanged.connect(self.highlightLine)
        self.textChanged.connect(self.highlightCode)

        # editor config
        font = QFont()
        font.setFamily("Courier")
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(12)
        self.setFont(font)
        metrics = QFontMetrics(font)
        self.setTabStopWidth(3 * metrics.width('a'))

        # highlighter
        self.highlighter = Highlighter(self.document())

        # init
        self.updateNumWidth(0)
        self.highlightLine()

    def highlightCode(self):
        self.highlighter.highlightBlock(str(self.document()))

    def resizeEvent(self, event):
        """
        Override. Resize the editor
        :param event:
        :return:
        """
        super(CodeEditor, self).resizeEvent(event)

        # reset the position and size of the line number area
        cr = self.contentsRect()
        self.numArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumWidth(), cr.height()))

    def numPaintEvent(self, event):
        """
        Paint the editor
        :param event:
        :return:
        """
        painter = QPainter(self.numArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_num + 1
                painter.setPen(Qt.darkRed)
                painter.drawText(0, top, self.numArea.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, ' %s ' % str(number))  # padding

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_num += 1

    def lineNumWidth(self):
        """
        Get the width of the line number
        """
        digits = 1
        _max = max(1, self.blockCount())  # blockCount means line count
        while _max >= 10:
            _max /= 10
            digits += 1

        # make it wider for padding
        return self.fontMetrics().width('8') * (digits + 2)

    @pyqtSlot(int)
    def updateNumWidth(self, count):
        """
        Triggered when blockCountChanged
        """
        # make some margin to the line number area
        self.setViewportMargins(self.lineNumWidth() + 1, 0, 0, 0)

    @pyqtSlot()
    def highlightLine(self):
        """
        Triggered when cursorPositionChanged
        :return:
        """
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            self.setExtraSelections(extra_selections)

    @pyqtSlot(QRect, int)
    def updateNum(self, rect, dy):
        """
        Triggered when updateRequest.

        This signal is emitted when the text document needs an update of the specified rect.
        If the text is scrolled, rect will cover the entire viewport area.
        If the text is scrolled vertically, dy carries the amount of pixels the viewport was scrolled.
        :param rect:
        :param dy: carries the amount of pixels the viewport was scrolled.
        :return:
        """
        if dy:
            self.numArea.scroll(0, dy)
        else:
            self.numArea.update(0, rect.y(), self.numArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateNumWidth(0)
