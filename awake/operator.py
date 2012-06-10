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

import operand

class Operator(operand.Operand):
    def __init__(self):
        pass

    def childs(self):
        return []

    def getMemreads(self):
        out = set()
        for x in self.childs():
            out |= x.getMemreads()
        return out

def isConstant(x):
    if hasattr(x, 'getValue'):
        return True
    else:
        return False

class BinOp(Operator):
    def __init__(self, symbol, left, right):
        self.symbol = symbol
        self.left = left
        self.right = right

    def optimizedWithContext(self, ctx):
        left = self.left.optimizedWithContext(ctx)
        right = self.right.optimizedWithContext(ctx)
        if isConstant(left) and isConstant(right):
            return operand.Constant(self.calculate(left.getValue(), right.getValue()))
        return self.__class__(left, right)

    def __str__(self):

        left = str(self.left)
        if self.left.needParen(0):
            left = '(' + left + ')'

        right = str(self.right)
        if self.right.needParen(0):
            right = '(' + right + ')'

        return '{0} {1} {2}'.format(left, self.symbol, right)

    def __eq__(self, other):
        if not hasattr(other, 'symbol') or not hasattr(other, 'left') or not hasattr(other, 'right'):
            return False
        return self.symbol == other.symbol and self.left == other.left and self.right == other.right

    def html(self):
        left = self.left.html()
        if self.left.needParen(0):
            left = '(' + left + ')'
        right = self.right.html()
        if self.right.needParen(0):
            right = '(' + right + ')'
        return '{0} {1} {2}'.format(left, self.symbol, right)

    def childs(self):
        return [self.left, self.right]

    def needParen(self, priority):
        return True

class Add(BinOp):
    def __init__(self, a, b):
        super(Add, self).__init__('+', a, b)

    def calculate(self, left, right):
        return (left + right) & 0xFF

    def optimizedWithContext(self, ctx):

        a = self.left.optimizedWithContext(ctx)
        b = self.right.optimizedWithContext(ctx)
        if isConstant(a) and a.getValue() == 0:
            return b
        if isConstant(b) and b.getValue() == 0:
            return a

        return BinOp.optimizedWithContext(self, ctx)

class Sub(BinOp):
    def __init__(self, a, b):
        super(Sub, self).__init__('-', a, b)

    def calculate(self, left, right):
        return (left - right) & 0xFF

class And(BinOp):
    def __init__(self, a, b):
        super(And, self).__init__('&', a, b)

    def calculate(self, left, right):
        return left & right

    def optimizedWithContext(self, ctx):
        if self.left == self.right:
            return self.left.optimizedWithContext(ctx)
        if isinstance(self.left, And):
            return And(self.left.left, And(self.left.right, self.right)).optimizedWithContext(ctx)

        if isConstant(self.right) and self.left.getValueMask() == self.right.getValue():
            return self.left

        return BinOp.optimizedWithContext(self, ctx)

class Or(BinOp):
    def __init__(self, a, b):
        super(Or, self).__init__('|', a, b)

    def calculate(self, left, right):
        return left | right

    def optimizedWithContext(self, ctx):
        left = self.left.optimizedWithContext(ctx)
        right = self.right.optimizedWithContext(ctx)
        if isConstant(left) and left.getValue() == 0:
            return right
        if isConstant(right) and right.getValue() == 0:
            return left
        if isinstance(left, And) and isinstance(right, And):
            if left.left == right.left:
                return And(left.left, Or(left.right, right.right)).optimizedWithContext(ctx)
        return BinOp.optimizedWithContext(self, ctx)

class Xor(BinOp):
    def __init__(self, a, b):
        super(Xor, self).__init__('^', a, b)

    def calculate(self, left, right):
        return left ^ right

class Equals(BinOp):
    def __init__(self, a, b):
        super(Equals, self).__init__('==', a, b)

    def calculate(self, left, right):
        return left == right

    def logicalNot(self):
        return NotEquals(self.left, self.right)

class NotEquals(BinOp):
    def __init__(self, a, b):
        super(NotEquals, self).__init__('!=', a, b)

    def calculate(self, left, right):
        return left != right

    def logicalNot(self):
        return Equals(self.left, self.right)

class Less(BinOp):
    def __init__(self, a, b):
        super(Less, self).__init__('<', a, b)

    def calculate(self, left, right):
        return left < right

    def logicalNot(self):
        return GreaterEqual(self.left, self.right)

