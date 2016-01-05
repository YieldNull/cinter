# coding:utf-8
"""
Nodes of abstract grammar tree.

create on '11/9/15 12:54 PM'
"""
import StringIO
import tokens
from stable import Symbol, STypeFunc, STable, SType, STypeArray, SUnknown, IndexMissingError
from inter import Code

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
        """
        The node after itself in parent children nodes
        :return:
        """
        index = self.indexInParent()
        return self.childAt(index + 1)

    def gen_tree(self):
        """
        Print tree with itself as the root node using DFS.
        """
        stack = [self]
        stdout = StringIO.StringIO()
        while len(stack) > 0:
            node = stack.pop()
            parent = node.parent
            indent = []  # output indent
            while parent:
                if parent.parent and parent.indexInParent() < parent.parent.childCount() - 1:
                    indent.append('|     ')
                else:
                    indent.append('      ')
                parent = parent.parent

            indent.reverse()  # reserve children list in order to search from left to right
            stdout.write(''.join(indent))
            stdout.write('|----> %s\n' % str(node))
            chilrenl = list(node.childItems)
            chilrenl.reverse()
            stack += chilrenl
        value = stdout.getvalue()
        return value

    def gen_location(self):
        """
        For error promoting
        :return:
        """
        # TODO print the whole line instead of one token
        return 'near row:%d column:%d   "%s"'

    def gen_stable(self, stable):
        """
        Append a new variable to symbol table or add a new table
        For generator symbol table and semantics analysing
        :param stable:
        :return:
        """
        assert isinstance(stable, STable)
        return None

    def gen_stype(self):
        """
        Generate the symbol type in symbol table.
        For semantics analysing.

        :return: **must return a list**
        """
        return []

    def gen_code(self):
        """
        Generate  Intermediate Code
        :return: **must return a list**
        """
        return []


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

    def gen_code(self):
        return self.token.lexeme

    def gen_location(self):
        return self.token.get_location()


class LiteralNode(LeafNode):
    """
    A real or integer literal node.
    """

    def __init__(self, token):
        assert isinstance(token, tokens.IntLiteral) or isinstance(token, tokens.RealLiteral)
        super(LiteralNode, self).__init__(token)

    def gen_stype(self):
        if isinstance(self.token, tokens.IntLiteral):
            return SType(tokens.Token_INT)
        else:
            return SType(tokens.Token_REAL)

    def gen_code(self):
        if self.token == tokens.Token_IntLiteral:
            return int(self.token.lexeme)
        else:
            return float(self.token.lexeme)


class DataTypeNode(LeafNode):
    """
    dataType    ::=( <INT> | <REAL> )
    """

    def __init__(self, token):
        super(DataTypeNode, self).__init__(token)
        assert token in [tokens.Token_INT, tokens.Token_REAL]

    def gen_stype(self):
        return SType(self.token)


class ArrayNode(Node):
    """
    array   ::=	<LBRACKET> ( <INT_LITERAL> | <ID> )? <RBRACKET>
    """

    def __init__(self, _id=None, literal=None):
        """
        literal or id is required, unless it's in func return type or func def param type.
        """
        super(ArrayNode, self).__init__('Array')
        assert not (_id and literal)

        self.size = None
        if _id:
            assert isinstance(_id, IdNode)
            self.append(_id)
            self.size = _id  # size can be calculated from the _id node
        if literal:
            assert isinstance(literal, LiteralNode)
            self.append(literal)
            self.size = int(literal.token.lexeme)

    def gen_code(self):
        if isinstance(self.size, int):
            return self.size
        else:
            return self.size.name


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

    def gen_stype(self):
        return self.stype

    def gen_symbol(self):
        return Symbol(self.name, self.gen_stype())


class FuncId(LeafNode):
    def __init__(self, rtype, _id, params):
        assert isinstance(rtype, ReturnTypeNode)
        assert isinstance(_id, IdNode)
        super(FuncId, self).__init__(_id.token)

        self.rtype = rtype
        self.name = _id.name
        self.params = params

    def gen_stype(self):
        return STypeFunc(self.rtype.gen_stype(), self.params.gen_stype())

    def gen_symbol(self):
        return Symbol(self.name, self.gen_stype())


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

    def gen_code(self):
        codes = []
        for stmt in self.childItems:
            codes += stmt.gen_code()
        return codes


