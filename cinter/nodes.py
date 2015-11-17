# coding:utf-8
"""
create on '11/9/15 12:54 PM'
"""
import StringIO
import copy
from cinter import tokens

__author__ = 'hejunjie'


class Node(object):
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
        # try:
        #     self.childItems.index(item)
        # except ValueError:
        #     pass
        # else:
        item = copy.deepcopy(item)  # TreeView item should be different
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


class LeafNode(Node):
    def __init__(self, token):
        super(LeafNode, self).__init__(token.cate)
        self.type = token.type
        self.token = token

    def __str__(self):
        return '%s : "%s"' % (self.token.cate, self.token.lexeme)


class IdNode(LeafNode):
    def __init__(self, token, data_type=None):
        super(IdNode, self).__init__(token)
        self.data_type = data_type


class LiteralNode(LeafNode):
    def __init__(self, token):
        super(LiteralNode, self).__init__(token)
        self.data_type = token.type


class StmtsNode(Node):
    """
    statements   ::=
    (ifStmt | whileStmt | readStmt | writeStmt | assignStmt | declareStmt)+
    """

    def __init__(self, stmt_list):
        super(StmtsNode, self).__init__('Stmts')
        for stmt in stmt_list:
            self.append(stmt)


class IfStmtNode(Node):
    """
    ifStmt  ::=
    <IF> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE> ( <ELSE> <LBRACE> statements <RBRACE> )?
    """

    def __init__(self, cond, stmts1, stmts2=None):
        super(IfStmtNode, self).__init__('IfStmt')
        self.append(Node_IF)
        self.append(Node_LPAREN)
        self.append(cond)
        self.append(Node_RPAREN)
        self.append(Node_LBRACE)
        self.append(stmts1)
        self.append(Node_RBRACE)
        if stmts2:
            self.append(Node_ELSE)
            self.append(Node_LBRACE)
            self.append(stmts2)
            self.append(Node_RBRACE)


class WhileStmtNode(Node):
    """
    whileStmt   ::=
    <WHILE> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE>
    """

    def __init__(self, cond, stmts):
        super(WhileStmtNode, self).__init__('WhileStmt')
        self.append(Node_WHILE)
        self.append(Node_LPAREN)
        self.append(cond)
        self.append(Node_RPAREN)
        self.append(Node_LBRACE)
        self.append(stmts)
        self.append(Node_RBRACE)


class ReadStmtNode(Node):
    """
    readStmt    ::=	<READ> <LPAREN> <ID> <RPAREN> <SEMICOLON>
    """

    def __init__(self, _id):
        super(ReadStmtNode, self).__init__('ReadStmt')
        self.append(Node_READ)
        self.append(Node_LPAREN)
        self.append(_id)
        self.append(Node_RPAREN)
        self.append(Node_SEMICOLON)


class WriteStmtNode(Node):
    """
    writeStmt   ::=	<WRITE> <LPAREN> expression <RPAREN> <SEMICOLON>
    """

    def __init__(self, expr):
        super(WriteStmtNode, self).__init__('WriteStmt')
        self.append(Node_WRITE)
        self.append(Node_LPAREN)
        self.append(expr)
        self.append(Node_RPAREN)
        self.append(Node_SEMICOLON)


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
        self.append(Node_ASSIGN)
        self.append(expr)
        self.append(Node_SEMICOLON)


class DeclareStmtNode(Node):
    """
    declareStmt ::=	(<INT> | <REAL>) <ID>[array] ( <COMMA> <ID> [array] )* <SEMICOLON>
    """

    def __init__(self, literal, id_arr_list):
        super(DeclareStmtNode, self).__init__('DeclareStmt')
        self.append(literal)
        for pair in id_arr_list:
            self.append(pair[0])
            if pair[1]:
                self.append(pair[1])
            self.append(Node_COMMA)
        self.pop()
        self.append(Node_SEMICOLON)


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
            self.append(Node_LPAREN)
            self.append(expr)
            self.append(Node_RPAREN)
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
        self.append(Node_LBRACKET)
        self.append(_id or literal)
        self.append(Node_RBRACKET)


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


# pass these nodes when appending to whose parent,
# and deepcopy them in the function Node.append()
Node_IF = LeafNode(tokens.Token_IF)
Node_ELSE = LeafNode(tokens.Token_ELSE)
Node_WHILE = LeafNode(tokens.Token_WHILE)
Node_READ = LeafNode(tokens.Token_READ)
Node_WRITE = LeafNode(tokens.Token_WRITE)
Node_INT = LeafNode(tokens.Token_INT)
Node_REAL = LeafNode(tokens.Token_REAL)
Node_PLUS = LeafNode(tokens.Token_PLUS)
Node_MINUS = LeafNode(tokens.Token_MINUS)
Node_TIMES = LeafNode(tokens.Token_TIMES)
Node_DIVIDE = LeafNode(tokens.Token_DIVIDE)
Node_ASSIGN = LeafNode(tokens.Token_ASSIGN)
Node_GT = LeafNode(tokens.Token_GT)
Node_LT = LeafNode(tokens.Token_LT)
Node_NEQUAL = LeafNode(tokens.Token_NEQUAL)
Node_EQUAL = LeafNode(tokens.Token_EQUAL)
Node_LPAREN = LeafNode(tokens.Token_LPAREN)
Node_RPAREN = LeafNode(tokens.Token_RPAREN)
Node_LBRACE = LeafNode(tokens.Token_LBRACE)
Node_RBRACE = LeafNode(tokens.Token_RBRACE)
Node_LBRACKET = LeafNode(tokens.Token_LBRACKET)
Node_RBRACKET = LeafNode(tokens.Token_RBRACKET)
Node_COMMA = LeafNode(tokens.Token_COMMA)
Node_SEMICOLON = LeafNode(tokens.Token_SEMICOLON)
