"""
An interpreter base on `Code`
"""


class Code(object):
    tindex = 0  # index of temp variable
    line = 0  # line number

    def __init__(self, op=None, arg1=None, arg2=None, tar=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.tar = tar
        Code.line += 1

    def __str__(self):
        return '%d : (%s ,%s ,%s ,%s)' % (Code.line, self.op, str(self.arg1), str(self.arg2), str(self.tar))

    @classmethod
    def gen_temp(cls):
        Code.line += 1
        return '_t%d' % (Code.line)