class FuncDefStmtNode(Node):
    """
    funcDefStmt ::= returnType  <ID>  <LPAREN> ( funcDefParamList )?  <RPAREN> <LBRACE> innerStmts <RBRACE>
    """

    def __init__(self, rtype, _id, params, innerStmts):
        super(FuncDefStmtNode, self).__init__('FuncDefStmt')
        assert params is not None

        # set func_id type
        self.id = _id
        self.name = _id.name
        self.funcId = FuncId(rtype, _id, params)
        self.append(rtype)
        self.append(self.funcId)
        self.append(params)
        self.append(innerStmts)

    def gen_location(self):
        row, column = self.id.gen_location()
        return super(FuncDefStmtNode, self).gen_location() % (row, column, self.id.name)

    def gen_stable(self, stable):
        stable.symbol_append(self.funcId.gen_symbol())

    def def_param(self, stable):
        """
        invoke by innerstmt to declare params in innerstmt scope
        :param stable:
        :return:
        """
        for param in self.childAt(2).childItems:
            stable.symbol_append(Symbol(param.name, param.stype), check=False)

    def gen_code(self):
        codes = [Code(op='f=', arg1=Code.line + 3, tar='%s' % self.name), Code(op='j')]
        codes += self.childAt(2).gen_code()
        codes += self.childAt(3).gen_code()
        codes[1].tar = codes[len(codes) - 1].line + 1  # jump over function definition
        return codes


class ReturnTypeNode(Node):
    """
    returnType ::= <VOID>  | dataType
    """

    def __init__(self, data_type):
        """
        :param data_type: if VOID, datatype is None
        :return:
        """
        super(ReturnTypeNode, self).__init__('ReturnType')
        self.data_type = data_type

        if data_type:
            assert isinstance(data_type, DataTypeNode)

            self.stype = data_type.gen_stype()
            self.append(data_type)
        else:
            self.stype = SType(tokens.Token_VOID)

    def gen_stype(self):
        return self.stype

    def __str__(self):
        if not self.data_type:
            return 'ReturnType: VOID'
        else:
            return super(ReturnTypeNode, self).__str__()


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
        self.data_type = self.stype.type
        self.name = _id.name

    def gen_stype(self):
        return self.stype


class FuncDefParamList(Node):
    """
    funcDefParamList  ::= ( funcDefParam ( <COMMA> funcDefParam )* | <VOID> )
    """

    def __init__(self, params):
        """
        :param params: if param is void, `params` is None
        :return:
        """
        super(FuncDefParamList, self).__init__('FuncDefParams')
        self.params = params
        if params:
            for param in params:
                assert isinstance(param, FuncDefParam)
                self.append(param)

    def __str__(self):
        if not self.params:
            return 'FuncDefParams: VOID'
        else:
            return super(FuncDefParamList, self).__str__()

    def gen_stype(self):
        """
        Gen param stype list
        """
        if self.childCount() == 0:
            return []
        else:
            return [param.gen_stype() for param in self.childItems]

    def gen_code(self):
        if self.params:
            # def and assign
            codes = [Code(op='=', arg1='_i' if self.params[i].data_type == tokens.Token_INT else '_f',
                          tar='%s' % self.params[i].name)
                     for i in range(len(self.params))]
            codes += [Code(op='=p', arg1='_p%d' % i, tar='%s' % self.params[i].name)
                      for i in range(len(self.params))]
            return codes
        else:
            return []


class FuncCallExprNode(Node):
    """
    funcCallExpr    ::= <ID> <LPAREN> ( funcCallParamList )?  <RPAREN>
    """

    def __init__(self, _id, params):
        super(FuncCallExprNode, self).__init__('FuncCallExpr')

        self.append(_id)
        self.id = _id
        self.name = _id.name
        if params:
            self.append(params)
            self.params = params
        else:
            self.params = None

    def gen_location(self):
        row, column = self.id.gen_location()
        return super(FuncCallExprNode, self).gen_location() % (row, column, self.id.name)

    def gen_stype(self):
        return [SUnknown(self.name, is_func=True)]

    def gen_stable(self, stable):
        stable.invoke_func(self.name, self.params.gen_stype() if self.params else [])

    def gen_code(self):
        codes = self.params.gen_code() if self.params else []
        codes += [Code(op='=', arg1=Code.line + 3, tar='_ra')]
        codes.append(Code(op='c', tar='%s' % self.name))
        codes.append(Code(op='=', arg1='_rv', tar=Code.gen_temp()))
        return codes


