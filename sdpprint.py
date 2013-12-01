# -*- coding: utf-8 -*-
import re
import sys as _sys
from collections import OrderedDict as _OrderedDict
from io import StringIO as _StringIO
import pprint as _pprint

import copy

from pprint import (
    isreadable,
    isrecursive,
    saferepr,
    _safe_repr,
    _safe_key,
    _safe_tuple,
)

def single_dispatch_pprint(object, stream=None, indent=1, width=80, depth=None, *,
           compact=False):
    printer = SingleDispatchPrettyPrinter(
        stream=stream, indent=indent, width=width, depth=depth,
        compact=compact)
    printer.pprint(object)

pprint = single_dispatch_pprint


def single_dispatch_pformat(object, indent=1, width=80, depth=None, *, compact=False):
    return SingleDispatchPrettyPrinter(indent=indent, width=width, depth=depth,
                         compact=compact).pformat(object)

pformat = single_dispatch_pformat


class SingleDispatchPrettyPrinter(_pprint.PrettyPrinter):
    def _format(self, object, stream, indent, allowance, context, level):
        level = level + 1
        SingleDispatchPrettyPrinterContext(
            self, object, stream, indent, allowance, context, level).format_self()


class SingleDispatchPrettyPrinterContext:
    def __init__(self, pprinter, object, stream, indent, allowance, context, level):
        self.pprinter = pprinter
        self.object = object
        self.stream = stream
        self.indent = indent
        self.allowance = allowance
        self.context = context
        self.level = level

        self.indent_per_level = self.pprinter._indent_per_level
        self.repr = self.pprinter._repr
        self.format = self.pprinter._format
        self.width = self.pprinter._width


    def format_self(self):
        if id(self.object) in self.context:
            self.stream.write(_recursion(self.object))
            self.pprinter._recursive = True
            self.pprinter._readable = False
            return
        return self._format_main()

    def _get_default(self):
        return self.pprinter._repr(self.object, self.context, self.level - 1)

    def _format_default(self):
        self.stream.write(self._get_default())

    def _format_main(self):
        rep = self.pprinter._repr(self.object, self.context, self.level - 1)
        max_width = self.pprinter._width - 1 - self.indent - self.allowance

        if len(rep) > max_width:
            self._format_main_seplines()
        else:
            self.stream.write(rep)

    def _format_items(self, additional_indent, sort):
        context = dict(self.context)
        context[id(self.object)] = 1

        items = list(self.object)
        if sort:
            items.sort(key=_safe_key)

        self.pprinter._format_items(
            items,
            self.stream,
            self.indent + self.indent_per_level + additional_indent,
            self.allowance + 1,
            context,
            self.level
        )

    def _format_dict_items(self, sort,):
        context = dict(self.context)
        context[id(self.object)] = 1

        items = list(self.object.items())
        if sort:
            items.sort(key=_safe_tuple)

        f = lambda ent:self.pprinter._format(
            ent,
            stream,
            indent + len(rep) + 2 + self.indent_per_level,
            allowance + 1,
            context,
            level
        )

        key, ent = items[0]
        rep = self.repr(key, context, level)
        stream.write('%s:' % (rep,))
        f(ent)

        if length > 1:
            for key, ent in items[1:]:
                rep = self.repr(key, context, level)
                stream.write(',\n%s%s: ' % (' '*indent, rep))
                f(ent)


    def _format_main_seplines(self):
        if isinstance(self.object, dict):
            _format_dict(self)
        elif isinstance(self.object, list):
            _format_list(self)
        elif isinstance(self.object, tuple):
            _format_tuple(self)
        elif isinstance(self.object, set):
            _format_set(self)
        elif isinstance(self.object, frozenset):
            _format_frozenset(self)
        elif isinstance(self.object, str):
            _format_str(self)
        else:
            self._format_default()

PrettyPrinter = SingleDispatchPrettyPrinter



def _format_dict(pprinter_context):
    indent_per_level = pprinter_context.indent_per_level
    repr = pprinter_context.repr
    format = pprinter_context.format
    object = pprinter_context.object
    stream = pprinter_context.stream
    indent = pprinter_context.indent
    allowance = pprinter_context.allowance
    context = pprinter_context.context
    level = pprinter_context.level
    format_dict_items = pprinter_context._format_dict_items

    if not (len(object) > 0 and getattr(type(object), "__repr__", None) is dict.__repr__):
        pprinter_context._format_default()
    else:
        stream.write('{')
        if indent_per_level > 1:
            stream.write((indent_per_level - 1) * ' ')

        sort = isinstance(object, _OrderedDict)
        format_dict_items(sort=sort)
        stream.write('}')


def _format_sequence(pprinter_context, class_, startchar, endchar, sort, comma_for_one):
    object = pprinter_context.object
    stream = pprinter_context.stream
    indent_per_level = pprinter_context.indent_per_level

    if not (len(object) > 0 and getattr(type(object), "__repr__", None) is class_.__repr__):
        pprinter_context._format_default()
    else:
        rep = pprinter_context._get_default()
        length = len(object)

        stream.write(startchar)

        if indent_per_level > 1:
            stream.write((indent_per_level - 1) * ' ')
        if length:
            pprinter_context._format_items(
                sort=sort,
                additional_indent=len(startchar) - 1,
            )

        if comma_for_one and length == 1:
            stream.write(',')
        stream.write(endchar)


def _format_list(pprinter_context):
    _format_sequence(pprinter_context, list, '[', ']', False, False)

def _format_tuple(pprinter_context):
    _format_sequence(pprinter_context, tuple, '(', ')', False, True)

def _format_set(pprinter_context):
    if type(pprinter_context.object) is set:
        startchar = '{'
        endchar = '}'
    else:
        startchar = type(pprinter_context.object).__name__ + '({'
        endchar = '})'
    _format_sequence(pprinter_context, set, startchar, endchar, True, False)

def _format_frozenset(pprinter_context):
    startchar = type(pprinter_context.object).__name__ + '({'
    _format_sequence(pprinter_context, frozenset, startchar, '})', True, False)


def _format_str(pprinter_context):
    object = pprinter_context.object
    stream = pprinter_context.stream
    indent = pprinter_context.indent
    allowance = pprinter_context.allowance
    context = pprinter_context.context
    level = pprinter_context.level
    width = pprinter_context.width

    if not (len(object) > 0 and getattr(type(object), "__repr__", None) is str.__repr__):
        pprinter_context._format_default()
    else:
        max_width = width - 1 - indent - allowance
        def _str_parts(s):
            """
            Return a list of string literals comprising the repr()
            of the given string using literal concatenation.
            """
            lines = s.splitlines(True)
            for i, line in enumerate(lines):
                rep = repr(line)
                if len(rep) <= max_width:
                    yield rep
                else:
                    # A list of alternating (non-space, space) strings
                    parts = re.split(r'(\s+)', line) + ['']
                    current = ''
                    for i in range(0, len(parts), 2):
                        part = parts[i] + parts[i+1]
                        candidate = current + part
                        if len(repr(candidate)) > max_width:
                            if current:
                                yield repr(current)
                            current = part
                        else:
                            current = candidate
                    if current:
                        yield repr(current)
        for i, rep in enumerate(_str_parts(object)):
            if i > 0:
                stream.write('\n' + ' '*indent)
            stream.write(rep)


