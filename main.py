# coding:utf-8
"""
create on '11/15/15 2:37 PM'
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.window import MainWindow

__author__ = 'hejunjie'

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