class FuncCallStmtNode(Node):
    """
    funcCallStmt    ::= funcCallExpr  <SEMICOLON>
    """

    def __init__(self, funcCallExpr):
        super(FuncCallStmtNode, self).__init__('FuncCallStmt')
        self.append(funcCallExpr)
        self.funcCall = funcCallExpr

    def gen_code(self):
        return self.funcCall.gen_code()


class FuncCallParamList(Node):
    """
    funcCallParamList  ::= ( expr   ( <COMMA> expr  )* | <VOID> )
    """

    def __init__(self, params):
        """
        :param params: if VOID, params is None
        :return:
        """
        super(FuncCallParamList, self).__init__('FuncCallParamList')
        if params:
            for param in params:
                assert isinstance(param, ExprNode)
                self.append(param)

    def gen_stype(self):
        return [expr.gen_stype() for expr in self.childItems]

    def gen_code(self):
        codes = []
        for i in range(self.childCount()):
            p = self.childAt(i).gen_code()
            codes += p
            codes.append(Code(op='p=', arg1=p[len(p) - 1].tar, tar='_p%d' % i))
        return codes


class ReturnStmtNode(Node):
    """
    returnStmt      ::= <RETURN> (expression)? <SEMICOLON>
    """

    def __init__(self, returnNode, expr=None):
        super(ReturnStmtNode, self).__init__('ReturnStmt')
        self.returnNode = returnNode  # in order to gen location
        if expr:
            self.append(expr)

    def gen_location(self):
        row, column = self.returnNode.get_location()
        return super(ReturnStmtNode, self).gen_location() % (row, column, 'return')

    def gen_stable(self, stable):
        stable.invoke_return(self.childAt(0).gen_stype() if self.childCount() > 0 else None)

    def gen_code(self):
        if self.childCount() > 0:
            codes = self.childAt(0).gen_code()
            codes.append(Code(op='=', arg1=codes[len(codes) - 1].tar, tar='_rv'))
            codes.append(Code('r'))  # Code('r', tar='_ra')
        else:
            codes = [Code(op='=', arg1='00', tar='_rv'), Code('r')]  # Code('r', tar='_ra')
        return codes


class DeclareStmtNode(Node):
    """
    declareStmt ::= dataType (array)? <ID>  ( <COMMA> <ID> )* ( <ASSIGN> ( expression | arrayInit ) )?<SEMICOLON>
    """

    def __init__(self, data_type, id_list, arr=None, expr_or_init=None):
        """
        In parser **must check**:
            1. dataType compare with arrayInit type
            2. array.size must be a literal
            3. single ID cannot be assigned with arrayInit, array cannot be assigned with expr
            4. literals in arrayInit must be of the same type
            5. init list cannot be larger than array size
        """
        super(DeclareStmtNode, self).__init__('DeclareStmt')
        assert isinstance(data_type, DataTypeNode)

        self.id_list = id_list
        self.assign = expr_or_init

        stype = data_type.gen_stype()
        if arr:
            if arr.size is None:
                raise IndexMissingError()
            self.stype = STypeArray(stype.type, arr.size)
        else:
            self.stype = stype

        # append to tree
        self.append(data_type)
        if arr:
            self.append(arr)
        for _id in id_list:
            assert isinstance(_id, IdNode)
            self.append(_id)
            _id.set_stype(self.stype)  # set id type

        if expr_or_init:
            self.append(expr_or_init)

    def gen_location(self):
        row, column = self.id_list[0].gen_location()
        return super(DeclareStmtNode, self).gen_location() % (row, column, self.id_list[0].name)

    def gen_stable(self, stable):
        """
        if arrayInit, type has been checked in parser.
        so wo just have to check <ID>* = expression,
        in other word, just compare dataType'stype with expression'stype
        """
        for _id in self.id_list:
            stable.symbol_append(_id.gen_symbol())

        if self.assign:
            stable.invoke_compare([self.stype], self.assign.gen_stype())

    def gen_code(self):
        data_type = '_i' if self.stype.type == tokens.Token_INT else '_f'
        # pure declare
        arg1 = data_type
        arg2 = ''
        if isinstance(self.stype, STypeArray):
            arg1 = '%s[]' % arg1
            arg2 = self.stype.size
        codes = [Code(op='=', arg1=arg1, arg2=arg2, tar=_id.gen_code()) for _id in self.id_list]

        if self.assign:  # decalre and assign
            if isinstance(self.stype, STypeArray):  # array init
                literals = self.assign.literals
                size = self.stype.size
                for _id in self.id_list:
                    codes.append(Code(op='=', arg1='%s[]' % data_type, arg2=size, tar=_id.gen_code()))
                    for i in range(len(literals)):
                        codes.append(Code(op='[]=', arg1=i, arg2=literals[i].gen_code(), tar=_id.gen_code()))
            else:
                codes += self.assign.gen_code()  # inited with expr
                arg1 = codes[len(codes) - 1].tar
                codes += [Code(op='=', arg1=arg1, tar=_id.gen_code()) for _id in self.id_list]
        return codes


