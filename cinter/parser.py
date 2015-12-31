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
import copy
import sys

from cinter.inter import Interpreter
from tokens import *
from nodes import *
from stable import STable, SemanticsError
from lexer import Lexer, InvalidTokenError

__author__ = 'hejunjie'


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


class Parser(object):
    mode_lexer = 0
    mode_parser = 1
    mode_stable = 2
    mode_compile = 3
    mode_execute = 4

    def __init__(self, stdin, stdout=sys.stdout, stderr=sys.stderr, mode=mode_execute):
        """
        Those streams will be closed at last.
        :param stdin: the source code input stream
        :param stdout: the standard output stream
        :param stderr: the standard error stream
        :param mode: mode
        """
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.lexer = Lexer(stdin, stdout=stdout, stderr=stderr)

        self.mode = mode

        self.tokenTree = TokenTree()
        self.rootNode = None
        self.stable = STable()
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
                return
        return self.tokenTree.rootNode

    def parse(self):
        """
        Run parser
        :return: syntax_tree_root_node,token_tree_root_node
        """
        try:
            self.rootNode = self._parse_exter_stmts()
        except InvalidTokenError:
            return None
        else:
            if self.mode == Parser.mode_parser:
                self.stdout.write('%s\n' % self.rootNode.gen_tree())
            return self.rootNode, self.tokenTree.rootNode

    def semantic(self):
        """
        Semantic analysing using DFS.
        :return: root_stable, root_node, root_token_node
        """

        # do parse first
        parse_result = self.parse()
        if not parse_result:
            return None

        # add `read` and `write` function to stable
        self.stable.symbol_append(Symbol('read', STypeFunc(SType(tokens.Token_INT), [])))
        self.stable.symbol_append(Symbol('write', STypeFunc(SType(tokens.Token_VOID), [SType(Token_INT)])))

        stack = [(self.rootNode, self.stable)]  # the node and the direct symbol table which it is in
        while len(stack) > 0:
            node, stable = stack.pop()
            try:
                table = node.gen_stable(stable)
            except SemanticsError, e:
                self.stderr.write('%s %s\n' % (str(e), node.gen_location()))
                return None
            else:
                children = list(node.childItems)
                children.reverse()
                children = [(child, table or stable) for child in children]
                stack += children

        # check main function
        error = self.stable.check_main()
        if error:
            self.stderr.write('%s\n' % error)
            return None
        elif self.mode == Parser.mode_stable:
            self.stdout.write(self.stable.gen_tree())

        return self.stable, parse_result[0], parse_result[1]

    def compile(self):
        """
        Gen Intermediate code
        :return: code_list, root_stable, root_node, root_token_node
        """
        result = self.semantic()
        if not result:
            return None

        Code.line = -1  # initialize line before each compiling
        codes = self.rootNode.gen_code()

        if self.mode == Parser.mode_compile:
            for code in codes:
                self.stdout.write('%s\n' % str(code))

        return codes, result[0], result[1], result[2]

    def execute(self):
        """
        execute the code
        """
        result = self.compile()
        if not result:
            return None

        interp = Interpreter(result[0], stdin=self.stdin, stdout=self.stdout, stderr=self.stderr)
        interp.inter()

        return result

    def close_stream(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()

    def _get(self):
        """
        get one token from lexer.
        :return:
        """
        if len(self.buff) == 0:
            self.ahead = self.lexer.next_token()
            if self.ahead:  # set token location
                self.ahead = copy.copy(self.ahead)  # copy the token to make difference
                self.ahead.set_location(self.lexer.get_location())
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
            if self.mode == Parser.mode_lexer:
                self.stdout.write('%s\n' % '%d: %s' % (self.currentLine, self.ahead))
        elif self.mode == Parser.mode_lexer:
            self.stdout.write('%s\n' % '   %d: %s' % (self.currentLine, self.ahead))

        if self.ahead:
            self.tokenTree.append(TokenNode(self.ahead))

    def _print_error(self, expect=None):
        """
        Print error if not match grammer
        :param expect:
        :return:
        """
        line, offset = self.lexer.get_location()
        offset -= len(self.ahead.lexeme) if self.ahead else 0
        msg = '\nInvalid token near row %d, column %d:' % (line, offset)
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
            declare ::= dataType (array)? <ID>  ( <COMMA> <ID> )* <SEMICOLON>
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
                m = self._match(Token_LBRACKET)
                self._unget()
                if m:
                    self._unget(_type.token)
                    stmts.append(self._parse_stmt_declare())
                else:
                    _id = IdNode(self._expect(Token_Identifier))
                    m = self._match(Token_LPAREN)
                    self._unget()
                    self._unget(_id.token)
                    self._unget(_type.token)
                    if m:
                        stmts.append(self._parse_stmt_func_def())
                    else:
                        stmts.append(self._parse_stmt_declare())
        return ExterStmtsNode(stmts)

    def _parse_stmt_func_def(self):
        """
        funcDefStmt ::= returnType  <ID>  <LPAREN> ( funcDefParamList )?  <RPAREN> <LBRACE> innerStmts <RBRACE>
        """
        rtype = self._parse_return_type()
        _id = IdNode(self._expect(Token_Identifier))
        self._expect(Token_LPAREN)

        params = FuncDefParamList(None)
        if not self._match(Token_RPAREN):
            self._unget()
            params = self._parse_func_def_param_list()
            self._expect(Token_RPAREN)
        self._expect(Token_LBRACE)
        stmts = self._parse_inner_stmts()

        # function must return
        if stmts.childCount() == 0 or \
                (True not in [isinstance(stmt, ReturnStmtNode) for stmt in stmts.childItems]):
            self._parse_stmt_return()

        self._expect(Token_RBRACE)
        return FuncDefStmtNode(rtype, _id, params, stmts)

    def _parse_stmt_return(self):
        """
        returnStmt      ::= <RETURN> (expression)? <SEMICOLON>
        """
        returnNode = self._expect(Token_RETURN)
        if self._match(Token_SEMICOLON):
            return ReturnStmtNode(returnNode)
        else:
            self._unget()
            expr = self._parse_expr()
        self._expect(Token_SEMICOLON)
        return ReturnStmtNode(returnNode, expr)

    def _parse_stmt_func_call(self):
        """
        funcCallStmt    ::= funcCallExpr <SEMICOLON>
        """
        funcCall = self._parse_func_call_expr()
        self._expect(Token_SEMICOLON)
        return FuncCallStmtNode(funcCall)

    def _parse_func_call_expr(self):
        """
        funcCallExpr    ::= <ID> <LPAREN> ( funcCallParamList )?  <RPAREN>
        """
        _id = self._expect(Token_Identifier)
        self._expect(Token_LPAREN)

        params = None
        if not self._match(Token_RPAREN):
            self._unget()
            params = self._parse_func_call_param_list()
            self._expect(Token_RPAREN)
        return FuncCallExprNode(IdNode(_id), params)

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

    def _parse_return_type(self):
        """
        returnType ::= <VOID>  | dataType
        """
        _type = self._expect([Token_INT, Token_REAL, Token_VOID])
        if _type == Token_VOID:
            return ReturnTypeNode(None)
        else:
            self._unget()
            data_type = self._parse_data_type()
            return ReturnTypeNode(data_type)

    def _parse_stmt_declare(self):
        """
        declareStmt ::= dataType (array)? <ID>  ( <COMMA> <ID> )* ( <ASSIGN> ( expression | arrayInit ) )?<SEMICOLON>
        """
        id_list = []
        data_type = self._parse_data_type()
        arr = self._match_arr(int_index=True)
        _id = self._expect(Token_Identifier)
        id_list.append(IdNode(_id))
        while True:
            if self._match(Token_COMMA):
                _id = self._expect(Token_Identifier)
                id_list.append((IdNode(_id)))
            else:
                self._unget()
                break

        if self._match(Token_ASSIGN):  # handle assign
            if self._match(Token_LBRACE):  # array init
                self._unget()
                if not arr:  # raise an error
                    self._expect([Token_IntLiteral, Token_RealLiteral,
                                  Token_Identifier, Token_LPAREN])

                arrInit = self._parse_arr_init(data_type.token, arr.size)
                self._expect(Token_SEMICOLON)
                return DeclareStmtNode(data_type, id_list, arr=arr, expr_or_init=arrInit)
            else:  # expression
                self._unget()
                if arr:
                    self._expect(Token_LBRACE)  # raise an error
                expr = self._parse_expr()
                self._expect(Token_SEMICOLON)
                return DeclareStmtNode(data_type, id_list, expr_or_init=expr)
        else:
            self._unget()
            self._expect(Token_SEMICOLON)
            return DeclareStmtNode(data_type, id_list, arr=arr)

    def _parse_arr_init(self, data_type, size):
        """
        arrayInit   ::= <LBRACE>( INT_LITERAL (<COMMA> INT_LITERAL)* | REAL_LITERAL(<COMMA> REAL_LITERAL)* ) <RBRACE>
        :return:
        """
        self._expect(Token_LBRACE)
        self._expect([Token_IntLiteral, Token_RealLiteral])
        liter = self.ahead

        _type = Token_INT if isinstance(liter, IntLiteral) else Token_REAL

        if _type != data_type:  # raise an error
            self._unget()
            if _type == Token_INT:
                self._expect(Token_RealLiteral)
            else:
                self._expect(Token_IntLiteral)

        literals = [LiteralNode(liter)]
        while True:
            if len(literals) == size:
                break
            m = self._match(Token_COMMA)
            if m:
                li = self._expect(Token_IntLiteral if liter == Token_IntLiteral else Token_RealLiteral)
            else:
                self._unget()
                break
            literals.append(LiteralNode(li))
        self._expect(Token_RBRACE)
        return ArrayInitNode(literals)

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
        dataType    ::= ( <INT> | <REAL> )
        """
        _type = self._expect([Token_INT, Token_REAL])
        return DataTypeNode(_type)

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
        return AssignStmtNode(IdNode(t), expr, arr=arr)

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
        factor	::= <REAL_LITERAL> | <INT_LITERAL> | <ID> ( array )?
                    | funcCallExpr | <LPAREN> expression <RPAREN>
        """
        self._expect((Token_RealLiteral, Token_IntLiteral, Token_Identifier, Token_LPAREN))
        t = self.ahead
        if self.ahead == Token_LPAREN:
            expr = self._parse_expr()
            self._expect(Token_RPAREN)
            return FactorNode(expr=expr)
        elif self.ahead == Token_Identifier:
            m = self._match(Token_LPAREN)
            self._unget()
            if m:
                self._unget(t)
                funcCall = self._parse_func_call_expr()
                return FactorNode(funcCall=funcCall)
            else:
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

    def _match_arr(self, int_index=False):
        """
        array   ::=	<LBRACKET> ( <INT_LITERAL> | <ID> ) ? <RBRACKET>

        If next is array which starts with <LBRACKET>, return the ArrayNode.
        Else return None.

        Error should be raised when the array is under parsing.

        :param int_index: index must be int literal? default is false
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
                if int_index:
                    self._unget()
                    self._unget(index)
                    self._expect(Token_IntLiteral)  # this code will raise an error
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
