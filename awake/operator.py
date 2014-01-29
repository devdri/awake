# This file is part of Awake - GB decompiler.
# Copyright (C) 2012  Wojciech Marczenko (devdri) <wojtek.marczenko@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from awake.operand import Constant, Operand

class Operator(Operand):

    def __init__(self, *args):
        self.childs = args

    # XXX
    #def getMemreads(self):
    #    return set.union(set(), *(ch.getMemreads() for ch in self.childs))

    def optimizedWithContext(self, ctx):
        childs = (ch.optimizedWithContext(ctx) for ch in self.childs)
        return self.__class__.make(*childs)

    @classmethod
    def make(cls, *args):
        return cls(*args)

def isConstant(x):
    return x.value is not None

class BinOp(Operator):
    symbol = None

    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.childs = (left, right)

    def __str__(self):

        left = str(self.left)
        if self.left.needParen(0):
            left = '(' + left + ')'

        right = str(self.right)
        if self.right.needParen(0):
            right = '(' + right + ')'

        return '{0} {1} {2}'.format(left, self.symbol, right)

    def __hash__(self):
        return hash((self.symbol, self.left, self.right))

    def __eq__(self, other):
        try:
            return self.symbol == other.symbol and self.left == other.left and self.right == other.right
        except AttributeError:
            return False

    def render(self, renderer):
        if self.left.needParen(0):
            renderer.add('(')
        self.left.render(renderer)
        if self.left.needParen(0):
            renderer.add(')')
        renderer.add(' '+self.symbol+' ')
        if self.right.needParen(0):
            renderer.add('(')
        self.right.render(renderer)
        if self.right.needParen(0):
            renderer.add(')')

    def needParen(self, priority):
        return True

    @classmethod
    def make(cls, left, right):
        if isConstant(left) and isConstant(right):
            return Constant(cls.calculate(left.value, right.value))
        else:
            return super(BinOp, cls).make(left, right)

class Add(BinOp):
    symbol = '+'

    @staticmethod
    def calculate(left, right):
        return (left + right) & 0xFF

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left
        if right.value == 0:
            return left
        if left == right:
            return Shl.make(left, Constant(1))
        if isConstant(right) and isinstance(left, Sub) and isConstant(left.right):
            return Add.make(left.left, Constant(Sub.calculate(right.value, left.right.value)))
        return super(Add, cls).make(left, right)

class Sub(BinOp):
    symbol = '-'

    @staticmethod
    def calculate(left, right):
        return (left - right) & 0xFF

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left
        if right.value == 0:
            return left
        if left == right:
            return Constant(0)
        if isConstant(right) and isinstance(left, Sub) and isConstant(left.right):
            return Sub.make(left.left, Constant(Add.calculate(right.value, left.right.value)))
        return super(Sub, cls).make(left, right)

class And(BinOp):
    symbol = '&'

    @staticmethod
    def calculate(left, right):
        return left & right

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left

        if isConstant(right):
            if (left.value_mask & right.value) == left.value_mask:
                return left
            if (left.value_mask & right.value) == 0:
                return Constant(0)

        if right == left:
            return left

        #if isinstance(left, And):
        #    return And.make(left.left, And(left.right, right))
        #if isinstance(right, And):
        #    return And.make(right.left, And(right.right, left))
        if isinstance(left, Or) and isConstant(right):
            return Or.make(And.make(left.left, right), And.make(left.right, right))
        return super(And, cls).make(left, right)

class Or(BinOp):
    symbol = '|'

    @staticmethod
    def calculate(left, right):
        return left | right

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left

        if left == right:
            return left

        if right.value == 0:
            return left
        if isinstance(left, And) and isinstance(right, And):
            if left.left == right.left:
                return And.make(left.left, Or.make(left.right, right.right))
        return super(Or, cls).make(left, right)

class Xor(BinOp):
    symbol = '^'

    @staticmethod
    def calculate(left, right):
        return left ^ right

    @classmethod
    def make(cls, left, right):
        if left == right:
            return Constant(0)
        return super(Xor, cls).make(left, right)

class Equals(BinOp):
    symbol = '=='
    bits = 1

    @staticmethod
    def calculate(left, right):
        return int(left == right)

    def logicalNot(self):
        return NotEquals(self.left, self.right)

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left
        if isinstance(left, Sub) and isConstant(left.right) and isConstant(right):
            return Equals.make(left.left, Constant(Add.calculate(right.value, left.right.value)))
        return super(Equals, cls).make(left, right)

class NotEquals(BinOp):
    symbol = '!='
    bits = 1

    @staticmethod
    def calculate(left, right):
        return int(left != right)

    def logicalNot(self):
        return Equals(self.left, self.right)

class Less(BinOp):
    symbol = '<'
    bits = 1

    @staticmethod
    def calculate(left, right):
        return int(left < right)

    def logicalNot(self):
        return GreaterEqual(self.left, self.right)

class GreaterEqual(BinOp):
    symbol = '>='
    bits = 1

    @staticmethod
    def calculate(left, right):
        return int(left >= right)

    def logicalNot(self):
        return Less(self.left, self.right)

class Shl(BinOp):
    symbol = '<<'

    @staticmethod
    def calculate(left, right):
        return (left << right) & 0xFF

    @classmethod
    def make(cls, left, right):

        if isConstant(right):

            if isinstance(left, Shl) and isConstant(left.right):
                right = Constant(right.value + left.right.value)
                left = left.left

            if isinstance(left, Shr) and isConstant(left.right):
                sh_a = left.right.value
                sh_b = right.value
                mask = Constant(((0xFF >> sh_a) << sh_b) & 0xFF)
                sum_shift = sh_b - sh_a

                if sum_shift < 0:
                    return And.make(Shr.make(left.left, Constant(-sum_shift)), mask)
                else:
                    return And.make(Shl.make(left.left, Constant(sum_shift)), mask)

            if isinstance(left, And):
                a = left.left
                b = left.right
                return And.make(Shl.make(a, right), Shl.make(b, right))

        return super(Shl, cls).make(left, right)

    @property
    def value_mask(self):
        if isConstant(self.right):
            return (self.left.value_mask << self.right.value) & 0xFF
        else:
            return 0xFF #self.left.value_mask