class ArrayInitNode(Node):
    """
    arrayInit   ::= <LBRACE>( INT_LITERAL (<COMMA> INT_LITERAL)* | REAL_LITERAL(<COMMA> REAL_LITERAL)* ) <RBRACE>
    """

    def __init__(self, literal_list):
        """
        int literal or real literal list.
        ** must be the same type**
        :param literal_list:
        :return:
        """
        super(ArrayInitNode, self).__init__('ArrayInitNode')
        assert len(literal_list) > 0

        self.literals = literal_list
        self.size = len(literal_list)

        for literal in literal_list:
            self.append(literal)

    def gen_stype(self):
        return self.literals[0].gen_stype()


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
        if isinstance(self.parent, FuncDefStmtNode):  # add function param list to stable
            self.parent.def_param(table)
        return table

    def gen_code(self):
        codes = []
        for stmt in self.childItems:
            c = stmt.gen_code()
            codes += c
        return codes


class IfStmtNode(Node):
    """
    ifStmt  ::= <IF> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE>
                ( <ELSE> <LBRACE> innerStmts <RBRACE> )?
    """

    def __init__(self, cond, stmts1, stmts2=None):
        super(IfStmtNode, self).__init__('IfStmt')
        self.append(cond)
        self.append(stmts1)
        if stmts2:
            self.append(stmts2)

    def gen_code(self):
        cond = self.childAt(0).gen_code()
        stmt1 = self.childAt(1).gen_code()
        stmt2 = self.childAt(2)
        if stmt2:  # backfill the jump address
            stmt2 = stmt2.gen_code()
            cond[len(cond) - 1].tar = stmt2[0].line
        else:
            stmt2 = []
            if len(stmt1) > 0:
                cond[len(cond) - 1].tar = stmt1[len(stmt1) - 1].line + 1
            else:
                cond[len(cond) - 1].tar = cond[len(cond) - 1].line + 1
        return cond + stmt1 + stmt2


class WhileStmtNode(Node):
    """
    whileStmt   ::=
    <WHILE> <LPAREN> condition <RPAREN> <LBRACE> innerStmts <RBRACE>
    """

    def __init__(self, cond, stmts):
        super(WhileStmtNode, self).__init__('WhileStmt')
        self.append(cond)
        self.append(stmts)

    def gen_code(self):
        cond = self.childAt(0).gen_code()
        stmts = self.childAt(1).gen_code()
        cond[len(cond) - 1].tar = stmts[len(stmts) - 1].line + 2  # backfill the jump address
        return cond + stmts + [Code(op='j', tar=cond[0].line)]  # go back to cond


class AssignStmtNode(Node):
    """
    assignStmt  ::= <ID> (array)? <ASSIGN> expression <SEMICOLON>
    """

    def __init__(self, _id, expr, arr=None):
        super(AssignStmtNode, self).__init__('AssignStmt')
        self.name = _id.name
        self.id = _id
        self.arr = arr
        self.expr = expr

        _id.brother = arr or expr
        self.append(_id)
        if arr:
            self.append(arr)
        self.append(expr)

    def gen_location(self):
        row, column = self.id.gen_location()
        return super(AssignStmtNode, self).gen_location() % (row, column, self.id.name)

    def gen_stable(self, stable):
        if self.arr and (self.arr.size is None):
            raise IndexMissingError()
        stable.invoke_assign(self.name, self.expr.gen_stype(), is_arr=True if self.arr else False)

    def gen_code(self):
        codes = self.expr.gen_code()
        arg = codes[len(codes) - 1].tar
        if self.arr:
            code = Code(op='[]=', arg1=self.arr.gen_code(), arg2=arg, tar=self.name)
        else:
            code = Code(op='=', arg1=arg, tar=self.name)
        codes.append(code)
        return codes


