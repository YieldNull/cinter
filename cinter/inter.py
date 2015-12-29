# coding:utf-8

"""
An interpreter base on `Code`

may cause ZeroDivisionError and IndexError
"""
import sys


class Code(object):
    """
    Intermediate code
    """
    line = -1  # line number of code

    def __init__(self, op='', arg1='', arg2='', tar=''):
        """
        I forgot why i set '' as default value to these params....
        Just use it, refactor may cause crash.
        :param op:  operator
        :param arg1: operand #1
        :param arg2: operand #2
        :param tar:  target
        """
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.tar = tar

        Code.line += 1
        self.line = Code.line

    def __str__(self):
        return '%3d: ( %-3s , %-5s , %-5s , %-8s )' % \
               (self.line, self.op, str(self.arg1), str(self.arg2), str(self.tar))

    @classmethod
    def gen_temp(cls):
        return '_t%d' % (Code.line + 1)  # use code index as the temp variable index


class Symbol(object):
    """
    Symbol
    """
    type_int = 0
    type_real = 1
    type_func = 3

    def __init__(self, name, _type, value=None, size=-1):
        self.name = name
        self.type = _type
        self.size = size
        self.value = value


class Frame(object):
    """
    Function frame
    """

    def __init__(self):
        self.symbols = []

    def append(self, symbol):
        self.symbols.append(symbol)

    def find(self, name):
        for symbol in self.symbols:
            if symbol.name == name:
                return symbol
        else:
            return None


class Interpreter(object):
    def __init__(self, codes, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        self.codes = codes  # code list to be interpreted
        self.functions = []  # functions
        self.stack = [Frame()]  # stack of function frame, initializes with main Frame
        self.symbols = [  # global single value symbols
            Symbol('_ra', Symbol.type_int, value=len(codes)),  # return address
            Symbol('_rv', Symbol.type_real)  # return value
        ]

    @property
    def top_frame(self):
        return self.stack[len(self.stack) - 1]

    def inter(self):
        line = 0
        while line < len(self.codes) - 1:
            code = self.codes[line]
            op = code.op
            arg1 = code.arg1
            arg2 = code.arg2
            tar = code.tar

            if op == '=':
                if str(arg1)[:2] in ['_i', '_r']:
                    self._handle_def(arg1, arg2, tar)
                else:
                    self._handle_assign(arg1, tar)
            elif op == 'f=':
                if tar == 'main':  # enter the main function
                    line += 2
                    continue
                self._handle_def_func(arg1, tar)
            elif op == '[]=':
                self._handle_arr_assign(arg1, arg2, tar)
            elif op == '=[]':
                self._handle_arr_access(arg1, arg2, tar)
            elif op in ['+', '-', '*', '/']:
                self._handle_arithmetic(op, arg1, arg2, tar)
            elif op == 'j':
                line = tar
                continue
            elif op[:1] == 'j':
                result = self._handle_jump_cond(op[1:], arg1, arg2)
                if not result:  # does not meet the condition, jump
                    line = tar
                    continue
            elif op == 'p=':
                self._handle_param_pass(arg1, tar)
            elif op == '=p':
                self._handle_param_receive(arg1, tar)
            elif op == 'c':
                address = self._handle_func_call(tar)
                line = address
                continue
            elif op == 'r':
                line = self._handle_func_return(tar)
                continue
            line += 1

    def _find(self, name):
        """
        find the symbol  with the name `name`.

        find in top frame and global symbols
        if not found, return None
        """
        symbol = self.top_frame.find(name)
        if symbol:
            return symbol

        for symbol in self.symbols:
            if symbol.name == name:
                return symbol
        else:
            return None

    def _handle_def(self, _type, size, tar):
        """
        Declare a variable or assign value to it.
        """

        # gen data type
        dtype = Symbol.type_int if _type[:2] == '_i' else Symbol.type_real
        if len(_type) == 2:
            symbol = Symbol(tar, dtype)
        else:  # array
            symbol = Symbol(tar, dtype, size=size)
        self.top_frame.append(symbol)

    def _handle_assign(self, source, tar):
        """
        find the two symbols and assign the value of `source`  to `tar`
        """
        # TODO normalize type
        try:
            float(source)  # literal
        except ValueError:
            s_source = self._find(source)
            _type = s_source.type
            value = s_source.value
        else:
            _type = Symbol.type_real
            value = float(source)

        s_tar = self._find(tar)
        if s_tar is None:
            symbol = Symbol(tar, _type, value=value)
            self.top_frame.append(symbol)
        else:
            if s_tar.type == Symbol.type_int:
                s_tar.value = int(value)
            else:
                s_tar.value = float(value)

    def _handle_def_func(self, entrance, name):
        """
        Add the function to function list
        """
        self.functions.append(Symbol(name, Symbol.type_func, value=entrance))

    def _handle_arr_access(self, name, index, tar):
        """
        assign the [index]th value of the array with name of `name` to tar
        """
        arr = self._find(name)
        tar = self._find(tar)

        if not isinstance(index, int):  # index is a variable name
            index = self._find(index).value

        if index > arr.size - 1:
            raise IndexError

        tar.value = arr.value[index]  # arr's value is a list of literal value

    def _handle_arr_assign(self, index, source, name):
        """
        assign source's value to the [index]th value of the array with name of `name`
        """
        arr = self._find(name)
        source = self._find(source)

        if not isinstance(index, int):  # index is a variable name
            index = self._find(index).value
        arr.value[index] = source.value

    def _handle_arithmetic(self, op, arg1, arg2, tar):
        """
        arg1,arg2 are all variable names, because every literal value are assigned to a temp variable
        """
        arg1 = self._find(arg1).value
        arg2 = self._find(arg2).value

        symbol = self._find(tar)
        if symbol is None:
            symbol = Symbol(tar, Symbol.type_real)
            self.top_frame.append(symbol)

        if op == '+':
            symbol.value = arg1 + arg2
        elif op == '-':
            symbol.value = arg1 - arg2
        elif op == '*':
            symbol.value = arg1 * arg2
        else:
            symbol.value = arg1 / arg2  # may cause ZeroDivisionError

    def _handle_jump_cond(self, cond, arg1, arg2):
        """
        return whether meets the cond `arg1 cond arg2`
        """
        assert cond in ['>', '<', '==']
        left = self._find(arg1).value
        right = self._find(arg2).value

        if cond == '>':
            return left > right
        elif cond == '<':
            return left < right
        else:
            return left == right

    def _handle_param_pass(self, source, tar):
        """
        pass value to function.

        Just store these params in global.
        Def it if has not def
        """
        source = self._find(source)
        symbol = self._find(tar)
        if symbol is None:
            symbol = Symbol(tar, source.type)
            self.symbols.append(symbol)
        symbol.value = source.value

    def _handle_param_receive(self, source, tar):
        """
        Receive params passed to a function
        """
        source = self._find(source)
        tar = self._find(tar)
        tar.value = source.value

    def _handle_func_call(self, name):
        """
        Call a function.
        return function entrance address
        """
        if name == 'write':
            param = self._find('_p0').value
            ra = self._find('_ra').value
            self.stdout.write('%s\n' % str(param))
            return ra
        elif name == 'read':
            rv = self._find('_rv')
            ra = self._find('_ra').address
            rv.value = self.stdin.read()
            return ra
        else:
            func = self._find(name)
            frame = Frame()
            self.stack.append(frame)
            return func.value

    def _handle_func_return(self, tar):
        """
        return the return address
        """
        self.functions.pop()
        ra = self._find(tar)
        return ra.value
