# coding:utf-8

"""
Symbol table.
"""
import StringIO

import tokens


class RedefinedError(Exception):
    pass


class UndefinedError(Exception):
    pass


class TypeMismatchError(Exception):
    pass


class ParamMismatchError(Exception):
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

    def __init__(self, token, size=None):
        """
        :param token: Token_INT or Token_REAL
        :param size: when used in return type, func define param list ,size is None
        """
        super(STypeArray, self).__init__(token)
        self.size = size


class STypeFunc(SType):
    """
    Function type
    """

    def __init__(self, stype, param_stypes):
        super(STypeFunc, self).__init__(stype.type)
        self.stype = stype
        self.param_stypes = param_stypes


class SUnknown(object):
    def __init__(self, name, is_arr=False):
        self.name = name
        self.is_arr = is_arr


class Symbol(object):
    """
    Symbol Object
    """

    def __init__(self, name, stype):
        assert isinstance(name, basestring)
        assert isinstance(stype, SType)

        self.name = name
        self.stype = stype
        self.lexeme = None  # assigned when parse `AssignStmtNode`
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
        self.children_tsindex = []  # tsindex of children

    def table_append(self, child):
        """
        Append child table
        """
        assert isinstance(child, STable)
        child.parent = self
        child.tsindex = len(self.symbols) - 1
        self.children.append(child)
        self.children_tsindex.append(child.tsindex)

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

    def symbol_at(self, index):
        try:
            symbol = self.symbols[index]
        except IndexError:
            return None
        else:
            return symbol

    def symbol_find(self, name, ends=None):
        """
        find the symbol defined before with name of `name`

        :param ends: searching in [0,ends] in the symbol list of current table.
                    Used when searching in parent table whose value is `tsindex`
        :return: the symbol or None
        """
        if not ends:
            ends = len(self.symbols) - 1

        for i in range(ends + 1):  # check self
            smb = self.symbol_at(i)
            if smb.name == name:
                return smb
        else:  # check parent tables
            if self.parent:
                return self.parent.symbol_find(name, self.tsindex)
            else:  # recursion ends at root table whose parent is None
                return None

    def symbol_has_defined(self, symbol):
        """
        Check if the symbol has been defined before when appending it to table.
        :param symbol:
        :return:
        """
        if self.symbol_find(symbol.name):
            return True
        else:
            return False

    def calc_data_type(self, stype_or_list):
        """
        calc the data type of the `stype_or_list`
        ** Type Cast is Not Allowed!!! **
        ** The data type of each item must be the same **

        :param stype_or_list: single SType instance or its list
        :return: the data type or raise an error
        """

        # TODO enable real int cast?

        if isinstance(stype_or_list, SType):
            stype_or_list = [stype_or_list]

        the_type = None
        for stype in stype_or_list:
            if isinstance(stype, SUnknown):  # calc the type of the id
                stype = self.invoke(stype.name, stype.is_arr).stype
            if the_type:
                if stype.type != the_type:
                    raise TypeMismatchError()
            else:
                the_type = stype.type
        return the_type

    def invoke(self, name, is_arr=False):
        """
        When invoking an `id`, check its validity.
        :param name: the name of `id`
        :param is_arr: id is an array? default is False
        :return: the symbol we found with the name or raise an error
        """
        symbol = self.symbol_find(name)  # find the symbol with name `name`
        if not symbol:
            raise UndefinedError()  # raise error if not found

        # symbol.stype must be corresponding to `is_arr`
        if isinstance(symbol.stype, STypeArray) ^ is_arr:
            raise TypeMismatchError()

        # symbol cannot be a function, 'cause function would be handled in `invoke_func`
        if isinstance(symbol.stype, STypeFunc):
            raise TypeMismatchError()

        return symbol

    def invoke_assign(self, name, stype_list, is_arr=False):
        """
        check the validity of the `AssignStmt`
        :param name: the name of the left-value
        :param stype_list: a list of the stype of each right value in the expression
        :param is_arr: left-value is_array or not
        :return:
        """

        # calc left type
        left_type = self.invoke(name, is_arr).stype.type
        right_type = self.calc_data_type(stype_list)
        if left_type != right_type:
            raise TypeMismatchError()

    def invoke_compare(self, stype_list1, stype_list2):
        """
        check the validity of the `CompareStmt`
        calc data type of both side, and compare them
        :param stype_list1:
        :param stype_list2:
        :return:
        """
        if self.calc_data_type(stype_list1) != self.calc_data_type(stype_list2):
            raise TypeMismatchError()

    def invoke_func(self, name, param_stype_lists):
        """
        call a function. check the validity of param type
        :param name:
        :param param_stype_lists: list of (expr) stype_list
        :return:
        """
        symbol = self.symbol_find(name)

        # check if defined
        if not symbol:
            raise UndefinedError()

        # check if function
        if not isinstance(symbol.stype, STypeFunc):
            raise TypeMismatchError()

        # matching
        defined_types = symbol.stype.param_stypes
        if len(defined_types) != len(param_stype_lists):
            raise ParamMismatchError()

        for i in range(len(defined_types)):
            stype1 = defined_types[i]
            stype2 = param_stype_lists[i]  # a list of stype because each param can be a expression

            # TODO stype2 is a list
            continue

            # calc stype
            if isinstance(stype2, SUnknown):
                stype2 = self.invoke(stype2.name).stype

            # STypeArray
            if isinstance(stype1, STypeArray) and not isinstance(stype2, STypeArray):
                raise TypeMismatchError()

            # normal SType
            if stype1.type != stype2.type:
                raise TypeMismatchError()

    def invoke_return(self, stype_list):
        # TODO find the nearest func def and match return type with stype_list
        pass

    def gen_tree(self, level=1):
        """
        print symbol tabls
        :param level: the level of table. top level is 1
        :return:
        """
        stdout = StringIO.StringIO()
        for i in range(len(self.symbols)):
            symbol = self.symbol_at(i)
            indent = '|----' + '------' * (level - 1) + '>'
            stdout.write('%s(%s:%s)\n' % (indent, symbol.name, symbol.stype.type.lexeme))

            if i in self.children_tsindex:
                stdout.write(self.table_child_at(self.children_tsindex.index(i)).gen_tree(level + 1))
        value = stdout.getvalue()
        stdout.close()
        return value
