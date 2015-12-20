#!/usr/bin/env python
# coding:utf-8

"""
Using a recursive descent parser for analysing.

Similar to lexer, a reading buffer is set.
We can `get` a token from lexer and `unget` it to the buffer.

When parsing,
`expect(token)` means that the following token must be the same as the provided one,
    or it would raise an error.
`match(token)` means we expect a token but return None instead of raising an error when mismatching.

In Parser:
    _parse_* (check=False) means that
        When encountering a mismatch, if check is True, it returns None. Otherwise raising an error.

    _match_*() means that
        _parse_* setting check=True

    Attention:
        Param `check` is only enabled when judging whether entering into the syntax state or not.
        After entering it, `check` will be ignored.

Each parsing function return a Node which is defined in nodes.py
Finally it will gen a `ExterStmtsNode` and that is the root of the AST tree.

To connect with GUI, we need to redirect std streams.

create on '10/5/15 10:36 PM'
"""
import sys
from tokens import *
from nodes import *
from lexer import Lexer, InvalidTokenError

__author__ = 'hejunjie'


class Parser(object):
    def __init__(self, stdin, stdout=sys.stdout, stderr=sys.stderr,
                 lexer_mode=False, parser_mode=False,
                 compiler_mode=False, execute_mode=False):
        """
        Those streams will be closed at last.
        :param stdin: the source code input stream
        :param stdout: the standard output stream
        :param stderr: the standard error stream
        :param lexer_mode: Run lexer
        :param parser_mode: Run parser
        :param compiler_mode: Run compiler
        :param execute_mode: Run program
        """
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.lexer = Lexer(stdin, stdout=stdout, stderr=stderr)

        self.lexer_mode = lexer_mode
        self.parser_mode = parser_mode
        self.compiler_mode = compiler_mode
        self.execute_mode = execute_mode

        self.syntaxTree = None
        self.tokenTree = TokenTree()

        self.ahead = None  # The token just read
        self.buff = []  # unget buffer
        self.currentLine = 0  # controller for printing lexer analysis result

    def lexse(self):
        """
        Run lexer
        :return: token_tree_root_node
        """
        self.ahead = self.lexer.next_token()
        while self.ahead:
            self._build_token_tree()
            try:
                self.ahead = self.lexer.next_token()
            except InvalidTokenError:
                self._close_stream()
                return
        self._close_stream()
        return self.tokenTree.rootNode

    def parse(self):
        """
        Run parser
        :return: syntax_tree_root_node,token_tree_root_node
        """
        try:
            self.syntaxTree = self._parse_exter_stmts()
        except InvalidTokenError:
            return None
        else:
            self.stdout.write('%s\n' % self.syntaxTree.gen())
            return self.syntaxTree, self.tokenTree.rootNode
        finally:
            self._close_stream()

    def _close_stream(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()

    def _get(self):
        """
        get one token from lexer.
        Print token if in lexer_mode
        :return:
        """
        if len(self.buff) == 0:
            self.ahead = self.lexer.next_token()
            self._build_token_tree()
        else:
            self.ahead = self.buff.pop()
        return self.ahead

    def _unget(self, t=None):
        """
        put current token to buff
        :return:
        """
        self.buff.append(t or self.ahead)

    def _match(self, t):
        """
        Check if the next token matches t or not.
        If not match, unget current token.
        :param t: single token or token list
        :return:
        """
        if isinstance(t, Token):
            t = (t,)
        self._get()
        if self.ahead and self.ahead.type in [tp.type for tp in t]:
            return True
        else:
            return False

    def _expect(self, t):
        """
        expect next token to be t (or int a list of t).
        if not, raise an error
        :param t:
        :return:
        """
        if not self._match(t):
            self._print_error(t)
        else:
            return self.ahead

    def _build_token_tree(self):
        """
        Build token tree and print the lexer analysis result when each _get()
        :return:
        """
        if self.lexer.line != self.currentLine:
            self.currentLine = self.lexer.line
            self.tokenTree.newLine('Line %d' % self.currentLine)
            if self.lexer_mode:
                self.stdout.write('%s\n' % '%d: %s' % (self.currentLine, self.ahead))
        elif self.lexer_mode:
            self.stdout.write('%s\n' % '   %d: %s' % (self.currentLine, self.ahead))

        if self.ahead:
            self.tokenTree.append(TokenNode(self.ahead))

    def _print_error(self, expect=None):
        """
        Print error if not match grammer
        :param expect:
        :return:
        """
        offset = len(self.lexer.read) + 1
        offset -= len(self.ahead.lexeme) if self.ahead else 0
        msg = '\nInvalid token near row %d, column %d:' % (self.lexer.line, offset)
        self.lexer.read_line_rest()

        self.stderr.write('%s\n' % msg)
        self.stderr.write('%s\n' % ''.join(self.lexer.read))
        self.stderr.write('%s' % ' ' * (offset - 1) + '^')
        if isinstance(expect, Token):
            expect = (expect,)
        if expect:
            self.stderr.write('%s\n' % 'Expected %s' % (' or '.join([t.cate for t in expect])))
        # sys.exit(0)
        raise InvalidTokenError()

    def _parse_exter_stmts(self):
        """
        exterStmts  ::= ( declareStmt | FuncDefStmt)*

        The beginning of parsing.

        Judge which stmt to parse in the loop.
            declare ::= dataType <ID>  ( <COMMA> <ID> )* <SEMICOLON>
            VS
            funcDef  ::= (<VOID>  | dataType)  <ID>  <LPAREN> ( funcDefParamList )?  <RPAREN> ...
        """
        stmts = []
        while self._get():
            self._unget()
            if self.ahead == Token_VOID:
                stmts.append(self._parse_stmt_func_def())
            else:
                _type = self._parse_data_type()
                _id = IdNode(self._expect(Token_Identifier))
                m = self._match(Token_LPAREN)
                self._unget()
                if m:
                    stmts.append(self._parse_stmt_func_def(_type=_type, _id=_id))
                else:
                    stmts.append(self._parse_stmt_declare(_type=_type, _id=_id))
        return ExterStmtsNode(stmts)

    def _parse_stmt_func_def(self, _type=None, _id=None):
        """
        funcDefStmt ::= returnType  <ID>  <LPAREN> ( funcDefParamList )?  <RPAREN> <LBRACE> innerStmts <RBRACE>
        """
        if _type and _id:
            rtype = FuncTypeNode(_type)
        else:
            rtype = self._parse_func_type()
            _id = IdNode(self._expect(Token_Identifier))
        self._expect(Token_LPAREN)

        params = None
        if not self._match(Token_RPAREN):
            self._unget()
            params = self._parse_func_def_param_list()
            self._expect(Token_RPAREN)
        self._expect(Token_LBRACE)
        stmts = self._parse_inner_stmts()
        self._expect(Token_RBRACE)
        return FuncDefStmtNode(rtype, _id, params, stmts)

    def _parse_stmt_declare(self, _type=None, _id=None):
        """
        declareStmt ::= dataType <ID>  ( <COMMA> <ID> )* <SEMICOLON>
        """
        id_list = []
        if _type and _id:
            data_type = _type
            id_list.append(_id)
        else:
            data_type = self._parse_data_type()
            _id = self._expect(Token_Identifier)
            id_list.append(IdNode(_id))
        while True:
            if self._match(Token_COMMA):
                _id = self._expect(Token_Identifier)
                id_list.append((IdNode(_id)))
            else:
                self._unget()
                break
        self._expect(Token_SEMICOLON)
        return DeclareStmtNode(data_type, id_list)

    def _parse_stmt_func_call(self):
        """
        funcCallStmt    ::= <ID> <LPAREN> ( funcCallParamList )?  <RPAREN> <SEMICOLON>
        """
        _id = self._expect(Token_Identifier)
        self._expect(Token_LPAREN)

        params = None
        if not self._match(Token_RPAREN):
            self._unget()
            params = self._parse_func_call_param_list()
            self._expect(Token_RPAREN)
        self._expect(Token_SEMICOLON)
        return FuncCallStmtNode(IdNode(_id), params)

    def _parse_stmt_return(self):
        """
        returnStmt      ::= <RETURN> expression <SEMICOLON>
        """
        self._expect(Token_RETURN)
        expr = self._parse_expr()
        self._expect(Token_SEMICOLON)
        return ReturnStmtNode(expr)

    def _parse_func_def_param(self):
        """
        funcDefParam   ::=  dataType <ID>
        """
        data_type = self._parse_data_type()
        _id = self._expect(Token_Identifier)
        return FuncDefParam(data_type, IdNode(_id))

    def _parse_func_def_param_list(self):
        """
        funcDefParamList  ::= ( funcDefParam ( <COMMA> funcDefParam )* | <VOID> )
        """
        if self._match(Token_VOID):
            return FuncDefParamList(None)

        self._unget()
        params = [self._parse_func_def_param()]
        while True:
            if self._match(Token_COMMA):
                params.append(self._parse_func_def_param())
            else:
                self._unget()
                break
        return FuncDefParamList(params)

    def _parse_func_call_param_list(self):
        """
        funcCallParamList  ::= ( expr   ( <COMMA> expr  )* | <VOID> )
        """
        if self._match(Token_VOID):
            return FuncCallParamList(None)

        self._unget()
        params = [self._parse_expr()]
        while True:
            if self._match(Token_COMMA):
                params.append(self._parse_expr())
            else:
                self._unget()
                break
        return FuncCallParamList(params)

    def _parse_func_type(self):
        """
        funcType ::= <VOID>  | dataType
        """
        _type = self._expect([Token_INT, Token_REAL, Token_VOID])
        if _type == Token_VOID:
            return FuncTypeNode(DataTypeNode(_type, None))
        else:
            self._unget()
            data_type = self._parse_data_type()
            return FuncTypeNode(data_type)

    def _parse_inner_stmts(self):
        """
        innerStmts   ::= ( ifStmt | whileStmt | declareStmt | assignStmt | funcCallStmt | returnStmt )*
        """
        stmts = []
        while self._get():
            t = self.ahead
            if t == Token_IF:
                self._unget()
                stmts.append(self._parse_stmt_if())
            elif t == Token_WHILE:
                self._unget()
                stmts.append(self._parse_stmt_while())
            elif t in [Token_INT, Token_REAL]:
                self._unget()
                stmts.append(self._parse_stmt_declare())
            elif t == Token_RETURN:
                self._unget()
                stmts.append(self._parse_stmt_return())
            elif isinstance(t, Identifier):
                m = self._match(Token_LPAREN)
                self._unget()
                self._unget(t)
                if m:
                    stmts.append(self._parse_stmt_func_call())
                else:
                    stmts.append(self._parse_stmt_assign())
            else:
                self._unget()
                break
        return InnerStmtsNode(stmts)

    def _parse_data_type(self):
        """
        dataType    ::= ( <INT> | <REAL> ) (array)?
        """
        _type = self._expect([Token_INT, Token_REAL])
        arr = self._match_arr()
        return DataTypeNode(_type, arr)

    def _parse_stmt_if(self):
        """
        ifStmt  ::= <IF> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE>
                    ( <ELSE> <LBRACE> innerStmts  <RBRACE> )?
        :return:
        """
        self._expect(Token_IF)
        self._expect(Token_LPAREN)
        cond = self._parse_cond()
        self._expect(Token_RPAREN)
        self._expect(Token_LBRACE)
        stmts = self._parse_inner_stmts()
        stmts2 = None
        self._expect(Token_RBRACE)
        if self._match(Token_ELSE):
            self._expect(Token_LBRACE)
            stmts2 = self._parse_inner_stmts()
            self._expect(Token_RBRACE)
        else:
            self._unget()
        return IfStmtNode(cond, stmts, stmts2)

    def _parse_stmt_while(self):
        """
        whileStmt   ::= <WHILE> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE>
        :return:
        """
        self._expect(Token_WHILE)
        self._expect(Token_LPAREN)
        cond = self._parse_cond()
        self._expect(Token_RPAREN)
        self._expect(Token_LBRACE)
        stmts = self._parse_inner_stmts()
        self._expect(Token_RBRACE)
        return WhileStmtNode(cond, stmts)

    def _parse_stmt_assign(self):
        """
        assignStmt  ::= <ID> (array)? <ASSIGN> expression <SEMICOLON>
        """
        self._expect(Token_Identifier)
        t = self.ahead
        arr = self._match_arr()
        self._expect(Token_ASSIGN)
        expr = self._parse_expr()
        self._expect(Token_SEMICOLON)
        return AssignStmtNode(IdNode(t), expr, arr)

    def _parse_cond(self):
        """
        condition	::=expression compOp expression
        :return:
        """
        expr1 = self._parse_expr()
        comp = self._parse_op_comp()
        expr2 = self._parse_expr()
        return ConditionNode(expr1, comp, expr2)

    def _parse_expr(self):
        """
        expression  ::=	term (addOp term)*
        :return:
        """
        term = self._parse_term()
        l = []
        while True:
            add = self._match_op_add()
            if add:
                t = self._parse_term()
            else:
                self._unget()
                break
            l.append((add, t))
        return ExprNode(term, l)

    def _parse_term(self):
        """
        term    ::=	factor (mulOp factor)*
        :return:
        """
        l = []
        factor = self._parse_factor()
        while True:
            m = self._match_op_mul()
            if m:
                f = self._parse_factor()
            else:
                self._unget()
                break
            l.append((m, f))
        return TermNode(factor, l)

    def _parse_factor(self):
        """
        factor	::= <REAL_LITERAL> | <INT_LITERAL> | <ID> ( array )? | <LPAREN> expression <RPAREN>
        """
        self._expect((Token_RealLiteral, Token_IntLiteral, Token_Identifier, Token_LPAREN))
        t = self.ahead
        if self.ahead.type == Token_LPAREN.type:
            expr = self._parse_expr()
            self._expect(Token_RPAREN)
            return FactorNode(expr=expr)
        elif self.ahead.type == Token_Identifier.type:
            arr = self._match_arr()
            return FactorNode(_id=IdNode(t), arr=arr)
        else:
            return FactorNode(literal=LiteralNode(t))

    def _parse_op_comp(self):
        """
        compOp      ::=	<LT> | <GT> | <EQUAL> | <NEQUAL>
        """
        self._expect((Token_LT, Token_GT, Token_EQUAL, Token_NEQUAL))
        return CompNode(LeafNode(self.ahead))

    def _match_arr(self):
        """
        array   ::=	<LBRACKET> ( <INT_LITERAL> | <ID> ) ? <RBRACKET>

        If next is array which starts with <LBRACKET>, return the ArrayNode.
        Else return None.

        Error should be raised when the array is under parsing.
        """

        m = self._match(Token_LBRACKET)
        if not m:
            self._unget()
            return None

        if self._match(Token_RBRACKET):
            return ArrayNode()
        else:
            self._unget()
            index = self._expect([Token_IntLiteral, Token_Identifier])
            self._expect(Token_RBRACKET)
            if isinstance(index, Identifier):
                return ArrayNode(_id=IdNode(index))
            else:
                return ArrayNode(literal=LiteralNode(index))

    def _match_op_add(self):
        """
        addOp	    ::=	<PLUS> | <MINUS>
        """
        if self._match((Token_PLUS, Token_MINUS)):
            return AddNode(LeafNode(self.ahead))

    def _match_op_mul(self):
        """
        mulOp	    ::=	<TIMES> | <DIVIDE>
        """
        if self._match((Token_TIMES, Token_DIVIDE)):
            return MulNode(LeafNode(self.ahead))


def _read_keyboard():
    """
    read source from keyboard
    :return:
    """
    fileobj = StringIO.StringIO()
    while True:
        try:
            line = raw_input()
        except EOFError:
            break
        # add '\n' to each line
        fileobj.write(line + '\n')

    content = fileobj.getvalue()
    fileobj.close()
    return StringIO.StringIO(content)


def _read_file(path):
    """
    read source from file
    :param path: path to file
    :return:
    """
    return open(path, 'rU')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print 'too many args'
        sys.exit(0)

    if len(sys.argv) == 1:
        stdin = _read_keyboard()
    else:
        stdin = _read_file(sys.argv[1])
    p = Parser(stdin)
    p.parse()
