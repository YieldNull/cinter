"""
create on '11/14/15 11:44 AM'
"""

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QTextDocument

__author__ = 'YieldNull'


class Rule(object):
    def __init__(self, pattern, _format):
        self.pattern = pattern
        self.format = _format


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super(Highlighter, self).__init__(parent)

        self.highlightingRules = []

        self.commentStartExpression = QRegExp()
        self.commentEndExpression = QRegExp()

        self.keywordFormat = QTextCharFormat()
        self.classFormat = QTextCharFormat()
        self.singleLineCommentFormat = QTextCharFormat()
        self.multiLineCommentFormat = QTextCharFormat()
        self.quotationFormat = QTextCharFormat()
        self.functionFormat = QTextCharFormat()

        self.keywordFormat.setForeground(Qt.darkBlue)
        self.keywordFormat.setFontWeight(QFont.Bold)

        keywords = [
            'char', 'class', 'const',
            'double', 'enum', 'explicit',
            'friend', 'inline', 'int',
            'long', 'namespace', 'operator',
            'private', 'protected', 'public',
            'short', 'signals', 'signed',
            'slots', 'static', 'struct',
            'template', 'typedef', 'typename',
            'union', 'unsigned', 'virtual',
            'void', 'volatile']

        for keyword in keywords:
            self.highlightingRules.append(Rule(QRegExp('\\b%s\\b' % keyword), self.keywordFormat))

        self.classFormat.setFontWeight(QFont.Bold)
        self.classFormat.setForeground(Qt.darkMagenta)
        self.highlightingRules.append(Rule(QRegExp('Q[A-Za-z]+'), self.classFormat))

        self.singleLineCommentFormat.setForeground(Qt.red)
        self.highlightingRules.append(Rule(QRegExp('//[^\n]*'), self.singleLineCommentFormat))

        self.multiLineCommentFormat.setForeground(Qt.red)

        self.quotationFormat.setForeground(Qt.darkGreen)
        self.highlightingRules.append(Rule(QRegExp('\'.*\''), self.quotationFormat))

        self.functionFormat.setFontItalic(True)
        self.functionFormat.setForeground(Qt.blue)
        self.highlightingRules.append(Rule(QRegExp('[A-Za-z0-9_]+(?=\\()'), self.functionFormat))

        self.commentStartExpression = QRegExp('/\\*')
        self.commentEndExpression = QRegExp('\\*/')

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)
            if (endIndex == -1):
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text, startIndex + commentLength)
