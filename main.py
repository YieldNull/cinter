"""
create on '11/15/15 2:37 PM'
"""

import sys
from PyQt5.QtWidgets import QApplication
from cinter.gui.window import MainWindow

import logging

__author__ = 'YieldNull'

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
