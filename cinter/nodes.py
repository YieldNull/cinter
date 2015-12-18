# coding:utf-8
"""
Nodes of abstract grammar tree.

create on '11/9/15 12:54 PM'
"""
import StringIO

from cinter import tokens

__author__ = 'hejunjie'


class Node(object):
    """
    Basic node which is also used in QAbstractItemModel.
    """

    def __init__(self, lexeme, parent=None):
        self.lexeme = lexeme
        self.parent = parent
        self.childItems = []

    def __str__(self):
        return self.lexeme

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
        return self.childItems[row]

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

    def gen(self):
        """
        Print tree with itself as the root node.
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

    def __init__(self, t):
        super(LeafNode, self).__init__(t.cate)

        self.type = t.type
        self.token = t

    def __str__(self):
        return '%s : "%s"' % (self.token.cate, self.token.lexeme)


class LiteralNode(LeafNode):
    """
    A real or integer literal node.
    """

    def __init__(self, t):
        super(LiteralNode, self).__init__(t)
        self.type = t.type


class IdNode(LeafNode):
    """
    An Id node which needs to record the **type** of it.

    Type means 'int','real', 'array' or 'function name'?
    """

    def __init__(self, _id, _type=None):
        assert isinstance(_id, tokens.Token)
        assert _type is None or isinstance(_type, tokens.Token)
        super(IdNode, self).__init__(_id)
        self.type = _type.type


class VoidParamNode(Node):
    """
    Void function call param or declare param
    """

    def __init__(self):
        super(VoidParamNode, self).__init__('Void')


class EmptyBodyNode(Node):
    """
    Empty innerStmts body.
    """

    def __int__(self):
        super(EmptyBodyNode, self).__init__('EmptyBody')


#####################################################
#################### grammar nodes ##################
#####################################################

class ExterStmtsNode(Node):
    """
    exterStmts  ::= ( declareStmt | funcDeclStmt )*
    """

    def __init__(self, stmt_list):
        super(ExterStmtsNode, self).__init__('ExterStmts')
        for stmt in stmt_list:
            self.append(stmt)


class InnerStmtsNode(Node):
    """
    innerStmts   ::=
    ( declareStmt | assignStmt | ifStmt | whileStmt | funcCallStmt | returnStmt )*
    """

    def __init__(self, stmt_list):
        super(InnerStmtsNode, self).__init__('InnerStmts')
        if len(stmt_list) > 0:
            for stmt in stmt_list:
                self.append(stmt)
        else:
            self.append(EmptyBodyNode())


class FuncDeclStmtNode(Node):
    """
    funcDeclStmt ::= ( <INT> | <REAL> | <VOID>) [ array ] <ID>
                <LPAREN> ( funcDeclParamList )?  <RPAREN> <LBRACE> innerStmts <LBRACE>
    """

    def __init__(self, _id, params, innerStmts, arr=None):
        super(FuncDeclStmtNode, self).__init__('FuncDeclStmt')
        self.append(_id)
        if arr:
            self.append(arr)
        if params is None:
            params = VoidParamNode()
        self.append(params)
        self.append(innerStmts)


class FuncCallStmtNode(Node):
    """
    funcCallStmt    ::= <ID> <LPAREN> funcCallParams  <RPAREN> <SEMICOLON>
    """

    def __init__(self, _id, param):
        super(FuncCallStmtNode, self).__init__('FuncCallStmt')
        self.append(_id)
        if param is None:
            param = VoidParamNode()
        self.append(param)


class FuncDeclParam(Node):
    """
    funcDeclParam   ::= ( <INT> | <REAL> | <VOID>) <ID>[array]
    """

    def __init__(self, _id, arr=None):
        super(FuncDeclParam, self).__init__('FuncDeclParam')
        assert isinstance(_id, IdNode)
        self.append(_id)
        if arr:
            self.append(arr)


class FuncDeclParamList(Node):
    """
    funcDeclParamList  ::= ( funcDeclParam ( <COMMA> funcDeclParam )* )?
    """

    def __init__(self, decl_param_list):
        super(FuncDeclParamList, self).__init__('FuncDeclParams')
        if not decl_param_list:
            self.append(VoidParamNode)
        else:
            for param in decl_param_list:
                self.append(param)


class FuncCallParamList(Node):
    """
    funcCallParams  ::= <ID>  ( <COMMA> <ID> )*
    """

    def __init__(self, id_list):
        super(FuncCallParamList, self).__init__('FuncCallParamList')
        for _id in id_list:
            assert isinstance(_id, IdNode)
            self.append(_id)


class ReturnStmtNode(Node):
    """
    returnStmt      ::= <RETURN> expression <SEMICOLON>
    """

    def __init__(self, expr):
        super(ReturnStmtNode, self).__init__('ReturnStmt')
        self.append(expr)


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
    assignStmt  ::=	<ID> [array] <ASSIGN> expression <SEMICOLON>
    """

    def __init__(self, _id, expr, arr=None):
        super(AssignStmtNode, self).__init__('AssignStmt')
        _id.brother = arr or expr
        self.append(_id)
        if arr:
            self.append(arr)
        self.append(expr)


class DeclareStmtNode(Node):
    """
    declareStmt ::=	(<INT> | <REAL>) <ID>[array] ( <COMMA> <ID> [array] )* <SEMICOLON>
    """

    def __init__(self, id_arr_list):
        super(DeclareStmtNode, self).__init__('DeclareStmt')
        for pair in id_arr_list:
            self.append(pair[0])
            if pair[1]:
                self.append(pair[1])


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


class FactorNode(Node):
    """
    factor	::=
    <REAL_LITERAL> | <INT_LITERAL> | <ID> | <LPAREN> expression <RPAREN> | <ID> array
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


class ArrayNode(Node):
    """
    array 	::=	<LBRACKET> ( <INT_LITERAL> | <ID> ) <RBRACKET>
    """

    def __init__(self, _id=None, literal=None):
        super(ArrayNode, self).__init__('Array')
        self.append(_id or literal)


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