class GreaterEqual(BinOp):
    def __init__(self, a, b):
        super(GreaterEqual, self).__init__('>=', a, b)

    def calculate(self, left, right):
        return left < right

    def logicalNot(self):
        return Less(self.left, self.right)

class Shl(BinOp):
    def __init__(self, a, b):
        super(Shl, self).__init__('<<', a, b)

    def calculate(self, left, right):
        return (left << right) & 0xFF

    def optimizedWithContext(self, ctx):
        left = self.left.optimizedWithContext(ctx)
        right = self.right.optimizedWithContext(ctx)

        if not isConstant(right):
            return Shl(left, right)

        if isConstant(left):
            return operand.Constant(self.calculate(left.getValue(), right.getValue()))

        if isinstance(left, Shl) and isConstant(left.right):
            right = operand.Constant(right.getValue() + left.right.getValue())
            left = left.left

        if isinstance(left, Shr) and isConstant(left.right):
            sh_a = left.right.getValue()
            sh_b = right.getValue()
            mask = operand.Constant(((0xFF >> sh_a) << sh_b) & 0xFF)
            sum_shift = sh_b - sh_a

            if sum_shift < 0:
                return And(Shr(left.left, operand.Constant(-sum_shift)), mask)
            else:
                return And(Shl(left.left, operand.Constant(sum_shift)), mask)

        if isinstance(left, And):
            a = left.left
            b = left.right
            return And(Shl(a, right), Shl(b, right))

        return Shl(left, right)

    def getValueMask(self):
        if isConstant(self.right):
            return (self.left.getValueMask() << self.right.getValue()) & 0xFF
        else:
            return self.left.getValueMask()

class Shr(BinOp):
    def __init__(self, a, b):
        super(Shr, self).__init__('>>', a, b)

    def calculate(self, left, right):
        return (left >> right) & 0xFF

    def optimizedWithContext(self, ctx):
        left = self.left.optimizedWithContext(ctx)
        right = self.right.optimizedWithContext(ctx)

        if not isConstant(right):
            return Shl(left, right)

        if isConstant(left):
            return operand.Constant(self.calculate(left.getValue(), right.getValue()))


        if isinstance(left, Shr) and isConstant(left.right):
            right = operand.Constant(right.getValue() + left.right.getValue())
            left = left.left

        if isinstance(left, Shl) and isConstant(left.right):
            sh_a = left.right.getValue()
            sh_b = right.getValue()
            mask = operand.Constant(((0xFF << sh_a) & 0xFF) >> sh_b)
            sum_shift = sh_b - sh_a

            if sum_shift < 0:
                return And(Shl(left.left, operand.Constant(-sum_shift)), mask)
            else:
                return And(Shr(left.left, operand.Constant(sum_shift)), mask)

        if isinstance(left, And):
            a = left.left
            b = left.right
            return And(Shr(a, right), Shr(b, right))

        return Shr(left, right)

    def getValueMask(self):
        if isConstant(self.right):
            return self.left.getValueMask() >> self.right.getValue()
        else:
            return self.left.getValueMask()

class LogicalNot(Operator):
    def __init__(self, a):
        self.a = a

    def __str__(self):
        return 'not '+str(self.a)

    def optimizedWithContext(self, ctx):
        inner = self.a.optimizedWithContext(ctx)
        if hasattr(inner, 'logicalNot'):
            return inner.logicalNot()
        return LogicalNot(inner)

    def childs(self):
        return set([self.a])


class FuncOperator(Operator):
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __str__(self):
        return '{0}({1})'.format(self.name, ', '.join(str(x) for x in self.args))

    def html(self):
        return '{0}({1})'.format(self.name, ', '.join(x.html() for x in self.args))

    def childs(self):
        return self.args

    def optimizedWithContext(self, ctx):
        args = [a.optimizedWithContext(ctx) for a in self.args]

        if hasattr(self, 'calculate') and all(isConstant(x) for x in args):
            values = [x.getValue() for x in args]
            return operand.Constant(self.calculate(*values))

        return self.__class__(*args)

    def __eq__(self, other):
        if not hasattr(other, 'name') or not hasattr(other, 'args'):
            return False
        return self.name == other.name and self.args == other.args

