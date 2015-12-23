# coding:utf-8

"""
Symbol table.
"""
import tokens


class RedefinedError(Exception):
    pass


class SymbolNotDefinedError(Exception):
    pass


class SType(object):
    """
    Basic Symbol Type
    """

    def __init__(self, token):
        """
        :param token:  Token_INT or Token_REAL
        """
        assert token in [tokens.Token_REAL, tokens.Token_INT, tokens.Token_VOID]
        self.type = token


class STypeArray(SType):
    """
    Array type
    """

    def __init__(self, token, size):
        super(STypeArray, self).__init__(token)
        self.size = size


class STypeFunc(object):
    """
    Function type
    """

    def __init__(self, stype, param_stypes):
        # assert isinstance(params, FuncDefParamList)

        if stype:
            assert isinstance(stype, SType)
            self.stype = stype  # basic type or array type
        else:
            self.stype = None  # void


class Symbol(object):
    """
    Symbol Object
    """

    def __init__(self, name, stype):
        assert isinstance(name, basestring)
        assert isinstance(stype, SType)

        self.name = name
        self.type = stype
        self.table = None


class STable(object):
    """
    Manage Symbol Tables
    """

    def __init__(self):
        self.parent = None  # parent table
        self.children = []  # children tables
        self.symbols = []  # symbols in the table
        self.tsindex = -1  # The Symbol index in parent after which the table was appended

    def table_append(self, child):
        """
        Append child table
        """
        assert isinstance(child, STable)
        child.parent = self
        self.children.append(child)
        child.tsindex = len(self.symbols) - 1

    def table_index_in_parent(self):
        """
        Table index in parent table.
        """
        if self.parent:
            return self.parent.tchildren.index(self)
        else:
            return -1

    def table_brother(self):
        """
        Brother table in parent.
        """
        index = self.table_index_in_parent()
        if index >= 0:
            return self.parent.table_child_at(index + 1)
        else:
            return None

    def table_child_count(self):
        """
        Child table count.
        """
        return len(self.children)

    def table_child_at(self, index):
        """
        Child table at index
        :param index:
        :return:
        """
        try:
            c = self.children[index]
        except IndexError:
            return None
        else:
            return c

    def symbol_append(self, symbol):
        """
        Append table object
        """
        if self.symbol_has_defined(symbol):
            raise RedefinedError()
        else:
            self.symbols.append(symbol)
            symbol.table = self

    def symbol_at_index(self, index):
        try:
            symbol = self.symbols[index]
        except IndexError:
            return None
        else:
            return symbol

    def symbol_index(self, symbol):
        assert isinstance(symbol, Symbol)
        return self.symbols.index(symbol)

    @staticmethod
    def symbol_equal(symbol1, symbol2):
        assert isinstance(symbol1, Symbol)
        assert isinstance(symbol2, Symbol)

        if symbol1.name == symbol2.name:
            # TODO check type
            pass
        else:
            return False

    def symbol_same_name(self, name):
        pass

    def symbol_has_defined(self, symbol, ends=None):
        """
        check whether symbol has been defined or not.

        :param symbol: the Symbol object
        :param ends: searching in [0,ends] in the symbol list of current table.
                    Used when searching in parent table whose value is `tsindex`
        """
        if not ends:
            ends = len(self.symbols) - 1

        for i in range(ends + 1):  # check self
            if self.symbol_equal(self.parent.symbol_at_index(i), symbol):
                return True
        else:  # check parent tables
            if self.parent:
                return self.parent.symbol_has_defined(symbol, self.tsindex)
            else:  # recursion ends at root table whose parent is None
                return False

    def symbol_invoke(self, symbol):
        if not self.symbol_has_defined(symbol):
            raise SymbolNotDefinedError()

    def symbol_invoke_func(self, name, stype_list):
        pass
