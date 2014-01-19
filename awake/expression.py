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

import re, shlex
from awake.operator import binary_operators, functions
from awake.operand import Dereference, Constant, Register

class ExpressionError(Exception):
    def __init__(self, msg):
        self.msg = msg

def operator_priority(symbol):
    return operator.binary_operators[symbol][0]

def make_operator(symbol, arg1, arg2):
    return operator.binary_operators[symbol][1](arg1, arg2)

def arglist(lexer):
    out = [expression(lexer)]
    while True:
        token = lexer.get_token()
        if token == ',':
            out.append(expression(lexer))
        else:
            lexer.push_token(token)
            break
    return out

def function(name, args):
    needed_args = operator.functions[name][1]
    if len(args) != needed_args:
        raise ExpressionError('Expected ' + needed_args + ' args, got ' + len(args))
    return operator.functions[name][0](*args)

def dereference(target):
    return Dereference(target)

def constant(arg):
    if arg.startswith('0x'):
        value = int(arg, 16)
    else:
        value = int(arg)
    return Constant(value)

def register(arg):
    return Register(arg)

def expression(lexer):
    stack = [term(lexer)]

    def merge_top():
        arg2 = stack.pop()
        symbol = stack.pop()
        arg1 = stack.pop()
        stack.append(make_operator(symbol, arg1, arg2))

    while True:
        token = lexer.get_token()

        if token in ('=', '!', '<'):
            x = lookup(lexer)
            if x == '=':
                lexer.get_token()
                token += x

        if token in ('+', '-'):
            x = lookup(lexer)
            if x == '.':
                lexer.get_token()
                token += x

        if token in ('<', '>'):
            x = lookup(lexer)
            if x == token:
                lexer.get_token()
                token += x

        if token in operator.binary_operators:
            if len(stack) > 1 and operator_priority(stack[-2]) >= operator_priority(token):
                merge_top()
            stack.append(token)
            stack.append(term(lexer))
        else:
            lexer.push_token(token)
            break
    while len(stack) > 1 :
        merge_top()
    return stack[0]

def expect(lexer, expected):
    token = lexer.get_token()
    if token != expected:
        raise ExpressionError('Expected ' + expected + ' got ' + token)

def term(lexer):
    token = lexer.get_token()
    if token == '(':
        inner = expression(lexer)
        expect(lexer, ')')
        return inner
    elif token == '[':
        inner = expression(lexer)
        expect(lexer, ']')
        return dereference(inner)
    elif token in operator.functions:
        name = token
        expect(lexer, '(')
        args = arglist(lexer)
        expect(lexer, ')')
        return function(name, args)
    elif re.match('^(0x[0-9a-fA-F]+)|[0-9]+$', token):
        return constant(token)
    elif token in operator.binary_operators:
        raise ExpressionError('ERROR: unexpected operator ' + token)
    elif token:
        return register(token)

def lookup(lexer):
    token = lexer.get_token()
    lexer.push_token(token)
    return token

def parse(text):
    try:
        lexer = shlex.shlex(text)
        lexer.commenters = ''
        lexer.wordchars += '#'
        return expression(lexer)
    except ExpressionError as e:
        print('ERROR:', e.msg, 'in', text)
