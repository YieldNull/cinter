"""
An interpreter base on `Code`
"""


class Code(object):
    line = -1  # line number

    def __init__(self, op='', arg1='', arg2='', tar=''):
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
