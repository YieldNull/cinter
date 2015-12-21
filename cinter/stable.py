# coding:utf-8

"""
Symbol table.
"""
import tokens


class RedefinedError(Exception):
    pass


class SType(object):
    """
    Basic Symbol Type
    """

    def __init__(self, _type):
        """
        :param _type:  Token_INT or Token_REAL
        """
        assert _type == tokens.Token_INT or _type == tokens.Token_REAL
        self.type = _type


class STypeArray(SType):
    """
    Array type
    """

    def __init__(self, _type, size):
        super(STypeArray, self).__init__(_type)
        self.size = size


class STypeFunc(object):
    """
    Function type
    """

    def __init__(self, stype, params):
        # assert isinstance(params, FuncDefParamList)
        self.params = params

        if stype:
            assert isinstance(stype, SType)
            self.stype = stype  # basic type or array type
        else:
            self.stype = None  # void


class SObject(object):
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

    def symbol_append(self, sobj):
        """
        Append table object
        """
        if self._symbol_has_defined(sobj):
            raise RedefinedError()
        else:
            self.symbols.append(sobj)
            sobj.table = self

    def symbol_at_index(self, index):
        try:
            obj = self.symbols[index]
        except IndexError:
            return None
        else:
            return obj

    def symbol_index(self, obj):
        assert isinstance(obj, SObject)
        return self.symbols.index(obj)

    def _symbol_equal(self, obj1, obj2):
        assert isinstance(obj1, SObject)
        assert isinstance(obj2, SObject)

        if obj1.name == obj2.name:
            # TODO check type
            pass
        else:
            return False

    def _symbol_has_defined(self, obj, ends=None):
        if not ends:
            ends = len(self.symbols) - 1

        for i in range(ends + 1):  # check self
            if self._symbol_equal(self.parent.symbol_at_index(i), obj):
                return True
        else:  # check parent tables
            if self.parent:
                return self.parent._symbol_has_defined(obj, self.tsindex)
            else:  # recursion ends at root table whose parent is None
                return False

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