class Shr(BinOp):
    symbol = '>>'

    @staticmethod
    def calculate(left, right):
        return (left >> right) & 0xFF

    @classmethod
    def make(cls, left, right):

        if isConstant(right):

            if isinstance(left, Shr) and isConstant(left.right):
                right = Constant(right.value + left.right.value)
                left = left.left

            if isinstance(left, Shl) and isConstant(left.right):
                sh_a = left.right.value
                sh_b = right.value
                mask = Constant(((0xFF << sh_a) & 0xFF) >> sh_b)
                sum_shift = sh_b - sh_a

                if sum_shift < 0:
                    return And.make(Shl.make(left.left, Constant(-sum_shift)), mask)
                else:
                    return And.make(Shr.make(left.left, Constant(sum_shift)), mask)

            if isinstance(left, And):
                a = left.left
                b = left.right
                return And.make(Shr.make(a, right), Shr.make(b, right))

        return super(Shr, cls).make(left, right)

    @property
    def value_mask(self):
        if isConstant(self.right):
            return self.left.value_mask >> self.right.value
        else:
            return 0xFF #self.left.value_mask

class LogicalNot(Operator):
    bits = 1

    def __str__(self):
        return 'not '+str(self.childs[0])

    @classmethod
    def make(cls, inner):
        try:
            return inner.logicalNot()
        except AttributeError:
            return super(LogicalNot, cls).make(inner)

class Add16(BinOp):
    symbol = '+.'
    bits = 16

    @staticmethod
    def calculate(a, b):
        return (a + b) & 0xFFFF

    @classmethod
    def make(cls, left, right):
        if isConstant(left):
            left, right = right, left
        if right.value == 0:
            return left
        if isinstance(left, Add16) and isConstant(right) and isConstant(left.right):
            return cls.make(left.left, Constant(cls.calculate(right.value, left.right.value)))
        return super(Add16, cls).make(left, right)

class Sub16(BinOp):
    symbol = '-.'
    bits = 16

    @staticmethod
    def calculate(a, b):
        return (a - b) & 0xFFFF

class Shl16(BinOp):
    symbol = '<<.'
    bits = 16

    @staticmethod
    def calculate(a, b):
        return (a << b) & 0xFFFF

class Shr16(BinOp):
    symbol = '>>.'
    bits = 16

    @staticmethod
    def calculate(a, b):
        return (a >> b) & 0xFFFF

class FuncOperator(Operator):
    name = None

    def __str__(self):
        return '{0}({1})'.format(self.name, ', '.join(str(x) for x in self.childs))

    def render(self, renderer):
        renderer.add(self.name)
        renderer.add('(')
        renderer.renderList(self.childs)
        renderer.add(')')

    def __hash__(self):
        return hash((self.name, self.childs))

    def __eq__(self, other):
        try:
            return self.name == other.name and self.args == other.args
        except AttributeError:
            return False

    @classmethod
    def make(cls, *args):
        if hasattr(cls, 'calculate') and all(isConstant(x) for x in args):
            values = [x.value for x in args]
            return Constant(cls.calculate(*values))
        return super(FuncOperator, cls).make(*args)

class PopValue(FuncOperator):
    name = 'popval'

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])

    @classmethod
    def make(cls, a):
        if isinstance(a, Push):
            return a.childs[1]
        return super(PopValue, cls).make(a)

class PopStack(FuncOperator):
    name = 'popst'

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])

    @classmethod
    def make(cls, a):
        if isinstance(a, Push):
            return a.childs[0]
        return super(PopStack, cls).make(a)


class Push(FuncOperator):
    name = 'push'

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])

class CarryOfAdd(FuncOperator):
    name = 'c_add'

class LowByte(FuncOperator):
    name = 'lo'

    @staticmethod
    def calculate(arg):
        return arg & 0xFF

class HighByte(FuncOperator):
    name = 'hi'

    @staticmethod
    def calculate(arg):
        return arg >> 8

class Word(FuncOperator):
    name = 'word'
    bits = 16

    @staticmethod
    def calculate(hi, lo):
        return (hi << 8) | lo

    @classmethod
    def make(cls, hi, lo):
        # merge word
        if isinstance(hi, HighByte) and isinstance(lo, LowByte):
            if hi.childs[0] == lo.childs[0]:
                return hi.childs[0]

        # high zero
        if hi.value == 0:
            return lo

        if isinstance(hi, Shr) and isinstance(lo, Shl) and hi.left == lo.left and isConstant(hi.right) and isConstant(lo.right):
            hi_sh = hi.right.value
            lo_sh = lo.right.value
            if hi_sh + lo_sh == 8:
                return Shl16.make(lo.left, Constant(lo_sh))

        return super(Word, cls).make(hi, lo)

binary_operators = {
    '+': (1, Add),
    '-': (1, Sub),
    '&': (1, And),
    '|': (1, Or),
    '^': (1, Xor),
    '==': (1, Equals),
    '<': (1, Less),
    '+.': (1, Add16),
    '-.': (1, Sub16),
    '<<': (1, Shl),
    '>>': (1, Shr),
}

functions = {
    'add16': (Add16, 2),
    'c_add': (CarryOfAdd, 2),
    'popval': (PopValue, 1),
    'popst': (PopStack, 1),
    'push': (Push, 2),
}
