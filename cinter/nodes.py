# coding:utf-8
"""
Nodes of abstract grammar tree.

create on '11/9/15 12:54 PM'
"""
import StringIO

import tokens
from stable import Symbol, STypeFunc, STable, SType, STypeArray

__author__ = 'hejunjie'


class Node(object):
    """
    Basic node which is also used in QAbstractItemModel.
    """

    def __init__(self, cate, parent=None):
        self.cate = cate  # for print
        self.parent = parent
        self.childItems = []

    def __str__(self):
        return self.cate

    def append(self, item):
        """
        Append a item as its child.Show as a sub row in treeView
        :param item:
        """
        assert isinstance(item, Node)
        item.parent = self
        self.childItems.append(item)

    def pop(self):
        self.childItems.pop()

    def childAt(self, row):
        """
        Return the child item at index(row) in the sub row
        :param row:
        """
        try:
            c = self.childItems[row]
        except IndexError:
            return None
        else:
            return c

    def childCount(self):
        return len(self.childItems)

    def data(self):
        return self.__str__()

    def indexInParent(self):
        """
        The index of the item in the same lever row
        :return:
        """
        if self.parent:
            return self.parent.childItems.index(self)
        return 0

    def brother(self):
        index = self.indexInParent()
        return self.childAt(index + 1)

    def str_tree(self):
        """
        Print tree with itself as the root node using DFS.
        """
        stack = [self]
        stdout = StringIO.StringIO()
        while len(stack) > 0:
            n = stack.pop()
            p = n.parent
            indent = []
            while p:
                if p.parent and p.indexInParent() < p.parent.childCount() - 1:
                    indent.append('|     ')
                else:
                    indent.append('      ')
                p = p.parent

            indent.reverse()
            stdout.write(''.join(indent))
            stdout.write('|----> %s\n' % str(n))
            l = list(n.childItems)
            l.reverse()
            stack += l
        return stdout.getvalue()

    def gen_stable(self, stable):
        assert isinstance(stable, STable)
        return None

    def gen_stype(self):
        return None


#####################################################
#############  for building token tree ##############
#####################################################

class TokenNode(Node):
    def __init__(self, t):
        super(TokenNode, self).__init__(t.lexeme)
        self.token = t

    def __str__(self):
        return str(self.token)


class TokenTree(object):
    """
    Generate Token Tree which is used in QAbstractItemModel.
    Each line is a sub tree.
    When newLine, gen a new sub tree
    When append, append a node to the bottom sub tree.
    """

    def __init__(self):
        self.currentLine = 0
        self.rootNode = Node('Token Tree')
        self.bottomTree = None

    def newLine(self, lexeme):
        self.bottomTree = Node(lexeme)
        self.rootNode.append(self.bottomTree)

    def append(self, node):
        self.bottomTree.append(node)


#############################################################
#############  Util nodes for building grammar tree #########
#############################################################


class LeafNode(Node):
    """
    A leaf node which does not have a child node.
    """

    def __init__(self, token):
        super(LeafNode, self).__init__(token.cate)
        self.token = token

    def __str__(self):
        return '%s : "%s"' % (self.token.cate, self.token.lexeme)


class LiteralNode(LeafNode):
    """
    A real or integer literal node.
    """

    def __init__(self, token):
        assert isinstance(token, tokens.IntLiteral) or isinstance(token, tokens.RealLiteral)
        super(LiteralNode, self).__init__(token)


class DataTypeNode(LeafNode):
    """
    dataType    ::=( <INT> | <REAL> ) (array)?
    """

    def __init__(self, token, arr=None):
        super(LeafNode, self).__init__(token)
        assert token in [tokens.Token_INT, tokens.Token_REAL]
        assert arr is None or isinstance(arr, ArrayNode)
        self.arr = arr

    def gen_stype(self):
        if self.arr:
            return STypeArray(self.token, self.arr.size)
        else:
            return SType(self.token)


class IdNode(LeafNode):
    def __init__(self, _id):
        assert isinstance(_id, tokens.Identifier)
        super(IdNode, self).__init__(_id)

        self.name = self.token.lexeme
        self.stype = None
        self.type = None
        self.arr = None

    def set_stype(self, stype):
        self.stype = stype

    def update_stype(self, token, arr=None):
        self.type = token
        self.arr = arr

    def gen_stype(self):
        if not self.arr:
            return SType(self.type)
        else:
            return STypeArray(self.type, self.arr.size)

    def gen_symbol(self):
        return Symbol(self.name, self.gen_stype())


class FuncId(LeafNode):
    def __init__(self, rtype, _id, param_stypes):
        assert isinstance(rtype, ReturnTypeNode)
        assert isinstance(_id, IdNode)
        super(FuncId, self).__init__(_id.token)

        self.rtype = rtype
        self.name = _id.name
        self.param_stypes = param_stypes

    def gen_stype(self):
        return STypeFunc(self.rtype.gen_stype(), self.param_stypes)

    def gen_symbol(self):
        return Symbol(self.name, self.gen_stype())


