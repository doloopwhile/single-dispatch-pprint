import re
import collections
from ._main import format_instance


@format_instance.register(dict)
def format_dict(object, pprinter_context):
    indent_per_level = pprinter_context.indent_per_level
    stream = pprinter_context.stream
    format_dict_items = pprinter_context._format_dict_items

    if not len(object) > 0:
        pprinter_context._format_default(object)
    else:
        stream.write('{')
        if indent_per_level > 1:
            stream.write((indent_per_level - 1) * ' ')

        sort = not isinstance(object, collections.OrderedDict)
        format_dict_items(object, sort=sort)
        stream.write('}')


def _format_sequence(object, pprinter_context, class_, startchar, endchar, sort, comma_for_one):
    stream = pprinter_context.stream
    indent_per_level = pprinter_context.indent_per_level

    if not (len(object) > 0 and getattr(type(object), "__repr__", None) is class_.__repr__):
        pprinter_context._format_default(object)
    else:
        length = len(object)

        stream.write(startchar)

        if indent_per_level > 1:
            stream.write((indent_per_level - 1) * ' ')
        if length:
            pprinter_context._format_items(
                object,
                sort=sort,
                additional_indent=len(startchar) - 1,
            )

        if comma_for_one and length == 1:
            stream.write(',')
        stream.write(endchar)


@format_instance.register(list)
def format_list(object, pprinter_context):
    _format_sequence(object, pprinter_context, list, '[', ']', False, False)

@format_instance.register(tuple)
def format_tuple(object, pprinter_context):
    _format_sequence(object, pprinter_context, tuple, '(', ')', False, True)

@format_instance.register(set)
def format_set(object, pprinter_context):
    if type(object) is set:
        startchar = '{'
        endchar = '}'
    else:
        startchar = type(object).__name__ + '({'
        endchar = '})'
    _format_sequence(object, pprinter_context, set, startchar, endchar, True, False)


@format_instance.register(frozenset)
def format_frozenset(object, pprinter_context):
    startchar = type(object).__name__ + '({'
    _format_sequence(object, pprinter_context, frozenset, startchar, '})', True, False)


@format_instance.register(str)
def format_str(object, pprinter_context):
    stream = pprinter_context.stream
    indent = pprinter_context.indent
    allowance = pprinter_context.allowance
    context = pprinter_context.context
    level = pprinter_context.level
    width = pprinter_context.width

    if not (len(object) > 0 and getattr(type(object), "__repr__", None) is str.__repr__):
        pprinter_context._format_default(object)
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