class Add16(BinOp):
    def __init__(self, a, b):
        super(Add16, self).__init__('+.', a, b)

    def optimizedWithContext(self, ctx):

        a = self.left.optimizedWithContext(ctx)
        b = self.right.optimizedWithContext(ctx)
        if isConstant(a) and a.getValue() == 0:
            return b
        if isConstant(b) and b.getValue() == 0:
            return a

        return BinOp.optimizedWithContext(self, ctx)

    def calculate(self, a, b):
        return (a + b) & 0xFFFF

    def bits(self):
        return 16

class Sub16(BinOp):
    def __init__(self, a, b):
        super(Sub16, self).__init__('-.', a, b)

    def calculate(self, a, b):
        return (a - b) & 0xFFFF

    def bits(self):
        return 16

class Shl16(BinOp):
    def __init__(self, a, b):
        super(Shl16, self).__init__('<<.', a, b)

    def calculate(self, a, b):
        return (a << b) & 0xFFFF

    def bits(self):
        return 16

class Shr16(BinOp):
    def __init__(self, a, b):
        super(Shr16, self).__init__('>>.', a, b)

    def calculate(self, a, b):
        return (a >> b) & 0xFFFF

    def bits(self):
        return 16

class PopValue(FuncOperator):
    def __init__(self, a):
        super(PopValue, self).__init__('popval', [a])
        self.a = a

    def optimizedWithContext(self, ctx):
        a = self.a.optimizedWithContext(ctx)
        if hasattr(a, 'name') and a.name == 'push':
            return a.args[1]
        return self.__class__(a)

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])

class PopStack(FuncOperator):
    def __init__(self, a):
        super(PopStack, self).__init__('popst', [a])
        self.a = a

    def optimizedWithContext(self, ctx):
        a = self.a.optimizedWithContext(ctx)
        if hasattr(a, 'name') and a.name == 'push':
            return a.args[0]
        return self.__class__(a)

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])


class Push(FuncOperator):
    def __init__(self, a, b):
        super(Push, self).__init__('push', [a, b])

    def getDependencies(self):
        return FuncOperator.getDependencies(self) | set(['mem'])

class CarryOfAdd(FuncOperator):
    def __init__(self, a, b):
        super(CarryOfAdd, self).__init__('c_add', [a, b])

class LowByte(FuncOperator):
    def __init__(self, arg):
        super(LowByte, self).__init__('lo', [arg])
        self.arg = arg

    def optimizedWithContext(self, ctx):
        arg = self.arg.optimizedWithContext(ctx)
        if isConstant(arg):
            return operand.Constant(self.calculate(arg.getValue()))
        return self.__class__(arg)

    def calculate(self, arg):
        return arg & 0xFF

class HighByte(FuncOperator):
    def __init__(self, arg):
        super(HighByte, self).__init__('hi', [arg])
        self.arg = arg

    def optimizedWithContext(self, ctx):
        arg = self.arg.optimizedWithContext(ctx)
        if isConstant(arg):
            return operand.Constant(self.calculate(arg.getValue()))
        return self.__class__(arg)

    def calculate(self, arg):
        return arg >> 8

class Word(FuncOperator):
    def __init__(self, h, l):
        super(Word, self).__init__('word', [h, l])
        self.hi = h
        self.lo = l

    def optimizedWithContext(self, ctx):
        hi = self.hi.optimizedWithContext(ctx)
        lo = self.lo.optimizedWithContext(ctx)
        if isConstant(hi) and isConstant(lo):
            return operand.Constant(self.calculate(hi.getValue(), lo.getValue()))

        # merge word
        if isinstance(hi, HighByte) and isinstance(lo, LowByte):
            if hi.arg == lo.arg:
                return hi.arg

        # high zero
        if isConstant(hi) and hi.getValue() == 0:
            return lo

        if isinstance(hi, Shr) and isinstance(lo, Shl) and hi.left == lo.left and isConstant(hi.right) and isConstant(lo.right):
            hi_sh = hi.right.getValue()
            lo_sh = lo.right.getValue()
            if hi_sh + lo_sh == 8:
                return Shl16(lo.left, operand.Constant(lo_sh))

        return self.__class__(hi, lo)

    def calculate(self, hi, lo):
        return (hi << 8) | lo

    def bits(self):
        return 16

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
