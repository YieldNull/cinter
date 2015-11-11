# coding:utf-8
"""
create on '11/9/15 12:54 PM'
"""
__author__ = 'hejunjie'


class Node(object):
    def __init__(self, lexeme, son=None):
        self.lexeme = lexeme
        self.son = son
        self.brother = None

    def __str__(self):
        return self.lexeme


class LeafNode(Node):
    def __init__(self, token):
        super(LeafNode, self).__init__(token.cate)
        self.type = token.type


class IdNode(LeafNode):
    def __init__(self, token, data_type=None):
        super(IdNode, self).__init__(token)
        self.data_type = data_type


class LiteralNode(LeafNode):
    def __init__(self, token):
        super(LiteralNode, self).__init__(token)
        self.data_type = token.type


class NodeTree(object):
    def __init__(self):
        self.root = None

    def append(self, node):
        self.root = node

    def gen(self):
        stack = [(self.root.son, 0)]
        while len(stack) > 0:
            n, dep = stack.pop()
            print ' |' * dep + str(n)
            b = n.brother
            l = []
            while b:
                l.append((b, dep))
                b = b.brother
            l.reverse()
            stack += l
            if n.son:
                stack.append((n.son, dep + 1))


class StmtsNode(Node):
    """
    statements   ::=
    (ifStmt | whileStmt | readStmt | writeStmt | assignStmt | declareStmt)+
    """

    def __init__(self, stmt_list):
        super(StmtsNode, self).__init__('Stmts', stmt_list[0])
        for i in range(len(stmt_list) - 1):
            stmt_list[i].brother = stmt_list[i + 1]


class IfNode(Node):
    """
    ifStmt  ::=
    <IF> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE> ( <ELSE> <LBRACE> statements <RBRACE> )?
    """

    def __init__(self, cond, stmts1, stmts2=None):
        super(IfNode, self).__init__('IfStmt', cond)
        cond.brother = stmts1
        stmts1.brother = stmts2


class WhileNode(Node):
    """
    whileStmt   ::=
    <WHILE> <LPAREN> condition <RPAREN> <LBRACE> statements <RBRACE>
    """

    def __init__(self, cond, stmts):
        super(WhileNode, self).__init__('WhileStmt', cond)
        cond.brother = stmts


class ReadNode(Node):
    """
    readStmt    ::=	<READ> <LPAREN> <ID> <RPAREN> <SEMICOLON>
    """

    def __init__(self, _id):
        super(ReadNode, self).__init__('ReadStmt', _id)


class WriteNode(Node):
    """
    writeStmt   ::=	<WRITE> <LPAREN> expression <RPAREN> <SEMICOLON>
    """

    def __init__(self, expr):
        super(WriteNode, self).__init__('WriteStmt', expr)


class AssignNode(Node):
    """
    assignStmt  ::=	<ID> [array] <ASSIGN> expression <SEMICOLON>
    """

    def __init__(self, _id, expr, arr=None):
        super(AssignNode, self).__init__('AssignStmt', _id)
        _id.brother = arr or expr


class DeclareNode(Node):
    """
    declareStmt ::=	(<INT> | <REAL>) <ID>[array] ( <COMMA> <ID> [array] )* <SEMICOLON>
    """

    def __init__(self, id_arr_list):
        super(DeclareNode, self).__init__('DeclareStmt', id_arr_list[0][0])
        for i in range(len(id_arr_list) - 1):
            if id_arr_list[i][1] is None:
                id_arr_list[i][0].brother = id_arr_list[i + 1][0]
            else:
                id_arr_list[i][0].brother = id_arr_list[i][1]
                id_arr_list[i][1].brother = id_arr_list[i + 1][0]


class ConditionNode(Node):
    """
    condition	::=	expression compOp expression
    """

    def __init__(self, expr1, compOp, expr2):
        super(ConditionNode, self).__init__('Condition', expr1)
        expr1.brother = compOp
        compOp.brother = expr2


class ExprNode(Node):
    """
    expression  ::=	term (addOp term)*
    """

    def __init__(self, term, addOp_term_list):
        super(ExprNode, self).__init__('Expression', term)
        if addOp_term_list:
            term.brother = addOp_term_list[0][0]
            for addOp_term in addOp_term_list:
                addOp_term[0].brother = addOp_term[1]
            for i in range(len(addOp_term_list) - 1):
                addOp_term_list[i][1].brother = addOp_term_list[i + 1][0]


class TermNode(Node):
    """
    term	::=	factor (mulOp factor)*
    """

    def __init__(self, factor, mulOp_factor_list):
        super(TermNode, self).__init__('Term', factor)
        if mulOp_factor_list:
            factor.brother = mulOp_factor_list[0][0]
            for addOp_term in mulOp_factor_list:
                addOp_term[0].brother = addOp_term[1]
            for i in range(len(mulOp_factor_list) - 1):
                mulOp_factor_list[i][1].brother = mulOp_factor_list[i + 1][0]


class FactorNode(Node):
    """
    factor	::=
    <REAL_LITERAL> | <INT_LITERAL> | <ID> | <LPAREN> expression <RPAREN> | <ID> array
    """

    def __init__(self, literal=None, expr=None, _id=None, arr=None):
        super(FactorNode, self).__init__('Factor', literal or expr or _id)
        if _id and arr:
            _id.brother = arr


class ArrayNode(Node):
    """
    array 	::=	<LBRACKET> ( <INT_LITERAL> | <ID> ) <RBRACKET>
    """

    def __init__(self, id=None, literal=None):
        super(ArrayNode, self).__init__('Array', id or literal)


class CompNode(Node):
    """
    compOp  ::=	<LT> | <GT> | <EQUAL> | <NEQUAL>
    """

    def __init__(self, op):
        super(CompNode, self).__init__('Compare', op)


class AddNode(Node):
    """
    addOp	    ::=	<PLUS> | <MINUS>
    """

    def __init__(self, op):
        super(AddNode, self).__init__('Add', op)


class MulNode(Node):
    """
    mulOp	    ::=	<TIMES> | <DIVIDE>
    """

    def __init__(self, op):
        super(MulNode, self).__init__('Multiply', op)