class ArrayNode(Node):
    """
    array   ::=	<LBRACKET> ( <INT_LITERAL> | <ID> )? <RBRACKET>
    """

    def __init__(self, _id=None, literal=None):
        super(ArrayNode, self).__init__('Array')
        assert not (_id and literal)

        if _id:
            assert isinstance(_id, IdNode)
            self.append(_id)
        if literal:
            assert isinstance(literal, LiteralNode)
            assert isinstance(literal.token.lexeme, int)
            self.append(literal)
            self.size = int(literal.token.lexeme)
            self.index = self.size

    def gen_stable(self, stable):
        _id = self.childAt(0)
        if isinstance(_id, IdNode):
            stable.symbol_invoke(_id.gen_symbol())


class VoidParamNode(Node):
    """
    Void function call param or declare param
    """

    def __init__(self):
        super(VoidParamNode, self).__init__('VoidParam')


class EmptyBodyNode(Node):
    """
    Empty innerStmts body.
    """

    def __init__(self):
        super(EmptyBodyNode, self).__init__('EmptyBody')


#####################################################
#################### grammar nodes ##################
#####################################################

class ExterStmtsNode(Node):
    """
    exterStmts  ::= ( declareStmt | funcDefStmt )*
    """

    def __init__(self, stmt_list):
        super(ExterStmtsNode, self).__init__('ExterStmts')
        for stmt in stmt_list:
            self.append(stmt)


class FuncDefStmtNode(Node):
    """
    funcDefStmt ::= returnType  <ID>  <LPAREN> ( funcDefParamList )?  <RPAREN> <LBRACE> innerStmts <RBRACE>
    """

    def __init__(self, rtype, _id, params, innerStmts):
        super(FuncDefStmtNode, self).__init__('FuncDefStmt')

        # set func_id type
        self.funcId = FuncId(rtype.gen_stype(), _id, params.gen_stype())

        self.append(rtype)
        self.append(self.funcId)
        if params is None:
            params = FuncDefParamList(None)
        self.append(params)
        self.append(innerStmts)

    def gen_stable(self, stable):
        stable.symbol_append(self.funcId.gen_symbol())


class DeclareStmtNode(Node):
    """
    declareStmt ::= dataType <ID>  ( <COMMA> <ID> )* <SEMICOLON>
    """

    def __init__(self, data_type, id_list):
        super(DeclareStmtNode, self).__init__('DeclareStmt')
        assert isinstance(data_type, DataTypeNode)

        self.stype = data_type.gen_stype()

        self.append(data_type)
        for _id in id_list:
            assert isinstance(_id, IdNode)
            self.append(_id)
            _id.set_stype(self.stype)  # set id type

        self.id_list = id_list

    def gen_stable(self, stable):
        for _id in self.id_list:
            stable.symbol_append(_id.gen_symbol())


class FuncCallStmtNode(Node):
    """
    funcCallStmt    ::= <ID> <LPAREN> ( funcCallParamList )?  <RPAREN> <SEMICOLON>
    """

    def __init__(self, _id, params):
        super(FuncCallStmtNode, self).__init__('FuncCallStmt')
        assert params is not None

        self.append(_id)
        self.append(params)

        self.name = _id.name
        self.params = params

    def gen_stable(self, stable):
        stable.symbol_invoke_func(self.name, self.params.gen_stype())


class FuncDefParam(Node):
    """
    funcDefParam   ::=  dataType <ID>
    """

    def __init__(self, data_type, _id):
        super(FuncDefParam, self).__init__('FuncDefParam')
        assert isinstance(data_type, DataTypeNode)
        assert isinstance(_id, IdNode)

        self.append(data_type)
        self.append(_id)

        self.stype = data_type.gen_stype()
        self.name = _id.name

    def gen_stype(self):
        return self.stype


class FuncDefParamList(Node):
    """
    funcDefParamList  ::= ( funcDefParam ( <COMMA> funcDefParam )* | <VOID> )
    """

    def __init__(self, params):
        """
        if param is void, `params` is None
        :param params:
        :return:
        """
        super(FuncDefParamList, self).__init__('FuncDefParams')
        if params:
            for param in params:
                assert isinstance(param, FuncDefParam)
                self.append(param)

    def gen_stype(self):
        """
        Gen param stype list
        """
        if self.childCount() == 0:
            return [SType(tokens.Token_VOID)]
        else:
            return [param.gen_stype() for param in self.childItems]


class FuncCallParamList(Node):
    """
    funcCallParamList  ::= ( expr   ( <COMMA> expr  )* | <VOID> )
    """

    def __init__(self, params):
        super(FuncCallParamList, self).__init__('FuncCallParamList')
        if params:
            for param in params:
                assert isinstance(param, ExprNode)
                self.append(param)

    def gen_stype(self):
        return [expr.gen_stype() for expr in self.childItems]


