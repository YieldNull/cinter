#!/usr/bin/env python
# coding:utf-8

"""
create on '10/5/15 10:36 PM'
"""
import StringIO
import sys
from lexer import Lexer

__author__ = 'hejunjie'

# the file-like object
_file = None


def _read_keyboard():
    """
    read source from keyboard
    :return:
    """
    global _file
    _file = StringIO.StringIO()
    while True:
        try:
            line = raw_input()
        except EOFError:
            break
        # add '\n' to each line
        _file.write(line + '\n')

    content = _file.getvalue()
    _file.close()
    _file = StringIO.StringIO(content)


def _read_file(path):
    """
    read source from file
    :param path: path to file
    :return:
    """
    global _file
    _file = open(path, 'rU')


def main(argv):
    if len(argv) > 2:
        print 'too many args'
        return
    if len(argv) == 1:
        _read_keyboard()
    else:
        _read_file(argv[1])

    le = Lexer(_file)
    token = le.next_token()
    while token is not None:
        print token
        token = le.next_token()


if __name__ == '__main__':
    main(sys.argv)
