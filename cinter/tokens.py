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
        if, else, while, read, write, int, real

    regexp:
        LETTER	    ::=	["a"-"z"]|["A"-"Z"]
        DIGIT	    ::=	["0"-"9"]
        ID          ::= <LETTER> ( ( <LETTER> | <DIGIT> | "_" ) * ( <LETTER> | <DIGIT> ) )?
        INT_LITERAL ::= ["1"-"9"] <DIGIT>* | "0"
        REAL_LITERAL::= <INT_LITERAL> ( "."(INT_LITERAL)+ )?
"""

__author__ = 'hejunjie'


class Token(object):
    def __init__(self, lexeme, cate):
        """
        :param lexeme: the lexeme of the token
        :param cate: the type of the token, as a str
        :return:
        """
        self.lexeme = lexeme
        self.type = TYPE[cate]
        self.cate = cate  # the category of the token.like 'COMMA' corresponds to ','

    def __str__(self):
        return "<%s: '%s'>" % (self.cate, self.lexeme)


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
    def __init__(self, lexeme, cate):
        super(ReservedToken, self).__init__(lexeme, cate)

    def __str__(self):
        return "<%s: '%s'>" % ('RESERVE', self.lexeme)


TYPE = {
    'IF': 255, 'ELSE': 256, 'WHILE': 257, 'READ': 258, 'WRITE': 259,
    'INT': 260, 'REAL': 261, 'PLUS': 264,
    'MINUS': 265, 'TIMES': 267, 'DIVIDE': 268, 'ASSIGN': 269, 'LT': 270,
    'GT': 271, 'EQUAL': 272, 'NEQUAL': 273, 'LPAREN': 274, 'RPAREN': 275,
    'LBRACE': 276, 'RBRACE': 277, 'LBRACKET': 278, 'RBRACKET': 279,
    'COMMA': 283, 'SEMICOLON': 284, 'ID': 287,
    'INT_LITERAL': 288, 'REAL_LITERAL': 289, 'RETURN': 290, 'VOID': 291
}

Token_IF = ReservedToken('if', 'IF')
Token_ELSE = ReservedToken('else', 'ELSE')
Token_WHILE = ReservedToken('while', 'WHILE')
Token_READ = ReservedToken('read', 'READ')
Token_WRITE = ReservedToken('write', 'WRITE')
Token_INT = ReservedToken('int', 'INT')
Token_REAL = ReservedToken('real', 'REAL')
Token_RETURN = ReservedToken('return', 'RETURN')
Token_VOID = ReservedToken('void', 'VOID')

Token_PLUS = Token('+', 'PLUS')
Token_MINUS = Token('-', 'MINUS')
Token_TIMES = Token('*', 'TIMES')
Token_DIVIDE = Token('/', 'DIVIDE')
Token_ASSIGN = Token('=', 'ASSIGN')
Token_GT = Token('>', 'GT')
Token_LT = Token('<', 'LT')
Token_NEQUAL = Token('<>', 'NEQUAL')
Token_EQUAL = Token('==', 'EQUAL')
Token_LPAREN = Token('(', 'LPAREN')
Token_RPAREN = Token(')', 'RPAREN')
Token_LBRACE = Token('{', 'LBRACE')
Token_RBRACE = Token('}', 'RBRACE')
Token_LBRACKET = Token('[', 'LBRACKET')
Token_RBRACKET = Token(']', 'RBRACKET')
Token_COMMA = Token(',', 'COMMA')
Token_SEMICOLON = Token(';', 'SEMICOLON')

# just used for type matching in parser
Token_IntLiteral = IntLiteral(0)
Token_RealLiteral = RealLiteral(0.0)
Token_Identifier = Identifier(';')

TOKEN_RESERVED = {
    'if': Token_IF, 'else': Token_ELSE, 'while': Token_WHILE,
    'int': Token_INT, 'real': Token_REAL, 'return': Token_RETURN,
    'void': Token_VOID
}
TOKEN_NON_CONF = {
    '+': Token_PLUS, '-': Token_MINUS, '*': Token_TIMES, '>': Token_GT,
    '(': Token_LPAREN, ')': Token_RPAREN, '{': Token_LBRACE, '}': Token_RBRACE,
    '[': Token_LBRACKET, ']': Token_RBRACKET, ',': Token_COMMA, ';': Token_SEMICOLON,
}