class ReturnTypeNode(Node):
    """
    returnType ::= <VOID>  | dataType
    """

    def __init__(self, data_type=None):
        super(ReturnTypeNode, self).__init__('ReturnType')
        if data_type:
            assert isinstance(data_type, DataTypeNode)

            self.stype = data_type.gen_stype()
        else:
            self.stype = SType(tokens.Token_VOID)

    def gen_stype(self):
        return self.stype


class ReturnStmtNode(Node):
    """
    returnStmt      ::= <RETURN> expression <SEMICOLON>
    """

    def __init__(self, expr):
        super(ReturnStmtNode, self).__init__('ReturnStmt')
        self.append(expr)

    def gen_stype(self):
        return self.childAt(0).gen_stype()  # TODO


class InnerStmtsNode(Node):
    """
    innerStmts   ::= ( declareStmt | assignStmt | ifStmt | whileStmt | funcCallStmt | returnStmt )*
    """

    def __init__(self, stmt_list):
        super(InnerStmtsNode, self).__init__('InnerStmts')
        if len(stmt_list) > 0:
            for stmt in stmt_list:
                self.append(stmt)

    def gen_stable(self, stable):
        table = STable()
        stable.table_append(table)
        return table


class IfStmtNode(Node):
    """
    ifStmt  ::=
    <IF> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE> ( <ELSE> <LBRACE> innerStmts <RBRACE> )?
    """

    def __init__(self, cond, stmts1, stmts2=None):
        super(IfStmtNode, self).__init__('IfStmt')
        self.append(cond)
        self.append(stmts1)
        if stmts2:
            self.append(stmts2)


class WhileStmtNode(Node):
    """
    whileStmt   ::=
    <WHILE> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE>
    """

    def __init__(self, cond, stmts):
        super(WhileStmtNode, self).__init__('WhileStmt')
        self.append(cond)
        self.append(stmts)


class AssignStmtNode(Node):
    """
    assignStmt  ::= <ID> (array)? <ASSIGN> expression <SEMICOLON>
    """

    def __init__(self, _id, expr, arr=None):
        super(AssignStmtNode, self).__init__('AssignStmt')
        _id.brother = arr or expr
        self.append(_id)
        if arr:
            self.append(arr)
        self.append(expr)

        self.token = _id.token
        self.arr = arr

    def gen_stable(self, stable):
        stable.symbol_invoke()  # TODO


class ConditionNode(Node):
    """
    condition	::=	expression compOp expression
    """

    def __init__(self, expr1, compOp, expr2):
        super(ConditionNode, self).__init__('Condition')
        self.append(expr1)
        self.append(compOp)
        self.append(expr2)


class ExprNode(Node):
    """
    expression  ::=	term (addOp term)*
    """

    def __init__(self, term, addOp_term_list=None):
        super(ExprNode, self).__init__('Expression')
        self.append(term)
        if addOp_term_list:
            for pair in addOp_term_list:
                self.append(pair[0])
                self.append(pair[1])

    def gen_stype(self):
        return [term.gen_stype() for term in self.childItems]


class TermNode(Node):
    """
    term	::=	factor (mulOp factor)*
    """

    def __init__(self, factor, mulOp_factor_list=None):
        super(TermNode, self).__init__('Term')
        self.append(factor)
        if mulOp_factor_list:
            for pair in mulOp_factor_list:
                self.append(pair[0])
                self.append(pair[1])

    def gen_stype(self):
        return [factor.gen_stype() for factor in self.childItems]


class FactorNode(Node):
    """
    factor	::= <REAL_LITERAL> | <INT_LITERAL> | <ID> ( array )? | <LPAREN> expression <RPAREN>
    """

    def __init__(self, literal=None, expr=None, _id=None, arr=None):
        super(FactorNode, self).__init__('Factor')
        if literal:
            self.append(literal)
        elif expr:
            self.append(expr)
        else:
            self.append(_id)
            if arr:
                self.append(arr)

    def gen_stable(self, stable):
        _id = self.childAt(0)
        if isinstance(_id, IdNode):
            arr = self.childAt(1)
            if arr:
                stable.symbol_invoke(Symbol(_id.name, _id.gen_stype()))

    def gen_stype(self):
        _id = self.childAt(0)
        arr = self.childAt(1)
        if arr:
            return STypeArray(_id.gen_stype(), arr.size)
        else:
            return self.childAt(0).gen_stype()


class CompNode(Node):
    """
    compOp  ::=	<LT> | <GT> | <EQUAL> | <NEQUAL>
    """

    def __init__(self, op):
        super(CompNode, self).__init__('Compare')
        self.append(op)


class AddNode(Node):
    """
    addOp	    ::=	<PLUS> | <MINUS>
    """

    def __init__(self, op):
        super(AddNode, self).__init__('Add')
        self.append(op)


class MulNode(Node):
    """
    mulOp	    ::=	<TIMES> | <DIVIDE>
    """

    def __init__(self, op):
        super(MulNode, self).__init__('Multiply')
        self.append(op)
