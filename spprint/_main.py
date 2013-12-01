# -*- coding: utf-8 -*-
from pprint import PrettyPrinter as _PrettyPrinter

from pprint import (
    _safe_key,
    _safe_tuple,
)

from functools import singledispatch


def pprint(object, stream=None, indent=1, width=80, depth=None, *,
           compact=False):
    return PrettyPrinter(
        stream=stream,
        indent=indent,
        width=width,
        depth=depth,
        compact=compact,
    ).pprint(object)


def pformat(object, indent=1, width=80, depth=None, *, compact=False):
    return PrettyPrinter(
        indent=indent,
        width=width,
        depth=depth,
        compact=compact
    ).pformat(object)


class PrettyPrinter(_PrettyPrinter):
    def _format(self, object, stream, indent, allowance, context, level):
        level = level + 1
        PrettyPrinterContext(
            self,
            stream,
            indent,
            allowance,
            context,
            level
        ).format(object)


class PrettyPrinterContext:
    def __init__(self, pprinter, stream, indent, allowance, context, level):
        self.pprinter = pprinter
        self.stream = stream
        self.indent = indent
        self.allowance = allowance
        self.context = context
        self.level = level

        self.indent_per_level = self.pprinter._indent_per_level
        self.repr = self.pprinter._repr
        self.width = self.pprinter._width


    def format(self, object):
        if id(object) in self.context:
            self.stream.write(_recursion(object))
            self.pprinter._recursive = True
            self.pprinter._readable = False
            return
        return self._format_main(object)

    def _format_default(self, object):
        rep = self.pprinter._repr(object, self.context, self.level - 1)
        self.stream.write(rep)

    def _format_main(self, object):
        rep = self.pprinter._repr(object, self.context, self.level - 1)
        max_width = self.pprinter._width - 1 - self.indent - self.allowance

        if len(rep) > max_width:
            self._format_main_seplines(object)
        else:
            self.stream.write(rep)

    def _format_items(self, object, additional_indent, sort):
        context = dict(self.context)
        context[id(object)] = 1

        items = list(object)
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

    def _format_dict_items(self, object, sort):
        indent = self.indent + self.indent_per_level

        context = dict(self.context)
        context[id(object)] = 1

        items = list(object.items())
        if sort:
            items.sort(key=_safe_tuple)

        for i, (key, ent) in enumerate(items):
            rep = self.pprinter._repr(key, context, self.level)
            if i == 0:
                self.stream.write('%s: ' % (rep,))
            else:
                self.stream.write(',\n%s%s: ' % (' '*indent, rep))
            self.pprinter._format(
                ent,
                self.stream,
                indent + len(rep) + 2,
                self.allowance + 1,
                context,
                self.level
            )


    def _format_main_seplines(self, object):
        format_instance(object, self)


@singledispatch
def format_instance(object, pprinter_context):
    pprinter_context._format_default(object)
