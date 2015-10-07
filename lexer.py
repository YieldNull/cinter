# coding:utf-8
# coding:utf-8
"""
create on '10/5/15 10:36 PM'
"""
import sys
import token

"""
non-conflict:
    + - * > ( ) { } [ ] , ;

conflict:
    / // /*
    = ==
    < <>

regexp:
    LETTER	    ::=	["a"-"z"]|["A"-"Z"]
    DIGIT	    ::=	["0"-"9"]
    ID          ::= <LETTER> ( ( <LETTER> | <DIGIT> | "_" ) * ( <LETTER> | <DIGIT> ) )?
    INT_LITERAL ::= ["1"-"9"] <DIGIT>* | "0"
    REAL_LITERAL::= <INT_LITERAL> ( "."(INT_LITERAL)+ )?
"""

__author__ = 'hejunjie'

# we use 'rU' to read a file and
# append '\n' to the end of per line
# when read from keyboard, so '\r' is left out
_IGNORE = ['\t', '\n', ' ']


class Lexer(object):
    def __init__(self, source):
        self.input = source
        self.buf = []  # read buffer
        self.line = 1  # current line
        self.offset = 0  # current char in current line
        self.pre_offset = 0  # store length of previous line when go to newline
        self.read = []  # store chars which has been read in current line
        self.pre_read = []  # store previous read when go to newline

    def next_token(self):
        c = self._getch()

        # consume white character
        while c in _IGNORE:
            c = self._getch()

        # end of file
        if len(c) == 0:
            return None

        # consume comment or divide
        if c == '/':
            c = self._getch()
            if c == '/':
                while c not in ['\r', '\n']:
                    c = self._getch()
                return self.next_token()
            elif c == '*':
                while True:
                    c = self._getch()
                    after = self._getch()
                    if c + after == '*/':
                        break
                    else:
                        self._ungetc(after)
                return self.next_token()
            else:
                return token.DIVIDE

        # consume identifier
        if c.isalpha():
            identifier = ''
            while c.isdigit() or c.isalpha() or c == '_':
                identifier += c
                c = self._getch()

            self._ungetc(c)
            if identifier[len(identifier) - 1] == '_':
                self._print_error()
            else:
                if identifier in token.TOKEN_RESERVE.keys():
                    return token.TOKEN_RESERVE[identifier]
                else:
                    return token.Identifier(identifier)

        # consume integer or decimal
        if c.isdigit():
            number = self._consume_int(c)
            c = self._getch()
            if c == '.':  # decimal
                c = self._getch()
                if c.isdigit():
                    number += '.'
                    number += self._consume_int(c, True)
                    return token.RealLiteral(float(number))
                else:
                    self._ungetc(c)
                    self._print_error()
            else:
                self._ungetc(c)
                return token.IntLiteral(int(number))

        # consume less greater than or not equal
        if c == '<':
            c = self._getch()
            if c == '>':
                return token.NEQUAL
            else:
                self._ungetc(c)
                return token.LT

        # consume assign or equal
        if c == '=':
            c = self._getch()
            if c == '=':
                return token.EQUAL
            else:
                self._ungetc(c)
                return token.ASSIGN

        # consume non conflict character
        if c in token.TOKEN_NON_CONF.keys():
            return token.TOKEN_NON_CONF[c]

        # not match above, encounter error
        self._ungetc(c)
        self._print_error()

    def _consume_int(self, c, tail=False):
        """
        consume a integer and return the str format
        :param c: the first digit of the integer as str format
        :param tail: if true,"0"<digit>+ is valid. default is false
        :return: the integer
        """
        num = ''
        if tail is False and c == '0':
            c = self._getch()
            self._ungetc(c)
            if c.isdigit():
                self._print_error()
            else:
                return '0'
        else:
            while c.isdigit():
                num += c
                c = self._getch()
            self._ungetc(c)
            return num

    def _getch(self):
        """
        get char from buffer or input
        :return:
        """
        if len(self.buf) == 0:
            c = self.input.read(1)
        else:
            c = self.buf.pop()

        if c == '\n':
            self.line += 1
            self.pre_offset = self.offset
            self.pre_read = self.read
            self.offset = 0
            self.read = []
        else:
            self.offset += 1
            self.read.append(c)
        return c

    def _ungetc(self, c):
        """
        unget a char to buffer
        :param c: the char to unget
        :return:
        """
        self.buf.append(c)
        if c == '\n':
            self.line -= 1
            self.offset = self.pre_offset
            self.read = self.pre_read
            self.pre_read = []
            self.pre_offset = 0
        else:
            self.read.pop()
            self.offset -= 1

    def _print_error(self):
        """
        print invalid token message
        if wanna print error, REMEMBER TO  unget a char IN ADVANCE
        :return:
        """
        msg = 'Invalid token at row %d, column %d:' % (self.line, self.offset)
        offset = self.offset

        # read rest chars
        c = self._getch()
        while c != '\n':
            c = self._getch()
        self._ungetc(c)

        print msg
        print ''.join(self.read)
        print ' ' * (offset - 1) + '^'
        sys.exit(0)
