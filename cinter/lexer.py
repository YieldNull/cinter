# coding:utf-8
"""
A lexer to recognize tokens
create on '10/5/15 10:36 PM'

We need to draw a DFA(Deterministic Finite Automaton) of
the language's lexical rule first of all, because the main analysis arithmetic
is based on it although CMM is very simple.

We maintain a input buffer to enable lookahead mechanism.
When read a useless char, put it to the input buffer, where we can read char later.
A char is popped from the input buffer when it is read,
and when the buffer is empty, we read from input source instead.

To make error prompting possible, we use a counter to record the lines we have read,
and a buffer to record what we have read in current line. But there exists a bug when
we encounter a newline and switch to it. If we unget the '\n', we need to go back to the
previous state, but the buffer has been cleared. So, a pre_read_buffer is used
to record the previous line when we switch to a new line.

"""

import sys
import tokens

__author__ = 'hejunjie'

# we use 'rU' to read a file and
# append '\n' to the end of per line
# when read from keyboard, so '\r' is left out
_IGNORE = ['\t', '\n', ' ']


class EOF(object):
    """
    When encounter EOF in stdin,return an EOF object.

    A returned char by Lexer._get() will be judged by "isdigit()","isalpha()" and "=="
    just return False to escape current DFA state
    """

    def isdigit(self):
        return False

    def isalpha(self):
        return False


class InValidTokenError(Exception):
    """
    When encountered with an invalid token in lexer or parser,
    raise an InvalidTokenError to stop analysing.

    Invoker should catch this exception
    """
    pass


class Lexer(object):
    def __init__(self, stdin, stdout=sys.stdout, stderr=sys.stderr):
        """
        Those streams will be closed at last by parser.
        :param stdin: the source code input stream
        :param stdout: the standard output stream
        :param stderr:  the standard error stream
        :return:
        """
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.buf = []  # read buffer
        self.line = 1  # current line
        self.read = []  # store chars which has been read in current line
        self.pre_read = []  # store previous read when go to newline to avoid go back

    def next_token(self):
        """
        recognize the next token
        :return: the specific token as the type of token.Token or its subclasses,
                None if it is the end of file
        """
        c = self._getch()

        # consume white character
        while c in _IGNORE:
            c = self._getch()

        # end of file
        if isinstance(c, EOF):
            return None

        # consume comment or divide
        if c == '/':
            c = self._getch()
            if c == '/':
                while c != '\n':
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
                self._ungetc(c)
                return tokens.Token_DIVIDE

        # consume identifier
        if c.isalpha():
            identifier = ''
            while c.isdigit() or c.isalpha() or c == '_':
                identifier += c
                c = self._getch()

            self._ungetc(c)
            if identifier[len(identifier) - 1] == '_':  # ended with '_' is invalid
                self._ungetc('_')
                self._print_error()
            else:
                if identifier in tokens.TOKEN_RESERVED.keys():
                    return tokens.TOKEN_RESERVED[identifier]
                else:
                    return tokens.Identifier(identifier)

        # consume integer or decimal
        if c.isdigit():
            number = self._consume_int(c)
            c = self._getch()
            if c == '.':  # decimal
                c = self._getch()
                if c.isdigit():
                    number += '.'
                    number += self._consume_int(c, True)
                    return tokens.RealLiteral(float(number))
                else:
                    self._ungetc(c)
                    self._print_error()
            else:
                self._ungetc(c)
                return tokens.IntLiteral(int(number))

        # consume less greater than or not equal
        if c == '<':
            c = self._getch()
            if c == '>':
                return tokens.Token_NEQUAL
            else:
                self._ungetc(c)
                return tokens.Token_LT

        # consume assign or equal
        if c == '=':
            c = self._getch()
            if c == '=':
                return tokens.Token_EQUAL
            else:
                self._ungetc(c)
                return tokens.Token_ASSIGN

        # consume non conflict character
        if c in tokens.TOKEN_NON_CONF.keys():
            return tokens.TOKEN_NON_CONF[c]

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
            c = self.stdin.read(1)
            if len(c) == 0:
                return EOF()
        else:
            c = self.buf.pop()

        if c == '\n':  # record current state and prepare for a new line
            self.line += 1
            self.pre_read = self.read
            self.read = []
        elif not isinstance(c, EOF):
            self.read.append(c)
        return c

    def _ungetc(self, c):
        """
        put a char that was read to buffer
        :param c: the char to unget
        :return:
        """
        self.buf.append(c)
        if c == '\n':  # if unget '\n', recover to the previous state which has been recorded
            self.line -= 1
            self.read = self.pre_read
            self.pre_read = []
        elif len(self.read) > 0:
            self.read.pop()

    def read_line_rest(self):
        # read rest chars
        c = self._getch()
        while c != '\n' and not isinstance(c, EOF):
            c = self._getch()
        if not isinstance(c, EOF):
            self._ungetc(c)

    def _print_error(self):
        """
        print invalid token message
        if wanna print error, REMEMBER TO  unget a char IN ADVANCE
        :return:
        """
        offset = len(self.read) + 1
        msg = '\nInvalid token at row %d, column %d:' % (self.line, offset)
        self.read_line_rest()
        self.stderr.write('%s\n' % msg)
        self.stderr.write('%s\n' % ''.join(self.read))
        self.stderr.write('%s\n' % ' ' * (offset - 1) + '^')

        # sys.exit(0)
        raise InValidTokenError()