class ConditionNode(Node):
    """
    condition	::=	expression compOp expression
    """

    def __init__(self, expr1, compOp, expr2):
        super(ConditionNode, self).__init__('Condition')
        self.append(expr1)
        self.append(compOp)
        self.append(expr2)

    def gen_location(self):
        row, column = self.childAt(1).gen_location()
        return super(ConditionNode, self).gen_location() % (row, column, self.childAt(1).name)

    def gen_stable(self, stable):
        stable.invoke_compare(self.childAt(0).gen_stype(), self.childAt(2).gen_stype())

    def gen_code(self):
        codes = []
        arg1 = self.childAt(0).gen_code()
        op = self.childAt(1).gen_code()
        arg2 = self.childAt(2).gen_code()

        codes += arg1
        codes += arg2
        link = Code(op=op, arg1=arg1[len(arg1) - 1].tar,
                    arg2=arg2[len(arg2) - 1].tar, tar=-1)  # unknown jump target, so set -1
        codes.append(link)
        return codes


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
        stypes = []
        for i in range(0, self.childCount(), 2):
            stypes += self.childAt(i).gen_stype()
        return stypes

    def gen_code(self):
        codes = self.childAt(0).gen_code()
        for i in range(1, self.childCount() - 1, 2):
            op = self.childAt(i).gen_code()
            arg2 = self.childAt(i + 1).gen_code()

            arg1 = codes[len(codes) - 1].tar
            codes += arg2
            codes.append(Code(op=op, arg1=arg1, arg2=arg2[len(arg2) - 1].tar, tar=Code.gen_temp()))
        return codes


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
        stypes = []
        for i in range(0, self.childCount(), 2):
            stypes += self.childAt(i).gen_stype()
        return stypes

    def gen_code(self):
        codes = self.childAt(0).gen_code()
        for i in range(1, self.childCount() - 1, 2):
            op = self.childAt(i).gen_code()
            arg2 = self.childAt(i + 1).gen_code()

            arg1 = codes[len(codes) - 1].tar
            codes += arg2
            codes.append(Code(op=op, arg1=arg1, arg2=arg2[len(arg2) - 1].tar, tar=Code.gen_temp()))
        return codes


class FactorNode(Node):
    """
    factor	::= <REAL_LITERAL> | <INT_LITERAL> | <ID> ( array )?
                | funcCallExpr  | <LPAREN> expression <RPAREN>
    """

    def __init__(self, literal=None, expr=None, _id=None, arr=None, funcCall=None):
        super(FactorNode, self).__init__('Factor')
        if literal:
            self.append(literal)
        elif expr:
            self.append(expr)
        elif funcCall:
            self.append(funcCall)
        else:
            self.append(_id)
            if arr:
                self.append(arr)

    def gen_stype(self):
        """
        :return: a stype list
        """
        child = self.childAt(0)
        if isinstance(child, IdNode):
            arr = self.childAt(1)
            if arr:
                if arr.size is None:  # if arr, its size must exists
                    raise IndexMissingError()
                return [SUnknown(child.name, True)]
            else:
                return [SUnknown(child.name, False)]
        elif isinstance(child, LiteralNode):
            return [child.gen_stype()]
        else:
            return child.gen_stype()  # expr or funcCall

    def gen_code(self):
        """
        list of codes or variable name or single literal
        :return:
        """
        child = self.childAt(0)
        if isinstance(child, IdNode):
            arr = self.childAt(1)
            if arr:
                return [Code(op='=[]', arg1=child.gen_code(), arg2=arr.gen_code(), tar=Code.gen_temp())]
            else:
                return [Code(op='=', arg1=child.gen_code(), tar=Code.gen_temp())]
        elif isinstance(child, LiteralNode):
            return [Code(op='=', arg1=child.gen_code(), tar=Code.gen_temp())]
        else:
            return child.gen_code()


class CompNode(Node):
    """
    compOp  ::=	<LT> | <GT> | <EQUAL> | <NEQUAL>
    """

    def __init__(self, op):
        super(CompNode, self).__init__('Compare')
        self.append(op)
        self.name = op.token.lexeme

    def gen_code(self):
        return 'j' + self.childAt(0).gen_code()

    def gen_location(self):
        return self.childAt(0).token.get_location()


class AddNode(Node):
    """
    addOp	    ::=	<PLUS> | <MINUS>
    """

    def __init__(self, op):
        super(AddNode, self).__init__('Add')
        self.append(op)

    def gen_code(self):
        return self.childAt(0).gen_code()


class MulNode(Node):
    """
    mulOp	    ::=	<TIMES> | <DIVIDE>
    """

    def __init__(self, op):
        super(MulNode, self).__init__('Multiply')
        self.append(op)

    def gen_code(self):
        return self.childAt(0).gen_code()
