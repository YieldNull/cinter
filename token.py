# coding:utf-8
"""
create on '10/5/15 10:36 PM'

Here is all the tokens:
    non-conflict:
        + - * > ( ) { } [ ] , ;

    conflict:
        / // /*
        = ==
        < <>

    reserved:
        if, else, while, read, write,
        int, real, bool, true, false

    regexp:
        LETTER	    ::=	["a"-"z"]|["A"-"Z"]
        DIGIT	    ::=	["0"-"9"]
        ID          ::= <LETTER> ( ( <LETTER> | <DIGIT> | "_" ) * ( <LETTER> | <DIGIT> ) )?
        INT_LITERAL ::= ["1"-"9"] <DIGIT>* | "0"
        REAL_LITERAL::= <INT_LITERAL> ( "."(INT_LITERAL)+ )?
"""

__author__ = 'hejunjie'


class Token(object):
    def __init__(self, lexeme, t):
        """
        :param lexeme: the lexeme of the token
        :param t: the type of the token, as a str
        :return:
        """
        self.lexeme = lexeme
        self.type = TYPE[t]
        self._type = t  # the str format token type, in order to print

    def __str__(self):
        return "<%s: '%s'>" % (self._type, self.lexeme)


class IntLiteral(Token):
    def __init__(self, value):
        super(IntLiteral, self).__init__(str(value), 'INT_LITERAL')
        self.value = value


class RealLiteral(Token):
    def __init__(self, value):
        super(RealLiteral, self).__init__(str(value), 'REAL_LITERAL')
        self.value = value


class Identifier(Token):
    def __init__(self, lexeme):
        super(Identifier, self).__init__(lexeme, 'ID')


class ReservedToken(Token):
    def __init__(self, lexeme, t):
        super(ReservedToken, self).__init__(lexeme, t)

    def __str__(self):
        return "<%s: '%s'>" % ('RESERVE', self.lexeme)


TYPE = {
    'IF': 255, 'ELSE': 256, 'WHILE': 257, 'READ': 258, 'WRITE': 259,
    'INT': 260, 'REAL': 261, 'PLUS': 264,
    'MINUS': 265, 'TIMES': 267, 'DIVIDE': 268, 'ASSIGN': 269, 'LT': 270,
    'GT': 271, 'EQUAL': 272, 'NEQUAL': 273, 'LPAREN': 274, 'RPAREN': 275,
    'LBRACE': 276, 'RBRACE': 277, 'LBRACKET': 278, 'RBRACKET': 279,
    'COMMA': 283, 'SEMICOLON': 284, 'ID': 287,
    'INT_LITERAL': 288, 'REAL_LITERAL': 289
}

IF = ReservedToken('if', 'IF')
ELSE = ReservedToken('else', 'ELSE')
WHILE = ReservedToken('while', 'WHILE')
READ = ReservedToken('read', 'READ')
WRITE = ReservedToken('write', 'WRITE')
INT = ReservedToken('int', 'INT')
REAL = ReservedToken('real', 'REAL')

PLUS = Token('+', 'PLUS')
MINUS = Token('-', 'MINUS')
TIMES = Token('*', 'TIMES')
DIVIDE = Token('/', 'DIVIDE')
ASSIGN = Token('=', 'ASSIGN')
GT = Token('>', 'GT')
LT = Token('<', 'LT')
NEQUAL = Token('<>', 'NEQUAL')
EQUAL = Token('==', 'EQUAL')
LPAREN = Token('(', 'LPAREN')
RPAREN = Token(')', 'RPAREN')
LBRACE = Token('{', 'LBRACE')
RBRACE = Token('}', 'RBRACE')
LBRACKET = Token('[', 'LBRACKET')
RBRACKET = Token(']', 'RBRACKET')
COMMA = Token(',', 'COMMA')
SEMICOLON = Token(';', 'SEMICOLON')

TOKEN_RESERVE = {
    'if': IF, 'else': ELSE, 'while': WHILE, 'read': READ,
    'write': WRITE, 'int': INT, 'real': REAL
}
TOKEN_NON_CONF = {
    '+': PLUS, '-': MINUS, '*': TIMES, '>': GT,
    '(': LPAREN, ')': RPAREN, '{': LBRACE, '}': RBRACE,
    '[': LBRACKET, ']': RBRACKET, ',': COMMA, ';': SEMICOLON,
}
