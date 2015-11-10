#!/usr/bin/env python
# coding:utf-8

"""
create on '10/5/15 10:36 PM'
"""
import sys
import StringIO
from tokens import *
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


class Parser(object):
    def __init__(self):
        self.lexer = Lexer(_file)
        self.ahead = None
        self.buff = []
        self.current = 0  # print token controller

    def parse(self):
        self._parse_stmts(False)

    def _print_lexer(self):
        if self.lexer.line != self.current:
            current = self.lexer.line
            print '%d: %s' % (current, self.ahead)
        else:
            print '   %d: %s' % (self.current, self.ahead)

    def _print_error(self, expect=None):
        offset = len(self.lexer.read) + 1
        offset -= len(self.ahead.lexeme) if self.ahead else 0
        msg = '\nInvalid token near row %d, column %d:' % (self.lexer.line, offset)
        self.lexer.read_line_rest()

        print msg
        print ''.join(self.lexer.read)
        print ' ' * (offset - 1) + '^'
        if isinstance(expect, Token):
            expect = (expect,)
        if expect:
            print 'Expected %s' % (' or '.join([t.cate for t in expect]))
        sys.exit(0)

    def _get(self):
        if len(self.buff) == 0:
            self.ahead = self.lexer.next_token()
            # self._print_lexer()
        else:
            self.ahead = self.buff.pop()

    def _unget(self):
        self.buff.append(self.ahead)

    def _match(self, t):
        if isinstance(t, Token):
            t = (t,)
        self._get()
        if self.ahead and self.ahead.type in [tp.type for tp in t]:
            return True

    def _expect(self, t):
        if not self._match(t):
            self._print_error(t)

    def _parse_stmts(self, match=True):
        """
        statements   ::=
        (ifStmt | whileStmt | readStmt | writeStmt | assignStmt | declareStmt)+
        :return:
        """
        self._get()
        while self.ahead:
            t = self.ahead
            self._unget()
            if t == IF:
                self._parse_stmt_if()
            elif t == WHILE:
                self._parse_stmt_while()
            elif t == READ:
                self._parse_stmt_read()
            elif t == WRITE:
                self._parse_stmt_write()
            elif isinstance(t, Identifier):
                self._parse_stmt_assign()
            elif t == INT or t == REAL:
                self._parse_stmt_declare()
            elif not match:
                self._print_error()
            else:
                break
            self._get()

    def _parse_stmt_if(self):
        """
        ifStmt  ::=
        <IF> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE> ( <ELSE> <LBRACE> statements <RBRACE> )?
        :return:
        """
        self._expect(IF)
        self._expect(LPAREN)
        self._parse_cond()
        self._expect(RPAREN)
        self._expect(LBRACE)
        self._parse_stmts()
        self._expect(RBRACE)
        if self._match(ELSE):
            self._expect(LBRACE)
            self._parse_stmts()
            self._expect(RBRACE)
        else:
            self._unget()

    def _parse_stmt_while(self):
        """
        whileStmt   ::=
        <WHILE> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE>
        :return:
        """
        self._expect(WHILE)
        self._expect(LPAREN)
        self._parse_cond()
        self._expect(RPAREN)
        self._expect(LBRACE)
        self._parse_stmts()
        self._expect(RBRACE)

    def _parse_stmt_read(self):
        """
        readStmt    ::=
        <READ> <LPAREN> <ID> <RPAREN> <SEMICOLON>
        :return:
        """
        self._expect(READ)
        self._expect(LPAREN)
        self._expect(IdentifierToken)
        self._expect(RPAREN)
        self._expect(SEMICOLON)

    def _parse_stmt_write(self):
        """
        writeStmt   ::=
        <WRITE> <LPAREN> expression <RPAREN> <SEMICOLON>
        :return:
        """
        self._expect(WRITE)
        self._expect(LPAREN)
        self._parse_expr()
        self._expect(RPAREN)
        self._expect(SEMICOLON)

    def _parse_stmt_assign(self):
        """
        assignStmt  ::=
        <ID> [array] <ASSIGN> expression <SEMICOLON>
        :return:
        """
        self._expect(IdentifierToken)
        if not self._match(ASSIGN):
            self._unget()
            self._parse_arr()
            self._expect(ASSIGN)
        self._parse_expr()
        self._expect(SEMICOLON)

    def _parse_stmt_declare(self):
        """
        declareStmt ::=
        (<INT> | <REAL>) <ID>[array] ( <COMMA> <ID> [array] )* <SEMICOLON>
        :return:
        """
        self._expect((INT, REAL))
        self._match(IdentifierToken)
        self._parse_arr(True)
        while True:
            if self._match(COMMA):
                self._expect(IdentifierToken)
                self._parse_arr(True)
            else:
                self._unget()
                break
        self._expect(SEMICOLON)

    def _parse_cond(self):
        """
        condition	::=expression compOp expression
        :return:
        """
        self._parse_expr()
        self._parse_op_comp()
        self._parse_expr()

    def _parse_expr(self):
        """
        expression  ::=	term (addOp term)*
        :return:
        """
        self._parse_term()
        while True:
            if self._parse_op_add(True):
                self._parse_term()
            else:
                self._unget()
                break

    def _parse_term(self):
        """
        term    ::=	factor (mulOp factor)*
        :return:
        """
        self._parse_factor()
        while True:
            if self._parse_op_mul(True):
                self._parse_factor()
            else:
                self._unget()
                break

    def _parse_factor(self):
        """
        factor	::=
        <REAL_LITERAL> | <INT_LITERAL> | <ID> | <LPAREN> expression <RPAREN> | <ID> array
        :return:
        """
        self._expect((RealLiteralToken, IntLiteralToken, IdentifierToken, LPAREN))
        if self.ahead.type == LPAREN.type:
            self._parse_expr()
            self._expect(RPAREN)
        elif self.ahead.type == IdentifierToken.type:
            self._parse_arr(True)

    def _parse_arr(self, match=False):
        """
        array   ::=	<LBRACKET> ( <INT_LITERAL> | <ID> ) <RBRACKET>
        :return:
        """
        if match:
            if self._match(LBRACKET):
                self._expect((IntLiteralToken, IdentifierToken))
                self._expect(RBRACKET)
            else:
                self._unget()
        else:
            self._expect(LBRACKET)
            self._expect((IntLiteralToken, IdentifierToken))
            self._expect(RBRACKET)

    def _parse_op_comp(self):
        """
        compOp      ::=	<LT> | <GT> | <EQUAL> | <NEQUAL>
        :return:
        """
        self._expect((LT, GT, EQUAL, NEQUAL))

    def _parse_op_add(self, match=False):
        """
        addOp	    ::=	<PLUS> | <MINUS>
        :param match:
        :return:
        """
        if match:
            return self._match((PLUS, MINUS))
        else:
            self._expect((PLUS, MINUS))

    def _parse_op_mul(self, match=False):
        """
        mulOp	    ::=	<TIMES> | <DIVIDE>
        :param match:
        :return:
        """
        if match:
            return self._match((TIMES, DIVIDE))
        else:
            self._expect((TIMES, DIVIDE))


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print 'too many args'
        sys.exit(0)

    if len(sys.argv) == 1:
        _read_keyboard()
    else:
        _read_file(sys.argv[1])
    p = Parser()
    p.parse()
    _file.close()
